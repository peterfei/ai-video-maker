"""
高级并行批处理器
支持智能资源管理和GPU加速的视频批量处理
"""

import dataclasses
import concurrent.futures
import threading
import psutil
import time
from pathlib import Path
from typing import Dict, Any, Optional, Callable, List, Tuple
from datetime import datetime
import traceback
import logging

from tasks.task_queue import TaskQueue, VideoTask, TaskStatus
from utils import setup_logger, ProgressTracker


@dataclasses.dataclass
class TaskResult:
    """任务执行结果"""
    task_id: str
    success: bool
    duration: float
    error_message: Optional[str] = None
    result_data: Optional[Dict[str, Any]] = None


@dataclasses.dataclass
class BatchResult:
    """批处理结果"""
    total_tasks: int
    successful_tasks: int
    failed_tasks: int
    total_duration: float
    average_task_duration: float
    throughput: float  # tasks per second
    peak_memory_usage: int  # MB
    results: List[TaskResult]


class ResourceManager:
    """资源管理器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._lock = threading.Lock()
        self._active_tasks = 0
        self._memory_usage = 0

    def calculate_optimal_workers(self) -> int:
        """计算最优工作线程数"""
        cpu_count = psutil.cpu_count(logical=True)
        memory_gb = psutil.virtual_memory().total / (1024**3)

        # 基础线程数：CPU核心数的2/3
        base_workers = max(1, int(cpu_count * 0.67))

        # 内存限制：假设每个线程需要2GB内存
        memory_workers = max(1, int(memory_gb / 2))

        # 配置限制
        config_max = self.config.get('performance', {}).get('threading', {}).get('max_workers', 8)
        if isinstance(config_max, str) and config_max.lower() == 'auto':
            config_max = min(base_workers, memory_workers)
        elif isinstance(config_max, int):
            config_max = min(config_max, base_workers, memory_workers)

        return max(1, config_max)

    def can_start_task(self, estimated_memory_mb: int = 512) -> bool:
        """检查是否可以启动新任务"""
        with self._lock:
            max_concurrent = self.config.get('performance', {}).get('threading', {}).get('max_concurrent_tasks', 4)

            if self._active_tasks >= max_concurrent:
                return False

            # 检查内存使用
            current_memory = psutil.virtual_memory()
            memory_limit = self.config.get('performance', {}).get('threading', {}).get('worker_memory_limit', 2048)

            if (current_memory.used / (1024**2) + estimated_memory_mb) > memory_limit:
                return False

            self._active_tasks += 1
            self._memory_usage += estimated_memory_mb
            return True

    def task_completed(self, memory_used_mb: int = 512) -> None:
        """任务完成回调"""
        with self._lock:
            self._active_tasks = max(0, self._active_tasks - 1)
            self._memory_usage = max(0, self._memory_usage - memory_used_mb)

    def get_resource_usage(self) -> Dict[str, Any]:
        """获取资源使用情况"""
        with self._lock:
            return {
                'active_tasks': self._active_tasks,
                'estimated_memory_usage_mb': self._memory_usage,
                'cpu_percent': psutil.cpu_percent(interval=0.1),
                'memory_percent': psutil.virtual_memory().percent
            }


class ParallelBatchProcessor:
    """支持智能资源管理的并行批处理器"""

    def __init__(
        self,
        task_queue: TaskQueue,
        config: Dict[str, Any],
        video_generator: Optional[Callable] = None
    ):
        """
        初始化并行批处理器

        Args:
            task_queue: 任务队列
            config: 配置字典
            video_generator: 视频生成函数
        """
        self.task_queue = task_queue
        self.config = config
        self.video_generator = video_generator

        # 资源管理
        self.resource_manager = ResourceManager(config)
        self.max_workers = self.resource_manager.calculate_optimal_workers()

        # 性能配置
        perf_config = config.get('performance', {})
        threading_config = perf_config.get('threading', {})

        self.task_timeout = threading_config.get('task_timeout', 3600)
        self.retry_on_error = threading_config.get('retry_on_error', True)
        self.retry_times = threading_config.get('retry_times', 3)
        self.save_logs = threading_config.get('save_logs', True)

        # 线程池
        self.executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=self.max_workers,
            thread_name_prefix="VideoWorker"
        )

        # 日志和监控
        self.logger = setup_logger("parallel_batch_processor", config.get('log_level', 'INFO'))
        self._shutdown_event = threading.Event()

        # 统计信息
        self.stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'start_time': None,
            'end_time': None,
            'peak_memory_usage': 0,
            'average_task_duration': 0.0
        }

        self.logger.info(f"初始化并行批处理器: max_workers={self.max_workers}, timeout={self.task_timeout}s")

    def process_batch(self, tasks: Optional[List[VideoTask]] = None) -> BatchResult:
        """
        并行处理视频任务批次

        Args:
            tasks: 要处理的视频任务列表，如果为None则处理所有待处理任务

        Returns:
            批处理结果
        """
        if tasks is None:
            tasks = self.task_queue.get_pending_tasks()

        if not tasks:
            self.logger.info("没有待处理的任务")
            return BatchResult(
                total_tasks=0,
                successful_tasks=0,
                failed_tasks=0,
                total_duration=0.0,
                average_task_duration=0.0,
                throughput=0.0,
                peak_memory_usage=0,
                results=[]
            )

        self.logger.info(f"开始并行处理 {len(tasks)} 个任务 (max_workers={self.max_workers})")
        start_time = time.time()

        # 重置统计信息
        self.stats.update({
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'start_time': datetime.now(),
            'peak_memory_usage': 0
        })

        # 提交任务到线程池
        future_to_task = {}
        for task in tasks:
            if self._shutdown_event.is_set():
                break

            # 等待资源可用
            while not self.resource_manager.can_start_task():
                time.sleep(0.1)
                if self._shutdown_event.is_set():
                    break

            future = self.executor.submit(self._process_single_task, task)
            future_to_task[future] = task

        # 收集结果
        results = []
        completed_count = 0

        with ProgressTracker(len(future_to_task), "并行处理视频任务") as progress:
            for future in concurrent.futures.as_completed(future_to_task):
                if self._shutdown_event.is_set():
                    future.cancel()
                    continue

                task = future_to_task[future]
                task_start_time = time.time()

                try:
                    task_result = future.result(timeout=self.task_timeout)
                    results.append(task_result)

                    if task_result.success:
                        self.stats['successful'] += 1
                    else:
                        self.stats['failed'] += 1

                except concurrent.futures.TimeoutError:
                    error_msg = f"任务执行超时 ({self.task_timeout}s)"
                    self.logger.error(f"{error_msg}: {task.task_id}")
                    self.task_queue.update_task_status(
                        task.task_id,
                        TaskStatus.FAILED,
                        error_message=error_msg
                    )

                    task_result = TaskResult(
                        task_id=task.task_id,
                        success=False,
                        duration=time.time() - task_start_time,
                        error_message=error_msg
                    )
                    results.append(task_result)
                    self.stats['failed'] += 1

                except Exception as e:
                    error_msg = str(e)
                    self.logger.error(f"任务执行异常: {task.task_id} - {error_msg}")
                    self.logger.error(traceback.format_exc())

                    task_result = TaskResult(
                        task_id=task.task_id,
                        success=False,
                        duration=time.time() - task_start_time,
                        error_message=error_msg
                    )
                    results.append(task_result)
                    self.stats['failed'] += 1

                self.stats['total_processed'] += 1

                # 更新资源使用情况
                resource_usage = self.resource_manager.get_resource_usage()
                self.stats['peak_memory_usage'] = max(
                    self.stats['peak_memory_usage'],
                    resource_usage['estimated_memory_usage_mb']
                )

                # 释放资源
                self.resource_manager.task_completed()

                completed_count += 1
                progress.update(1)

                # 定期记录进度
                if completed_count % max(1, len(tasks) // 10) == 0:
                    self._log_progress(completed_count, len(tasks), time.time() - start_time)

        # 计算最终统计信息
        end_time = time.time()
        total_duration = end_time - start_time

        batch_result = BatchResult(
            total_tasks=len(tasks),
            successful_tasks=self.stats['successful'],
            failed_tasks=self.stats['failed'],
            total_duration=total_duration,
            average_task_duration=total_duration / len(tasks) if tasks else 0.0,
            throughput=len(tasks) / total_duration if total_duration > 0 else 0.0,
            peak_memory_usage=self.stats['peak_memory_usage'],
            results=results
        )

        self.stats['end_time'] = datetime.now()

        # 记录最终结果
        self.logger.info("=" * 50)
        self.logger.info("并行批处理完成:")
        self.logger.info(f"  总任务数: {batch_result.total_tasks}")
        self.logger.info(f"  成功: {batch_result.successful_tasks}")
        self.logger.info(f"  失败: {batch_result.failed_tasks}")
        self.logger.info(f"  总耗时: {batch_result.total_duration:.2f}s")
        self.logger.info(f"  平均任务耗时: {batch_result.average_task_duration:.2f}s")
        self.logger.info(f"  处理吞吐量: {batch_result.throughput:.2f} tasks/s")
        self.logger.info(f"  峰值内存使用: {batch_result.peak_memory_usage} MB")
        self.logger.info("=" * 50)

        return batch_result

    def _process_single_task(self, task: VideoTask) -> TaskResult:
        """
        处理单个视频任务

        Args:
            task: VideoTask对象

        Returns:
            任务结果
        """
        task_start_time = time.time()

        try:
            self.logger.debug(f"开始处理任务: {task.task_id}")

            # 更新状态为处理中
            self.task_queue.update_task_status(task.task_id, TaskStatus.PROCESSING)

            retry_count = 0
            max_retries = self.retry_times if self.retry_on_error else 1

            while retry_count < max_retries:
                try:
                    # 调用视频生成器
                    if self.video_generator:
                        result = self.video_generator(task)

                        # 更新任务状态为完成
                        self.task_queue.update_task_status(
                            task.task_id,
                            TaskStatus.COMPLETED,
                            result=result
                        )

                        duration = time.time() - task_start_time
                        self.logger.debug(f"任务完成: {task.task_id} ({duration:.2f}s)")

                        return TaskResult(
                            task_id=task.task_id,
                            success=True,
                            duration=duration,
                            result_data=result
                        )
                    else:
                        raise ValueError("未设置视频生成器")

                except Exception as e:
                    retry_count += 1
                    error_msg = str(e)

                    self.logger.warning(f"任务失败 ({retry_count}/{max_retries}): {task.task_id} - {error_msg}")

                    if retry_count >= max_retries:
                        # 达到最大重试次数，标记为失败
                        self.task_queue.update_task_status(
                            task.task_id,
                            TaskStatus.FAILED,
                            error_message=error_msg
                        )

                        # 保存错误日志
                        if self.save_logs:
                            self._save_error_log(task, error_msg)

                        duration = time.time() - task_start_time
                        return TaskResult(
                            task_id=task.task_id,
                            success=False,
                            duration=duration,
                            error_message=error_msg
                        )

        except Exception as e:
            error_msg = f"任务处理异常: {str(e)}"
            self.logger.error(f"任务异常: {task.task_id} - {error_msg}")
            self.logger.error(traceback.format_exc())

            duration = time.time() - task_start_time
            return TaskResult(
                task_id=task.task_id,
                success=False,
                duration=duration,
                error_message=error_msg
            )

    def _log_progress(self, completed: int, total: int, elapsed: float) -> None:
        """记录处理进度"""
        if total == 0:
            return

        progress_percent = (completed / total) * 100
        remaining = total - completed
        avg_time_per_task = elapsed / completed if completed > 0 else 0
        estimated_remaining = remaining * avg_time_per_task

        self.logger.info(
            f"进度: {completed}/{total} ({progress_percent:.1f}%) | "
            f"耗时: {elapsed:.1f}s | 预计剩余: {estimated_remaining:.1f}s"
        )

    def _save_error_log(self, task: VideoTask, error_msg: str) -> None:
        """
        保存错误日志

        Args:
            task: 任务对象
            error_msg: 错误信息
        """
        log_dir = Path("output/logs")
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / f"error_{task.task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(f"任务ID: {task.task_id}\\n")
                f.write(f"时间: {datetime.now().isoformat()}\\n")
                f.write(f"脚本路径: {task.script_path}\\n")
                f.write(f"素材目录: {task.materials_dir}\\n")
                f.write(f"输出路径: {task.output_path}\\n")
                f.write(f"配置覆盖: {task.config_override}\\n")
                f.write(f"\\n错误信息:\\n{error_msg}\\n")
                f.write(f"\\n堆栈跟踪:\\n{traceback.format_exc()}\\n")

            self.logger.info(f"错误日志已保存: {log_file}")
        except Exception as e:
            self.logger.error(f"保存错误日志失败: {e}")

    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        resource_usage = self.resource_manager.get_resource_usage()

        return {
            'thread_pool': {
                'max_workers': self.max_workers,
                'active_threads': len([t for t in threading.enumerate() if t.name.startswith('VideoWorker')])
            },
            'resource_usage': resource_usage,
            'processing_stats': self.stats.copy(),
            'config': {
                'task_timeout': self.task_timeout,
                'retry_on_error': self.retry_on_error,
                'retry_times': self.retry_times
            }
        }

    def shutdown(self, wait: bool = True) -> None:
        """关闭处理器"""
        self.logger.info("正在关闭并行批处理器...")

        self._shutdown_event.set()

        # 关闭线程池
        self.executor.shutdown(wait=wait)

        self.logger.info("并行批处理器已关闭")

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.shutdown(wait=True)
