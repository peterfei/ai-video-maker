#!/usr/bin/env python3
"""
GPU vs CPU 性能对比测试
测试M4 GPU加速相对于CPU的性能提升
"""

import sys
import time
from pathlib import Path
import tempfile

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config_loader import get_config
from video_engine.gpu_accelerator import GPUVideoAccelerator
from main import VideoFactory


def run_benchmark(use_gpu: bool, output_suffix: str):
    """运行单次基准测试"""
    print(f"\n{'='*60}")
    print(f"{'GPU 加速模式' if use_gpu else 'CPU 模式'} 性能测试")
    print(f"{'='*60}")

    # 加载配置
    config_loader = get_config("config/default_config.yaml")

    # 获取配置字典
    config_dict = config_loader.config

    # 修改GPU配置
    if 'performance' not in config_dict:
        config_dict['performance'] = {}
    if 'gpu' not in config_dict['performance']:
        config_dict['performance']['gpu'] = {}

    config_dict['performance']['gpu']['enabled'] = use_gpu

    # 创建临时配置文件
    import yaml
    temp_config = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
    yaml.dump(config_dict, temp_config)
    temp_config.close()

    try:
        # 创建视频工厂
        factory = VideoFactory(temp_config.name)

        # 准备测试脚本
        test_script = """人工智能正在改变世界。
深度学习技术的发展推动了AI的进步。
计算机视觉和自然语言处理取得了重大突破。
未来AI将在更多领域发挥重要作用。"""

        # 记录开始时间
        start_time = time.time()

        # 生成视频
        output_path = f"output/benchmark_{output_suffix}.mp4"
        result = factory.generate_video(
            script_text=test_script,
            output_path=output_path,
            title=f"benchmark_{output_suffix}"
        )

        # 记录结束时间
        end_time = time.time()
        duration = end_time - start_time

        # 获取GPU信息（如果启用）
        gpu_info = None
        if use_gpu and factory.gpu_accelerator.is_gpu_available():
            gpu_info = factory.gpu_accelerator.get_gpu_info()

        # 清理临时配置
        Path(temp_config.name).unlink()

        if result['success']:
            print(f"✅ 视频生成成功!")
            print(f"   输出路径: {result['output_path']}")
            print(f"   视频时长: {result['duration']:.2f}秒")
            print(f"   处理时间: {duration:.2f}秒")
            print(f"   字幕数量: {result['subtitle_count']}")

            if gpu_info:
                print(f"   GPU信息: {gpu_info['name']}")
                print(f"   GPU核心: {gpu_info.get('compute_units', 'N/A')}")

            return {
                'success': True,
                'mode': 'GPU' if use_gpu else 'CPU',
                'processing_time': duration,
                'video_duration': result['duration'],
                'output_path': result['output_path'],
                'gpu_info': gpu_info
            }
        else:
            print(f"❌ 视频生成失败: {result.get('error', 'Unknown error')}")
            Path(temp_config.name).unlink(missing_ok=True)
            return {
                'success': False,
                'mode': 'GPU' if use_gpu else 'CPU',
                'error': result.get('error', 'Unknown error')
            }

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        Path(temp_config.name).unlink(missing_ok=True)
        return {
            'success': False,
            'mode': 'GPU' if use_gpu else 'CPU',
            'error': str(e)
        }


def main():
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║     GPU vs CPU 性能对比测试 - Apple M4                    ║")
    print("╚═══════════════════════════════════════════════════════════╝")

    results = []

    # 测试 1: GPU 加速模式
    print("\n🎮 第一轮测试: GPU 加速模式")
    gpu_result = run_benchmark(use_gpu=True, output_suffix="gpu")
    results.append(gpu_result)

    # 等待系统冷却
    print("\n⏳ 等待 5 秒让系统冷却...")
    time.sleep(5)

    # 测试 2: CPU 模式
    print("\n💻 第二轮测试: CPU 模式")
    cpu_result = run_benchmark(use_gpu=False, output_suffix="cpu")
    results.append(cpu_result)

    # 性能对比分析
    print("\n" + "="*60)
    print("📊 性能对比分析")
    print("="*60)

    if gpu_result['success'] and cpu_result['success']:
        gpu_time = gpu_result['processing_time']
        cpu_time = cpu_result['processing_time']
        speedup = cpu_time / gpu_time
        time_saved = cpu_time - gpu_time
        improvement_pct = ((cpu_time - gpu_time) / cpu_time) * 100

        print(f"\n处理时间对比:")
        print(f"  GPU 模式: {gpu_time:.2f} 秒")
        print(f"  CPU 模式: {cpu_time:.2f} 秒")
        print(f"\n性能提升:")
        print(f"  加速比: {speedup:.2f}x")
        print(f"  节省时间: {time_saved:.2f} 秒")
        print(f"  性能提升: {improvement_pct:.1f}%")

        if gpu_result.get('gpu_info'):
            print(f"\nGPU 硬件信息:")
            print(f"  芯片: {gpu_result['gpu_info']['name']}")
            print(f"  GPU 核心: {gpu_result['gpu_info'].get('compute_units', 'N/A')}")

        # 性能评级
        print(f"\n性能评级:")
        if speedup >= 5.0:
            print(f"  🌟🌟🌟🌟🌟 卓越 - GPU 加速效果显著!")
        elif speedup >= 3.0:
            print(f"  🌟🌟🌟🌟 优秀 - GPU 加速效果良好!")
        elif speedup >= 2.0:
            print(f"  🌟🌟🌟 良好 - GPU 加速有明显提升")
        elif speedup >= 1.5:
            print(f"  🌟🌟 一般 - GPU 加速有一定提升")
        else:
            print(f"  🌟 较低 - GPU 加速效果不明显")

        # 建议
        print(f"\n💡 建议:")
        if speedup >= 2.0:
            print(f"  建议在批量视频生成中始终启用 GPU 加速")
        else:
            print(f"  对于单个视频，GPU 加速提升有限")
            print(f"  建议在批量处理时启用 GPU 加速以获得更大收益")

    else:
        print("❌ 某些测试失败，无法进行对比分析")
        for r in results:
            if not r['success']:
                print(f"   {r['mode']} 模式失败: {r.get('error', 'Unknown')}")

    print("\n" + "="*60)
    print("测试完成!")
    print("="*60)

    # 输出文件信息
    print(f"\n生成的测试视频:")
    if gpu_result['success']:
        print(f"  GPU 模式: {gpu_result['output_path']}")
    if cpu_result['success']:
        print(f"  CPU 模式: {cpu_result['output_path']}")


if __name__ == "__main__":
    main()
