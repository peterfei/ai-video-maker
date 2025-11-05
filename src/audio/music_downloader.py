"""
背景音乐下载器

负责下载和缓存无版权背景音乐文件。
"""

import os
import hashlib
import logging
from typing import Optional, Dict, Any
from pathlib import Path
from urllib.parse import urlparse
import asyncio
import aiohttp
from aiohttp import ClientTimeout
import time

from .models import MusicRecommendation, MusicLibraryEntry

logger = logging.getLogger(__name__)


class MusicDownloader:
    """
    背景音乐下载器

    支持异步下载音乐文件，包含完整性验证、缓存管理和错误处理。
    """

    def __init__(self, config: Dict[str, Any]):
        """
        初始化下载器

        Args:
            config: 下载相关配置
        """
        self.download_dir = Path(config.get('dir', 'assets/music'))
        self.max_file_size = config.get('max_size', 50 * 1024 * 1024)  # 50MB
        self.timeout = config.get('timeout', 30)  # 30秒超时
        self.chunk_size = config.get('chunk_size', 8192)  # 8KB块大小

        # 确保下载目录存在
        self.download_dir.mkdir(parents=True, exist_ok=True)

        # 支持的文件格式
        self.supported_formats = ['.mp3', '.wav', '.flac', '.ogg', '.m4a', '.aac']

        # HTTP客户端会话
        self.session: Optional[aiohttp.ClientSession] = None

        logger.info(f"MusicDownloader initialized with dir: {self.download_dir}")

    async def __aenter__(self):
        """异步上下文管理器入口"""
        timeout = ClientTimeout(total=self.timeout)
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
            self.session = None

    async def download_music(
        self,
        recommendation: MusicRecommendation,
        force_redownload: bool = False
    ) -> Optional[str]:
        """
        下载音乐文件

        Args:
            recommendation: 音乐推荐信息
            force_redownload: 是否强制重新下载

        Returns:
            本地文件路径，如果下载失败则返回None
        """
        if not self.session:
            raise RuntimeError("Downloader must be used as async context manager")

        try:
            # 0. 检查URL是否是本地文件路径
            if self._is_local_file(recommendation.url):
                local_file = Path(recommendation.url)
                if local_file.exists() and local_file.is_file():
                    logger.info(f"Using local music file: {local_file}")
                    return str(local_file)
                else:
                    logger.warning(f"Local file not found: {local_file}")
                    return None

            # 1. 生成本地文件路径
            local_path = self._generate_local_path(recommendation)

            # 2. 检查文件是否已存在
            if local_path.exists() and not force_redownload:
                logger.info(f"Music file already exists: {local_path}")
                return str(local_path)

            # 3. 下载文件
            logger.info(f"Downloading music: {recommendation.title} from {recommendation.url}")
            start_time = time.time()

            success = await self._download_file(recommendation.url, local_path)

            if success:
                download_time = time.time() - start_time
                file_size = local_path.stat().st_size
                logger.info(
                    f"Downloaded {recommendation.title} "
                    f"({file_size} bytes) in {download_time:.2f}s"
                )

                # 4. 验证下载的文件
                if await self._validate_download(recommendation, local_path):
                    return str(local_path)
                else:
                    # 验证失败，删除文件
                    local_path.unlink(missing_ok=True)
                    return None
            else:
                return None

        except Exception as e:
            logger.error(f"Error downloading music {recommendation.title}: {e}")
            return None

    def _is_local_file(self, url: str) -> bool:
        """
        检查URL是否是本地文件路径

        Args:
            url: URL字符串

        Returns:
            是否是本地文件路径
        """
        # 检查是否是HTTP/HTTPS URL
        if url.startswith(('http://', 'https://')):
            return False

        # 检查是否包含URL scheme
        parsed = urlparse(url)
        if parsed.scheme and parsed.scheme not in ('file', ''):
            return False

        # 检查是否是有效的文件路径
        try:
            path = Path(url)
            # 如果路径是绝对路径或存在，则认为是本地文件
            return path.is_absolute() or path.exists()
        except:
            return False

    def _generate_local_path(self, recommendation: MusicRecommendation) -> Path:
        """
        生成本地文件路径

        Args:
            recommendation: 音乐推荐信息

        Returns:
            本地文件路径
        """
        # 从URL提取文件扩展名
        parsed_url = urlparse(recommendation.url)
        url_path = parsed_url.path

        # 尝试从URL路径获取扩展名
        file_ext = '.mp3'  # 默认扩展名
        for ext in self.supported_formats:
            if url_path.lower().endswith(ext):
                file_ext = ext
                break

        # 生成安全的文件名
        # 使用标题的哈希值确保唯一性，避免特殊字符问题
        title_hash = hashlib.md5(recommendation.title.encode()).hexdigest()[:8]
        safe_filename = f"{title_hash}_{recommendation.source}{file_ext}"

        return self.download_dir / safe_filename

    async def _download_file(self, url: str, local_path: Path) -> bool:
        """
        下载文件到本地

        Args:
            url: 下载URL
            local_path: 本地路径

        Returns:
            下载是否成功
        """
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    logger.warning(f"HTTP {response.status} for URL: {url}")
                    return False

                # 检查文件大小
                content_length = response.headers.get('Content-Length')
                if content_length:
                    size = int(content_length)
                    if size > self.max_file_size:
                        logger.warning(f"File too large: {size} bytes")
                        return False

                # 下载文件
                downloaded_size = 0
                with open(local_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(self.chunk_size):
                        if chunk:
                            f.write(chunk)
                            downloaded_size += len(chunk)

                            # 检查大小限制
                            if downloaded_size > self.max_file_size:
                                logger.warning(f"Download exceeded size limit: {downloaded_size}")
                                local_path.unlink(missing_ok=True)
                                return False

                return True

        except asyncio.TimeoutError:
            logger.warning(f"Download timeout for URL: {url}")
            return False
        except aiohttp.ClientError as e:
            logger.warning(f"HTTP error downloading {url}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error downloading {url}: {e}")
            return False

    async def _validate_download(
        self,
        recommendation: MusicRecommendation,
        local_path: Path
    ) -> bool:
        """
        验证下载的文件

        Args:
            recommendation: 音乐推荐信息
            local_path: 本地文件路径

        Returns:
            文件是否有效
        """
        try:
            # 1. 检查文件大小
            stat = local_path.stat()
            if stat.st_size == 0:
                logger.warning("Downloaded file is empty")
                return False

            if stat.st_size > self.max_file_size:
                logger.warning(f"File size {stat.st_size} exceeds limit")
                return False

            # 2. 检查文件格式（通过扩展名）
            if local_path.suffix.lower() not in self.supported_formats:
                logger.warning(f"Unsupported file format: {local_path.suffix}")
                return False

            # 3. 尝试读取文件头部验证格式
            is_valid_format = await self._check_audio_format(local_path)
            if not is_valid_format:
                logger.warning("File format validation failed")
                return False

            # 4. 计算文件哈希（用于完整性验证）
            file_hash = self._calculate_file_hash(local_path)

            # 更新推荐信息
            recommendation.file_size = stat.st_size
            recommendation.file_hash = file_hash

            return True

        except Exception as e:
            logger.error(f"Error validating download: {e}")
            return False

    async def _check_audio_format(self, file_path: Path) -> bool:
        """
        检查音频文件格式

        Args:
            file_path: 文件路径

        Returns:
            格式是否有效
        """
        try:
            # 读取文件头部几个字节来判断格式
            with open(file_path, 'rb') as f:
                header = f.read(12)  # 读取前12字节

            if len(header) < 4:
                return False

            # 检查常见音频格式的文件头
            if header.startswith(b'RIFF') and header[8:12] == b'WAVE':
                return True  # WAV
            elif header.startswith(b'ID3') or header.startswith(b'\xff\xfb'):
                return True  # MP3
            elif header.startswith(b'fLaC'):
                return True  # FLAC
            elif header.startswith(b'OggS'):
                return True  # OGG
            elif header[4:8] == b'ftyp':
                return True  # M4A/AAC
            else:
                # 对于未知格式，暂时认为有效（可能有其他音频格式）
                logger.warning(f"Unknown audio format header: {header[:4].hex()}")
                return True

        except Exception as e:
            logger.error(f"Error checking audio format: {e}")
            return False

    def _calculate_file_hash(self, file_path: Path) -> str:
        """
        计算文件的MD5哈希值

        Args:
            file_path: 文件路径

        Returns:
            哈希字符串
        """
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating file hash: {e}")
            return ""

    async def batch_download(
        self,
        recommendations: list[MusicRecommendation],
        max_concurrent: int = 3
    ) -> Dict[str, Optional[str]]:
        """
        批量下载音乐文件

        Args:
            recommendations: 音乐推荐列表
            max_concurrent: 最大并发下载数

        Returns:
            URL到本地路径的映射，下载失败的条目值为None
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        results = {}

        async def download_with_semaphore(rec: MusicRecommendation) -> tuple[str, Optional[str]]:
            async with semaphore:
                local_path = await self.download_music(rec)
                return rec.url, local_path

        tasks = [download_with_semaphore(rec) for rec in recommendations]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in batch_results:
            if isinstance(result, Exception):
                logger.error(f"Batch download task failed: {result}")
                continue
            url, local_path = result
            results[url] = local_path

        successful = sum(1 for path in results.values() if path is not None)
        logger.info(f"Batch download completed: {successful}/{len(recommendations)} successful")

        return results

    def cleanup_expired_files(self, max_age_days: int = 30) -> int:
        """
        清理过期的下载文件

        Args:
            max_age_days: 最大保存天数

        Returns:
            清理的文件数量
        """
        import time
        current_time = time.time()
        max_age_seconds = max_age_days * 24 * 60 * 60

        cleaned_count = 0
        for file_path in self.download_dir.glob('*'):
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > max_age_seconds:
                    try:
                        file_path.unlink()
                        cleaned_count += 1
                        logger.info(f"Cleaned up expired file: {file_path}")
                    except Exception as e:
                        logger.warning(f"Failed to clean up {file_path}: {e}")

        logger.info(f"Cleaned up {cleaned_count} expired files")
        return cleaned_count

    def get_download_stats(self) -> Dict[str, Any]:
        """
        获取下载统计信息

        Returns:
            统计信息字典
        """
        total_files = 0
        total_size = 0
        file_types = {}

        for file_path in self.download_dir.glob('*'):
            if file_path.is_file():
                total_files += 1
                size = file_path.stat().st_size
                total_size += size

                ext = file_path.suffix.lower()
                file_types[ext] = file_types.get(ext, 0) + 1

        return {
            'total_files': total_files,
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'file_types': file_types,
            'download_dir': str(self.download_dir),
        }
