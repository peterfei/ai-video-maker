"""
免费图库API集成
支持 Unsplash 和 Pexels
"""

import requests
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import hashlib
import json
from datetime import datetime


class ImageAPI:
    """图片API基类"""

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化图片API

        Args:
            api_key: API密钥
        """
        self.api_key = api_key
        self.cache_dir = Path("data/image_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def search(self, query: str, count: int = 5) -> List[Dict[str, Any]]:
        """
        搜索图片

        Args:
            query: 搜索关键词
            count: 返回数量

        Returns:
            图片信息列表
        """
        raise NotImplementedError

    def download_image(self, url: str, keyword: str) -> Optional[Path]:
        """
        下载图片

        Args:
            url: 图片URL
            keyword: 关键词（用于文件命名）

        Returns:
            下载后的文件路径
        """
        try:
            # 生成文件名
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            safe_keyword = keyword.replace(' ', '_').replace('/', '_')
            filename = f"{safe_keyword}_{url_hash}.jpg"
            filepath = self.cache_dir / filename

            # 如果已存在，直接返回
            if filepath.exists():
                return filepath

            # 下载图片
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            with open(filepath, 'wb') as f:
                f.write(response.content)

            return filepath

        except Exception as e:
            print(f"下载图片失败: {e}")
            return None

    def get_cached_results(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """
        获取缓存的搜索结果

        Args:
            query: 搜索关键词

        Returns:
            缓存的结果列表
        """
        cache_file = self.cache_dir / f"search_{query}.json"

        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # 检查缓存是否过期（7天）
                cached_time = datetime.fromisoformat(data['timestamp'])
                if (datetime.now() - cached_time).days < 7:
                    return data['results']

            except Exception:
                pass

        return None

    def save_search_cache(self, query: str, results: List[Dict[str, Any]]) -> None:
        """
        保存搜索结果缓存

        Args:
            query: 搜索关键词
            results: 搜索结果
        """
        cache_file = self.cache_dir / f"search_{query}.json"

        data = {
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'results': results
        }

        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


class UnsplashAPI(ImageAPI):
    """Unsplash API"""

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化Unsplash API

        Args:
            api_key: Unsplash Access Key
        """
        super().__init__(api_key)
        self.api_key = api_key or os.getenv('UNSPLASH_ACCESS_KEY')
        self.base_url = "https://api.unsplash.com"

    def search(self, query: str, count: int = 5) -> List[Dict[str, Any]]:
        """
        在Unsplash搜索图片

        Args:
            query: 搜索关键词
            count: 返回数量

        Returns:
            图片信息列表
        """
        # 先检查缓存
        cached = self.get_cached_results(query)
        if cached:
            return cached[:count]

        if not self.api_key:
            print("警告: 未设置 UNSPLASH_ACCESS_KEY")
            return []

        try:
            url = f"{self.base_url}/search/photos"
            params = {
                'query': query,
                'per_page': count,
                'orientation': 'landscape'
            }
            headers = {
                'Authorization': f'Client-ID {self.api_key}'
            }

            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()
            results = []

            for item in data.get('results', []):
                result = {
                    'id': item['id'],
                    'url': item['urls']['regular'],
                    'download_url': item['urls']['full'],
                    'thumbnail': item['urls']['small'],
                    'description': item.get('description', query),
                    'author': item['user']['name'],
                    'source': 'unsplash',
                    'link': item['links']['html']
                }
                results.append(result)

            # 保存缓存
            self.save_search_cache(query, results)

            return results

        except Exception as e:
            print(f"Unsplash搜索失败: {e}")
            return []


class PexelsAPI(ImageAPI):
    """Pexels API"""

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化Pexels API

        Args:
            api_key: Pexels API Key
        """
        super().__init__(api_key)
        self.api_key = api_key or os.getenv('PEXELS_API_KEY')
        self.base_url = "https://api.pexels.com/v1"

    def search(self, query: str, count: int = 5) -> List[Dict[str, Any]]:
        """
        在Pexels搜索图片

        Args:
            query: 搜索关键词
            count: 返回数量

        Returns:
            图片信息列表
        """
        # 先检查缓存
        cached = self.get_cached_results(query)
        if cached:
            return cached[:count]

        if not self.api_key:
            print("警告: 未设置 PEXELS_API_KEY")
            return []

        try:
            url = f"{self.base_url}/search"
            params = {
                'query': query,
                'per_page': count,
                'orientation': 'landscape'
            }
            headers = {
                'Authorization': self.api_key
            }

            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()
            results = []

            for item in data.get('photos', []):
                result = {
                    'id': item['id'],
                    'url': item['src']['large'],
                    'download_url': item['src']['original'],
                    'thumbnail': item['src']['medium'],
                    'description': item.get('alt', query),
                    'author': item['photographer'],
                    'source': 'pexels',
                    'link': item['url']
                }
                results.append(result)

            # 保存缓存
            self.save_search_cache(query, results)

            return results

        except Exception as e:
            print(f"Pexels搜索失败: {e}")
            return []


class MultiSourceImageAPI:
    """多源图片API聚合器"""

    def __init__(self, unsplash_key: Optional[str] = None, pexels_key: Optional[str] = None):
        """
        初始化多源API

        Args:
            unsplash_key: Unsplash API密钥
            pexels_key: Pexels API密钥
        """
        self.apis = []

        if unsplash_key or os.getenv('UNSPLASH_ACCESS_KEY'):
            self.apis.append(UnsplashAPI(unsplash_key))

        if pexels_key or os.getenv('PEXELS_API_KEY'):
            self.apis.append(PexelsAPI(pexels_key))

    def search(self, query: str, count: int = 5, per_source: int = 3) -> List[Dict[str, Any]]:
        """
        从多个源搜索图片

        Args:
            query: 搜索关键词
            count: 总共返回数量
            per_source: 每个源的数量

        Returns:
            图片信息列表（混合多个来源）
        """
        all_results = []

        for api in self.apis:
            try:
                results = api.search(query, per_source)
                all_results.extend(results)
            except Exception as e:
                print(f"搜索失败 ({api.__class__.__name__}): {e}")

        # 去重并限制数量
        unique_results = []
        seen_ids = set()

        for result in all_results:
            if result['id'] not in seen_ids:
                unique_results.append(result)
                seen_ids.add(result['id'])

            if len(unique_results) >= count:
                break

        return unique_results[:count]

    def download_images(self, results: List[Dict[str, Any]], keyword: str) -> List[Path]:
        """
        批量下载图片

        Args:
            results: 搜索结果列表
            keyword: 关键词

        Returns:
            下载后的文件路径列表
        """
        downloaded = []

        for result in results:
            # 使用第一个可用的API下载
            for api in self.apis:
                if result['source'] == api.__class__.__name__.replace('API', '').lower():
                    filepath = api.download_image(result['download_url'], keyword)
                    if filepath:
                        downloaded.append(filepath)
                    break

        return downloaded
