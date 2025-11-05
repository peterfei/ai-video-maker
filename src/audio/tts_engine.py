"""
TTS语音合成引擎
支持多种TTS服务
"""

import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List
import os


class TTSEngine:
    """TTS引擎类"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化TTS引擎

        Args:
            config: 配置字典
        """
        self.config = config
        self.engine = config.get('engine', 'edge-tts')
        self.voice = config.get('voice', 'zh-CN-XiaoxiaoNeural')
        self.rate = config.get('rate', 1.0)
        self.volume = config.get('volume', 1.0)
        self.pitch = config.get('pitch', 0)

    def text_to_speech(
        self,
        text: str,
        output_path: str,
        voice: Optional[str] = None,
        return_duration: bool = False
    ) -> Path:
        """
        将文本转换为语音

        Args:
            text: 要转换的文本
            output_path: 输出音频文件路径
            voice: 语音（可选，覆盖默认设置）
            return_duration: 是否返回音频时长（返回元组）

        Returns:
            输出文件路径，或 (输出文件路径, 音频时长) 元组
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        voice = voice or self.voice

        if self.engine == 'edge-tts':
            result = self._edge_tts(text, output_path, voice)
        elif self.engine == 'pyttsx3':
            result = self._pyttsx3(text, output_path)
        else:
            raise ValueError(f"不支持的TTS引擎: {self.engine}")

        if return_duration:
            duration = self.get_audio_duration(str(result))
            return (result, duration)
        else:
            return result

    def _edge_tts(self, text: str, output_path: Path, voice: str) -> Path:
        """
        使用Edge TTS生成语音（带重试机制）

        Args:
            text: 文本
            output_path: 输出路径
            voice: 语音

        Returns:
            输出文件路径
        """
        import time
        import logging
        logger = logging.getLogger(__name__)

        max_retries = 3
        retry_delay = 2  # 秒

        for attempt in range(max_retries):
            try:
                import edge_tts

                # 创建异步任务
                async def generate():
                    communicate = edge_tts.Communicate(
                        text=text,
                        voice=voice,
                        rate=self._format_rate(self.rate),
                        volume=self._format_volume(self.volume),
                        pitch=self._format_pitch(self.pitch)
                    )
                    await communicate.save(str(output_path))

                # 运行异步任务 - 处理事件循环冲突
                try:
                    # 尝试获取当前运行的事件循环
                    loop = asyncio.get_running_loop()
                    # 如果已经有运行中的循环，使用 run_in_executor 在新线程中运行
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, generate())
                        future.result()
                except RuntimeError:
                    # 没有运行中的循环，可以直接使用 asyncio.run()
                    asyncio.run(generate())

                return output_path

            except Exception as e:
                error_msg = str(e)

                # 检查是否是401认证错误
                if "401" in error_msg or "Invalid response status" in error_msg:
                    logger.warning(f"Edge TTS 认证失败 (尝试 {attempt + 1}/{max_retries})")

                    if attempt < max_retries - 1:
                        logger.info(f"等待 {retry_delay} 秒后重试...")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # 指数退避
                        continue
                    else:
                        # 最后一次尝试失败，尝试使用本地TTS
                        logger.warning("Edge TTS 服务不可用，尝试使用本地TTS引擎")
                        try:
                            # macOS优先使用say命令
                            import platform
                            if platform.system() == 'Darwin':
                                return self._macos_say(text, output_path)
                            else:
                                return self._pyttsx3(text, output_path)
                        except Exception as fallback_error:
                            raise RuntimeError(
                                f"Edge TTS 和本地TTS都失败。"
                                f"Edge TTS错误: {error_msg}; "
                                f"本地TTS错误: {str(fallback_error)}"
                            )
                else:
                    # 其他错误直接抛出
                    if attempt < max_retries - 1:
                        logger.warning(f"Edge TTS 生成失败 (尝试 {attempt + 1}/{max_retries}): {error_msg}")
                        time.sleep(retry_delay)
                        continue
                    else:
                        raise RuntimeError(f"Edge TTS生成失败: {error_msg}")

    def _macos_say(self, text: str, output_path: Path) -> Path:
        """
        使用macOS say命令生成语音

        Args:
            text: 文本
            output_path: 输出路径

        Returns:
            输出文件路径
        """
        try:
            import subprocess
            import tempfile

            # 使用say命令生成AIFF文件
            temp_aiff = tempfile.NamedTemporaryFile(suffix='.aiff', delete=False)
            temp_aiff_path = temp_aiff.name
            temp_aiff.close()

            # 调整语速 (默认175，range: 90-720)
            rate = int(175 * self.rate)

            # 使用中文语音
            voice = "Ting-Ting"  # 中文女声

            # 生成语音
            cmd = ['say', '-v', voice, '-r', str(rate), '-o', temp_aiff_path, text]
            subprocess.run(cmd, check=True, capture_output=True)

            # 转换为MP3格式（使用ffmpeg）
            ffmpeg_cmd = [
                'ffmpeg', '-y', '-i', temp_aiff_path,
                '-acodec', 'libmp3lame', '-b:a', '128k',
                str(output_path)
            ]
            subprocess.run(ffmpeg_cmd, check=True, capture_output=True)

            # 清理临时文件
            import os
            os.remove(temp_aiff_path)

            return output_path

        except Exception as e:
            raise RuntimeError(f"macOS say命令生成失败: {str(e)}")

    def _pyttsx3(self, text: str, output_path: Path) -> Path:
        """
        使用pyttsx3生成语音

        Args:
            text: 文本
            output_path: 输出路径

        Returns:
            输出文件路径
        """
        try:
            import pyttsx3

            engine = pyttsx3.init()

            # 设置语速
            engine.setProperty('rate', 150 * self.rate)

            # 设置音量
            engine.setProperty('volume', self.volume)

            # 保存到文件
            engine.save_to_file(text, str(output_path))
            engine.runAndWait()

            return output_path

        except Exception as e:
            raise RuntimeError(f"pyttsx3生成失败: {str(e)}")

    def _format_rate(self, rate: float) -> str:
        """
        格式化语速参数为Edge TTS格式

        Args:
            rate: 语速倍数 (0.5-2.0)

        Returns:
            格式化的语速字符串
        """
        if rate == 1.0:
            return "+0%"

        percentage = int((rate - 1.0) * 100)
        return f"{percentage:+d}%"

    def _format_volume(self, volume: float) -> str:
        """
        格式化音量参数为Edge TTS格式

        Args:
            volume: 音量 (0.0-1.0)

        Returns:
            格式化的音量字符串
        """
        if volume == 1.0:
            return "+0%"

        percentage = int((volume - 1.0) * 100)
        return f"{percentage:+d}%"

    def _format_pitch(self, pitch: int) -> str:
        """
        格式化音调参数为Edge TTS格式

        Args:
            pitch: 音调 (-20 to +20)

        Returns:
            格式化的音调字符串
        """
        return f"{pitch:+d}Hz"

    def batch_text_to_speech(
        self,
        texts: List[str],
        output_dir: str,
        prefix: str = "audio"
    ) -> List[Path]:
        """
        批量转换文本为语音

        Args:
            texts: 文本列表
            output_dir: 输出目录
            prefix: 文件名前缀

        Returns:
            输出文件路径列表
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        output_paths = []

        for i, text in enumerate(texts):
            output_path = output_dir / f"{prefix}_{i:03d}.mp3"
            self.text_to_speech(text, str(output_path))
            output_paths.append(output_path)

        return output_paths

    def generate_segments(
        self,
        sentences: List[str],
        output_dir: str,
        prefix: str = "segment",
        progress_callback: Optional[callable] = None
    ) -> tuple[List[Path], List[float]]:
        """
        为句子列表分段生成音频，并返回每段的实际时长

        Args:
            sentences: 句子列表
            output_dir: 输出目录
            prefix: 文件名前缀
            progress_callback: 进度回调函数，接收 (current, total) 参数

        Returns:
            (音频文件路径列表, 音频时长列表) 元组
        """
        if not sentences:
            return ([], [])

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        audio_paths = []
        audio_durations = []

        import logging
        logger = logging.getLogger(__name__)

        total = len(sentences)
        for i, sentence in enumerate(sentences):
            # 跳过空句子
            if not sentence or not sentence.strip():
                logger.warning(f"跳过空句子 (索引 {i})")
                continue

            try:
                # 生成音频文件
                output_path = output_dir / f"{prefix}_{i:03d}.mp3"
                self.text_to_speech(sentence.strip(), str(output_path))

                # 获取音频时长
                duration = self.get_audio_duration(str(output_path))

                audio_paths.append(output_path)
                audio_durations.append(duration)

                logger.info(f"生成音频片段 {i+1}/{total}: {sentence[:30]}... ({duration:.2f}秒)")

                # 调用进度回调
                if progress_callback:
                    progress_callback(i + 1, total)

            except Exception as e:
                logger.error(f"生成音频片段 {i} 失败: {str(e)}")
                # 继续处理下一个，不中断整个流程
                continue

        logger.info(f"共生成 {len(audio_paths)} 个音频片段，总时长 {sum(audio_durations):.2f}秒")

        return (audio_paths, audio_durations)

    def get_audio_duration(self, audio_path: str) -> float:
        """
        获取音频文件时长

        Args:
            audio_path: 音频文件路径

        Returns:
            时长（秒）
        """
        try:
            from moviepy.editor import AudioFileClip

            audio = AudioFileClip(audio_path)
            duration = audio.duration
            audio.close()

            return duration

        except Exception as e:
            raise RuntimeError(f"获取音频时长失败: {str(e)}")

    def list_available_voices(self) -> List[str]:
        """
        列出可用的语音

        Returns:
            语音列表
        """
        if self.engine == 'edge-tts':
            # 返回配置中的语音列表
            return self.config.get('available_voices', [
                'zh-CN-XiaoxiaoNeural',
                'zh-CN-YunxiNeural',
                'zh-CN-YunyangNeural',
                'zh-CN-XiaoyiNeural'
            ])
        elif self.engine == 'pyttsx3':
            try:
                import pyttsx3
                engine = pyttsx3.init()
                voices = engine.getProperty('voices')
                return [voice.id for voice in voices]
            except Exception:
                return []
        else:
            return []

    def estimate_speech_duration(self, text: str, chars_per_second: float = 3.0) -> float:
        """
        估算语音时长

        Args:
            text: 文本
            chars_per_second: 每秒字符数（根据语速调整）

        Returns:
            估算的时长（秒）
        """
        char_count = len(text)
        base_duration = char_count / chars_per_second
        # 根据语速调整
        adjusted_duration = base_duration / self.rate
        return adjusted_duration
