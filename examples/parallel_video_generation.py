#!/usr/bin/env python3
"""
并行视频生成示例
演示如何使用新的并行批处理器和GPU加速功能
"""

import sys
import os
from pathlib import Path

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tasks.task_queue import TaskQueue, VideoTask
from tasks.parallel_batch_processor import ParallelBatchProcessor
from video_engine.gpu_accelerator import GPUVideoAccelerator
from config_loader import ConfigLoader


def mock_video_generator(task):
    """
    模拟视频生成器
    在实际使用中，这里会是真正的视频生成逻辑
    """
    import time
    import random

    # 模拟处理时间 (0.1-0.5秒，加快演示)
    process_time = random.uniform(0.1, 0.5)
    time.sleep(process_time)

    # 模拟输出路径
    output_path = f"output/{task.task_id}.mp4"

    # 确保输出目录存在
    Path("output").mkdir(exist_ok=True)

    # 创建一个空的输出文件作为标记
    Path(output_path).touch()

    return {
        "output_path": output_path,
        "duration": process_time,
        "status": "completed"
    }


def main():
    """主函数"""
    print("🚀 并行视频生成示例")
    print("=" * 50)

    # 1. 初始化配置
    print("📋 加载配置...")
    config_path = Path("config/default_config.yaml")
    if not config_path.exists():
        print("❌ 配置文件不存在，使用默认配置")
        config = {
            'performance': {
                'threading': {
                    'enabled': True,
                    'max_workers': 'auto',
                    'task_timeout': 30,
                    'max_concurrent_tasks': 3
                },
                'gpu': {
                    'enabled': True,
                    'device': 'auto'
                }
            },
            'log_level': 'INFO'
        }
    else:
        config_loader = ConfigLoader(str(config_path))
        config = config_loader.config

    # 2. 初始化GPU加速器
    print("🎮 初始化GPU加速器...")
    gpu_accelerator = GPUVideoAccelerator(config.get('performance', {}).get('gpu', {}))
    print(f"   GPU可用: {gpu_accelerator.is_gpu_available()}")
    if gpu_accelerator.is_gpu_available():
        gpu_info = gpu_accelerator.get_gpu_info()
        print(f"   GPU型号: {gpu_info['name']}")
        print(f"   GPU内存: {gpu_info['memory_total_gb']:.1f}GB")
    else:
        print("   使用CPU处理")

    # 3. 创建任务队列和任务
    print("📝 创建任务队列...")
    task_queue = TaskQueue()

    # 创建示例任务
    sample_scripts = [
        "欢迎来到AI视频生成的世界！",
        "多线程处理可以显著提升性能。",
        "GPU加速让视频渲染更快更流畅。"
    ]

    tasks = []
    for i, script in enumerate(sample_scripts):
        task = VideoTask(
            task_id=f"demo_task_{i+1:02d}",
            script_text=script,
            output_path=f"output/demo_video_{i+1:02d}.mp4"
        )
        task_queue.add_task(task)
        tasks.append(task)
        print(f"   添加任务: {task.task_id}")

    print(f"✅ 创建了 {len(tasks)} 个视频生成任务")

    # 4. 初始化并行批处理器
    print("⚡ 初始化并行批处理器...")
    processor = ParallelBatchProcessor(
        task_queue=task_queue,
        config=config,
        video_generator=mock_video_generator
    )

    print("🏃 开始并行处理任务...")
    print(f"   最大工作线程数: {processor.max_workers}")
    print(f"   任务超时时间: {processor.task_timeout}秒")

    # 5. 执行批处理
    try:
        result = processor.process_batch(tasks)

        # 6. 显示结果
        print("\n🎉 批处理完成!")
        print("=" * 50)
        print(f"📊 处理统计:")
        print(f"   总任务数: {result.total_tasks}")
        print(f"   成功任务: {result.successful_tasks}")
        print(f"   失败任务: {result.failed_tasks}")
        print(f"   总耗时: {result.total_duration:.2f}秒")
        print(f"   平均任务耗时: {result.average_task_duration:.2f}秒")
        print(f"   处理吞吐量: {result.throughput:.2f} tasks/秒")
        print(f"   峰值内存使用: {result.peak_memory_usage} MB")

        if result.successful_tasks == result.total_tasks:
            print("✅ 所有任务处理成功!")
        else:
            print(f"⚠️  有 {result.failed_tasks} 个任务失败")

        # 显示详细结果
        print("\n📋 任务详情:")
        for task_result in result.results:
            status = "✅" if task_result.success else "❌"
            print(f"   {status} {task_result.task_id}: {task_result.duration:.2f}秒")

    except KeyboardInterrupt:
        print("\n⏹️  用户中断处理")
    except Exception as e:
        print(f"\n❌ 处理过程中发生错误: {e}")
    finally:
        # 清理资源
        processor.shutdown()
        print("🧹 资源清理完成")

    # 7. 显示系统信息
    print("\n💻 系统信息:")
    system_info = GPUVideoAccelerator.get_system_info()
    print(f"   平台: {system_info['platform']}")
    print(f"   CPU核心数: {system_info['cpu_count']}")
    print(f"   系统内存: {system_info['memory_total_gb']:.1f}GB")
    print(f"   GPU可用: {system_info['gpu_available']}")
    if system_info['gpu_available']:
        print(f"   GPU数量: {system_info['gpu_count']}")
        for gpu in system_info['gpus']:
            if 'name' in gpu:
                print(f"   GPU: {gpu['name']} ({gpu['memory_gb']:.1f}GB)")


if __name__ == "__main__":
    main()
