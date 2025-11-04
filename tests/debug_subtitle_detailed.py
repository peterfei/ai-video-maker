#!/usr/bin/env python3
"""
详细调试字幕渲染过程
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def debug_subtitle_rendering():
    print("🔍 详细调试字幕渲染过程...")

    try:
        # 模拟配置
        from src.config_loader import get_config
        config_loader = get_config()
        config = config_loader.config['subtitle']
        print(f"📋 使用实际配置文件")

        # 导入字幕渲染器
        from src.subtitle import SubtitleRenderer
        print("✅ 字幕渲染器导入成功")

        # 创建渲染器
        renderer = SubtitleRenderer(config)
        print("✅ 字幕渲染器初始化成功")
        print(f"   字体: {renderer.font}")
        print(f"   字体名称: {renderer.font_name}")
        print(f"   启用状态: {renderer.enabled}")

        # 创建一些测试字幕片段，模拟实际的字幕数据
        from src.subtitle import SubtitleSegment
        test_segments = [
            SubtitleSegment("欢迎来到Python编程入门教程！", 0.0, 3.34, 1),
            SubtitleSegment("今天我们将学习Python的基础语法。", 3.34, 6.77, 2),
            SubtitleSegment("Python是一种简单易学、功能强大的编程语言，被广泛应用于数据分析、人工智能、Web开发等领域。", 6.77, 16.52, 3),
        ]
        print(f"✅ 创建了 {len(test_segments)} 个测试字幕片段")

        # 逐个测试字幕片段创建
        video_size = (1920, 1080)
        text_clips = []

        for i, segment in enumerate(test_segments):
            print(f"\n🔸 测试字幕片段 {i+1}: '{segment.text[:30]}...'")
            print(f"   时间: {segment.start_time:.2f}s - {segment.end_time:.2f}s")
            print(f"   时长: {segment.duration:.2f}s")

            try:
                # 尝试创建字幕片段
                clips = renderer.create_text_clips([segment], video_size)
                if clips:
                    clip = clips[0]
                    text_clips.append(clip)
                    print(f"   ✅ 创建成功: {clip.duration:.2f}s")
                else:
                    print("   ❌ 创建失败: 返回空列表")
            except Exception as e:
                print(f"   ❌ 创建失败: {e}")
                import traceback
                traceback.print_exc()

        print(f"\n📊 总计: {len(text_clips)}/{len(test_segments)} 个字幕片段创建成功")

        # 测试视频合成
        if text_clips:
            print("\n🎬 测试视频合成...")
            try:
                from moviepy.editor import ColorClip

                # 创建一个简单的背景视频
                background = ColorClip(size=video_size, color=(0,0,0), duration=20)

                # 合成字幕
                from moviepy.editor import CompositeVideoClip
                final_clip = CompositeVideoClip([background] + text_clips)

                # 导出短视频用于测试
                output_path = "output/debug_subtitle_test.mp4"
                final_clip.write_videofile(
                    output_path,
                    fps=24,
                    codec="libx264",
                    audio=False,
                    verbose=False,
                    logger=None
                )

                print(f"✅ 测试视频导出成功: {output_path}")
                final_clip.close()
                background.close()

            except Exception as e:
                print(f"❌ 视频合成失败: {e}")
                import traceback
                traceback.print_exc()

        print("\n🎉 字幕渲染调试完成！")
        return True

    except Exception as e:
        print(f"❌ 字幕渲染调试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = debug_subtitle_rendering()
    sys.exit(0 if success else 1)
