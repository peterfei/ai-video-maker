"""
批量处理器
处理视频生成任务队列
"""

from pathlib import Path
from typing import Dict, Any, Optional, Callable
import concurrent.futures
import traceback
from datetime import datetime

from tasks.task_queue import TaskQueue, VideoTask, TaskStatus
from utils import setup_logger, ProgressTracker


class BatchProcessor:
    """批量处理器类"""

    def __init__(
        self,
        task_queue: TaskQueue,
        config: Dict[str, Any],
        video_generator: Optional[Callable] = None
    ):
        """
        初始化批处理器

        Args:
            task_queue: 任务队列
            config: 配置字典
            video_generator: 视频生成函数
        """
        self.task_queue = task_queue
        self.config = config
        self.video_generator = video_generator

        self.max_workers = config.get('max_workers', 2)
        self.retry_on_error = config.get('retry_on_error', True)
        self.retry_times = config.get('retry_times', 3)
        self.save_logs = config.get('save_logs', True)

        self.logger = setup_logger("batch_processor", config.get('log_level', 'INFO'))

        # 统计信息
        self.stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'start_time': None,
            'end_time': None
        }

    def process_single_task(self, task: VideoTask) -> bool:
        """
        处理单个任务

        Args:
            task: VideoTask对象

        Returns:
            是否成功
        """
        self.logger.info(f"开始处理任务: {task.task_id}")

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

                    self.logger.info(f"任务完成: {task.task_id}")
                    self.stats['successful'] += 1
                    return True
                else:
                    raise ValueError("未设置视频生成器")

            except Exception as e:
                retry_count += 1
                error_msg = str(e)

                self.logger.error(f"任务失败 ({retry_count}/{max_retries}): {task.task_id}")
                self.logger.error(f"错误信息: {error_msg}")

                if retry_count >= max_retries:
                    # 达到最大重试次数，标记为失败
                    self.task_queue.update_task_status(
                        task.task_id,
                        TaskStatus.FAILED,
                        error_message=error_msg
                    )

                    self.stats['failed'] += 1

                    # 保存错误日志
                    if self.save_logs:
                        self._save_error_log(task, error_msg)

                    return False

        return False

    def process_all_pending(self) -> Dict[str, Any]:
        """
        处理所有待处理任务

        Returns:
            处理结果统计
        """
        pending_tasks = self.task_queue.get_pending_tasks()

        if not pending_tasks:
            self.logger.info("没有待处理的任务")
            return self.stats

        self.logger.info(f"开始批量处理 {len(pending_tasks)} 个任务")

        self.stats['start_time'] = datetime.now()
        self.stats['total_processed'] = 0
        self.stats['successful'] = 0
        self.stats['failed'] = 0

        # 使用线程池处理任务
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            futures = {
                executor.submit(self.process_single_task, task): task
                for task in pending_tasks
            }

            # 使用进度条
            with ProgressTracker(len(futures), "处理视频任务") as progress:
                for future in concurrent.futures.as_completed(futures):
                    task = futures[future]

                    try:
                        result = future.result()
                        self.stats['total_processed'] += 1
                    except Exception as e:
                        self.logger.error(f"任务执行异常: {task.task_id}")
                        self.logger.error(traceback.format_exc())
                        self.stats['failed'] += 1
                        self.stats['total_processed'] += 1

                    progress.update(1)

        self.stats['end_time'] = datetime.now()

        # 计算总时长
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        self.stats['duration_seconds'] = duration

        self.logger.info(f"批量处理完成:")
        self.logger.info(f"  总处理: {self.stats['total_processed']}")
        self.logger.info(f"  成功: {self.stats['successful']}")
        self.logger.info(f"  失败: {self.stats['failed']}")
        self.logger.info(f"  耗时: {duration:.2f}秒")

        return self.stats

    def process_tasks_sequentially(self) -> Dict[str, Any]:
        """
        顺序处理任务（不使用并行）

        Returns:
            处理结果统计
        """
        pending_tasks = self.task_queue.get_pending_tasks()

        if not pending_tasks:
            self.logger.info("没有待处理的任务")
            return self.stats

        self.logger.info(f"开始顺序处理 {len(pending_tasks)} 个任务")

        self.stats['start_time'] = datetime.now()
        self.stats['total_processed'] = 0
        self.stats['successful'] = 0
        self.stats['failed'] = 0

        with ProgressTracker(len(pending_tasks), "处理视频任务") as progress:
            for task in pending_tasks:
                self.process_single_task(task)
                self.stats['total_processed'] += 1
                progress.update(1)

        self.stats['end_time'] = datetime.now()
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        self.stats['duration_seconds'] = duration

        self.logger.info(f"顺序处理完成:")
        self.logger.info(f"  总处理: {self.stats['total_processed']}")
        self.logger.info(f"  成功: {self.stats['successful']}")
        self.logger.info(f"  失败: {self.stats['failed']}")
        self.logger.info(f"  耗时: {duration:.2f}秒")

        return self.stats

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

        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"任务ID: {task.task_id}\n")
            f.write(f"时间: {datetime.now().isoformat()}\n")
            f.write(f"脚本路径: {task.script_path}\n")
            f.write(f"素材目录: {task.materials_dir}\n")
            f.write(f"输出路径: {task.output_path}\n")
            f.write(f"\n错误信息:\n{error_msg}\n")
            f.write(f"\n堆栈跟踪:\n{traceback.format_exc()}\n")

        self.logger.info(f"错误日志已保存: {log_file}")

    def retry_failed_tasks(self) -> Dict[str, Any]:
        """
        重试失败的任务

        Returns:
            处理结果统计
        """
        failed_tasks = self.task_queue.get_tasks_by_status(TaskStatus.FAILED)

        if not failed_tasks:
            self.logger.info("没有失败的任务需要重试")
            return self.stats

        self.logger.info(f"重试 {len(failed_tasks)} 个失败任务")

        # 将失败任务状态改回待处理
        for task in failed_tasks:
            self.task_queue.update_task_status(task.task_id, TaskStatus.PENDING)

        # 处理任务
        return self.process_all_pending()

    def get_progress(self) -> Dict[str, Any]:
        """
        获取处理进度

        Returns:
            进度信息
        """
        queue_stats = self.task_queue.get_statistics()

        progress = {
            'queue_stats': queue_stats,
            'processing_stats': self.stats,
            'progress_percentage': 0.0
        }

        if queue_stats['total'] > 0:
            completed = queue_stats['completed'] + queue_stats['failed']
            progress['progress_percentage'] = (completed / queue_stats['total']) * 100

        return progress

    def cancel_all_pending(self) -> int:
        """
        取消所有待处理任务

        Returns:
            取消的任务数量
        """
        pending_tasks = self.task_queue.get_pending_tasks()

        count = 0
        for task in pending_tasks:
            if self.task_queue.cancel_task(task.task_id):
                count += 1

        self.logger.info(f"已取消 {count} 个待处理任务")

        return count
