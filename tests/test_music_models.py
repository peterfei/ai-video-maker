#!/usr/bin/env python3
"""
测试音乐相关数据模型
"""

import pytest
from datetime import datetime
from src.audio.models import (
    CopyrightStatus,
    MusicRecommendation,
    MusicSearchCriteria,
    MusicLibraryEntry,
)


class TestCopyrightStatus:
    """测试版权状态枚举"""

    def test_safe_to_use_property(self):
        """测试安全使用属性"""
        assert CopyrightStatus.PUBLIC_DOMAIN.is_safe_to_use == True
        assert CopyrightStatus.CREATIVE_COMMONS.is_safe_to_use == True
        assert CopyrightStatus.ROYALTY_FREE.is_safe_to_use == True
        assert CopyrightStatus.UNKNOWN.is_safe_to_use == False
        assert CopyrightStatus.COPYRIGHTED.is_safe_to_use == False

    def test_license_description(self):
        """测试许可证描述"""
        assert "公有领域" in CopyrightStatus.PUBLIC_DOMAIN.license_description
        assert "创意共享" in CopyrightStatus.CREATIVE_COMMONS.license_description
        assert "免版税" in CopyrightStatus.ROYALTY_FREE.license_description
        assert "未知" in CopyrightStatus.UNKNOWN.license_description
        assert "受版权保护" in CopyrightStatus.COPYRIGHTED.license_description


class TestMusicRecommendation:
    """测试音乐推荐模型"""

    def test_creation_success(self):
        """测试成功创建推荐"""
        rec = MusicRecommendation(
            title="Test Track",
            artist="Test Artist",
            url="https://example.com/track.mp3",
            duration=180.0,
            genre="electronic",
            mood="calm",
            copyright_status=CopyrightStatus.CREATIVE_COMMONS,
            confidence_score=0.85,
            source="jamendo",
        )

        assert rec.title == "Test Track"
        assert rec.artist == "Test Artist"
        assert rec.duration == 180.0
        assert rec.genre == "electronic"
        assert rec.mood == "calm"
        assert rec.copyright_status == CopyrightStatus.CREATIVE_COMMONS
        assert rec.confidence_score == 0.85
        assert rec.source == "jamendo"
        assert rec.is_safe_to_use == True

    def test_creation_validation(self):
        """测试创建验证"""
        # 测试空标题
        with pytest.raises(ValueError, match="title must be a non-empty string"):
            MusicRecommendation(
                title="",
                artist="Artist",
                url="https://example.com",
                duration=180.0,
                genre="electronic",
                mood="calm",
                copyright_status=CopyrightStatus.CREATIVE_COMMONS,
                confidence_score=0.8,
                source="test",
            )

        # 测试无效置信度
        with pytest.raises(ValueError, match="confidence_score must be between 0.0 and 1.0"):
            MusicRecommendation(
                title="Test",
                artist="Artist",
                url="https://example.com",
                duration=180.0,
                genre="electronic",
                mood="calm",
                copyright_status=CopyrightStatus.CREATIVE_COMMONS,
                confidence_score=1.5,  # 超出范围
                source="test",
            )

    def test_duration_formatted(self):
        """测试时长格式化"""
        rec = MusicRecommendation(
            title="Test",
            artist="Artist",
            url="https://example.com",
            duration=125.5,  # 2分5.5秒
            genre="electronic",
            mood="calm",
            copyright_status=CopyrightStatus.CREATIVE_COMMONS,
            confidence_score=0.8,
            source="test",
        )

        assert rec.duration_formatted == "2:05"

    def test_to_dict_and_from_dict(self):
        """测试字典序列化"""
        original = MusicRecommendation(
            title="Test Track",
            artist="Test Artist",
            url="https://example.com/track.mp3",
            duration=180.0,
            genre="electronic",
            mood="calm",
            copyright_status=CopyrightStatus.CREATIVE_COMMONS,
            confidence_score=0.85,
            source="jamendo",
            license_url="https://license.example.com",
        )

        # 转换为字典
        data = original.to_dict()

        # 从字典创建
        restored = MusicRecommendation.from_dict(data)

        # 验证属性
        assert restored.title == original.title
        assert restored.artist == original.artist
        assert restored.url == original.url
        assert restored.duration == original.duration
        assert restored.genre == original.genre
        assert restored.mood == original.mood
        assert restored.copyright_status == original.copyright_status
        assert restored.confidence_score == original.confidence_score
        assert restored.source == original.source
        assert restored.license_url == original.license_url


