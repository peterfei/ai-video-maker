"""
测试每个分段获取匹配素材的功能
验证每个脚本片段都能获得与内容相关的素材
"""

import sys
from pathlib import Path

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from config_loader import get_config
from content_sources import AutoMaterialManager, TextSource

def test_segment_matching():
    """测试每个片段的素材匹配"""

    print("=" * 60)
    print("测试每个分段的素材匹配功能")
    print("=" * 60)

    # 加载配置
    config = get_config()

    # 初始化管理器
    auto_materials_config = config.get('auto_materials', {})
    manager = AutoMaterialManager(auto_materials_config)

    # 创建多段测试脚本，每段内容不同
    text_source = TextSource({})
    test_script = """
[段落1]
在这个美丽的山区，我们可以看到壮观的自然风景。高耸的山峰直入云霄。

[段落2]
城市的夜景灯火辉煌，现代化的建筑展现了科技的力量。

[段落3]
在办公室里，团队成员们正在进行紧张的工作讨论。

[段落4]
学生们在图书馆认真学习，追求知识的梦想。
    """

    script_segments = text_source.parse_script(test_script)

    print(f"\n测试脚本:")
    print(f"  总片段数: {len(script_segments)}\n")

    # 显示每个片段的内容
    for i, seg in enumerate(script_segments):
        print(f"  片段 {i+1}:")
        print(f"    内容: {seg.text.strip()[:60]}...")

    # 分析每个片段的关键词（不实际下载）
    print("\n" + "=" * 60)
    print("分析每个片段的关键词")
    print("=" * 60)

    material_needs = manager.semantic_matcher.analyze_script_segments(script_segments)

    for need in material_needs:
        idx = need['segment_index'] + 1
        text_preview = need['text'][:50]
        keywords = need['keywords']
        primary = need['primary_keyword']

        print(f"\n片段 {idx}:")
        print(f"  文本: {text_preview}...")
        print(f"  提取的关键词: {', '.join(keywords)}")
        print(f"  主要关键词: {primary}")
        print(f"  将搜索图片: {manager.semantic_matcher.generate_search_query(keywords)}")

    # 实际获取素材
    print("\n" + "=" * 60)
    print("开始为每个片段获取匹配的素材")
    print("=" * 60)

    material_paths = manager.get_materials_for_script(
        script_segments,
        materials_per_segment=1  # 每个片段1个素材
    )

    print("\n" + "=" * 60)
    print(f"素材获取完成，共获取 {len(material_paths)} 个素材")
    print("=" * 60)

    # 显示素材分配情况
    print("\n素材与片段的匹配关系:")
    for i, path in enumerate(material_paths):
        segment_idx = i % len(script_segments)
        segment = script_segments[segment_idx]

        print(f"\n片段 {i+1}:")
        print(f"  文本: {segment.text.strip()[:50]}...")
        print(f"  素材: {path.name}")
        print(f"  路径: {path}")

    # 显示素材库统计
    print("\n" + "=" * 60)
    print("素材库统计")
    print("=" * 60)
    stats = manager.get_library_stats()
    print(f"  总图片数: {stats['total_images']}")
    print(f"  索引关键词数: {stats['total_keywords']}")
    print(f"  分类数: {stats['categories']}")
    print(f"  分类名称: {', '.join(stats['category_names'][:10])}")

    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)

if __name__ == '__main__':
    test_segment_matching()
