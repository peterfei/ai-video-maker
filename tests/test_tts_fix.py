#!/usr/bin/env python3
"""
测试TTS引擎修复
"""

import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from audio.tts_engine import TTSEngine


def test_tts_with_fallback():
    """测试TTS引擎（带fallback）"""
    print("=" * 60)
    print("测试TTS引擎修复")
    print("=" * 60)

    # 创建TTS引擎
    config = {
        'engine': 'edge-tts',
        'voice': 'zh-CN-XiaoxiaoNeural',
        'rate': 1.0,
        'volume': 1.0,
        'pitch': 0
    }

    engine = TTSEngine(config)

    # 测试文本
    test_text = "这是一个TTS测试，验证fallback机制是否正常工作。"
    output_file = "test_tts_output.mp3"

    print(f"\n1. 测试文本: {test_text}")
    print(f"2. 输出文件: {output_file}")
    print(f"3. TTS引擎: {config['engine']}")

    try:
        print("\n开始生成语音...")
        result = engine.text_to_speech(test_text, output_file)

        print(f"✓ 语音生成成功!")
        print(f"  输出文件: {result}")

        # 检查文件
        if result.exists():
            file_size = result.stat().st_size
            print(f"  文件大小: {file_size} bytes")

            if file_size > 0:
                print("\n✓ TTS引擎工作正常!")
                # 清理测试文件
                result.unlink()
                print("  测试文件已清理")
                return True
            else:
                print("\n✗ 生成的文件为空")
                return False
        else:
            print("\n✗ 输出文件不存在")
            return False

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    success = test_tts_with_fallback()

    print("\n" + "=" * 60)
    if success:
        print("✓ 测试通过")
        print("TTS引擎可以正常工作（Edge TTS或fallback到本地TTS）")
    else:
        print("✗ 测试失败")
        print("请检查TTS配置和依赖")
    print("=" * 60)

    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
