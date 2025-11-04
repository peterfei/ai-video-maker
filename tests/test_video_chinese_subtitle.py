#!/usr/bin/env python3
"""
创建一个简短的测试视频验证中文字幕渲染
"""

import logging
from moviepy.editor import ColorClip
from src.subtitle.subtitle_render import SubtitleRenderer
from src.subtitle.subtitle_gen import SubtitleSegment

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_video_with_chinese_subtitle():
    """创建带中文字幕的测试视频"""
    
    # 配置
    config = {
        'enabled': True,
        'font_size': 60,
        'font_color': 'white',
        'stroke_color': 'black',
        'stroke_width': 3,
        'position': 'bottom',
        'margin_bottom': 80,
        'align': 'center'
    }
    
    # 创建渲染器
    logger.info("初始化字幕渲染器...")
    renderer = SubtitleRenderer(config)
    logger.info(f"使用字体: {renderer.font}")
    
    # 创建测试字幕
    test_segments = [
        SubtitleSegment(text="Python", start_time=0.0, end_time=2.0, index=0),
        SubtitleSegment(text="你好世界", start_time=2.0, end_time=4.0, index=1),
        SubtitleSegment(text="Hello 中文 World", start_time=4.0, end_time=6.0, index=2),
        SubtitleSegment(text="测试中文字幕渲染", start_time=6.0, end_time=8.0, index=3),
    ]
    
    # 创建简单的彩色背景视频
    logger.info("创建背景视频...")
    video_clip = ColorClip(size=(1280, 720), color=(50, 50, 150), duration=8.0)
    
    # 渲染字幕到视频
    logger.info("渲染字幕...")
    final_clip = renderer.render_on_video(video_clip, test_segments)
    
    # 保存视频
    output_path = "output/test_chinese_subtitle.mp4"
    logger.info(f"保存视频到 {output_path}...")
    
    final_clip.write_videofile(
        output_path,
        fps=24,
        codec='libx264',
        audio=False,
        preset='ultrafast'
    )
    
    logger.info(f"✓ 测试视频已保存: {output_path}")
    logger.info("请打开视频检查中文字幕是否正确显示")

if __name__ == "__main__":
    test_video_with_chinese_subtitle()
