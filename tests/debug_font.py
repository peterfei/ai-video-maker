#!/usr/bin/env python3
"""
调试字体选择功能
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_font_selection():
    print("🔍 测试字体选择功能...")

    try:
        # 导入字体管理器
        from src.subtitle import FontManager
        print("✅ 字体管理器导入成功")

        # 创建字体管理器
        import logging
        logger = logging.getLogger()
        font_manager = FontManager(logger=logger)
        print("✅ 字体管理器初始化成功")

        # 测试获取系统字体
        system_fonts = font_manager.detect_system_fonts()
        print(f"✅ 系统字体数量: {len(system_fonts)}")

        # 测试中文字体检测
        chinese_fonts = font_manager.detect_chinese_fonts()
        print(f"✅ 检测到中文字体: {len(chinese_fonts)} 个")
        for font in chinese_fonts[:5]:  # 只显示前5个
            print(f"   - {font}")

        # 测试字体验证
        test_text = "测试中文字幕显示"
        valid_fonts = []
        for font in chinese_fonts[:3]:  # 测试前3个字体
            try:
                is_valid = font_manager.validate_font(font, test_text)
                if is_valid:
                    valid_fonts.append(font)
                    print(f"   ✓ {font}: 支持中文")
                else:
                    print(f"   ✗ {font}: 不支持中文")
            except Exception as e:
                print(f"   ⚠ {font}: 验证失败 - {e}")

        # 测试最佳字体选择
        preferred_fonts = ['STHeiti Medium', 'Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
        best_font = font_manager.get_best_font(preferred_fonts, test_text)
        print(f"✅ 最佳字体选择: {best_font}")

        # 测试平台默认字体
        platform_fonts = font_manager.get_default_chinese_fonts_by_platform()
        print(f"✅ 平台默认中文字体: {len(platform_fonts)} 个")
        for font in platform_fonts[:3]:
            print(f"   - {font}")

        print("\n🎉 字体选择功能测试通过！")
        return True

    except Exception as e:
        print(f"❌ 字体选择测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_font_selection()
    sys.exit(0 if success else 1)
