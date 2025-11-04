#!/usr/bin/env python3
"""
字体下载脚本
下载并设置项目所需的开源中文字体
"""

import os
import sys
import urllib.request
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple

# 添加src到路径
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

from subtitle.font_manager import FontManager

# 字体配置
FONTS_CONFIG = {
    'NotoSansCJKsc-Regular.otf': {
        'url': 'https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/SimplifiedChinese/NotoSansCJKsc-Regular.otf',
        'sha256': 'a2a4c8b3e4f5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1',  # 占位符，需要实际验证
        'description': 'Noto Sans CJK SC Regular - Google开源中文字体'
    },
    'SourceHanSansSC-Regular.otf': {
        'url': 'https://github.com/adobe-fonts/source-han-sans/raw/main/OTF/SimplifiedChinese/SourceHanSansSC-Regular.otf',
        'sha256': 'b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4',  # 占位符，需要实际验证
        'description': 'Source Han Sans SC Regular - Adobe + Google开源中文字体'
    },
    'WenQuanYiMicroHei-Regular.ttf': {
        'url': 'https://github.com/wqy-fonts/wqy-microhei/raw/main/wqy-microhei.ttc',  # 注意：这是复合字体文件
        'sha256': 'c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5',  # 占位符，需要实际验证
        'description': 'WenQuanYi Micro Hei - 文泉驿微米黑'
    }
}

class FontDownloader:
    """字体下载器"""

    def __init__(self, fonts_dir: Path):
        self.fonts_dir = fonts_dir
        self.font_manager = FontManager()

    def download_file(self, url: str, filepath: Path) -> bool:
        """下载文件"""
        try:
            print(f"📥 下载中: {url}")
            with urllib.request.urlopen(url) as response:
                with open(filepath, 'wb') as f:
                    f.write(response.read())
            print(f"✅ 下载完成: {filepath}")
            return True
        except Exception as e:
            print(f"❌ 下载失败: {e}")
            return False

    def verify_file(self, filepath: Path, expected_hash: str) -> bool:
        """验证文件完整性"""
        try:
            sha256 = hashlib.sha256()
            with open(filepath, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256.update(chunk)

            actual_hash = sha256.hexdigest()
            if actual_hash == expected_hash:
                print(f"✅ 文件验证通过: {filepath.name}")
                return True
            else:
                print(f"❌ 文件验证失败: {filepath.name}")
                print(f"  期望: {expected_hash}")
                print(f"  实际: {actual_hash}")
                return False
        except Exception as e:
            print(f"❌ 文件验证出错: {e}")
            return False

    def test_font(self, filepath: Path) -> bool:
        """测试字体是否可用"""
        try:
            if self.font_manager.validate_font(filepath, "测试中文字体"):
                print(f"✅ 字体测试通过: {filepath.name}")
                return True
            else:
                print(f"❌ 字体测试失败: {filepath.name}")
                return False
        except Exception as e:
            print(f"❌ 字体测试出错: {e}")
            return False

    def download_font(self, name: str, config: Dict) -> bool:
        """下载单个字体"""
        filepath = self.fonts_dir / name

        # 检查是否已存在
        if filepath.exists():
            print(f"⏭️ 字体已存在: {name}")
            if self.test_font(filepath):
                return True
            else:
                print(f"⚠️ 现有字体损坏，重新下载: {name}")
                filepath.unlink()

        # 下载字体
        if not self.download_file(config['url'], filepath):
            return False

        # 验证字体（暂时跳过哈希验证，因为我们还没有真实的哈希值）
        # if not self.verify_file(filepath, config['sha256']):
        #     filepath.unlink()
        #     return False

        # 测试字体
        if not self.test_font(filepath):
            filepath.unlink()
            return False

        return True

    def download_all_fonts(self) -> bool:
        """下载所有字体"""
        print("🎨 开始下载中文字体文件...")
        print("=" * 50)

        self.fonts_dir.mkdir(parents=True, exist_ok=True)

        success_count = 0
        total_count = len(FONTS_CONFIG)

        for name, config in FONTS_CONFIG.items():
            print(f"\n🔤 处理字体: {name}")
            print(f"📝 描述: {config['description']}")

            if self.download_font(name, config):
                success_count += 1
                print("✅ 字体准备完成")
            else:
                print("❌ 字体准备失败")

        print("\n" + "=" * 50)
        print(f"📊 下载结果: {success_count}/{total_count} 个字体成功")

        if success_count > 0:
            print("🎉 字体准备完成！现在可以使用预置中文字体了。")
            return True
        else:
            print("❌ 未能下载任何字体，请检查网络连接。")
            return False

def main():
    """主函数"""
    # 设置字体目录
    project_root = Path(__file__).parent.parent
    fonts_dir = project_root / "assets" / "fonts"

    # 创建下载器
    downloader = FontDownloader(fonts_dir)

    # 下载所有字体
    success = downloader.download_all_fonts()

    if success:
        print("\n💡 提示:")
        print("- 字体文件已保存到 assets/fonts/ 目录")
        print("- 配置文件已自动使用这些字体")
        print("- 运行 'python generate.py --list-fonts' 查看可用字体")
        sys.exit(0)
    else:
        print("\n❌ 字体下载失败，请重试或手动安装字体")
        sys.exit(1)

if __name__ == "__main__":
    main()
