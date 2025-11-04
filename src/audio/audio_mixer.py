"""
音频混合器
处理语音、背景音乐等音频的混合
"""

from pathlib import Path
from typing import Dict, Any, Optional
from moviepy.editor import AudioFileClip, CompositeAudioClip, concatenate_audioclips


class AudioMixer:
    """音频混合器类"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化音频混合器

        Args:
            config: 配置字典
        """
        self.config = config
        self.music_enabled = config.get('enabled', True)
        self.music_volume = config.get('volume', 0.2)
        self.fade_in = config.get('fade_in', 2.0)
        self.fade_out = config.get('fade_out', 3.0)
        self.loop = config.get('loop', True)

    def mix_voice_and_music(
        self,
        voice_path: str,
        music_path: str,
        output_path: str,
        music_volume: Optional[float] = None
    ) -> Path:
        """
        混合人声和背景音乐

        Args:
            voice_path: 人声音频路径
            music_path: 背景音乐路径
            output_path: 输出路径
            music_volume: 音乐音量（可选）

        Returns:
            输出文件路径
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        music_volume = music_volume or self.music_volume

        # 加载音频
        voice = AudioFileClip(voice_path)
        music = AudioFileClip(music_path)

        # 调整背景音乐
        music = self._prepare_background_music(music, voice.duration, music_volume)

        # 混合音频
        final_audio = CompositeAudioClip([voice, music])
        final_audio.fps = voice.fps  # 设置fps属性

        # 导出
        final_audio.write_audiofile(
            str(output_path),
            codec='mp3',
            bitrate='192k',
            logger=None
        )

        # 清理
        voice.close()
        music.close()
        final_audio.close()

        return output_path

    def _prepare_background_music(
        self,
        music_clip: AudioFileClip,
        target_duration: float,
        volume: float
    ) -> AudioFileClip:
        """
        准备背景音乐

        Args:
            music_clip: 音乐片段
            target_duration: 目标时长
            volume: 音量

        Returns:
            处理后的音乐片段
        """
        # 循环音乐以匹配目标时长
        if self.loop and music_clip.duration < target_duration:
            # 计算需要循环的次数
            loops = int(target_duration / music_clip.duration) + 1
            music_clips = [music_clip] * loops
            music_clip = concatenate_audioclips(music_clips)

        # 裁剪到目标时长
        if music_clip.duration > target_duration:
            music_clip = music_clip.subclip(0, target_duration)

        # 调整音量
        music_clip = music_clip.volumex(volume)

        # 添加淡入淡出
        if self.fade_in > 0:
            music_clip = music_clip.audio_fadein(self.fade_in)

        if self.fade_out > 0:
            music_clip = music_clip.audio_fadeout(self.fade_out)

        return music_clip

    def concatenate_audio_files(
        self,
        audio_paths: list,
        output_path: str,
        silence_duration: float = 0.0
    ) -> Path:
        """
        拼接多个音频文件为一个完整音频

        Args:
            audio_paths: 音频文件路径列表
            output_path: 输出路径
            silence_duration: 在片段间插入的静音时长（秒），默认0（无静音）

        Returns:
            输出文件路径
        """
        if not audio_paths:
            raise ValueError("音频文件列表不能为空")

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        import logging
        logger = logging.getLogger(__name__)

        # 单个文件直接复制
        if len(audio_paths) == 1:
            import shutil
            shutil.copy(str(audio_paths[0]), str(output_path))
            logger.info(f"单个音频文件，直接复制: {output_path}")
            return output_path

        # 加载所有音频
        clips = []
        for i, path in enumerate(audio_paths):
            try:
                clip = AudioFileClip(str(path))
                clips.append(clip)
            except Exception as e:
                logger.error(f"加载音频文件 {path} 失败: {str(e)}")
                raise

        # 如果需要在片段间插入静音
        if silence_duration > 0:
            from moviepy.editor import AudioClip
            import numpy as np

            # 创建带静音的片段列表
            clips_with_silence = []
            for i, clip in enumerate(clips):
                clips_with_silence.append(clip)

                # 在非最后一个片段后添加静音
                if i < len(clips) - 1:
                    silence = AudioClip(
                        lambda t: np.zeros(2) if clip.nchannels == 2 else np.array([0]),
                        duration=silence_duration,
                        fps=clip.fps
                    )
                    clips_with_silence.append(silence)

            clips = clips_with_silence

        # 拼接音频
        final_audio = concatenate_audioclips(clips)

        # 导出
        final_audio.write_audiofile(
            str(output_path),
            codec='mp3',
            bitrate='192k',
            logger=None
        )

        total_duration = final_audio.duration
        logger.info(f"拼接完成: {len(audio_paths)} 个音频片段 → {output_path} (总时长: {total_duration:.2f}秒)")

        # 清理
        for clip in clips:
            clip.close()
        final_audio.close()

        return output_path

    def adjust_volume(
        self,
        audio_path: str,
        output_path: str,
        volume_factor: float
    ) -> Path:
        """
        调整音频音量

        Args:
            audio_path: 输入音频路径
            output_path: 输出路径
            volume_factor: 音量倍数

        Returns:
            输出文件路径
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        audio = AudioFileClip(audio_path)
        audio = audio.volumex(volume_factor)

        audio.write_audiofile(
            str(output_path),
            codec='mp3',
            bitrate='192k',
            logger=None
        )

        audio.close()

        return output_path

    def trim_audio(
        self,
        audio_path: str,
        output_path: str,
        start: float = 0,
        end: Optional[float] = None
    ) -> Path:
        """
        裁剪音频

        Args:
            audio_path: 输入音频路径
            output_path: 输出路径
            start: 开始时间（秒）
            end: 结束时间（秒，None表示到结尾）

        Returns:
            输出文件路径
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        audio = AudioFileClip(audio_path)

        if end is None:
            end = audio.duration

        audio = audio.subclip(start, end)

        audio.write_audiofile(
            str(output_path),
            codec='mp3',
            bitrate='192k',
            logger=None
        )

        audio.close()

        return output_path

    def add_silence(
        self,
        audio_path: str,
        output_path: str,
        silence_duration: float,
        position: str = "start"
    ) -> Path:
        """
        在音频开头或结尾添加静音

        Args:
            audio_path: 输入音频路径
            output_path: 输出路径
            silence_duration: 静音时长（秒）
            position: 位置 (start/end)

        Returns:
            输出文件路径
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        from moviepy.editor import AudioClip
        import numpy as np

        audio = AudioFileClip(audio_path)

        # 创建静音片段
        silence = AudioClip(
            lambda t: np.zeros(2),  # 立体声静音
            duration=silence_duration,
            fps=audio.fps
        )

        # 拼接
        if position == "start":
            final_audio = concatenate_audioclips([silence, audio])
        else:
            final_audio = concatenate_audioclips([audio, silence])

        # 导出
        final_audio.write_audiofile(
            str(output_path),
            codec='mp3',
            bitrate='192k',
            logger=None
        )

        # 清理
        audio.close()
        silence.close()
        final_audio.close()

        return output_path

    def get_audio_info(self, audio_path: str) -> Dict[str, Any]:
        """
        获取音频信息

        Args:
            audio_path: 音频文件路径

        Returns:
            音频信息字典
        """
        try:
            audio = AudioFileClip(audio_path)
            info = {
                'duration': audio.duration,
                'fps': audio.fps,
                'nchannels': audio.nchannels,
                'path': audio_path
            }
            audio.close()
            return info
        except Exception as e:
            return {'error': str(e)}
