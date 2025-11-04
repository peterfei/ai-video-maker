"""
GPU加速视频效果处理器
提供GPU加速的视频特效处理
"""

import torch
import torch.nn.functional as F
import numpy as np
from typing import Optional, Tuple, Dict, Any, Callable
from moviepy.editor import VideoClip
import cv2

from .gpu_accelerator import GPUVideoAccelerator


class GPUEffectsProcessor:
    """
    GPU加速的特效处理器

    支持各种视频效果的GPU加速处理，
    在GPU不可用时自动回退到CPU处理。
    """

    def __init__(self, gpu_accelerator: GPUVideoAccelerator):
        """
        初始化GPU效果处理器

        Args:
            gpu_accelerator: GPU加速器实例
        """
        self.gpu = gpu_accelerator
        self.logger = gpu_accelerator.logger

    def is_gpu_available(self) -> bool:
        """检查GPU是否可用"""
        return self.gpu.is_gpu_available()

    def apply_transition_gpu(self,
                           clip_a: VideoClip,
                           clip_b: VideoClip,
                           transition_type: str = 'fade',
                           duration: float = 0.5) -> VideoClip:
        """
        GPU加速的转场效果

        Args:
            clip_a: 第一个视频片段
            clip_b: 第二个视频片段
            transition_type: 转场类型 ('fade', 'dissolve', 'slide')
            duration: 转场持续时间

        Returns:
            合成后的视频片段
        """
        if not self.is_gpu_available():
            return self._apply_transition_cpu(clip_a, clip_b, transition_type, duration)

        try:
            if transition_type == 'fade':
                return self._gpu_fade_transition(clip_a, clip_b, duration)
            elif transition_type == 'dissolve':
                return self._gpu_dissolve_transition(clip_a, clip_b, duration)
            elif transition_type == 'slide':
                return self._gpu_slide_transition(clip_a, clip_b, duration)
            else:
                self.logger.warning(f"Unsupported transition type: {transition_type}, falling back to CPU")
                return self._apply_transition_cpu(clip_a, clip_b, transition_type, duration)
        except Exception as e:
            self.logger.warning(f"GPU transition failed: {e}, falling back to CPU")
            return self._apply_transition_cpu(clip_a, clip_b, transition_type, duration)

    def _gpu_fade_transition(self, clip_a: VideoClip, clip_b: VideoClip, duration: float) -> VideoClip:
        """GPU加速的淡入淡出转场"""
        device = self.gpu.get_device()

        def gpu_fade_frame(t):
            if t < clip_a.duration - duration:
                # clip_a 正常播放
                return clip_a.get_frame(t)
            elif t < clip_a.duration:
                # 转场阶段
                progress = (t - (clip_a.duration - duration)) / duration
                frame_a = clip_a.get_frame(t)
                frame_b = clip_b.get_frame(t - (clip_a.duration - duration))

                # 转换为tensor
                tensor_a = self.gpu.create_tensor(frame_a / 255.0).permute(2, 0, 1).unsqueeze(0)
                tensor_b = self.gpu.create_tensor(frame_b / 255.0).permute(2, 0, 1).unsqueeze(0)

                # GPU线性插值
                alpha = torch.tensor(progress, device=device).unsqueeze(-1).unsqueeze(-1).unsqueeze(-1)
                result = tensor_a * (1 - alpha) + tensor_b * alpha

                # 转回numpy
                result = result.squeeze(0).permute(1, 2, 0).cpu().numpy()
                return (result * 255).astype(np.uint8)
            else:
                # clip_b 正常播放
                return clip_b.get_frame(t - clip_a.duration + duration)

        return VideoClip(gpu_fade_frame, duration=clip_a.duration + clip_b.duration - duration)

    def _gpu_dissolve_transition(self, clip_a: VideoClip, clip_b: VideoClip, duration: float) -> VideoClip:
        """GPU加速的溶解转场"""
        device = self.gpu.get_device()

        def gpu_dissolve_frame(t):
            if t < clip_a.duration - duration:
                return clip_a.get_frame(t)
            elif t < clip_a.duration:
                progress = (t - (clip_a.duration - duration)) / duration
                frame_a = clip_a.get_frame(t)
                frame_b = clip_b.get_frame(t - (clip_a.duration - duration))

                # 创建随机噪声蒙版
                np.random.seed(int(t * 1000))  # 确定性随机种子
                mask = np.random.random(frame_a.shape[:2]) < progress
                mask = mask.astype(np.float32)

                # 扩展到3通道
                mask = np.stack([mask, mask, mask], axis=-1)

                # GPU混合
                tensor_a = self.gpu.create_tensor(frame_a / 255.0)
                tensor_b = self.gpu.create_tensor(frame_b / 255.0)
                tensor_mask = self.gpu.create_tensor(mask)

                result = tensor_a * (1 - tensor_mask) + tensor_b * tensor_mask
                result = result.cpu().numpy()

                return (result * 255).astype(np.uint8)
            else:
                return clip_b.get_frame(t - clip_a.duration + duration)

        return VideoClip(gpu_dissolve_frame, duration=clip_a.duration + clip_b.duration - duration)

    def _gpu_slide_transition(self, clip_a: VideoClip, clip_b: VideoClip, duration: float) -> VideoClip:
        """GPU加速的滑动转场"""
        device = self.gpu.get_device()
        width, height = clip_a.size

        def gpu_slide_frame(t):
            if t < clip_a.duration - duration:
                return clip_a.get_frame(t)
            elif t < clip_a.duration:
                progress = (t - (clip_a.duration - duration)) / duration
                frame_a = clip_a.get_frame(t)
                frame_b = clip_b.get_frame(t - (clip_a.duration - duration))

                # 计算滑动偏移
                offset = int(width * progress)

                # GPU图像拼接
                tensor_a = self.gpu.create_tensor(frame_a / 255.0).permute(2, 0, 1).unsqueeze(0)
                tensor_b = self.gpu.create_tensor(frame_b / 255.0).permute(2, 0, 1).unsqueeze(0)

                # 创建滑动效果
                result = torch.zeros_like(tensor_a)

                # 左侧显示clip_a，右侧显示clip_b
                if offset < width:
                    result[:, :, :, :width-offset] = tensor_a[:, :, :, :width-offset]
                    result[:, :, :, width-offset:] = tensor_b[:, :, :, width-offset:]

                result = result.squeeze(0).permute(1, 2, 0).cpu().numpy()
                return (result * 255).astype(np.uint8)
            else:
                return clip_b.get_frame(t - clip_a.duration + duration)

        return VideoClip(gpu_slide_frame, duration=clip_a.duration + clip_b.duration - duration)

    def _apply_transition_cpu(self, clip_a: VideoClip, clip_b: VideoClip,
                            transition_type: str, duration: float) -> VideoClip:
        """CPU回退方案"""
        from .effects import VideoEffects
        return VideoEffects.create_fade_transition(clip_a, clip_b, duration)

    def apply_color_effect_gpu(self, clip: VideoClip, effect_type: str, **kwargs) -> VideoClip:
        """
        GPU加速的颜色效果

        Args:
            clip: 视频片段
            effect_type: 效果类型 ('brightness', 'contrast', 'saturation', 'sepia', 'bw')
            **kwargs: 效果参数

        Returns:
            处理后的视频片段
        """
        if not self.is_gpu_available():
            return self._apply_color_effect_cpu(clip, effect_type, **kwargs)

        try:
            if effect_type == 'brightness':
                return self._gpu_brightness(clip, kwargs.get('factor', 1.2))
            elif effect_type == 'contrast':
                return self._gpu_contrast(clip, kwargs.get('factor', 1.5))
            elif effect_type == 'saturation':
                return self._gpu_saturation(clip, kwargs.get('factor', 1.2))
            elif effect_type == 'sepia':
                return self._gpu_sepia(clip)
            elif effect_type == 'bw':
                return self._gpu_black_and_white(clip)
            else:
                self.logger.warning(f"Unsupported color effect: {effect_type}, falling back to CPU")
                return self._apply_color_effect_cpu(clip, effect_type, **kwargs)
        except Exception as e:
            self.logger.warning(f"GPU color effect failed: {e}, falling back to CPU")
            return self._apply_color_effect_cpu(clip, effect_type, **kwargs)

    def _gpu_brightness(self, clip: VideoClip, factor: float) -> VideoClip:
        """GPU加速的亮度调整"""
        device = self.gpu.get_device()

        def brightness_frame(t):
            frame = clip.get_frame(t)
            tensor = self.gpu.create_tensor(frame / 255.0)

            # GPU亮度调整
            result = torch.clamp(tensor * factor, 0, 1)
            result = result.cpu().numpy()

            return (result * 255).astype(np.uint8)

        return clip.fl(brightness_frame)

    def _gpu_contrast(self, clip: VideoClip, factor: float) -> VideoClip:
        """GPU加速的对比度调整"""
        device = self.gpu.get_device()

        def contrast_frame(t):
            frame = clip.get_frame(t)
            tensor = self.gpu.create_tensor(frame / 255.0)

            # 计算均值并调整对比度
            mean = torch.mean(tensor, dim=[0, 1, 2], keepdim=True)
            result = torch.clamp((tensor - mean) * factor + mean, 0, 1)
            result = result.cpu().numpy()

            return (result * 255).astype(np.uint8)

        return clip.fl(contrast_frame)

    def _gpu_saturation(self, clip: VideoClip, factor: float) -> VideoClip:
        """GPU加速的饱和度调整"""
        device = self.gpu.get_device()

        def saturation_frame(t):
            frame = clip.get_frame(t)
            tensor = self.gpu.create_tensor(frame / 255.0)

            # 转换为HSV
            tensor_hsv = self._rgb_to_hsv_gpu(tensor)

            # 调整饱和度
            tensor_hsv[:, :, 1] = torch.clamp(tensor_hsv[:, :, 1] * factor, 0, 1)

            # 转回RGB
            result = self._hsv_to_rgb_gpu(tensor_hsv)
            result = result.cpu().numpy()

            return (result * 255).astype(np.uint8)

        return clip.fl(saturation_frame)

    def _gpu_sepia(self, clip: VideoClip) -> VideoClip:
        """GPU加速的怀旧色调效果"""
        device = self.gpu.get_device()

        # Sepia矩阵
        sepia_matrix = torch.tensor([
            [0.393, 0.769, 0.189],
            [0.349, 0.686, 0.168],
            [0.272, 0.534, 0.131]
        ], dtype=torch.float32, device=device)

        def sepia_frame(t):
            frame = clip.get_frame(t)
            tensor = self.gpu.create_tensor(frame / 255.0)

            # 应用sepia矩阵
            result = torch.matmul(tensor.view(-1, 3), sepia_matrix.t())
            result = result.view(tensor.shape)
            result = torch.clamp(result, 0, 1)
            result = result.cpu().numpy()

            return (result * 255).astype(np.uint8)

        return clip.fl(sepia_frame)

    def _gpu_black_and_white(self, clip: VideoClip) -> VideoClip:
        """GPU加速的黑白效果"""
        device = self.gpu.get_device()

        def bw_frame(t):
            frame = clip.get_frame(t)
            tensor = self.gpu.create_tensor(frame / 255.0)

            # 转换为灰度
            gray = torch.sum(tensor * torch.tensor([0.299, 0.587, 0.114],
                          device=device).view(1, 1, -1), dim=-1, keepdim=True)
            result = torch.cat([gray, gray, gray], dim=-1)
            result = result.cpu().numpy()

            return result.astype(np.uint8)

        return clip.fl(bw_frame)

    def _rgb_to_hsv_gpu(self, rgb: torch.Tensor) -> torch.Tensor:
        """GPU版本的RGB到HSV转换"""
        r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]

        max_rgb, argmax_rgb = torch.max(rgb, dim=-1)
        min_rgb, _ = torch.min(rgb, dim=-1)
        diff = max_rgb - min_rgb

        # Hue
        h = torch.zeros_like(max_rgb)
        h = torch.where(argmax_rgb == 0, (g - b) / diff, h)
        h = torch.where(argmax_rgb == 1, 2 + (b - r) / diff, h)
        h = torch.where(argmax_rgb == 2, 4 + (r - g) / diff, h)
        h = (h / 6) % 1

        # Saturation
        s = torch.where(max_rgb == 0, torch.zeros_like(max_rgb), diff / max_rgb)

        # Value
        v = max_rgb

        return torch.stack([h, s, v], dim=-1)

    def _hsv_to_rgb_gpu(self, hsv: torch.Tensor) -> torch.Tensor:
        """GPU版本的HSV到RGB转换"""
        h, s, v = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]

        h = h * 6
        i = torch.floor(h).long()
        f = h - i
        p = v * (1 - s)
        q = v * (1 - f * s)
        t = v * (1 - (1 - f) * s)

        i = i % 6

        r = torch.where(i == 0, v, torch.where(i == 1, q, torch.where(i == 2, p, torch.where(i == 3, p, torch.where(i == 4, t, v)))))
        g = torch.where(i == 0, t, torch.where(i == 1, v, torch.where(i == 2, v, torch.where(i == 3, q, torch.where(i == 4, p, p)))))
        b = torch.where(i == 0, p, torch.where(i == 1, p, torch.where(i == 2, t, torch.where(i == 3, v, torch.where(i == 4, v, q)))))

        return torch.stack([r, g, b], dim=-1)

    def _apply_color_effect_cpu(self, clip: VideoClip, effect_type: str, **kwargs):
        """CPU回退方案"""
        from .effects import VideoEffects

        if effect_type == 'brightness':
            return VideoEffects.adjust_brightness(clip, kwargs.get('factor', 1.2))
        elif effect_type == 'contrast':
            return VideoEffects.adjust_contrast(clip, kwargs.get('factor', 1.5))
        elif effect_type == 'sepia':
            return VideoEffects.sepia(clip)
        elif effect_type == 'bw':
            return VideoEffects.black_and_white(clip)
        else:
            self.logger.warning(f"Unsupported color effect: {effect_type}")
            return clip

    def apply_blur_gpu(self, clip: VideoClip, blur_radius: int = 5) -> VideoClip:
        """
        GPU加速的模糊效果

        Args:
            clip: 视频片段
            blur_radius: 模糊半径

        Returns:
            处理后的视频片段
        """
        if not self.is_gpu_available():
            return self._apply_blur_cpu(clip, blur_radius)

        try:
            device = self.gpu.get_device()
            kernel_size = blur_radius * 2 + 1

            def blur_frame(t):
                frame = clip.get_frame(t)
                tensor = self.gpu.create_tensor(frame / 255.0).permute(2, 0, 1).unsqueeze(0)

                # GPU高斯模糊
                sigma = blur_radius / 3.0
                result = F.gaussian_blur(tensor, kernel_size, sigma=[sigma, sigma])

                result = result.squeeze(0).permute(1, 2, 0).cpu().numpy()
                return (result * 255).astype(np.uint8)

            return clip.fl(blur_frame)
        except Exception as e:
            self.logger.warning(f"GPU blur failed: {e}, falling back to CPU")
            return self._apply_blur_cpu(clip, blur_radius)

    def _apply_blur_cpu(self, clip: VideoClip, blur_radius: int):
        """CPU回退方案"""
        from .effects import VideoEffects
        return VideoEffects.blur(clip, blur_radius)

    def create_slideshow_gpu(self,
                            images: list,
                            audio_path: str,
                            image_duration: float = 5.0,
                            transition: str = 'fade',
                            transition_duration: float = 0.5,
                            **kwargs) -> VideoClip:
        """
        GPU加速的幻灯片制作

        Args:
            images: 图片路径列表
            audio_path: 音频文件路径
            image_duration: 每张图片显示时长
            transition: 转场效果类型
            transition_duration: 转场持续时间

        Returns:
            合成后的视频片段
        """
        from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips, ColorClip

        if not images:
            raise ValueError("No images provided")

        # 获取音频时长以动态调整图片时长
        audio_duration = None
        if audio_path:
            try:
                audio_clip = AudioFileClip(audio_path)
                audio_duration = audio_clip.duration
                self.logger.info(f"音频时长: {audio_duration:.2f}秒")
            except Exception as e:
                self.logger.warning(f"无法获取音频时长: {e}")

        # 计算每张图片的实际持续时间
        if audio_duration and len(images) > 1 and transition == "fade":
            # 更精确的时长计算
            n = len(images)
            # 总转场时间 = (n-1) * transition_duration
            total_transition_time = (n - 1) * transition_duration
            # 有效显示时间 = 音频时长 - 转场重叠时间
            effective_display_time = audio_duration - total_transition_time
            if effective_display_time > 0:
                adjusted_image_duration = effective_display_time / n
                self.logger.info(f"精确计算图片时长: {adjusted_image_duration:.2f}秒 (考虑{n}张图片和{total_transition_time:.2f}秒转场)")
            else:
                # 如果转场时间过长，使用最小图片时长
                adjusted_image_duration = max(1.0, audio_duration / n / 2)
                self.logger.warning(f"转场时间过长，使用最小图片时长: {adjusted_image_duration:.2f}秒")
        elif audio_duration:
            # 无转场，平均分配时间
            adjusted_image_duration = audio_duration / len(images)
            self.logger.info(f"平均分配图片时长: {adjusted_image_duration:.2f}秒")
        else:
            adjusted_image_duration = image_duration
            self.logger.info(f"使用默认图片时长: {adjusted_image_duration:.2f}秒")

        # 创建图片片段
        image_clips = []
        # 使用标准1080p分辨率，避免异常大的图片导致渲染问题
        target_resolution = (1920, 1080)
        
        for img_path in images:
            # 确保路径是字符串
            img_path_str = str(img_path) if not isinstance(img_path, str) else img_path
            img_clip = ImageClip(img_path_str, duration=adjusted_image_duration)
            
            # 调整到目标分辨率
            img_clip = img_clip.resize(target_resolution)
            
            image_clips.append(img_clip)

        # 应用转场效果
        if len(image_clips) > 1 and transition_duration > 0:
            transitioned_clips = [image_clips[0]]

            for i in range(1, len(image_clips)):
                transition_clip = self.apply_transition_gpu(
                    transitioned_clips[-1],
                    image_clips[i],
                    transition,
                    transition_duration
                )
                transitioned_clips.append(transition_clip)

            video_clip = transitioned_clips[-1]
        else:
            # 无转场，直接拼接
            video_clip = concatenate_videoclips(image_clips)

        # 微调视频时长以精确匹配音频
        if audio_duration and abs(video_clip.duration - audio_duration) > 0.1:
            if video_clip.duration > audio_duration:
                # 裁剪视频
                self.logger.info(f"裁剪视频: {video_clip.duration:.2f}秒 -> {audio_duration:.2f}秒")
                video_clip = video_clip.subclip(0, audio_duration)
            else:
                # 延长最后一帧
                extension_duration = audio_duration - video_clip.duration
                self.logger.info(f"延长视频: 添加{extension_duration:.2f}秒黑屏")
                extension = ColorClip(
                    size=video_clip.size,
                    color=[0, 0, 0],
                    duration=extension_duration
                )
                video_clip = concatenate_videoclips([video_clip, extension])

        # 添加音频
        if audio_path:
            try:
                if audio_duration:
                    # 重用已加载的音频
                    video_clip = video_clip.set_audio(audio_clip)
                else:
                    # 重新加载
                    audio_clip = AudioFileClip(audio_path)
                    video_clip = video_clip.set_audio(audio_clip)
            except Exception as e:
                self.logger.warning(f"Failed to load audio: {e}")

        return video_clip

    def get_performance_stats(self) -> Dict[str, Any]:
        """
        获取性能统计信息

        Returns:
            性能统计字典
        """
        return {
            'gpu_available': self.is_gpu_available(),
            'gpu_info': self.gpu.get_gpu_info(),
            'memory_usage': self.gpu.get_memory_usage(),
            'device': str(self.gpu.get_device())
        }
