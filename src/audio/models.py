"""
音频处理数据模型

定义语音转文字(STT)和背景音乐推荐功能的数据结构和类型。
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


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


# =============================================================================
# 背景音乐推荐相关数据模型
# =============================================================================

class CopyrightStatus(Enum):
    """音乐版权状态枚举"""

    PUBLIC_DOMAIN = "public_domain"
    """公有领域，无版权限制"""

    CREATIVE_COMMONS = "creative_commons"
    """创意共享许可"""

    ROYALTY_FREE = "royalty_free"
    """免版税音乐"""

    UNKNOWN = "unknown"
    """版权状态未知"""

    COPYRIGHTED = "copyrighted"
    """受版权保护，不可用"""

    @property
    def is_safe_to_use(self) -> bool:
        """判断是否安全使用"""
        return self in [self.PUBLIC_DOMAIN, self.CREATIVE_COMMONS, self.ROYALTY_FREE]

    @property
    def license_description(self) -> str:
        """获取许可证描述"""
        descriptions = {
            self.PUBLIC_DOMAIN: "公有领域，可自由使用",
            self.CREATIVE_COMMONS: "创意共享许可",
            self.ROYALTY_FREE: "免版税音乐",
            self.UNKNOWN: "版权状态未知，谨慎使用",
            self.COPYRIGHTED: "受版权保护，不可使用"
        }
        return descriptions.get(self, "未知状态")


@dataclass
class MusicRecommendation:
    """音乐推荐结果"""

    title: str
    """音乐标题"""

    artist: str
    """艺术家/创作者"""

    url: str
    """下载链接"""

    duration: float
    """时长（秒）"""

    genre: str
    """音乐类型（如 ambient, electronic, classical）"""

    mood: str
    """情绪标签（如 calm, inspiring, energetic）"""

    copyright_status: CopyrightStatus
    """版权状态"""

    confidence_score: float
    """推荐置信度 (0.0-1.0)"""

    source: str
    """来源平台（如 freemusicarchive, ccsearch）"""

    license_url: Optional[str] = None
    """许可证链接"""

    tags: Optional[List[str]] = None
    """附加标签"""

    file_size: Optional[int] = None
    """文件大小（字节）"""

    bitrate: Optional[int] = None
    """比特率（kbps）"""

    sample_rate: Optional[int] = None
    """采样率（Hz）"""

    created_at: Optional[datetime] = None
    """创建时间"""

    def __post_init__(self):
        """数据验证"""
        if not isinstance(self.title, str) or not self.title.strip():
            raise ValueError("title must be a non-empty string")

        if not isinstance(self.artist, str):
            raise ValueError("artist must be a string")

        if not isinstance(self.url, str) or not self.url.strip():
            raise ValueError("url must be a non-empty string")

        if not isinstance(self.duration, (int, float)) or self.duration <= 0:
            raise ValueError("duration must be a positive number")

        if not isinstance(self.genre, str):
            raise ValueError("genre must be a string")

        if not isinstance(self.mood, str):
            raise ValueError("mood must be a string")

        if not isinstance(self.copyright_status, CopyrightStatus):
            raise ValueError("copyright_status must be a CopyrightStatus enum")

        if not isinstance(self.confidence_score, (int, float)) or not (0.0 <= self.confidence_score <= 1.0):
            raise ValueError("confidence_score must be between 0.0 and 1.0")

        if not isinstance(self.source, str):
            raise ValueError("source must be a string")

        if self.tags is None:
            self.tags = []

        if self.created_at is None:
            self.created_at = datetime.now()

    @property
    def is_safe_to_use(self) -> bool:
        """判断是否安全使用"""
        return self.copyright_status.is_safe_to_use

    @property
    def duration_formatted(self) -> str:
        """格式化的时长字符串"""
        minutes = int(self.duration // 60)
        seconds = int(self.duration % 60)
        return f"{minutes}:{seconds:02d}"

    @property
    def file_size_formatted(self) -> Optional[str]:
        """格式化的文件大小字符串"""
        if self.file_size is None:
            return None

        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.file_size < 1024.0:
                return f"{self.file_size:.1f} {unit}"
            self.file_size /= 1024.0
        return f"{self.file_size:.1f} TB"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "title": self.title,
            "artist": self.artist,
            "url": self.url,
            "duration": self.duration,
            "genre": self.genre,
            "mood": self.mood,
            "copyright_status": self.copyright_status.value,
            "confidence_score": self.confidence_score,
            "source": self.source,
            "license_url": self.license_url,
            "tags": self.tags,
            "file_size": self.file_size,
            "bitrate": self.bitrate,
            "sample_rate": self.sample_rate,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MusicRecommendation':
        """从字典创建实例"""
        # 处理版权状态
        copyright_status = CopyrightStatus(data.get("copyright_status", "unknown"))

        # 处理创建时间
        created_at = None
        if data.get("created_at"):
            try:
                created_at = datetime.fromisoformat(data["created_at"])
            except (ValueError, TypeError):
                created_at = datetime.now()

        return cls(
            title=data["title"],
            artist=data.get("artist", "Unknown"),
            url=data["url"],
            duration=data["duration"],
            genre=data.get("genre", "unknown"),
            mood=data.get("mood", "neutral"),
            copyright_status=copyright_status,
            confidence_score=data.get("confidence_score", 0.5),
            source=data.get("source", "unknown"),
            license_url=data.get("license_url"),
            tags=data.get("tags", []),
            file_size=data.get("file_size"),
            bitrate=data.get("bitrate"),
            sample_rate=data.get("sample_rate"),
            created_at=created_at,
        )

    def __repr__(self) -> str:
        return (
            f"MusicRecommendation("
            f"title='{self.title}', "
            f"artist='{self.artist}', "
            f"genre='{self.genre}', "
            f"mood='{self.mood}', "
            f"copyright='{self.copyright_status.value}', "
            f"confidence={self.confidence_score:.2f}"
            f")"
        )


@dataclass
class MusicSearchCriteria:
    """音乐搜索条件"""

    genres: Optional[List[str]] = None
    """偏好的音乐类型"""

    moods: Optional[List[str]] = None
    """偏好的情绪类型"""

    max_duration: Optional[float] = None
    """最大时长（秒）"""

    min_duration: Optional[float] = None
    """最小时长（秒）"""

    copyright_only: bool = True
    """是否只搜索无版权音乐"""

    sources: Optional[List[str]] = None
    """指定的音乐来源"""

    def __post_init__(self):
        """参数验证"""
        if self.genres is None:
            self.genres = ["ambient", "electronic", "classical", "jazz"]

        if self.moods is None:
            self.moods = ["calm", "inspiring", "neutral"]

        if self.sources is None:
            # 优先使用 Jamendo（从 .env 读取配置）
            self.sources = ["jamendo", "freemusicarchive", "ccsearch", "epidemicsound"]

        if self.max_duration is not None and self.max_duration <= 0:
            raise ValueError("max_duration must be positive")

        if self.min_duration is not None and self.min_duration <= 0:
            raise ValueError("min_duration must be positive")

        if self.min_duration and self.max_duration and self.min_duration > self.max_duration:
            raise ValueError("min_duration cannot be greater than max_duration")

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "genres": self.genres,
            "moods": self.moods,
            "max_duration": self.max_duration,
            "min_duration": self.min_duration,
            "copyright_only": self.copyright_only,
            "sources": self.sources,
        }


@dataclass
class MusicLibraryEntry:
    """音乐库条目"""

    recommendation: MusicRecommendation
    """音乐推荐信息"""

    local_path: str
    """本地文件路径"""

    downloaded_at: datetime
    """下载时间"""

    last_used: Optional[datetime] = None
    """最后使用时间"""

    use_count: int = 0
    """使用次数"""

    file_hash: Optional[str] = None
    """文件哈希值（用于完整性验证）"""

    def __post_init__(self):
        """数据验证"""
        if not isinstance(self.recommendation, MusicRecommendation):
            raise ValueError("recommendation must be a MusicRecommendation instance")

        if not isinstance(self.local_path, str) or not self.local_path.strip():
            raise ValueError("local_path must be a non-empty string")

        if not isinstance(self.downloaded_at, datetime):
            raise ValueError("downloaded_at must be a datetime")

        if self.use_count < 0:
            raise ValueError("use_count must be non-negative")

    def mark_as_used(self):
        """标记为已使用"""
        self.last_used = datetime.now()
        self.use_count += 1

    def is_expired(self, max_age_days: int = 30) -> bool:
        """检查是否过期"""
        if self.last_used is None:
            # 如果从未使用，检查下载时间
            age = datetime.now() - self.downloaded_at
        else:
            age = datetime.now() - self.last_used

        return age.days > max_age_days

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "recommendation": self.recommendation.to_dict(),
            "local_path": self.local_path,
            "downloaded_at": self.downloaded_at.isoformat(),
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "use_count": self.use_count,
            "file_hash": self.file_hash,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MusicLibraryEntry':
        """从字典创建实例"""
        recommendation = MusicRecommendation.from_dict(data["recommendation"])

        downloaded_at = datetime.fromisoformat(data["downloaded_at"])

        last_used = None
        if data.get("last_used"):
            try:
                last_used = datetime.fromisoformat(data["last_used"])
            except (ValueError, TypeError):
                pass

        return cls(
            recommendation=recommendation,
            local_path=data["local_path"],
            downloaded_at=downloaded_at,
            last_used=last_used,
            use_count=data.get("use_count", 0),
            file_hash=data.get("file_hash"),
        )
