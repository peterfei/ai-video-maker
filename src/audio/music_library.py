"""
背景音乐库管理

管理本地音乐库，包括缓存、搜索、过期清理等功能。
"""

import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime, timedelta
import asyncio

from .models import (
    MusicRecommendation,
    MusicSearchCriteria,
    MusicLibraryEntry,
    CopyrightStatus,
)
from .music_recommender import MusicRecommender
from .music_downloader import MusicDownloader

logger = logging.getLogger(__name__)


class MusicLibrary:
    """
    背景音乐库管理器

    负责音乐文件的本地存储、缓存管理和检索。
    """

    def __init__(self, config: Dict[str, Any]):
        """
        初始化音乐库

        Args:
            config: 音乐库配置
        """
        self.library_path = Path(config.get('library_path', 'data/music_library.json'))
        self.cache_enabled = config.get('cache_enabled', True)
        self.max_cache_age = config.get('max_cache_age', 30)  # 天
        self.max_cache_files = config.get('max_cache_files', 100)

        # 确保数据目录存在
        self.library_path.parent.mkdir(parents=True, exist_ok=True)

        # 初始化组件
        # 传递完整的music配置，让MusicRecommender可以访问sources配置
        self.recommender = MusicRecommender(config)
        self.downloader = MusicDownloader(config.get('download', {}))

        # 加载音乐库
        self.entries: Dict[str, MusicLibraryEntry] = {}
        self._load_library()

        logger.info(f"MusicLibrary initialized with {len(self.entries)} entries")

    def _load_library(self):
        """加载音乐库数据"""
        if not self.library_path.exists():
            logger.info("Music library file not found, starting with empty library")
            return

        try:
            with open(self.library_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for entry_data in data.get('entries', []):
                try:
                    entry = MusicLibraryEntry.from_dict(entry_data)
                    # 验证本地文件是否存在
                    if Path(entry.local_path).exists():
                        self.entries[entry.recommendation.url] = entry
                    else:
                        logger.warning(f"Local file not found: {entry.local_path}")
                except Exception as e:
                    logger.warning(f"Failed to load library entry: {e}")

            logger.info(f"Loaded {len(self.entries)} valid entries from library")

        except Exception as e:
            logger.error(f"Error loading music library: {e}")
            self.entries = {}

    def _save_library(self):
        """保存音乐库数据"""
        try:
            data = {
                'metadata': {
                    'version': '1.0',
                    'last_updated': datetime.now().isoformat(),
                    'total_entries': len(self.entries),
                },
                'entries': [entry.to_dict() for entry in self.entries.values()],
            }

            with open(self.library_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.debug(f"Saved {len(self.entries)} entries to library")

        except Exception as e:
            logger.error(f"Error saving music library: {e}")

    async def get_music_for_content(
        self,
        content: str,
        duration: float,
        criteria: Optional[MusicSearchCriteria] = None
    ) -> Optional[MusicRecommendation]:
        """
        为指定内容获取合适的背景音乐

        Args:
            content: 内容文本
            duration: 时长（秒）
            criteria: 搜索条件

        Returns:
            推荐的音乐（包含local_path属性），如果没有找到则返回None
        """
        try:
            # 1. 在本地库中搜索
            local_match = self._find_in_library(content, duration, criteria)
            if local_match:
                logger.info(f"Found matching music in library: {local_match.recommendation.title}")
                local_match.mark_as_used()
                self._save_library()
                # 将本地路径添加到推荐对象上（临时属性）
                recommendation = local_match.recommendation
                recommendation.local_path = local_match.local_path
                return recommendation

            # 2. 如果缓存启用且没有找到，从远程获取
            if not self.cache_enabled:
                logger.info("Cache disabled, skipping remote search")
                return None

            # 3. 获取新的推荐
            recommendations = await self.recommender.recommend_music(content, duration, criteria)
            if not recommendations:
                logger.warning("No music recommendations found")
                return None

            # 4. 下载最好的推荐
            best_recommendation = recommendations[0]
            local_path = await self._download_and_cache(best_recommendation)

            if local_path:
                # 将本地路径添加到推荐对象上（临时属性）
                best_recommendation.local_path = local_path
                return best_recommendation
            else:
                logger.warning("Failed to download recommended music")
                return None

        except Exception as e:
            logger.error(f"Error getting music for content: {e}")
            return None

    def _find_in_library(
        self,
        content: str,
        duration: float,
        criteria: Optional[MusicSearchCriteria] = None
    ) -> Optional[MusicLibraryEntry]:
        """
        在本地库中查找匹配的音乐

        Args:
            content: 内容文本
            duration: 时长
            criteria: 搜索条件

        Returns:
            匹配的库条目
        """
        if not criteria:
            criteria = MusicSearchCriteria()

        # 简单的匹配逻辑：查找类型和情绪匹配的音乐
        candidates = []

        for entry in self.entries.values():
            rec = entry.recommendation

            # 检查是否过期
            if entry.is_expired(self.max_cache_age):
                continue

            # 检查版权状态
            if criteria.copyright_only and not rec.is_safe_to_use:
                continue

            # 检查时长范围
            if criteria.max_duration and rec.duration > criteria.max_duration:
                continue
            if criteria.min_duration and rec.duration < criteria.min_duration:
                continue

            # 计算匹配度（简单的关键词匹配）
            content_lower = content.lower()
            title_match = any(word in rec.title.lower() for word in content_lower.split())
            genre_match = rec.genre in criteria.genres
            mood_match = rec.mood in criteria.moods

            # 计算匹配分数
            match_score = (
                (1.0 if title_match else 0.0) * 0.4 +
                (1.0 if genre_match else 0.0) * 0.3 +
                (1.0 if mood_match else 0.0) * 0.3
            )

            if match_score > 0.3:  # 匹配阈值
                candidates.append((entry, match_score))

        if not candidates:
            return None

        # 按匹配分数和使用频率排序
        candidates.sort(key=lambda x: (x[1], x[0].use_count), reverse=True)
        return candidates[0][0]

    async def _download_and_cache(self, recommendation: MusicRecommendation) -> Optional[str]:
        """
        下载并缓存音乐

        Args:
            recommendation: 音乐推荐

        Returns:
            本地文件路径
        """
        async with self.downloader as downloader:
            local_path = await downloader.download_music(recommendation)

            if local_path:
                # 创建库条目
                entry = MusicLibraryEntry(
                    recommendation=recommendation,
                    local_path=local_path,
                    downloaded_at=datetime.now(),
                )

                # 添加到库中
                self.entries[recommendation.url] = entry
                self._save_library()

                logger.info(f"Cached music: {recommendation.title}")
                return local_path

        return None

    async def preload_music(
        self,
        recommendations: List[MusicRecommendation],
        max_concurrent: int = 3
    ) -> Dict[str, bool]:
        """
        预加载音乐到缓存

        Args:
            recommendations: 要预加载的音乐推荐列表
            max_concurrent: 最大并发下载数

        Returns:
            URL到下载成功状态的映射
        """
        results = {}

        async with self.downloader as downloader:
            batch_results = await downloader.batch_download(recommendations, max_concurrent)

            for rec in recommendations:
                local_path = batch_results.get(rec.url)
                if local_path:
                    entry = MusicLibraryEntry(
                        recommendation=rec,
                        local_path=local_path,
                        downloaded_at=datetime.now(),
                    )
                    self.entries[rec.url] = entry
                    results[rec.url] = True
                else:
                    results[rec.url] = False

        self._save_library()
        successful = sum(1 for success in results.values() if success)
        logger.info(f"Preloaded {successful}/{len(recommendations)} music files")

        return results

    def cleanup_expired_entries(self) -> int:
        """
        清理过期的库条目

        Returns:
            清理的条目数量
        """
        expired_urls = []
        cleaned_count = 0

        for url, entry in self.entries.items():
            if entry.is_expired(self.max_cache_age):
                expired_urls.append(url)
                cleaned_count += 1

        # 删除过期条目
        for url in expired_urls:
            del self.entries[url]

        if cleaned_count > 0:
            self._save_library()
            logger.info(f"Cleaned up {cleaned_count} expired library entries")

        return cleaned_count

    def cleanup_unused_files(self) -> int:
        """
        清理未在库中注册的文件

        Returns:
            清理的文件数量
        """
        library_paths = {Path(entry.local_path) for entry in self.entries.values()}
        download_dir = Path(self.downloader.download_dir)

        cleaned_count = 0
        for file_path in download_dir.glob('*'):
            if file_path.is_file() and file_path not in library_paths:
                try:
                    file_path.unlink()
                    cleaned_count += 1
                    logger.info(f"Cleaned up unused file: {file_path}")
                except Exception as e:
                    logger.warning(f"Failed to clean up {file_path}: {e}")

        logger.info(f"Cleaned up {cleaned_count} unused files")
        return cleaned_count

    def optimize_cache(self):
        """
        优化缓存：清理过期条目和未使用文件，限制缓存大小
        """
        logger.info("Starting cache optimization")

        # 清理过期条目
        expired_count = self.cleanup_expired_entries()

        # 清理未使用文件
        unused_count = self.cleanup_unused_files()

        # 如果仍然超过最大缓存文件数，删除最少使用的文件
        if len(self.entries) > self.max_cache_files:
            entries_list = list(self.entries.items())
            # 按使用次数和最后使用时间排序
            entries_list.sort(key=lambda x: (x[1].use_count, x[1].last_used or datetime.min))

            to_remove = len(entries_list) - self.max_cache_files
            removed_count = 0

            for url, entry in entries_list[:to_remove]:
                try:
                    Path(entry.local_path).unlink(missing_ok=True)
                    del self.entries[url]
                    removed_count += 1
                except Exception as e:
                    logger.warning(f"Failed to remove cached file {entry.local_path}: {e}")

            if removed_count > 0:
                self._save_library()
                logger.info(f"Removed {removed_count} least-used cached files")

        logger.info("Cache optimization completed")

    def get_library_stats(self) -> Dict[str, Any]:
        """
        获取库统计信息

        Returns:
            统计信息字典
        """
        total_entries = len(self.entries)
        total_size = sum(
            Path(entry.local_path).stat().st_size
            for entry in self.entries.values()
            if Path(entry.local_path).exists()
        )

        genres = {}
        sources = {}
        copyright_status = {}
        use_count_total = 0

        for entry in self.entries.values():
            rec = entry.recommendation

            genres[rec.genre] = genres.get(rec.genre, 0) + 1
            sources[rec.source] = sources.get(rec.source, 0) + 1
            copyright_status[rec.copyright_status.value] = \
                copyright_status.get(rec.copyright_status.value, 0) + 1
            use_count_total += entry.use_count

        return {
            'total_entries': total_entries,
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'genres': genres,
            'sources': sources,
            'copyright_status': copyright_status,
            'total_use_count': use_count_total,
            'average_use_count': round(use_count_total / max(total_entries, 1), 2),
            'library_path': str(self.library_path),
        }

    def search_library(
        self,
        query: str = "",
        genre: Optional[str] = None,
        mood: Optional[str] = None,
        source: Optional[str] = None,
        copyright_only: bool = True
    ) -> List[MusicLibraryEntry]:
        """
        在库中搜索音乐

        Args:
            query: 搜索关键词
            genre: 类型过滤
            mood: 情绪过滤
            source: 来源过滤
            copyright_only: 是否只返回无版权音乐

        Returns:
            匹配的库条目列表
        """
        results = []

        query_lower = query.lower()

        for entry in self.entries.values():
            rec = entry.recommendation

            # 版权过滤
            if copyright_only and not rec.is_safe_to_use:
                continue

            # 条件过滤
            if genre and rec.genre != genre:
                continue
            if mood and rec.mood != mood:
                continue
            if source and rec.source != source:
                continue

            # 关键词搜索
            if query:
                searchable_text = f"{rec.title} {rec.artist} {rec.genre} {rec.mood}".lower()
                if query_lower not in searchable_text:
                    continue

            results.append(entry)

        # 按使用次数排序
        results.sort(key=lambda x: x.use_count, reverse=True)
        return results

    def export_library(self, export_path: Optional[str] = None) -> str:
        """
        导出音乐库数据

        Args:
            export_path: 导出路径，如果不指定则使用默认路径

        Returns:
            导出文件路径
        """
        if not export_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_path = f"music_library_export_{timestamp}.json"

        export_data = {
            'export_info': {
                'timestamp': datetime.now().isoformat(),
                'total_entries': len(self.entries),
                'version': '1.0',
            },
            'stats': self.get_library_stats(),
            'entries': [entry.to_dict() for entry in self.entries.values()],
        }

        with open(export_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Exported library to {export_path}")
        return export_path