class TestMusicSearchCriteria:
    """测试音乐搜索条件"""

    def test_creation_with_defaults(self):
        """测试使用默认值创建"""
        criteria = MusicSearchCriteria()

        assert criteria.genres == ["ambient", "electronic", "classical", "jazz"]
        assert criteria.moods == ["calm", "inspiring", "neutral"]
        assert criteria.copyright_only == True
        assert criteria.sources == ["freemusicarchive", "ccsearch", "epidemicsound"]

    def test_creation_validation(self):
        """测试创建验证"""
        # 测试无效时长范围
        with pytest.raises(ValueError, match="min_duration cannot be greater than max_duration"):
            MusicSearchCriteria(min_duration=300, max_duration=200)

    def test_to_dict(self):
        """测试转换为字典"""
        criteria = MusicSearchCriteria(
            genres=["classical", "jazz"],
            moods=["calm"],
            max_duration=300,
            copyright_only=False,
        )

        data = criteria.to_dict()

        assert data["genres"] == ["classical", "jazz"]
        assert data["moods"] == ["calm"]
        assert data["max_duration"] == 300
        assert data["copyright_only"] == False


class TestMusicLibraryEntry:
    """测试音乐库条目"""

    def test_creation_success(self):
        """测试成功创建条目"""
        rec = MusicRecommendation(
            title="Test Track",
            artist="Test Artist",
            url="https://example.com/track.mp3",
            duration=180.0,
            genre="electronic",
            mood="calm",
            copyright_status=CopyrightStatus.CREATIVE_COMMONS,
            confidence_score=0.8,
            source="jamendo",
        )

        entry = MusicLibraryEntry(
            recommendation=rec,
            local_path="/path/to/track.mp3",
            downloaded_at=datetime.now(),
            use_count=5,
        )

        assert entry.recommendation == rec
        assert entry.local_path == "/path/to/track.mp3"
        assert entry.use_count == 5
        assert entry.file_hash is None

    def test_mark_as_used(self):
        """测试标记为已使用"""
        rec = MusicRecommendation(
            title="Test",
            artist="Artist",
            url="https://example.com",
            duration=180.0,
            genre="electronic",
            mood="calm",
            copyright_status=CopyrightStatus.CREATIVE_COMMONS,
            confidence_score=0.8,
            source="test",
        )

        entry = MusicLibraryEntry(
            recommendation=rec,
            local_path="/path/to/track.mp3",
            downloaded_at=datetime.now(),
        )

        initial_count = entry.use_count
        entry.mark_as_used()

        assert entry.use_count == initial_count + 1
        assert entry.last_used is not None

    def test_to_dict_and_from_dict(self):
        """测试字典序列化"""
        rec = MusicRecommendation(
            title="Test Track",
            artist="Test Artist",
            url="https://example.com/track.mp3",
            duration=180.0,
            genre="electronic",
            mood="calm",
            copyright_status=CopyrightStatus.CREATIVE_COMMONS,
            confidence_score=0.8,
            source="jamendo",
        )

        original = MusicLibraryEntry(
            recommendation=rec,
            local_path="/path/to/track.mp3",
            downloaded_at=datetime(2024, 1, 1, 12, 0, 0),
            use_count=3,
            file_hash="abc123",
        )

        # 转换为字典
        data = original.to_dict()

        # 从字典创建
        restored = MusicLibraryEntry.from_dict(data)

        # 验证属性
        assert restored.recommendation.title == original.recommendation.title
        assert restored.local_path == original.local_path
        assert restored.downloaded_at == original.downloaded_at
        assert restored.use_count == original.use_count
        assert restored.file_hash == original.file_hash


if __name__ == "__main__":
    pytest.main([__file__])
