#!/usr/bin/env python3
"""
调试字幕渲染功能
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_subtitle_rendering():
    print("🔍 测试字幕渲染功能...")

    try:
        # 模拟配置 - 使用实际的配置文件
        from src.config_loader import get_config
        config_loader = get_config()
        config = config_loader.config['subtitle']
        print(f"📋 使用配置文件中的字幕设置")
        print(f"   启用状态: {config.get('enabled', True)}")
        print(f"   字体路径: {config.get('font_path')}")
        print(f"   字体回退: {config.get('font_fallback', [])}")
        print(f"   旧版字体名: {config.get('font_name')}")
        print()

        # 导入字幕渲染器
        from src.subtitle import SubtitleRenderer
        print("✅ 字幕渲染器导入成功")

        # 创建渲染器
        renderer = SubtitleRenderer(config)
        print("✅ 字幕渲染器初始化成功")
        print(f"   字体: {renderer.font}")
        print(f"   字体名称: {renderer.font_name}")
        print(f"   启用状态: {renderer.enabled}")

        # 创建测试字幕片段
        from src.subtitle import SubtitleSegment
        test_segments = [
            SubtitleSegment("这是测试字幕", 0.0, 2.0, 1),
            SubtitleSegment("第二条字幕内容", 2.0, 4.0, 2),
        ]
        print(f"✅ 创建了 {len(test_segments)} 个测试字幕片段")

        # 测试创建文本片段
        video_size = (1920, 1080)
        text_clips = renderer.create_text_clips(test_segments, video_size)
        print(f"✅ 成功创建 {len(text_clips)} 个文本片段")

        for i, clip in enumerate(text_clips):
            print(f"   片段 {i+1}: {clip.duration:.1f}s")

        print("\n🎉 字幕渲染功能测试通过！")
        return True

    except Exception as e:
        print(f"❌ 字幕渲染测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_subtitle_rendering()
    sys.exit(0 if success else 1)
