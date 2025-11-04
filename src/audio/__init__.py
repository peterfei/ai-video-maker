"""
音频处理模块
提供TTS语音合成、音频混合、STT语音识别和智能背景音乐推荐功能
"""

from .tts_engine import TTSEngine
from .audio_mixer import AudioMixer
from .stt_engine import STTEngine, STTResult, STTSegment, get_stt_engine, unload_stt_engines
from .models import STTConfig

# 音乐推荐功能
from .music_recommender import MusicRecommender
from .music_library import MusicLibrary
from .music_downloader import MusicDownloader
from .models import (
CopyrightStatus,
MusicRecommendation,
MusicSearchCriteria,
MusicLibraryEntry,
)

__all__ = [
    # 现有功能
    'TTSEngine',
    'AudioMixer',
    # STT 功能
    'STTEngine',
    'STTResult',
    'STTSegment',
    'STTConfig',
    'get_stt_engine',
    'unload_stt_engines',
    # 音乐推荐功能
    'MusicRecommender',
    'MusicLibrary',
    'MusicDownloader',
    'CopyrightStatus',
    'MusicRecommendation',
    'MusicSearchCriteria',
    'MusicLibraryEntry',
]
