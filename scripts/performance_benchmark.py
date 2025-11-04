#!/usr/bin/env python3
"""
性能基准测试脚本
对比传统批处理器和并行批处理器的性能差异
"""

import sys
import time
import os
from pathlib import Path
from typing import Dict, List, Any
import json

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tasks.task_queue import TaskQueue, VideoTask
from tasks.batch_processor import BatchProcessor
from tasks.parallel_batch_processor import ParallelBatchProcessor
from video_engine.gpu_accelerator import GPUVideoAccelerator


def mock_video_generator(task):
    """模拟视频生成器（用于基准测试）"""
    import random

    # 模拟不同的处理时间（更真实的分布）
    base_time = random.uniform(1.0, 3.0)  # 基础处理时间1-3秒

    # 模拟I/O等待
    time.sleep(base_time * 0.1)  # 10%的I/O时间

    # 模拟CPU密集型处理
    start = time.time()
    while time.time() - start < base_time * 0.8:  # 80%的CPU时间
        _ = [i ** 2 for i in range(1000)]  # 轻量级计算

    # 模拟最终I/O
    time.sleep(base_time * 0.1)

    # 模拟输出
    output_path = f"output/benchmark_{task.task_id}.mp4"
    Path("output").mkdir(exist_ok=True)
    Path(output_path).touch()

    return {
        "output_path": output_path,
        "duration": base_time,
        "status": "completed",
        "mock": True
    }


def create_test_tasks(count: int = 10) -> List[VideoTask]:
    """创建测试任务"""
    tasks = []
    for i in range(count):
        task = VideoTask(
            task_id=f"bench_{i+1:03d}",
            script_text=f"这是基准测试任务 {i+1} 的脚本内容，用于性能测试和对比分析。",
            output_path=f"output/bench_{i+1:03d}.mp4"
        )
        tasks.append(task)
    return tasks


def benchmark_processor(processor_class, config: Dict[str, Any], tasks: List[VideoTask], name: str) -> Dict[str, Any]:
    """对处理器进行基准测试"""
    print(f"\n🏃 开始 {name} 基准测试...")
    print(f"   任务数量: {len(tasks)}")
    print(f"   处理器: {processor_class.__name__}")

    # 创建任务队列
    queue = TaskQueue()

    # 添加任务到队列
    for task in tasks:
        queue.add_task(task)

    # 初始化处理器
    if processor_class == ParallelBatchProcessor:
        processor = processor_class(
            task_queue=queue,
            config=config.get('performance', {}),
            video_generator=mock_video_generator
        )
    else:
        processor = processor_class(
            task_queue=queue,
            config=config.get('batch', {}),
            video_generator=mock_video_generator
        )

    # 执行基准测试
    start_time = time.time()

    try:
        if processor_class == ParallelBatchProcessor:
            result = processor.process_batch(tasks)
            stats = {
                'total_processed': result.total_tasks,
                'successful': result.successful_tasks,
                'failed': result.failed_tasks,
                'total_duration': result.total_duration,
                'throughput': result.throughput,
                'peak_memory_usage': result.peak_memory_usage
            }
        else:
            stats = processor.process_all_pending()

        end_time = time.time()
        wall_time = end_time - start_time

        # 计算额外指标
        if processor_class == ParallelBatchProcessor:
            efficiency = stats['throughput'] * stats['total_duration'] / len(tasks)
        else:
            efficiency = len(tasks) / wall_time if wall_time > 0 else 0

        benchmark_result = {
            'processor': name,
            'tasks_count': len(tasks),
            'wall_time': wall_time,
            'total_duration': stats.get('total_duration', wall_time),
            'throughput': stats.get('throughput', len(tasks) / wall_time if wall_time > 0 else 0),
            'efficiency': efficiency,
            'successful': stats['successful'],
            'failed': stats['failed'],
            'peak_memory_mb': stats.get('peak_memory_usage', 0),
            'success_rate': stats['successful'] / len(tasks) * 100 if len(tasks) > 0 else 0
        }

        print(f"✅ {name} 测试完成")
        print(f"   总耗时: {wall_time:.2f}秒")
        print(f"   处理任务: {stats['successful']}/{len(tasks)}")
        print(f"   吞吐量: {benchmark_result['throughput']:.2f} tasks/秒")

        # 关闭并行处理器
        if hasattr(processor, 'shutdown'):
            processor.shutdown()

        return benchmark_result

    except Exception as e:
        print(f"❌ {name} 测试失败: {e}")
        return {
            'processor': name,
            'error': str(e),
            'wall_time': time.time() - start_time
        }


def run_quick_test():
    """运行快速测试"""
    print("⚡ 快速性能测试")

    # 简单配置
    config = {
        'batch': {'max_workers': 1, 'retry_on_error': False, 'save_logs': False},
        'performance': {
            'threading': {'enabled': True, 'max_workers': 3, 'task_timeout': 10},
            'gpu': {'enabled': False}  # 快速测试禁用GPU
        },
        'log_level': 'ERROR'
    }

    # 创建少量测试任务
    tasks = create_test_tasks(3)

    print(f"测试 {len(tasks)} 个任务...")

    # 测试传统处理器
    traditional_result = benchmark_processor(
        BatchProcessor, config, tasks.copy(), "传统处理器"
    )

    time.sleep(0.5)

    # 测试并行处理器
    parallel_result = benchmark_processor(
        ParallelBatchProcessor, config, tasks.copy(), "并行处理器"
    )

    # 显示对比
    if 'error' not in traditional_result and 'error' not in parallel_result:
        speedup = traditional_result['wall_time'] / parallel_result['wall_time']
        print(f"   加速比: {speedup:.2f}x")
    else:
        print("❌ 测试中出现错误")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        run_quick_test()
    else:
        print("请使用 --quick 参数运行快速测试")
        print("完整基准测试功能待完善")
