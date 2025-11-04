#!/usr/bin/env python3
"""
复杂场景 GPU vs CPU 性能对比测试
- 15张图片
- 60秒视频
- VideoToolbox 硬件编码
- 复杂转场效果
"""

import sys
import time
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from main import VideoFactory


def run_complex_benchmark(use_gpu: bool, use_hw_encoder: bool, output_suffix: str):
    """
    运行复杂场景基准测试

    Args:
        use_gpu: 是否启用GPU加速
        use_hw_encoder: 是否使用硬件编码器
        output_suffix: 输出文件后缀
    """
    mode_name = f"{'GPU' if use_gpu else 'CPU'}"
    encoder_name = f"{'VideoToolbox' if use_hw_encoder else 'libx264'}"

    print(f"\n{'='*70}")
    print(f"{mode_name} + {encoder_name} 性能测试")
    print(f"{'='*70}")
    print(f"  图片数量: 15 张")
    print(f"  预计时长: ~60 秒")
    print(f"  转场效果: 交叉淡化")
    print(f"  GPU加速: {'✅ 启用' if use_gpu else '❌ 禁用'}")
    print(f"  硬件编码: {'✅ ' + encoder_name if use_hw_encoder else '❌ 软件编码'}")

    try:
        # 修改配置
        config_path = "config/gpu_benchmark_config.yaml"

        # 创建视频工厂
        factory = VideoFactory(config_path)

        # 临时修改GPU设置
        factory.gpu_accelerator._is_available = use_gpu
        if not use_gpu:
            factory.gpu_accelerator._device = __import__('torch').device('cpu')
            factory.gpu_accelerator._backend_type = 'cpu'

        # 修改编码器设置
        if use_hw_encoder:
            factory.video_compositor.config['codec'] = 'h264_videotoolbox'
        else:
            factory.video_compositor.config['codec'] = 'libx264'

        # 记录开始时间
        start_time = time.time()

        # 生成视频
        output_path = f"output/complex_{output_suffix}.mp4"
        result = factory.generate_video(
            script_path="data/scripts/complex_benchmark.txt",
            materials_dir="data/test_materials",
            output_path=output_path,
            title=f"complex_{output_suffix}"
        )

        # 记录结束时间
        end_time = time.time()
        duration = end_time - start_time

        # 获取GPU信息（如果启用）
        gpu_info = None
        if use_gpu and factory.gpu_accelerator.is_gpu_available():
            gpu_info = factory.gpu_accelerator.get_gpu_info()

        if result['success']:
            print(f"\n✅ 视频生成成功!")
            print(f"   输出路径: {result['output_path']}")
            print(f"   视频时长: {result['duration']:.2f}秒")
            print(f"   处理时间: {duration:.2f}秒")
            print(f"   字幕数量: {result['subtitle_count']}")
            print(f"   编码器: {encoder_name}")

            if gpu_info:
                print(f"   GPU: {gpu_info['name']} ({gpu_info.get('compute_units', 'N/A')}核)")

            # 检查输出文件大小
            output_file = Path(result['output_path'])
            if output_file.exists():
                file_size = output_file.stat().st_size / (1024 * 1024)
                print(f"   文件大小: {file_size:.2f} MB")

            return {
                'success': True,
                'mode': mode_name,
                'encoder': encoder_name,
                'processing_time': duration,
                'video_duration': result['duration'],
                'output_path': result['output_path'],
                'file_size_mb': file_size if output_file.exists() else 0,
                'gpu_info': gpu_info
            }
        else:
            print(f"❌ 视频生成失败: {result.get('error', 'Unknown error')}")
            return {
                'success': False,
                'mode': mode_name,
                'encoder': encoder_name,
                'error': result.get('error', 'Unknown error')
            }

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'mode': mode_name,
            'encoder': encoder_name,
            'error': str(e)
        }


