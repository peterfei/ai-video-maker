"""
测试自动素材获取功能
验证从空目录自动从Unsplash和Pexels下载素材
"""

import sys
from pathlib import Path

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from config_loader import get_config
from content_sources import AutoMaterialManager, TextSource

def test_auto_materials():
    """测试自动素材获取"""

    print("=" * 60)
    print("测试自动素材获取功能")
    print("=" * 60)

    # 加载配置
    config = get_config()

    # 检查API密钥
    unsplash_key = config.get('auto_materials.unsplash_key')
    pexels_key = config.get('auto_materials.pexels_key')

    print(f"\n配置检查:")
    print(f"  Unsplash API Key: {'✓ 已配置' if unsplash_key else '✗ 未配置'}")
    print(f"  Pexels API Key: {'✓ 已配置' if pexels_key else '✗ 未配置'}")
    print(f"  自动下载: {'✓ 启用' if config.get('auto_materials.auto_download') else '✗ 禁用'}")

    if not (unsplash_key or pexels_key):
        print("\n警告: 没有配置图库API密钥，无法从在线获取素材")
        print("请在 .env 文件中配置 UNSPLASH_ACCESS_KEY 或 PEXELS_API_KEY")
        return

    # 初始化管理器
    print("\n初始化自动素材管理器...")
    auto_materials_config = config.get('auto_materials', {})
    manager = AutoMaterialManager(auto_materials_config)

    # 创建测试脚本片段
    text_source = TextSource({})
    test_script = """
    这是一段关于自然风景的视频脚本。
    我们将展示美丽的山景和宁静的森林。
    最后是壮观的日落景色。
    """

    script_segments = text_source.parse_script(test_script)

    print(f"\n测试脚本:")
    print(f"  片段数: {len(script_segments)}")
    for i, seg in enumerate(script_segments):
        print(f"  片段{i+1}: {seg.text[:50]}...")

    # 获取素材
    print("\n开始获取素材...")
    print("-" * 60)
    material_paths = manager.get_materials_for_script(
        script_segments,
        materials_per_segment=2
    )

    print("-" * 60)
    print(f"\n✓ 成功获取 {len(material_paths)} 个素材")

    # 显示素材信息
    if material_paths:
        print("\n素材列表:")
        for i, path in enumerate(material_paths, 1):
            print(f"  {i}. {path.name}")
            print(f"     路径: {path}")

    # 显示素材库统计
    print("\n素材库统计:")
    stats = manager.get_library_stats()
    print(f"  总图片数: {stats['total_images']}")
    print(f"  索引关键词数: {stats['total_keywords']}")
    print(f"  分类数: {stats['categories']}")
    print(f"  库路径: {stats['library_path']}")

    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)

if __name__ == '__main__':
    test_auto_materials()
