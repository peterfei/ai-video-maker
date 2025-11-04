"""
字体大小管理器
统一管理字幕字体大小，确保在不同渲染引擎和分辨率下显示一致
"""

from typing import Dict, Tuple, List, Any, Optional
import logging


class FontSizeManager:
    """字体大小管理器类"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        初始化字体大小管理器

        Args:
            logger: 日志记录器
        """
        self.logger = logger or logging.getLogger(__name__)

        # 字体大小转换因子 (MoviePy vs PIL)
        # MoviePy TextClip 的字体大小大约是 PIL ImageFont 的 0.75 倍
        self.MOVIEPY_TO_PIL_FACTOR = 1.333  # PIL = MoviePy × 1.333
        self.PIL_TO_MOVIEPY_FACTOR = 0.75   # MoviePy = PIL × 0.75

        # 默认配置
        self.default_config = {
            'adaptive_font_size': True,
            'min_font_size': 24,
            'max_font_size': 72,
            'font_size_scale_factor': 0.02,
            'reference_width': 1920  # 1080p 宽度作为参考
        }

    def normalize_font_size(
        self,
        base_size: int,
        video_resolution: Tuple[int, int],
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, int]:
        """
        标准化字体大小为不同渲染引擎

        Args:
            base_size: 基础字体大小 (pt)
            video_resolution: 视频分辨率 (width, height)
            config: 配置字典

        Returns:
            包含不同引擎字体大小的字典
        """
        config = config or {}
        merged_config = {**self.default_config, **config}

        # 计算自适应字体大小
        if merged_config.get('adaptive_font_size', True):
            scaled_size = self.get_adaptive_font_size(
                base_size,
                video_resolution[0],
                merged_config.get('font_size_scale_factor', 0.02),
                merged_config.get('reference_width', 1920)
            )
        else:
            scaled_size = base_size

        # 确保在合理范围内
        scaled_size = max(
            merged_config.get('min_font_size', 24),
            min(scaled_size, merged_config.get('max_font_size', 72))
        )

        # 计算不同引擎的字体大小
        moviepy_size = scaled_size
        pil_size = int(scaled_size * self.MOVIEPY_TO_PIL_FACTOR)

        result = {
            'moviepy_size': moviepy_size,
            'pil_size': pil_size,
            'scaled_size': scaled_size,
            'base_size': base_size
        }

        self.logger.debug(f"标准化字体大小: {result}")
        return result

    def get_adaptive_font_size(
        self,
        base_size: int,
        video_width: int,
        scale_factor: float = 0.02,
        reference_width: int = 1920
    ) -> int:
        """
        计算自适应字体大小

        Args:
            base_size: 基础字体大小
            video_width: 视频宽度
            scale_factor: 缩放因子
            reference_width: 参考宽度

        Returns:
            自适应字体大小
        """
        if video_width <= 0 or reference_width <= 0:
            return base_size

        # 自适应公式: 基础大小 + 基础大小 × (视频宽度差比例 × 缩放因子)
        width_ratio = (video_width - reference_width) / reference_width
        adaptive_adjustment = base_size * width_ratio * scale_factor

        result = int(base_size + adaptive_adjustment)

        self.logger.debug(
            f"自适应字体大小: base={base_size}, width={video_width}, "
            f"ratio={width_ratio:.3f}, adjustment={adaptive_adjustment:.1f}, result={result}"
        )

        return result

    def validate_font_size_consistency(
        self,
        font_size: int,
        video_size: Tuple[int, int],
        text_sample: str = "测试字幕",
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        验证字体大小一致性

        Args:
            font_size: 字体大小
            video_size: 视频尺寸
            text_sample: 测试文本
            config: 配置字典

        Returns:
            验证结果字典
        """
        config = config or {}
        merged_config = {**self.default_config, **config}

        warnings = []
        is_valid = True
        metrics = {}

        # 检查字体大小范围
        min_size = merged_config.get('min_font_size', 24)
        max_size = merged_config.get('max_font_size', 72)

        if font_size < min_size:
            warnings.append(f"字体大小 {font_size} 小于最小值 {min_size}")
            is_valid = False

        if font_size > max_size:
            warnings.append(f"字体大小 {font_size} 大于最大值 {max_size}")
            is_valid = False

        # 计算相对于视频尺寸的比例
        video_width, video_height = video_size
        width_ratio = font_size / video_width
        height_ratio = font_size / video_height

        metrics.update({
            'width_ratio': width_ratio,
            'height_ratio': height_ratio,
            'video_width': video_width,
            'video_height': video_height,
            'font_size': font_size
        })

        # 检查比例是否合理 (经验值)
        if width_ratio > 0.05:  # 字体大小超过视频宽度的5%
            warnings.append(f"字体相对于视频宽度过大 ({width_ratio:.3f})")

        if height_ratio > 0.08:  # 字体大小超过视频高度的8%
            warnings.append(f"字体相对于视频高度过大 ({height_ratio:.3f})")

        # 记录验证结果
        if warnings:
            self.logger.warning(f"字体大小验证警告: {'; '.join(warnings)}")
        else:
            self.logger.debug(f"字体大小验证通过: size={font_size}, video={video_size}")

        return {
            'is_valid': is_valid,
            'warnings': warnings,
            'metrics': metrics
        }

    def get_recommended_font_size(
        self,
        video_resolution: Tuple[int, int],
        content_type: str = "normal",
        config: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        根据视频分辨率和内容类型推荐字体大小

        Args:
            video_resolution: 视频分辨率 (width, height)
            content_type: 内容类型 (normal, title, caption)
            config: 配置字典

        Returns:
            推荐的字体大小
        """
        config = config or {}
        video_width, video_height = video_resolution

        # 基础字体大小推荐 (基于视频宽度)
        if video_width <= 1280:  # 720p
            base_recommendation = 36
        elif video_width <= 1920:  # 1080p
            base_recommendation = 48
        elif video_width <= 2560:  # 1440p
            base_recommendation = 56
        else:  # 4K+
            base_recommendation = 64

        # 根据内容类型调整
        type_multipliers = {
            'title': 1.5,      # 标题更大
            'caption': 0.8,    # 字幕稍小
            'normal': 1.0      # 标准大小
        }

        multiplier = type_multipliers.get(content_type, 1.0)
        recommended = int(base_recommendation * multiplier)

        # 应用配置约束
        merged_config = {**self.default_config, **config}
        recommended = max(
            merged_config.get('min_font_size', 24),
            min(recommended, merged_config.get('max_font_size', 72))
        )

        self.logger.debug(
            f"推荐字体大小: resolution={video_resolution}, type={content_type}, "
            f"base={base_recommendation}, multiplier={multiplier}, final={recommended}"
        )

        return recommended

    def get_font_size_range_for_resolution(
        self,
        video_resolution: Tuple[int, int]
    ) -> Tuple[int, int]:
        """
        根据视频分辨率获取合适的字体大小范围

        Args:
            video_resolution: 视频分辨率 (width, height)

        Returns:
            (最小字体大小, 最大字体大小) 元组
        """
        video_width, _ = video_resolution

        if video_width <= 1280:  # 720p
            return (24, 48)
        elif video_width <= 1920:  # 1080p
            return (32, 64)
        elif video_width <= 2560:  # 1440p
            return (40, 72)
        else:  # 4K+
            return (48, 96)
