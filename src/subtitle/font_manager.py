"""
字体管理器
负责字体检测、验证和选择，确保字幕渲染器能够在所有平台上正确显示中文
"""

from pathlib import Path
from typing import List, Dict, Union, Optional
import platform
import logging


class FontManager:
    """字体管理器 - 负责字体检测、验证和选择"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        初始化字体管理器

        Args:
            logger: 日志记录器（可选）
        """
        self.logger = logger or logging.getLogger(__name__)

        # 缓存系统字体信息
        self._system_fonts_cache: Optional[List[Dict[str, str]]] = None
        self._chinese_fonts_cache: Optional[List[str]] = None

    def detect_chinese_fonts(self) -> List[str]:
        """
        检测系统中可用的中文字体

        Returns:
            中文字体名称列表
        """
        if self._chinese_fonts_cache is not None:
            return self._chinese_fonts_cache

        self.logger.debug("开始检测系统中文字体...")

        try:
            import matplotlib.font_manager as fm

            chinese_fonts = set()

            # 获取所有系统字体
            for font in fm.fontManager.ttflist:
                font_name = font.name

                # 检查字体名称是否包含中文相关的关键词
                # 或者是已知的中文字体
                chinese_keywords = [
                    'CJK', 'Chinese', 'SC', 'TC',
                    'Hei', 'Song', 'Kai', 'Fang',
                    'SimHei', 'SimSun', 'Microsoft YaHei',
                    'STHeiti', 'STSong', 'STKaiti', 'STFangsong',
                    'WenQuanYi', 'Noto Sans', 'Noto Serif',
                    'PingFang', 'Hiragino', 'Arial Unicode',
                    '黑体', '宋体', '楷体', '仿宋',
                    'Droid Sans'
                ]

                for keyword in chinese_keywords:
                    if keyword.lower() in font_name.lower():
                        chinese_fonts.add(font_name)
                        break

            self._chinese_fonts_cache = sorted(list(chinese_fonts))
            self.logger.debug(f"检测到 {len(self._chinese_fonts_cache)} 个中文字体")

            return self._chinese_fonts_cache

        except ImportError:
            self.logger.warning("matplotlib 未安装，无法自动检测中文字体")
            return []
        except Exception as e:
            self.logger.error(f"检测中文字体时出错: {str(e)}")
            return []

    def detect_system_fonts(self) -> List[Dict[str, str]]:
        """
        检测系统中所有字体

        Returns:
            字体信息列表，每个字典包含:
            - name: 字体名称
            - path: 字体文件路径
            - family: 字体家族
        """
        if self._system_fonts_cache is not None:
            return self._system_fonts_cache

        self.logger.debug("扫描系统字体...")

        try:
            import matplotlib.font_manager as fm

            fonts = []
            for font in fm.fontManager.ttflist:
                fonts.append({
                    'name': font.name,
                    'path': font.fname,
                    'family': font.name
                })

            self._system_fonts_cache = fonts
            self.logger.debug(f"找到 {len(fonts)} 个系统字体")

            return fonts

        except ImportError:
            self.logger.warning("matplotlib 未安装，无法扫描系统字体")
            return []
        except Exception as e:
            self.logger.error(f"扫描系统字体时出错: {str(e)}")
            return []

    def validate_font(
        self,
        font_spec: Union[str, Path],
        test_text: str = "测试中文字幕"
    ) -> bool:
        """
        验证字体是否支持中文

        Args:
            font_spec: 字体名称或字体文件路径
            test_text: 用于测试的中文文本

        Returns:
            True 如果字体支持中文，否则 False
        """
        try:
            from PIL import Image, ImageDraw, ImageFont

            # 检查是否为文件路径
            if isinstance(font_spec, Path) or (isinstance(font_spec, str) and '/' in font_spec):
                font_path = Path(font_spec)
                if not font_path.exists():
                    self.logger.debug(f"字体文件不存在: {font_path}")
                    return False

                # 尝试加载字体文件
                try:
                    font = ImageFont.truetype(str(font_path), 24)
                except Exception as e:
                    self.logger.debug(f"无法加载字体文件 {font_path}: {e}")
                    return False
            else:
                # 字体名称 - 尝试从系统加载
                try:
                    # 首先检查字体是否存在
                    if not self.font_exists(str(font_spec)):
                        self.logger.debug(f"系统中不存在字体: {font_spec}")
                        return False

                    # 获取字体路径
                    font_path = self.get_font_path(str(font_spec))
                    if not font_path:
                        self.logger.debug(f"无法获取字体路径: {font_spec}")
                        return False

                    font = ImageFont.truetype(str(font_path), 24)
                except Exception as e:
                    self.logger.debug(f"无法加载系统字体 {font_spec}: {e}")
                    return False

            # 尝试渲染测试文本
            try:
                img = Image.new('RGB', (200, 50), color='white')
                draw = ImageDraw.Draw(img)
                draw.text((10, 10), test_text, font=font, fill='black')

                # 如果能执行到这里，说明字体支持这些字符
                self.logger.debug(f"字体 {font_spec} 通过中文验证")
                return True
            except Exception as e:
                self.logger.debug(f"字体 {font_spec} 无法渲染中文: {e}")
                return False

        except ImportError:
            self.logger.warning("PIL/Pillow 未安装，无法验证字体")
            # 如果无法验证，假设字体可用（降级方案）
            return True
        except Exception as e:
            self.logger.debug(f"验证字体时出错 ({font_spec}): {e}")
            return False

    def font_exists(self, font_name: str) -> bool:
        """
        检查字体是否存在于系统中

        Args:
            font_name: 字体名称

        Returns:
            True 如果字体存在，否则 False
        """
        try:
            system_fonts = self.detect_system_fonts()

            # 大小写不敏感的匹配
            font_name_lower = font_name.lower()
            for font in system_fonts:
                if font['name'].lower() == font_name_lower:
                    return True

            return False

        except Exception as e:
            self.logger.debug(f"检查字体是否存在时出错: {e}")
            return False

    def get_font_path(self, font_name: str) -> Optional[Path]:
        """
        获取字体文件路径

        Args:
            font_name: 字体名称

        Returns:
            字体文件路径，如果未找到返回 None
        """
        try:
            system_fonts = self.detect_system_fonts()

            # 大小写不敏感的匹配
            font_name_lower = font_name.lower()
            for font in system_fonts:
                if font['name'].lower() == font_name_lower:
                    return Path(font['path'])

            return None

        except Exception as e:
            self.logger.debug(f"获取字体路径时出错: {e}")
            return None

    def get_best_font(
        self,
        preferred_fonts: List[Union[str, Path]],
        test_text: str = "测试中文"
    ) -> Optional[Union[str, Path]]:
        """
        从首选字体列表中获取第一个可用且支持中文的字体

        Args:
            preferred_fonts: 首选字体列表（名称或路径）
            test_text: 用于验证的测试文本

        Returns:
            可用的字体名称或路径，如果都不可用返回 None
        """
        self.logger.info(f"从 {len(preferred_fonts)} 个候选字体中选择最佳字体...")

        for font in preferred_fonts:
            self.logger.debug(f"检查字体: {font}")

            # 检查是否为文件路径
            if isinstance(font, Path) or (isinstance(font, str) and ('/' in font or '\\' in font)):
                font_path = Path(font)

                # 检查文件是否存在
                if not font_path.exists():
                    self.logger.debug(f"  ✗ 字体文件不存在")
                    continue

                # 验证字体
                if self.validate_font(font_path, test_text):
                    self.logger.debug(f"  ✓ 字体文件可用且支持中文")
                    return font_path
                else:
                    self.logger.debug(f"  ✗ 字体文件不支持中文")
            else:
                # 字体名称 - 检查系统中是否存在
                if not self.font_exists(str(font)):
                    self.logger.debug(f"  ✗ 系统中不存在该字体")
                    continue

                # 验证字体
                if self.validate_font(font, test_text):
                    self.logger.debug(f"  ✓ 字体可用且支持中文")
                    return font
                else:
                    self.logger.debug(f"  ✗ 字体不支持中文")

        self.logger.warning("未找到任何可用的字体")
        return None

    def get_default_chinese_fonts_by_platform(self) -> List[str]:
        """
        根据操作系统返回默认中文字体列表

        Returns:
            适合当前平台的中文字体列表
        """
        system = platform.system().lower()

        if system == 'darwin':  # macOS
            fonts = [
                'STHeiti Medium',
                'Heiti SC',
                'PingFang SC',
                'Hiragino Sans GB',
                'STSong',
                'Songti SC'
            ]
            self.logger.debug(f"平台: macOS, 默认字体: {fonts[:3]}")
        elif system == 'windows':
            fonts = [
                'Microsoft YaHei',
                'SimHei',
                'SimSun',
                'KaiTi',
                'FangSong'
            ]
            self.logger.debug(f"平台: Windows, 默认字体: {fonts[:3]}")
        elif system == 'linux':
            fonts = [
                'WenQuanYi Micro Hei',
                'WenQuanYi Zen Hei',
                'Noto Sans CJK SC',
                'Droid Sans Fallback',
                'AR PL UMing CN'
            ]
            self.logger.debug(f"平台: Linux, 默认字体: {fonts[:3]}")
        else:
            fonts = []
            self.logger.debug(f"未知平台: {system}")

        # 添加通用回退字体
        fonts.extend([
            'Arial Unicode MS',
            'DejaVu Sans'
        ])

        return fonts

    def get_font_info(self, font_spec: Union[str, Path]) -> Dict[str, str]:
        """
        获取字体详细信息

        Args:
            font_spec: 字体名称或路径

        Returns:
            字体信息字典
        """
        info = {
            'name': str(font_spec),
            'type': 'unknown',
            'exists': False,
            'path': None,
            'supports_chinese': False
        }

        try:
            # 判断是文件路径还是字体名称
            if isinstance(font_spec, Path) or (isinstance(font_spec, str) and '/' in font_spec):
                font_path = Path(font_spec)
                info['type'] = 'file'
                info['exists'] = font_path.exists()
                info['path'] = str(font_path) if font_path.exists() else None
            else:
                info['type'] = 'system'
                info['exists'] = self.font_exists(str(font_spec))
                if info['exists']:
                    path = self.get_font_path(str(font_spec))
                    info['path'] = str(path) if path else None

            # 验证是否支持中文
            if info['exists']:
                info['supports_chinese'] = self.validate_font(font_spec)

        except Exception as e:
            self.logger.debug(f"获取字体信息时出错: {e}")

        return info
