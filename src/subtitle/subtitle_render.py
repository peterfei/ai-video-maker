"""
字幕渲染器
将字幕渲染到视频上
"""

from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from moviepy.editor import TextClip, CompositeVideoClip


class SubtitleRenderer:
    """字幕渲染器类"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化字幕渲染器

        Args:
            config: 配置字典
        """
        self.config = config
        self.enabled = config.get('enabled', True)
        self.font_name = config.get('font_name', 'Arial')
        self.font_size = config.get('font_size', 48)
        self.font_color = config.get('font_color', 'white')
        self.stroke_color = config.get('stroke_color', 'black')
        self.stroke_width = config.get('stroke_width', 2)
        self.position = config.get('position', 'bottom')
        self.margin_bottom = config.get('margin_bottom', 100)
        self.align = config.get('align', 'center')

    def create_text_clips(
        self,
        subtitle_segments: List[Any],
        video_size: Tuple[int, int]
    ) -> List[TextClip]:
        """
        创建文本片段列表

        Args:
            subtitle_segments: 字幕片段列表
            video_size: 视频尺寸 (width, height)

        Returns:
            TextClip列表
        """
        if not self.enabled:
            return []

        text_clips = []

        for segment in subtitle_segments:
            # 创建文本片段
            txt_clip = TextClip(
                segment.text,
                fontsize=self.font_size,
                font=self.font_name,
                color=self.font_color,
                stroke_color=self.stroke_color,
                stroke_width=self.stroke_width,
                method='caption',
                size=(video_size[0] * 0.9, None),  # 宽度为视频的90%
                align=self.align
            )

            # 设置显示时间
            txt_clip = txt_clip.set_start(segment.start_time)
            txt_clip = txt_clip.set_duration(segment.duration)

            # 设置位置
            pos = self._calculate_position(txt_clip.size, video_size)
            txt_clip = txt_clip.set_position(pos)

            text_clips.append(txt_clip)

        return text_clips

    def _calculate_position(
        self,
        text_size: Tuple[int, int],
        video_size: Tuple[int, int]
    ) -> Tuple[str, int]:
        """
        计算字幕位置

        Args:
            text_size: 文本尺寸
            video_size: 视频尺寸

        Returns:
            位置元组 (x, y)
        """
        video_width, video_height = video_size

        # 水平居中
        if self.align == 'center':
            x = 'center'
        elif self.align == 'left':
            x = video_width * 0.05
        else:  # right
            x = video_width * 0.95 - text_size[0]

        # 垂直位置
        if self.position == 'top':
            y = self.margin_bottom
        elif self.position == 'center':
            y = (video_height - text_size[1]) // 2
        else:  # bottom
            y = video_height - text_size[1] - self.margin_bottom

        return (x, y)

    def render_on_video(
        self,
        video_clip: Any,
        subtitle_segments: List[Any]
    ) -> Any:
        """
        将字幕渲染到视频上

        Args:
            video_clip: 视频片段
            subtitle_segments: 字幕片段列表

        Returns:
            带字幕的视频片段
        """
        if not self.enabled or not subtitle_segments:
            return video_clip

        # 创建文本片段
        text_clips = self.create_text_clips(subtitle_segments, video_clip.size)

        if not text_clips:
            return video_clip

        # 合成视频
        final_clip = CompositeVideoClip([video_clip] + text_clips)

        return final_clip

    def create_subtitle_image(
        self,
        text: str,
        image_size: Tuple[int, int],
        font_path: Optional[str] = None
    ) -> Image.Image:
        """
        创建字幕图像（使用PIL）

        Args:
            text: 字幕文本
            image_size: 图像尺寸
            font_path: 字体文件路径

        Returns:
            PIL Image对象
        """
        # 创建透明背景
        img = Image.new('RGBA', image_size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # 加载字体
        try:
            if font_path and Path(font_path).exists():
                font = ImageFont.truetype(font_path, self.font_size)
            else:
                # 尝试使用系统字体
                font = ImageFont.truetype(self.font_name, self.font_size)
        except Exception:
            # 使用默认字体
            font = ImageFont.load_default()

        # 计算文本位置
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        x = (image_size[0] - text_width) // 2
        if self.position == 'bottom':
            y = image_size[1] - text_height - self.margin_bottom
        elif self.position == 'top':
            y = self.margin_bottom
        else:  # center
            y = (image_size[1] - text_height) // 2

        # 绘制描边
        if self.stroke_width > 0:
            for offset_x in range(-self.stroke_width, self.stroke_width + 1):
                for offset_y in range(-self.stroke_width, self.stroke_width + 1):
                    draw.text(
                        (x + offset_x, y + offset_y),
                        text,
                        font=font,
                        fill=self.stroke_color
                    )

        # 绘制主文本
        draw.text((x, y), text, font=font, fill=self.font_color)

        return img

    def create_animated_subtitle(
        self,
        text: str,
        duration: float,
        video_size: Tuple[int, int],
        effect: str = "fade"
    ) -> TextClip:
        """
        创建带动画效果的字幕

        Args:
            text: 字幕文本
            duration: 持续时间
            video_size: 视频尺寸
            effect: 动画效果 (fade, slide, zoom)

        Returns:
            TextClip对象
        """
        # 创建基础文本片段
        txt_clip = TextClip(
            text,
            fontsize=self.font_size,
            font=self.font_name,
            color=self.font_color,
            stroke_color=self.stroke_color,
            stroke_width=self.stroke_width,
            method='caption',
            size=(video_size[0] * 0.9, None),
            align=self.align
        )

        txt_clip = txt_clip.set_duration(duration)

        # 设置位置
        pos = self._calculate_position(txt_clip.size, video_size)
        txt_clip = txt_clip.set_position(pos)

        # 添加动画效果
        if effect == "fade":
            # 淡入淡出
            fade_duration = min(0.3, duration / 4)
            txt_clip = txt_clip.crossfadein(fade_duration)
            txt_clip = txt_clip.crossfadeout(fade_duration)

        elif effect == "slide":
            # 从底部滑入
            start_pos = (pos[0], video_size[1])
            txt_clip = txt_clip.set_position(
                lambda t: (
                    pos[0],
                    start_pos[1] - (start_pos[1] - pos[1]) * min(t / 0.5, 1.0)
                )
            )

        elif effect == "zoom":
            # 缩放效果
            txt_clip = txt_clip.resize(
                lambda t: 0.5 + 0.5 * min(t / 0.3, 1.0)
            )

        return txt_clip

    def batch_render_subtitles(
        self,
        video_clip: Any,
        subtitle_segments: List[Any],
        effect: Optional[str] = None
    ) -> Any:
        """
        批量渲染字幕到视频

        Args:
            video_clip: 视频片段
            subtitle_segments: 字幕片段列表
            effect: 动画效果（可选）

        Returns:
            带字幕的视频片段
        """
        if not self.enabled or not subtitle_segments:
            return video_clip

        text_clips = []

        for segment in subtitle_segments:
            if effect:
                txt_clip = self.create_animated_subtitle(
                    segment.text,
                    segment.duration,
                    video_clip.size,
                    effect
                )
            else:
                txt_clip = TextClip(
                    segment.text,
                    fontsize=self.font_size,
                    font=self.font_name,
                    color=self.font_color,
                    stroke_color=self.stroke_color,
                    stroke_width=self.stroke_width
                )

            txt_clip = txt_clip.set_start(segment.start_time)
            txt_clip = txt_clip.set_duration(segment.duration)

            pos = self._calculate_position(txt_clip.size, video_clip.size)
            txt_clip = txt_clip.set_position(pos)

            text_clips.append(txt_clip)

        # 合成视频
        final_clip = CompositeVideoClip([video_clip] + text_clips)

        return final_clip

    def get_available_fonts(self) -> List[str]:
        """
        获取系统可用字体列表

        Returns:
            字体名称列表
        """
        import matplotlib.font_manager as fm

        fonts = fm.findSystemFonts()
        font_names = [fm.FontProperties(fname=f).get_name() for f in fonts]

        return sorted(set(font_names))
