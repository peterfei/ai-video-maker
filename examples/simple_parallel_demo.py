#!/usr/bin/env python3
"""
简单的并行批处理演示
"""

import sys
import time
import random
from pathlib import Path

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tasks.task_queue import TaskQueue, VideoTask
from tasks.parallel_batch_processor import ParallelBatchProcessor


def simple_video_generator(task):
    """简单的视频生成器"""
    # 模拟处理时间
    process_time = random.uniform(0.2, 0.8)
    time.sleep(process_time)

    return {
        "output_path": f"output/{task.task_id}.mp4",
        "duration": process_time,
        "status": "completed"
    }


def main():
    """主演示函数"""
    print("🚀 简单的并行批处理演示")
    print("=" * 40)

    # 简单配置
    config = {
        'performance': {
            'threading': {
                'enabled': True,
                'max_workers': 3,
                'task_timeout': 10,
                'max_concurrent_tasks': 2
            }
        },
        'log_level': 'WARNING'  # 减少日志输出
    }

    # 创建任务队列
    task_queue = TaskQueue()

    # 创建一些测试任务
    tasks = []
    for i in range(5):
        task = VideoTask(
            task_id=f"demo_{i+1:02d}",
            script_text=f"这是测试任务 {i+1}",
            output_path=f"output/demo_{i+1:02d}.mp4"
        )
        task_queue.add_task(task)
        tasks.append(task)

    print(f"📝 创建了 {len(tasks)} 个任务")

    # 创建并行处理器
    processor = ParallelBatchProcessor(
        task_queue=task_queue,
        config=config,
        video_generator=simple_video_generator
    )

    print(f"⚡ 使用 {processor.max_workers} 个工作线程")

    try:
        # 执行批处理
        result = processor.process_batch(tasks)

        # 显示结果
        print("\n✅ 处理完成!")
        print(f"总任务数: {result.total_tasks}")
        print(f"成功: {result.successful_tasks}")
        print(f"失败: {result.failed_tasks}")
        print(f"总耗时: {result.total_duration:.2f}秒")
        print(f"平均耗时: {result.average_task_duration:.2f}秒")
        print(f"吞吐量: {result.throughput:.2f} tasks/秒")

        # 显示每个任务的结果
        print("\n📋 任务详情:")
        for task_result in result.results:
            status = "✅" if task_result.success else "❌"
            print(".2f")

    except Exception as e:
        print(f"❌ 错误: {e}")
    finally:
        processor.shutdown()

    print("🎉 演示完成!")


if __name__ == "__main__":
    main()
