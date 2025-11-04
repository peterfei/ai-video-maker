"""
测试字体管理器功能
"""

import sys
from pathlib import Path

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from subtitle.font_manager import FontManager
import logging

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s - %(message)s'
)

def main():
    print("=" * 60)
    print("字体管理器测试")
    print("=" * 60)

    # 创建字体管理器
    fm = FontManager()

    # 1. 检测中文字体
    print("\n1. 检测系统中文字体:")
    chinese_fonts = fm.detect_chinese_fonts()
    print(f"   找到 {len(chinese_fonts)} 个中文字体")
    for font in chinese_fonts[:10]:  # 只显示前10个
        print(f"   - {font}")

    # 2. 获取平台默认字体
    print("\n2. 平台默认中文字体:")
    platform_fonts = fm.get_default_chinese_fonts_by_platform()
    for font in platform_fonts:
        print(f"   - {font}")

    # 3. 测试字体验证
    print("\n3. 字体验证测试:")
    test_fonts = [
        "STHeiti Medium",
        "Arial Unicode MS",
        "NonExistentFont12345"
    ]

    for font_name in test_fonts:
        exists = fm.font_exists(font_name)
        if exists:
            valid = fm.validate_font(font_name)
            status = "✓ 可用且支持中文" if valid else "✗ 存在但不支持中文"
        else:
            status = "✗ 不存在"

        print(f"   {font_name}: {status}")

    # 4. 测试字体选择
    print("\n4. 字体选择测试:")
    preferred_fonts = [
        "Noto Sans CJK SC",
        "STHeiti Medium",
        "Microsoft YaHei",
        "Arial Unicode MS"
    ]

    best_font = fm.get_best_font(preferred_fonts)
    if best_font:
        print(f"   ✓ 选择的最佳字体: {best_font}")

        # 获取字体详细信息
        info = fm.get_font_info(best_font)
        print(f"   类型: {info['type']}")
        print(f"   路径: {info['path']}")
        print(f"   支持中文: {info['supports_chinese']}")
    else:
        print("   ✗ 未找到可用字体")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
