"""
视频效果处理
提供各种视频特效
"""

from typing import Callable, Tuple
from moviepy.editor import VideoClip
import numpy as np


class VideoEffects:
    """视频效果类"""

    @staticmethod
    def fade_in(clip: VideoClip, duration: float = 1.0) -> VideoClip:
        """
        淡入效果

        Args:
            clip: 视频片段
            duration: 淡入持续时间

        Returns:
            VideoClip对象
        """
        return clip.fadein(duration)

    @staticmethod
    def fade_out(clip: VideoClip, duration: float = 1.0) -> VideoClip:
        """
        淡出效果

        Args:
            clip: 视频片段
            duration: 淡出持续时间

        Returns:
            VideoClip对象
        """
        return clip.fadeout(duration)

    @staticmethod
    def crossfade_in(clip: VideoClip, duration: float = 1.0) -> VideoClip:
        """
        交叉淡入效果

        Args:
            clip: 视频片段
            duration: 持续时间

        Returns:
            VideoClip对象
        """
        return clip.crossfadein(duration)

    @staticmethod
    def crossfade_out(clip: VideoClip, duration: float = 1.0) -> VideoClip:
        """
        交叉淡出效果

        Args:
            clip: 视频片段
            duration: 持续时间

        Returns:
            VideoClip对象
        """
        return clip.crossfadeout(duration)

    @staticmethod
    def speed_up(clip: VideoClip, factor: float = 2.0) -> VideoClip:
        """
        加速视频

        Args:
            clip: 视频片段
            factor: 加速倍数

        Returns:
            VideoClip对象
        """
        return clip.speedx(factor)

    @staticmethod
    def slow_down(clip: VideoClip, factor: float = 0.5) -> VideoClip:
        """
        减速视频

        Args:
            clip: 视频片段
            factor: 减速倍数

        Returns:
            VideoClip对象
        """
        return clip.speedx(factor)

    @staticmethod
    def black_and_white(clip: VideoClip) -> VideoClip:
        """
        黑白效果

        Args:
            clip: 视频片段

        Returns:
            VideoClip对象
        """
        def bw_effect(get_frame, t):
            frame = get_frame(t)
            # 转换为灰度
            gray = np.dot(frame[...,:3], [0.299, 0.587, 0.114])
            # 扩展到3通道
            return np.stack([gray, gray, gray], axis=-1).astype('uint8')

        return clip.fl(bw_effect)

    @staticmethod
    def adjust_brightness(clip: VideoClip, factor: float = 1.2) -> VideoClip:
        """
        调整亮度

        Args:
            clip: 视频片段
            factor: 亮度倍数 (>1增加, <1减少)

        Returns:
            VideoClip对象
        """
        def brightness_effect(get_frame, t):
            frame = get_frame(t)
            adjusted = np.clip(frame * factor, 0, 255).astype('uint8')
            return adjusted

        return clip.fl(brightness_effect)

    @staticmethod
    def adjust_contrast(clip: VideoClip, factor: float = 1.5) -> VideoClip:
        """
        调整对比度

        Args:
            clip: 视频片段
            factor: 对比度倍数

        Returns:
            VideoClip对象
        """
        def contrast_effect(get_frame, t):
            frame = get_frame(t)
            # 计算均值
            mean = np.mean(frame)
            # 调整对比度
            adjusted = np.clip((frame - mean) * factor + mean, 0, 255).astype('uint8')
            return adjusted

        return clip.fl(contrast_effect)

    @staticmethod
    def vignette(clip: VideoClip, strength: float = 0.5) -> VideoClip:
        """
        添加暗角效果

        Args:
            clip: 视频片段
            strength: 强度 (0-1)

        Returns:
            VideoClip对象
        """
        def vignette_effect(get_frame, t):
            frame = get_frame(t)
            h, w = frame.shape[:2]

            # 创建径向渐变蒙版
            Y, X = np.ogrid[:h, :w]
            center_y, center_x = h / 2, w / 2

            # 计算距离
            dist = np.sqrt((X - center_x)**2 + (Y - center_y)**2)
            max_dist = np.sqrt(center_x**2 + center_y**2)

            # 创建蒙版
            mask = 1 - (dist / max_dist * strength)
            mask = np.clip(mask, 0, 1)

            # 应用蒙版
            if len(frame.shape) == 3:
                mask = mask[:, :, np.newaxis]

            vignetted = (frame * mask).astype('uint8')
            return vignetted

        return clip.fl(vignette_effect)

    @staticmethod
    def blur(clip: VideoClip, blur_radius: int = 5) -> VideoClip:
        """
        模糊效果

        Args:
            clip: 视频片段
            blur_radius: 模糊半径

        Returns:
            VideoClip对象
        """
        from PIL import Image, ImageFilter

        def blur_effect(get_frame, t):
            frame = get_frame(t)
            img = Image.fromarray(frame)
            blurred = img.filter(ImageFilter.GaussianBlur(blur_radius))
            return np.array(blurred)

        return clip.fl(blur_effect)

    @staticmethod
    def slide_in(
        clip: VideoClip,
        duration: float = 1.0,
        direction: str = "left"
    ) -> VideoClip:
        """
        滑入效果

        Args:
            clip: 视频片段
            duration: 持续时间
            direction: 方向 (left, right, top, bottom)

        Returns:
            VideoClip对象
        """
        w, h = clip.size

        if direction == "left":
            # 从左侧滑入
            return clip.set_position(
                lambda t: (max(0, w - w * (t / duration)), 0) if t < duration else (0, 0)
            )
        elif direction == "right":
            # 从右侧滑入
            return clip.set_position(
                lambda t: (min(0, -w + w * (t / duration)), 0) if t < duration else (0, 0)
            )
        elif direction == "top":
            # 从顶部滑入
            return clip.set_position(
                lambda t: (0, max(0, h - h * (t / duration))) if t < duration else (0, 0)
            )
        else:  # bottom
            # 从底部滑入
            return clip.set_position(
                lambda t: (0, min(0, -h + h * (t / duration))) if t < duration else (0, 0)
            )

    @staticmethod
    def zoom_effect(
        clip: VideoClip,
        zoom_ratio: float = 0.2,
        direction: str = "in"
    ) -> VideoClip:
        """
        缩放效果

        Args:
            clip: 视频片段
            zoom_ratio: 缩放比例
            direction: 方向 (in/out)

        Returns:
            VideoClip对象
        """
        def zoom(t):
            progress = t / clip.duration

            if direction == "in":
                # 放大
                scale = 1 + zoom_ratio * progress
            else:
                # 缩小
                scale = 1 + zoom_ratio * (1 - progress)

            return scale

        return clip.resize(zoom)

    @staticmethod
    def rotate(clip: VideoClip, angle: float) -> VideoClip:
        """
        旋转视频

        Args:
            clip: 视频片段
            angle: 旋转角度

        Returns:
            VideoClip对象
        """
        return clip.rotate(angle)

    @staticmethod
    def mirror_horizontal(clip: VideoClip) -> VideoClip:
        """
        水平镜像

        Args:
            clip: 视频片段

        Returns:
            VideoClip对象
        """
        return clip.fx(lambda c: c.fl_image(lambda img: np.fliplr(img)))

    @staticmethod
    def mirror_vertical(clip: VideoClip) -> VideoClip:
        """
        垂直镜像

        Args:
            clip: 视频片段

        Returns:
            VideoClip对象
        """
        return clip.fx(lambda c: c.fl_image(lambda img: np.flipud(img)))

    @staticmethod
    def sepia(clip: VideoClip) -> VideoClip:
        """
        怀旧色调效果

        Args:
            clip: 视频片段

        Returns:
            VideoClip对象
        """
        def sepia_effect(get_frame, t):
            frame = get_frame(t)

            # Sepia矩阵
            sepia_matrix = np.array([
                [0.393, 0.769, 0.189],
                [0.349, 0.686, 0.168],
                [0.272, 0.534, 0.131]
            ])

            # 应用矩阵变换
            sepia_frame = frame.dot(sepia_matrix.T)
            sepia_frame = np.clip(sepia_frame, 0, 255).astype('uint8')

            return sepia_frame

        return clip.fl(sepia_effect)

    @staticmethod
    def apply_multiple_effects(
        clip: VideoClip,
        effects: list
    ) -> VideoClip:
        """
        应用多个效果

        Args:
            clip: 视频片段
            effects: 效果函数列表

        Returns:
            VideoClip对象
        """
        result = clip

        for effect_func in effects:
            result = effect_func(result)

        return result
