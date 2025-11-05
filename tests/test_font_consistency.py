#!/usr/bin/env python3
"""
测试字幕字体大小一致性
"""

import logging
from src.subtitle.subtitle_render import SubtitleRenderer
from src.subtitle.subtitle_gen import SubtitleSegment

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_font_consistency():
    """测试字体大小一致性"""

    # 测试配置：启用统一字体大小
    config_uniform = {
        'enabled': True,
        'font_size': 48,
        'font_color': 'white',
        'stroke_color': 'black',
        'stroke_width': 2,
        'position': 'bottom',
        'margin_bottom': 100,
        'align': 'center',
        'uniform_font_size': True,  # 启用统一字体大小
        'video_width': 1920,
        'video_height': 1080
    }

    # 测试配置：禁用统一字体大小（内容感知）
    config_adaptive = {
        'enabled': True,
        'font_size': 48,
        'font_color': 'white',
        'stroke_color': 'black',
        'stroke_width': 2,
        'position': 'bottom',
        'margin_bottom': 100,
        'align': 'center',
        'uniform_font_size': False,  # 禁用统一字体大小
        'video_width': 1920,
        'video_height': 1080
    }

    # 创建包含特殊字符的测试字幕（模拟问题场景）
    test_segments = [
        SubtitleSegment(text="普通文本", start_time=0.0, end_time=2.0, index=0),
        SubtitleSegment(text="BIM、AI、BI、IoT", start_time=2.0, end_time=4.0, index=1),  # 问题文本
        SubtitleSegment(text="技术@内容#测试", start_time=4.0, end_time=6.0, index=2),
        SubtitleSegment(text="Python/JavaScript & C++", start_time=6.0, end_time=8.0, index=3),
    ]

    logger.info("测试统一字体大小模式...")
    renderer_uniform = SubtitleRenderer(config_uniform)

    # 验证统一字体大小
    consistency_uniform = renderer_uniform._validate_font_consistency(test_segments)
    logger.info(f"统一模式验证结果: {consistency_uniform}")

    # 预期：所有片段使用相同字体大小
    if consistency_uniform['is_valid']:
        metrics = consistency_uniform['metrics']
        if metrics['size_range'] == 0:
            logger.info("✓ 统一字体大小模式：所有片段使用相同字体大小")
        else:
            logger.warning(f"✗ 统一字体大小模式：字体大小仍有差异 {metrics['size_range']}px")
    else:
        logger.error(f"✗ 统一字体大小模式验证失败: {consistency_uniform['warnings']}")

    logger.info("\n测试内容感知字体大小模式...")
    renderer_adaptive = SubtitleRenderer(config_adaptive)

    # 验证内容感知字体大小
    consistency_adaptive = renderer_adaptive._validate_font_consistency(test_segments)
    logger.info(f"内容感知模式验证结果: {consistency_adaptive}")

    # 预期：可能有轻微调整，但不应该差异过大
    if consistency_adaptive['is_valid']:
        metrics = consistency_adaptive['metrics']
        if metrics['size_range'] <= 4:  # 允许4px差异
            logger.info(f"✓ 内容感知模式：字体大小差异在可接受范围内 ({metrics['size_range']}px)")
        else:
            logger.warning(f"✗ 内容感知模式：字体大小差异过大 ({metrics['size_range']}px)")
    else:
        logger.warning(f"! 内容感知模式有警告: {consistency_adaptive['warnings']}")

    # 测试具体配置获取
    logger.info("\n测试字体配置获取...")
    test_texts = ["普通文本", "BIM、AI、BI、IoT", "技术@内容#测试"]

    for text in test_texts:
        uniform_config = renderer_uniform._get_text_clip_config(text, 1920)
        adaptive_config = renderer_adaptive._get_text_clip_config(text, 1920)

        logger.info(f"文本: '{text}'")
        logger.info(f"  统一模式字体大小: {uniform_config['fontsize']}")
        logger.info(f"  内容感知字体大小: {adaptive_config['fontsize']}")

        # 检查统一模式是否真的统一
        if uniform_config['fontsize'] != adaptive_config['fontsize']:
            logger.info(f"  内容感知调整: {adaptive_config['fontsize'] - uniform_config['fontsize']}px")

    logger.info("\n✓ 字体一致性测试完成")

if __name__ == "__main__":
    test_font_consistency()
