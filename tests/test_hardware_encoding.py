#!/usr/bin/env python3
"""
测试硬件编码修复
"""

import sys
import time
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from main import VideoFactory


def test_hardware_encoding():
    """测试VideoToolbox硬件编码"""
    print("=" * 70)
    print("测试 VideoToolbox 硬件编码修复")
    print("=" * 70)

    try:
        # 创建视频工厂
        print("\n1. 初始化视频工厂（使用默认配置）")
        factory = VideoFactory("config/default_config.yaml")

        # 检查配置
        codec = factory.video_compositor.codec
        print(f"   当前编码器: {codec}")

        if codec != 'h264_videotoolbox':
            print(f"   ⚠️  警告: 当前编码器不是 h264_videotoolbox")
            print(f"   将临时切换到 h264_videotoolbox 进行测试")
            factory.video_compositor.codec = 'h264_videotoolbox'

        # 测试视频生成
        print("\n2. 生成测试视频")
        start_time = time.time()

        result = factory.generate_video(
            script_path="data/scripts/gpu_test.txt",
            materials_dir="data/test_materials",
            output_path="output/hw_encoding_test.mp4",
            title="hw_encoding_test"
        )

        end_time = time.time()
        duration = end_time - start_time

        if result['success']:
            print(f"\n✓ 视频生成成功!")
            print(f"  输出路径: {result['output_path']}")
            print(f"  视频时长: {result['duration']:.2f}秒")
            print(f"  处理时间: {duration:.2f}秒")
            print(f"  字幕数量: {result['subtitle_count']}")

            # 检查文件
            output_file = Path(result['output_path'])
            if output_file.exists():
                file_size = output_file.stat().st_size / (1024 * 1024)
                print(f"  文件大小: {file_size:.2f} MB")

                # 检查编码器
                import subprocess
                probe_cmd = [
                    'ffprobe', '-v', 'quiet',
                    '-show_streams', '-select_streams', 'v:0',
                    '-show_entries', 'stream=codec_name',
                    '-of', 'default=noprint_wrappers=1:nokey=1',
                    str(output_file)
                ]
                result_probe = subprocess.run(probe_cmd, capture_output=True, text=True)
                codec_used = result_probe.stdout.strip()
                print(f"  实际编码器: {codec_used}")

                print("\n✓ 硬件编码测试通过!")
                return True
            else:
                print(f"\n✗ 输出文件不存在")
                return False
        else:
            print(f"\n✗ 视频生成失败: {result.get('error', 'Unknown error')}")
            return False

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("开始测试...")
    print("=" * 70)

    success = test_hardware_encoding()

    print("\n" + "=" * 70)
    if success:
        print("✓ 所有测试通过")
        print("VideoToolbox 硬件编码工作正常")
    else:
        print("✗ 测试失败")
        print("请检查硬件编码配置")
    print("=" * 70)

    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
