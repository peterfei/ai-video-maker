"""
STT (Speech-to-Text) 引擎

提供中文语音转文字功能，使用 FasterWhisper 实现高效的语音识别。
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import time
from datetime import datetime

# 第三方依赖（将在后续添加）
try:
    from faster_whisper import WhisperModel
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False
    WhisperModel = None

from .models import STTResult, STTSegment, STTConfig


logger = logging.getLogger(__name__)


class STTEngine:
    """
    STT (Speech-to-Text) 引擎

    使用 FasterWhisper 提供中文语音转文字功能。
    支持多种模型大小和计算设备，优化中文识别性能。
    """

    # 支持的音频格式
    SUPPORTED_FORMATS = ['mp3', 'wav', 'flac', 'm4a', 'ogg', 'aac']

    def __init__(self, config: Dict[str, Any]):
        """
        初始化 STT 引擎

        Args:
            config: STT 配置字典

        Raises:
            ImportError: 如果未安装 faster-whisper
            ValueError: 如果配置无效
        """
        if not FASTER_WHISPER_AVAILABLE:
            raise ImportError(
                "faster-whisper is required for STT functionality. "
                "Install with: pip install faster-whisper"
            )

        # 解析配置
        self.config = STTConfig.from_dict(config)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # 模型缓存
        self._model = None
        self._model_loaded = False

        self.logger.info(f"STT 引擎初始化完成，模型: {self.config.model}")

    @property
    def model(self) -> Optional[WhisperModel]:
        """获取或加载 Whisper 模型"""
        if not self._model_loaded:
            self._load_model()
        return self._model

    def _load_model(self) -> None:
        """加载 Whisper 模型"""
        if self._model_loaded:
            return

        try:
            self.logger.info(f"正在加载 Whisper 模型: {self.config.model}")

            start_time = time.time()

            # 创建模型
            self._model = WhisperModel(
                self.config.model,
                device=self.config.device,
                compute_type=self.config.compute_type,
                cpu_threads=self.config.cpu_threads,
                num_workers=self.config.num_workers,
                download_root=None,  # 使用默认下载目录
                local_files_only=False,
                device_index=0,
                threads=self.config.cpu_threads,
            )

            load_time = time.time() - start_time
            self._model_loaded = True

            self.logger.info(f"Whisper 模型加载完成，耗时 {load_time:.2f}秒")
        except Exception as e:
            self.logger.error(f"模型加载失败: {str(e)}")
            raise RuntimeError(f"Failed to load Whisper model: {str(e)}") from e

    def transcribe(self, audio_path: str) -> STTResult:
        """
        转录音频文件为带时间戳的文本

        Args:
            audio_path: 音频文件路径

        Returns:
            STTResult: 识别结果

        Raises:
            FileNotFoundError: 音频文件不存在
            ValueError: 音频格式不支持或音频无效
            RuntimeError: 转录过程失败
        """
        audio_path = Path(audio_path)

        # 验证音频文件
        self._validate_audio_file(audio_path)

        # 确保模型已加载
        if not self.model:
            raise RuntimeError("STT model not loaded")

        self.logger.info(f"开始转录音频文件: {audio_path}")

        start_time = time.time()

        try:
            # 执行转录
            segments, info = self.model.transcribe(
                str(audio_path),
                language=self.config.language,
                beam_size=self.config.beam_size,
                patience=self.config.patience,
                length_penalty=self.config.length_penalty,
                repetition_penalty=self.config.repetition_penalty,
                no_repeat_ngram_size=self.config.no_repeat_ngram_size,
                compression_ratio_threshold=self.config.compression_ratio_threshold,
                logprob_threshold=self.config.logprob_threshold,
                temperature=self.config.temperature,
                initial_prompt=None,
                prefix=None,
                suppress_blank=True,
                suppress_tokens=[-1],
                without_timestamps=False,
                max_initial_timestamp=1.0,
                hallucination_silence_threshold=None,
                vad_filter=self.config.vad_filter,
                vad_parameters=dict(
                    threshold=self.config.vad_threshold,
                    min_speech_duration_ms=self.config.vad_min_speech_duration_ms,
                    max_speech_duration_s=self.config.vad_max_speech_duration_s,
                ) if self.config.vad_filter else None,
            )

            # 转换结果
            stt_segments = []
            for segment in segments:
                stt_segment = STTSegment(
                    text=segment.text.strip(),
                    start_time=segment.start,
                    end_time=segment.end,
                    confidence=getattr(segment, 'confidence', 0.8)  # 默认置信度
                )
                stt_segments.append(stt_segment)

            # 创建结果对象
            processing_time = time.time() - start_time

            result = STTResult(
                segments=stt_segments,
                language=info.language or self.config.language,
                duration=info.duration,
                model_used=self.config.model,
                processing_time=processing_time,
            )

            self.logger.info(
                f"转录完成: {len(stt_segments)} 个片段，"
                ".2f"
                ".2f"
            )

            return result

        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"转录失败 (耗时 {processing_time:.2f}s): {str(e)}")
            raise RuntimeError(f"Transcription failed: {str(e)}") from e

    def _validate_audio_file(self, audio_path: Path) -> None:
        """
        验证音频文件

        Args:
            audio_path: 音频文件路径

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 格式不支持或文件无效
        """
        # 检查文件存在性
        if not audio_path.exists():
            raise FileNotFoundError(f"音频文件不存在: {audio_path}")

        if not audio_path.is_file():
            raise ValueError(f"路径不是文件: {audio_path}")

        # 检查文件大小
        file_size = audio_path.stat().st_size
        if file_size == 0:
            raise ValueError(f"音频文件为空: {audio_path}")

        # 检查文件大小上限 (1GB)
        max_size = 1024 * 1024 * 1024  # 1GB
        if file_size > max_size:
            raise ValueError(f"音频文件过大 ({file_size/1024/1024:.1f}MB)，最大支持 1GB")

        # 检查文件扩展名
        suffix = audio_path.suffix.lower().lstrip('.')
        if suffix not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"不支持的音频格式: {suffix}。支持格式: {', '.join(self.SUPPORTED_FORMATS)}"
            )

        self.logger.debug(f"音频文件验证通过: {audio_path} ({file_size/1024/1024:.1f}MB)")

    def validate_audio_format(self, audio_path: str) -> bool:
        """
        验证音频格式是否支持

        Args:
            audio_path: 音频文件路径

        Returns:
            bool: 是否支持
        """
        try:
            self._validate_audio_file(Path(audio_path))
            return True
        except (FileNotFoundError, ValueError):
            return False

    def get_supported_formats(self) -> List[str]:
        """
        获取支持的音频格式列表

        Returns:
            List[str]: 支持的格式列表
        """
        return self.SUPPORTED_FORMATS.copy()

    def get_model_info(self) -> Dict[str, Any]:
        """
        获取当前模型信息

        Returns:
            Dict[str, Any]: 模型信息
        """
        return {
            "model_name": self.config.model,
            "language": self.config.language,
            "device": self.config.device,
            "compute_type": self.config.compute_type,
            "loaded": self._model_loaded,
            "supported_formats": self.get_supported_formats(),
        }

    def unload_model(self) -> None:
        """卸载模型以释放内存"""
        if self._model:
            self._model = None
            self._model_loaded = False
            self.logger.info("STT 模型已卸载")

    def __repr__(self) -> str:
        return (
            f"STTEngine("
            f"model='{self.config.model}', "
            f"language='{self.config.language}', "
            f"device='{self.config.device}', "
            f"loaded={self._model_loaded}"
            f")"
        )


class STTEngineManager:
    """
    STT 引擎管理器

    提供 STT 引擎的创建、管理和缓存功能。
    """

    def __init__(self):
        self._engines: Dict[str, STTEngine] = {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def get_engine(self, config: Dict[str, Any]) -> STTEngine:
        """
        获取或创建 STT 引擎

        Args:
            config: STT 配置

        Returns:
            STTEngine: STT 引擎实例
        """
        # 创建缓存键
        config_obj = STTConfig.from_dict(config)
        cache_key = f"{config_obj.model}_{config_obj.language}_{config_obj.device}"

        if cache_key not in self._engines:
            self.logger.info(f"创建新的 STT 引擎: {cache_key}")
            self._engines[cache_key] = STTEngine(config)
        else:
            self.logger.debug(f"使用缓存的 STT 引擎: {cache_key}")

        return self._engines[cache_key]

    def unload_all(self) -> None:
        """卸载所有引擎"""
        for engine in self._engines.values():
            engine.unload_model()
        self._engines.clear()
        self.logger.info("所有 STT 引擎已卸载")

    def list_engines(self) -> Dict[str, Dict[str, Any]]:
        """
        列出所有引擎信息

        Returns:
            Dict[str, Dict[str, Any]]: 引擎信息字典
        """
        return {
            cache_key: engine.get_model_info()
            for cache_key, engine in self._engines.items()
        }


# 全局引擎管理器实例
_engine_manager = STTEngineManager()


def get_stt_engine(config: Dict[str, Any]) -> STTEngine:
    """
    获取 STT 引擎的便捷函数

    Args:
        config: STT 配置

    Returns:
        STTEngine: STT 引擎实例
    """
    return _engine_manager.get_engine(config)


def unload_stt_engines() -> None:
    """卸载所有 STT 引擎"""
    _engine_manager.unload_all()
