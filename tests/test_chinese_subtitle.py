#!/usr/bin/env python3
"""
测试中文字幕渲染
"""

import logging
from src.subtitle.subtitle_render import SubtitleRenderer
from src.subtitle.subtitle_gen import SubtitleSegment

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_chinese_subtitle():
    """测试中文字幕"""
    
    # 配置
    config = {
        'enabled': True,
        'font_size': 48,
        'font_color': 'white',
        'stroke_color': 'black',
        'stroke_width': 2,
        'position': 'bottom',
        'margin_bottom': 100,
        'align': 'center'
    }
    
    # 创建渲染器
    logger.info("初始化字幕渲染器...")
    renderer = SubtitleRenderer(config)
    
    # 检查字体设置
    logger.info(f"选择的字体: {renderer.font}")
    logger.info(f"字体名称: {renderer.font_name}")
    
    # 创建测试字幕
    test_segments = [
        SubtitleSegment(text="Python", start_time=0.0, end_time=2.0, index=0),
        SubtitleSegment(text="你好世界", start_time=2.0, end_time=4.0, index=1),
        SubtitleSegment(text="Hello 中文 World", start_time=4.0, end_time=6.0, index=2),
        SubtitleSegment(text="测试中文字幕渲染", start_time=6.0, end_time=8.0, index=3),
    ]
    
    # 测试创建字幕片段
    logger.info("\n测试创建字幕片段...")
    video_size = (1920, 1080)
    
    try:
        text_clips = renderer.create_text_clips(test_segments, video_size)
        logger.info(f"✓ 成功创建 {len(text_clips)} 个字幕片段")
        
        for i, clip in enumerate(text_clips):
            logger.info(f"  片段 {i}: '{test_segments[i].text}' - {clip.duration}秒")
            
    except Exception as e:
        logger.error(f"✗ 创建字幕片段失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    logger.info("\n✓ 中文字幕测试通过！")
    return True

if __name__ == "__main__":
    test_chinese_subtitle()
