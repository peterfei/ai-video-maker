#!/usr/bin/env python3
"""
测试Edge TTS服务
"""

import asyncio
import sys

async def test_edge_tts():
    """测试Edge TTS"""
    try:
        import edge_tts

        print("1. 测试Edge TTS导入... ✓")

        # 测试语音合成
        text = "测试中文语音合成"
        voice = "zh-CN-XiaoxiaoNeural"
        output_file = "test_tts_output.mp3"

        print(f"2. 测试语音合成:")
        print(f"   文本: {text}")
        print(f"   语音: {voice}")
        print(f"   输出: {output_file}")

        # 创建通信对象
        communicate = edge_tts.Communicate(text=text, voice=voice)

        # 保存音频
        await communicate.save(output_file)

        print("   ✓ 语音合成成功!")

        # 检查文件
        import os
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            print(f"   文件大小: {file_size} bytes")
            # 清理测试文件
            os.remove(output_file)
            print("   ✓ 测试文件已清理")

        return True

    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_voice_list():
    """测试获取语音列表"""
    try:
        import edge_tts

        print("\n3. 测试获取可用语音列表:")
        voices = await edge_tts.list_voices()

        # 筛选中文语音
        zh_voices = [v for v in voices if v['Locale'].startswith('zh-')]

        print(f"   找到 {len(zh_voices)} 个中文语音:")
        for voice in zh_voices[:5]:  # 只显示前5个
            print(f"     - {voice['ShortName']}: {voice['FriendlyName']}")

        return True

    except Exception as e:
        print(f"✗ 获取语音列表失败: {e}")
        return False


async def main():
    """主函数"""
    print("=" * 60)
    print("Edge TTS 服务测试")
    print("=" * 60)

    # 测试1: 语音合成
    result1 = await test_edge_tts()

    # 测试2: 语音列表
    result2 = await test_voice_list()

    print("\n" + "=" * 60)
    if result1 and result2:
        print("✓ 所有测试通过!")
        print("Edge TTS 服务正常")
    else:
        print("✗ 部分测试失败")
        print("Edge TTS 服务可能存在问题")
    print("=" * 60)

    return result1 and result2


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
