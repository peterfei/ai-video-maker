"""
视频合成器
整合所有元素生成最终视频
"""

from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from moviepy.editor import (
    VideoClip, ImageClip, AudioFileClip, CompositeVideoClip,
    concatenate_videoclips, ColorClip
)
import numpy as np


class VideoCompositor:
    """视频合成器类"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化视频合成器

        Args:
            config: 配置字典
        """
        self.config = config
        self.resolution = tuple(config.get('resolution', [1920, 1080]))
        self.fps = config.get('fps', 30)
        self.codec = config.get('codec', 'libx264')
        self.bitrate = config.get('bitrate', '5000k')
        self.background_color = config.get('background_color', [0, 0, 0])

    def create_slideshow(
        self,
        images: List[Path],
        audio_path: Optional[str] = None,
        image_duration: float = 5.0,
        transition: str = "fade",
        transition_duration: float = 0.5
    ) -> VideoClip:
        """
        创建图片幻灯片视频

        Args:
            images: 图片路径列表
            audio_path: 音频文件路径
            image_duration: 每张图片持续时间
            transition: 转场效果 (fade/none)
            transition_duration: 转场持续时间

        Returns:
            VideoClip对象
        """
        if not images:
            raise ValueError("图片列表不能为空")

        # 如果有音频，先获取音频时长以调整素材时长
        audio_duration = None
        if audio_path:
            audio = AudioFileClip(audio_path)
            audio_duration = audio.duration

        # 创建图片片段列表
        clips = []

        # 计算每张图片的实际持续时间
        if audio_duration and len(images) > 1 and transition == "fade":
            # 考虑转场重叠，计算单个图片时长
            # 总时长 = n * 图片时长 - (n-1) * 转场时长
            # 图片时长 = (总时长 + (n-1) * 转场时长) / n
            n = len(images)
            adjusted_image_duration = (audio_duration + (n - 1) * transition_duration) / n
        elif audio_duration:
            # 无转场，平均分配时间
            adjusted_image_duration = audio_duration / len(images)
        else:
            adjusted_image_duration = image_duration

        for img_path in images:
            # 加载图片
            clip = ImageClip(str(img_path))

            # 调整大小
            clip = clip.resize(self.resolution)

            # 设置持续时间
            clip = clip.set_duration(adjusted_image_duration)

            clips.append(clip)

        # 应用转场效果
        if transition == "fade" and len(clips) > 1:
            # 使用crossfade进行转场
            for i in range(len(clips)):
                if i > 0:
                    clips[i] = clips[i].crossfadein(transition_duration)
                if i < len(clips) - 1:
                    clips[i] = clips[i].crossfadeout(transition_duration)

            # 使用compose方法进行拼接，支持重叠
            video = concatenate_videoclips(clips, method="compose")
        else:
            # 无转场，直接拼接
            video = concatenate_videoclips(clips)

        # 添加音频
        if audio_path:
            # 微调视频时长以精确匹配音频
            if abs(video.duration - audio_duration) > 0.1:
                if video.duration > audio_duration:
                    # 裁剪视频
                    video = video.subclip(0, audio_duration)
                else:
                    # 延长最后一帧
                    extension = ColorClip(
                        size=self.resolution,
                        color=self.background_color,
                        duration=audio_duration - video.duration
                    )
                    video = concatenate_videoclips([video, extension])

            # 设置音频
            video = video.set_audio(audio)

        video = video.set_fps(self.fps)

        return video

    def create_video_from_clips(
        self,
        video_clips: List[VideoClip],
        transition: str = "cut"
    ) -> VideoClip:
        """
        从多个视频片段创建完整视频

        Args:
            video_clips: 视频片段列表
            transition: 转场效果

        Returns:
            VideoClip对象
        """
        if not video_clips:
            raise ValueError("视频片段列表不能为空")

        # 调整所有片段的分辨率
        clips = []
        for clip in video_clips:
            resized_clip = clip.resize(self.resolution)
            clips.append(resized_clip)

        # 拼接视频
        if transition == "cut":
            final_video = concatenate_videoclips(clips)
        else:
            # 其他转场效果可以在这里添加
            final_video = concatenate_videoclips(clips, method="compose")

        return final_video.set_fps(self.fps)

    def create_background_video(
        self,
        duration: float,
        background_type: str = "color"
    ) -> VideoClip:
        """
        创建背景视频

        Args:
            duration: 持续时间
            background_type: 背景类型 (color, gradient)

        Returns:
            VideoClip对象
        """
        if background_type == "color":
            # 纯色背景
            bg = ColorClip(
                size=self.resolution,
                color=self.background_color,
                duration=duration
            )
        else:
            # 可以添加更多背景类型
            bg = ColorClip(
                size=self.resolution,
                color=self.background_color,
                duration=duration
            )

        return bg.set_fps(self.fps)

    def compose_video(
        self,
        background: VideoClip,
        overlays: List[VideoClip],
        audio: Optional[AudioFileClip] = None
    ) -> VideoClip:
        """
        合成视频（背景+叠加层）

        Args:
            background: 背景视频
            overlays: 叠加层列表
            audio: 音频（可选）

        Returns:
            VideoClip对象
        """
        # 合成所有层
        all_clips = [background] + overlays
        final_video = CompositeVideoClip(all_clips)

        # 添加音频
        if audio:
            final_video = final_video.set_audio(audio)

        return final_video

    def add_zoom_effect(
        self,
        clip: VideoClip,
        zoom_factor: float = 1.2,
        center: Optional[Tuple[float, float]] = None
    ) -> VideoClip:
        """
        添加缩放效果

        Args:
            clip: 视频片段
            zoom_factor: 缩放倍数
            center: 缩放中心点（归一化坐标）

        Returns:
            添加了缩放效果的VideoClip
        """
        if center is None:
            center = (0.5, 0.5)

        def zoom(get_frame, t):
            frame = get_frame(t)
            h, w = frame.shape[:2]

            # 计算缩放
            progress = t / clip.duration
            current_zoom = 1 + (zoom_factor - 1) * progress

            # 缩放中心
            cx = int(w * center[0])
            cy = int(h * center[1])

            # 裁剪区域
            new_w = int(w / current_zoom)
            new_h = int(h / current_zoom)

            x1 = max(0, cx - new_w // 2)
            y1 = max(0, cy - new_h // 2)
            x2 = min(w, x1 + new_w)
            y2 = min(h, y1 + new_h)

            # 裁剪并缩放
            cropped = frame[y1:y2, x1:x2]

            from PIL import Image
            img = Image.fromarray(cropped)
            img = img.resize((w, h), Image.Resampling.LANCZOS)

            return np.array(img)

        return clip.fl(zoom)

    def render_video(
        self,
        video_clip: VideoClip,
        output_path: str,
        preset: str = "medium"
    ) -> Path:
        """
        渲染并导出视频

        Args:
            video_clip: 视频片段
            output_path: 输出路径
            preset: 编码预设 (ultrafast, fast, medium, slow, veryslow)

        Returns:
            输出文件路径
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 导出视频
        video_clip.write_videofile(
            str(output_path),
            fps=self.fps,
            codec=self.codec,
            bitrate=self.bitrate,
            preset=preset,
            audio_codec='aac',
            logger=None,
            threads=4
        )

        # 清理
        video_clip.close()

        return output_path

    def create_picture_in_picture(
        self,
        main_video: VideoClip,
        overlay_video: VideoClip,
        position: Tuple[int, int] = (50, 50),
        scale: float = 0.25
    ) -> VideoClip:
        """
        创建画中画效果

        Args:
            main_video: 主视频
            overlay_video: 叠加视频
            position: 位置 (x, y)
            scale: 叠加视频的缩放比例

        Returns:
            VideoClip对象
        """
        # 缩放叠加视频
        overlay_resized = overlay_video.resize(scale)

        # 设置位置
        overlay_positioned = overlay_resized.set_position(position)

        # 合成
        final_video = CompositeVideoClip([main_video, overlay_positioned])

        return final_video

    def add_watermark(
        self,
        video: VideoClip,
        watermark_path: str,
        position: str = "bottom-right",
        opacity: float = 0.5,
        scale: float = 0.1
    ) -> VideoClip:
        """
        添加水印

        Args:
            video: 视频片段
            watermark_path: 水印图片路径
            position: 位置
            opacity: 透明度
            scale: 缩放比例

        Returns:
            VideoClip对象
        """
        # 加载水印
        watermark = ImageClip(watermark_path)

        # 调整大小
        wm_width = int(video.w * scale)
        watermark = watermark.resize(width=wm_width)

        # 设置透明度
        watermark = watermark.set_opacity(opacity)

        # 计算位置
        margin = 20
        if position == "bottom-right":
            pos = (video.w - watermark.w - margin, video.h - watermark.h - margin)
        elif position == "bottom-left":
            pos = (margin, video.h - watermark.h - margin)
        elif position == "top-right":
            pos = (video.w - watermark.w - margin, margin)
        else:  # top-left
            pos = (margin, margin)

        watermark = watermark.set_position(pos)
        watermark = watermark.set_duration(video.duration)

        # 合成
        final_video = CompositeVideoClip([video, watermark])

        return final_video

    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """
        获取视频信息

        Args:
            video_path: 视频文件路径

        Returns:
            视频信息字典
        """
        from moviepy.editor import VideoFileClip

        try:
            video = VideoFileClip(video_path)
            info = {
                'duration': video.duration,
                'fps': video.fps,
                'size': video.size,
                'has_audio': video.audio is not None
            }
            video.close()
            return info
        except Exception as e:
            return {'error': str(e)}