def main():
    print("╔" + "="*70 + "╗")
    print("║" + " "*10 + "复杂场景 GPU 性能测试 - Apple M4" + " "*20 + "║")
    print("║" + " "*10 + "15张图片 + 60秒视频 + 硬件编码" + " "*22 + "║")
    print("╚" + "="*70 + "╝")

    results = []

    # 测试 1: GPU + VideoToolbox 硬件编码
    print("\n🎮 第一轮测试: GPU + VideoToolbox 硬件编码")
    result1 = run_complex_benchmark(
        use_gpu=True,
        use_hw_encoder=True,
        output_suffix="gpu_hw"
    )
    results.append(result1)

    # 冷却
    print("\n⏳ 等待 5 秒让系统冷却...")
    time.sleep(5)

    # 测试 2: CPU + 软件编码
    print("\n💻 第二轮测试: CPU + libx264 软件编码")
    result2 = run_complex_benchmark(
        use_gpu=False,
        use_hw_encoder=False,
        output_suffix="cpu_sw"
    )
    results.append(result2)

    # 冷却
    print("\n⏳ 等待 5 秒让系统冷却...")
    time.sleep(5)

    # 测试 3: GPU + 软件编码（对比编码器差异）
    print("\n🎮 第三轮测试: GPU + libx264 软件编码（对比）")
    result3 = run_complex_benchmark(
        use_gpu=True,
        use_hw_encoder=False,
        output_suffix="gpu_sw"
    )
    results.append(result3)

    # 性能对比分析
    print("\n" + "="*70)
    print("📊 性能对比分析")
    print("="*70)

    # 检查所有测试是否成功
    successful_results = [r for r in results if r['success']]

    if len(successful_results) >= 2:
        print("\n处理时间对比:")
        for r in successful_results:
            print(f"  {r['mode']} + {r['encoder']}: {r['processing_time']:.2f} 秒")

        # GPU硬件编码 vs CPU软件编码
        if result1['success'] and result2['success']:
            speedup = result2['processing_time'] / result1['processing_time']
            time_saved = result2['processing_time'] - result1['processing_time']
            improvement_pct = ((result2['processing_time'] - result1['processing_time']) / result2['processing_time']) * 100

            print(f"\n🚀 GPU+硬件编码 vs CPU+软件编码:")
            print(f"  加速比: {speedup:.2f}x")
            print(f"  节省时间: {time_saved:.2f} 秒")
            print(f"  性能提升: {improvement_pct:.1f}%")

        # GPU软件编码 vs CPU软件编码（纯GPU效果）
        if result3['success'] and result2['success']:
            gpu_effect = result2['processing_time'] / result3['processing_time']
            print(f"\n🎮 纯GPU加速效果 (同为软件编码):")
            print(f"  GPU软件编码 vs CPU软件编码")
            print(f"  加速比: {gpu_effect:.2f}x")

        # 硬件编码 vs 软件编码（同为GPU）
        if result1['success'] and result3['success']:
            hw_effect = result3['processing_time'] / result1['processing_time']
            print(f"\n⚡ 硬件编码加速效果 (同为GPU):")
            print(f"  GPU+VideoToolbox vs GPU+libx264")
            print(f"  加速比: {hw_effect:.2f}x")

        # 文件大小对比
        print(f"\n📦 文件大小对比:")
        for r in successful_results:
            if 'file_size_mb' in r:
                print(f"  {r['mode']} + {r['encoder']}: {r['file_size_mb']:.2f} MB")

        # 性能评级
        if result1['success'] and result2['success']:
            speedup = result2['processing_time'] / result1['processing_time']
            print(f"\n🏆 综合性能评级:")
            if speedup >= 3.0:
                print(f"  🌟🌟🌟🌟🌟 卓越 - GPU+硬件编码效果显著!")
                print(f"  强烈推荐在所有场景下启用")
            elif speedup >= 2.0:
                print(f"  🌟🌟🌟🌟 优秀 - GPU+硬件编码效果良好!")
                print(f"  推荐在复杂场景和批量处理中启用")
            elif speedup >= 1.5:
                print(f"  🌟🌟🌟 良好 - GPU+硬件编码有明显提升")
                print(f"  建议在批量处理时启用")
            elif speedup >= 1.2:
                print(f"  🌟🌟 一般 - GPU+硬件编码有一定提升")
            else:
                print(f"  🌟 较低 - 可能CPU或编码器配置需要优化")

            # 优化建议
            print(f"\n💡 优化建议:")
            if speedup >= 2.0:
                print(f"  ✅ GPU+VideoToolbox 组合效果很好")
                print(f"  ✅ 建议在生产环境中使用此配置")
                print(f"  ✅ 批量处理时性能提升会更明显")
            else:
                print(f"  💭 当前场景可能不是GPU加速的最佳应用")
                print(f"  💭 建议测试更复杂的特效和转场")

    else:
        print("❌ 部分测试失败，无法进行完整对比分析")
        for r in results:
            if not r['success']:
                print(f"   {r['mode']} + {r['encoder']} 失败: {r.get('error', 'Unknown')}")

    print("\n" + "="*70)
    print("测试完成!")
    print("="*70)

    # 输出文件信息
    print(f"\n📹 生成的测试视频:")
    for r in successful_results:
        if 'output_path' in r:
            print(f"  {r['mode']} + {r['encoder']}: {r['output_path']}")

    print(f"\n💾 可以使用以下命令查看视频:")
    for r in successful_results:
        if 'output_path' in r:
            print(f"  open {r['output_path']}")


if __name__ == "__main__":
    main()
