"""
STT (Speech-to-Text) 数据模型

定义语音转文字功能的数据结构和类型。
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class STTSegment:
    """
    STT 识别片段

    表示语音转文字的一个识别片段，包含文本内容和时间戳信息。
    """
    text: str
    """识别的文本内容"""

    start_time: float
    """开始时间（秒）"""

    end_time: float
    """结束时间（秒）"""

    confidence: float
    """识别置信度 (0.0-1.0)"""

    def __post_init__(self):
        """数据验证"""
        if not isinstance(self.text, str):
            raise TypeError("text must be a string")
        if not isinstance(self.start_time, (int, float)):
            raise TypeError("start_time must be a number")
        if not isinstance(self.end_time, (int, float)):
            raise TypeError("end_time must be a number")
        if not isinstance(self.confidence, (int, float)):
            raise TypeError("confidence must be a number")

        if self.start_time < 0:
            raise ValueError("start_time must be non-negative")
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be greater than start_time")
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError("confidence must be between 0.0 and 1.0")

    @property
    def duration(self) -> float:
        """获取片段持续时间"""
        return self.end_time - self.start_time

    def __repr__(self) -> str:
        return (
            f"STTSegment("
            f"text='{self.text[:30]}...', "
            f"start={self.start_time:.2f}s, "
            f"end={self.end_time:.2f}s, "
            f"confidence={self.confidence:.2f}"
            f")"
        )


@dataclass
class STTResult:
    """
    STT 识别结果

    包含完整的语音转文字识别结果信息。
    """
    segments: List[STTSegment]
    """识别片段列表"""

    language: str
    """识别语言代码（如 'zh', 'en'）"""

    duration: float
    """音频总时长（秒）"""

    model_used: str
    """使用的模型名称"""

    processing_time: Optional[float] = None
    """处理耗时（秒）"""

    confidence_avg: Optional[float] = None
    """平均置信度"""

    created_at: Optional[datetime] = None
    """创建时间"""

    def __post_init__(self):
        """数据验证"""
        if not isinstance(self.segments, list):
            raise TypeError("segments must be a list")
        if not all(isinstance(seg, STTSegment) for seg in self.segments):
            raise TypeError("all segments must be STTSegment instances")

        if not isinstance(self.language, str):
            raise TypeError("language must be a string")
        if not isinstance(self.duration, (int, float)):
            raise TypeError("duration must be a number")
        if not isinstance(self.model_used, str):
            raise TypeError("model_used must be a string")

        if self.duration < 0:
            raise ValueError("duration must be non-negative")

        # 设置创建时间
        if self.created_at is None:
            self.created_at = datetime.now()

        # 计算平均置信度
        if self.confidence_avg is None and self.segments:
            self.confidence_avg = sum(seg.confidence for seg in self.segments) / len(self.segments)

    @property
    def total_segments(self) -> int:
        """获取总片段数"""
        return len(self.segments)

    @property
    def total_text_length(self) -> int:
        """获取总文本长度"""
        return sum(len(seg.text) for seg in self.segments)

    @property
    def confidence_min(self) -> float:
        """获取最小置信度"""
        if not self.segments:
            return 0.0
        return min(seg.confidence for seg in self.segments)

    @property
    def confidence_max(self) -> float:
        """获取最大置信度"""
        if not self.segments:
            return 0.0
        return max(seg.confidence for seg in self.segments)

    def get_segments_above_confidence(self, threshold: float) -> List[STTSegment]:
        """获取置信度高于阈值的片段"""
        return [seg for seg in self.segments if seg.confidence >= threshold]

    def get_segments_below_confidence(self, threshold: float) -> List[STTSegment]:
        """获取置信度低于阈值的片段"""
        return [seg for seg in self.segments if seg.confidence < threshold]

    def filter_low_confidence_segments(self, threshold: float) -> 'STTResult':
        """过滤低置信度片段，返回新的 STTResult"""
        filtered_segments = self.get_segments_above_confidence(threshold)
        return STTResult(
            segments=filtered_segments,
            language=self.language,
            duration=self.duration,
            model_used=self.model_used,
            processing_time=self.processing_time,
            confidence_avg=None,  # 将重新计算
            created_at=self.created_at
        )

    def merge_consecutive_segments(self, max_gap: float = 0.1) -> 'STTResult':
        """合并连续的片段（如果间隔小于 max_gap）"""
        if not self.segments:
            return self

        merged = []
        current = self.segments[0]

        for next_seg in self.segments[1:]:
            # 检查是否可以合并
            if (next_seg.start_time - current.end_time) <= max_gap:
                # 合并片段
                current = STTSegment(
                    text=current.text + " " + next_seg.text,
                    start_time=current.start_time,
                    end_time=next_seg.end_time,
                    confidence=min(current.confidence, next_seg.confidence)  # 取较小值
                )
            else:
                # 保存当前片段，开始新片段
                merged.append(current)
                current = next_seg

        merged.append(current)

        return STTResult(
            segments=merged,
            language=self.language,
            duration=self.duration,
            model_used=self.model_used,
            processing_time=self.processing_time,
            confidence_avg=None,  # 将重新计算
            created_at=self.created_at
        )

    def __repr__(self) -> str:
        return (
            f"STTResult("
            f"segments={self.total_segments}, "
            f"language='{self.language}', "
            f"duration={self.duration:.2f}s, "
            f"model='{self.model_used}', "
            f"avg_confidence={self.confidence_avg:.2f}"
            f")"
        )


@dataclass
class STTConfig:
    """
    STT 配置参数

    封装所有 STT 相关的配置选项。
    """
    model: str = "base"
    """模型大小: tiny, base, small, medium, large"""

    language: str = "zh"
    """语言代码"""

    device: str = "auto"
    """计算设备: auto, cpu, cuda"""

    compute_type: str = "auto"
    """计算类型: auto, float16, float32, int8"""

    cpu_threads: int = 4
    """CPU 线程数"""

    num_workers: int = 1
    """工作进程数"""

    # 推理参数
    beam_size: int = 5
    """束搜索大小"""

    patience: float = 1.0
    """耐心因子"""

    length_penalty: float = 1.0
    """长度惩罚"""

    repetition_penalty: float = 1.0
    """重复惩罚"""

    no_repeat_ngram_size: int = 0
    """无重复 n-gram 大小"""

    # 音频处理参数
    vad_filter: bool = True
    """启用语音活动检测"""

    vad_threshold: float = 0.35
    """VAD 阈值"""

    vad_min_speech_duration_ms: int = 250
    """最小语音持续时间 (毫秒)"""

    vad_max_speech_duration_s: int = 30
    """最大语音持续时间 (秒)"""

    # 质量控制参数
    compression_ratio_threshold: float = 2.4
    """压缩比阈值"""

    logprob_threshold: float = -1.0
    """对数概率阈值"""

    temperature: List[float] = None
    """温度参数列表"""

    def __post_init__(self):
        """参数验证"""
        if self.temperature is None:
            self.temperature = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]

        # 验证模型大小
        valid_models = ["tiny", "base", "small", "medium", "large"]
        if self.model not in valid_models:
            raise ValueError(f"model must be one of {valid_models}")

        # 验证设备
        valid_devices = ["auto", "cpu", "cuda"]
        if self.device not in valid_devices:
            raise ValueError(f"device must be one of {valid_devices}")

        # 验证语言代码
        if not isinstance(self.language, str) or len(self.language) != 2:
            raise ValueError("language must be a 2-letter language code")

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "model": self.model,
            "language": self.language,
            "device": self.device,
            "compute_type": self.compute_type,
            "cpu_threads": self.cpu_threads,
            "num_workers": self.num_workers,
            "beam_size": self.beam_size,
            "patience": self.patience,
            "length_penalty": self.length_penalty,
            "repetition_penalty": self.repetition_penalty,
            "no_repeat_ngram_size": self.no_repeat_ngram_size,
            "vad_filter": self.vad_filter,
            "vad_threshold": self.vad_threshold,
            "vad_min_speech_duration_ms": self.vad_min_speech_duration_ms,
            "vad_max_speech_duration_s": self.vad_max_speech_duration_s,
            "compression_ratio_threshold": self.compression_ratio_threshold,
            "logprob_threshold": self.logprob_threshold,
            "temperature": self.temperature,
        }

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'STTConfig':
        """从字典创建配置"""
        # 过滤出有效参数
        valid_keys = cls.__dataclass_fields__.keys()
        filtered_config = {k: v for k, v in config_dict.items() if k in valid_keys}
        return cls(**filtered_config)
