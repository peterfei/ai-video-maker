"""
智能素材管理器
自动从本地或在线获取素材，并构建素材库
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import json
from datetime import datetime
import shutil

from .material_source import MaterialSource, Material
from .semantic_matcher import SemanticMatcher
from .image_api import MultiSourceImageAPI
from utils import setup_logger


class AutoMaterialManager:
    """自动素材管理器"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化自动素材管理器

        Args:
            config: 配置字典
        """
        self.config = config
        self.logger = setup_logger("auto_material_manager")

        # 初始化各个组件
        self.material_source = MaterialSource(config.get('materials', {}))
        self.semantic_matcher = SemanticMatcher(config.get('semantic', {}))
        self.image_api = MultiSourceImageAPI(
            unsplash_key=config.get('unsplash_key'),
            pexels_key=config.get('pexels_key')
        )

        # 配置
        self.local_priority = config.get('local_priority', True)
        self.auto_download = config.get('auto_download', True)
        self.build_library = config.get('build_library', True)

        # 路径
        self.library_path = Path(config.get('library_path', 'data/material_library'))
        self.library_path.mkdir(parents=True, exist_ok=True)

        # 加载素材库索引
        self.library_index = self._load_library_index()

    def get_materials_for_script(
        self,
        script_segments: List[Any],
        materials_per_segment: int = 1
    ) -> List[Path]:
        """
        为脚本自动获取素材

        Args:
            script_segments: 脚本片段列表
            materials_per_segment: 每个片段的素材数量

        Returns:
            素材文件路径列表
        """
        self.logger.info(f"开始为 {len(script_segments)} 个脚本片段获取素材")

        # 分析脚本，生成素材需求
        material_needs = self.semantic_matcher.analyze_script_segments(script_segments)

        all_materials = []

        for need in material_needs:
            self.logger.info(f"片段 {need['segment_index']}: {need['text'][:30]}...")
            self.logger.info(f"  关键词: {', '.join(need['keywords'])}")

            # 获取素材
            materials = self._get_materials_for_need(need, materials_per_segment)

            if materials:
                all_materials.extend(materials)
                self.logger.info(f"  ✓ 获取了 {len(materials)} 个素材")
            else:
                self.logger.warning(f"  ✗ 未能获取素材")

        self.logger.info(f"总共获取了 {len(all_materials)} 个素材")

        return all_materials

    def _get_materials_for_need(
        self,
        need: Dict[str, Any],
        count: int
    ) -> List[Path]:
        """
        为单个需求获取素材

        Args:
            need: 素材需求
            count: 需要的数量

        Returns:
            素材路径列表
        """
        materials = []

        # 策略1: 优先从本地素材库查找
        if self.local_priority:
            local_materials = self._search_local_library(need['keywords'], count)
            materials.extend(local_materials)

        # 策略2: 如果本地素材不足，从API获取
        if len(materials) < count and self.auto_download:
            needed = count - len(materials)
            api_materials = self._download_from_api(need, needed)
            materials.extend(api_materials)

        # 策略3: 如果还是不足，使用已有的本地素材
        if len(materials) < count:
            fallback_materials = self._get_fallback_materials(count - len(materials))
            materials.extend(fallback_materials)

        return materials[:count]

    def _search_local_library(self, keywords: List[str], count: int) -> List[Path]:
        """
        在本地素材库中搜索

        Args:
            keywords: 关键词列表
            count: 需要的数量

        Returns:
            素材路径列表
        """
        matched_materials = []

        # 搜索索引
        for keyword in keywords:
            keyword_lower = keyword.lower()

            if keyword_lower in self.library_index:
                for material_path in self.library_index[keyword_lower]:
                    path = Path(material_path)
                    if path.exists() and path not in matched_materials:
                        matched_materials.append(path)

                    if len(matched_materials) >= count:
                        break

            if len(matched_materials) >= count:
                break

        return matched_materials[:count]

    def _download_from_api(self, need: Dict[str, Any], count: int) -> List[Path]:
        """
        从API下载素材

        Args:
            need: 素材需求
            count: 需要的数量

        Returns:
            素材路径列表
        """
        downloaded_paths = []

        try:
            # 生成搜索查询
            query = self.semantic_matcher.generate_search_query(need['keywords'])

            self.logger.info(f"  从在线图库搜索: {query}")

            # 搜索图片
            results = self.image_api.search(query, count=count)

            if not results:
                self.logger.warning(f"  未找到在线素材")
                return []

            # 下载图片
            downloaded_paths = self.image_api.download_images(results, query)

            # 如果启用素材库构建，将下载的图片添加到库中
            if self.build_library:
                for path in downloaded_paths:
                    self._add_to_library(path, need['keywords'])

            self.logger.info(f"  ✓ 下载了 {len(downloaded_paths)} 个素材")

        except Exception as e:
            self.logger.error(f"  从API下载素材失败: {e}")

        return downloaded_paths

    def _add_to_library(self, source_path: Path, keywords: List[str]) -> None:
        """
        将素材添加到素材库

        Args:
            source_path: 源文件路径
            keywords: 关键词列表
        """
        try:
            # 确定目标路径
            category = keywords[0] if keywords else 'general'
            category_dir = self.library_path / category
            category_dir.mkdir(exist_ok=True)

            # 复制文件
            target_path = category_dir / source_path.name

            if not target_path.exists():
                shutil.copy2(source_path, target_path)

                # 更新索引
                for keyword in keywords:
                    keyword_lower = keyword.lower()

                    if keyword_lower not in self.library_index:
                        self.library_index[keyword_lower] = []

                    if str(target_path) not in self.library_index[keyword_lower]:
                        self.library_index[keyword_lower].append(str(target_path))

                # 保存索引
                self._save_library_index()

                self.logger.info(f"  ✓ 添加素材到库: {target_path.name}")

        except Exception as e:
            self.logger.error(f"  添加素材到库失败: {e}")

    def _get_fallback_materials(self, count: int) -> List[Path]:
        """
        获取备用素材（当其他方法都失败时）

        Args:
            count: 需要的数量

        Returns:
            素材路径列表
        """
        # 从整个素材库中随机选择
        all_materials = list(self.library_path.rglob("*.jpg")) + \
                       list(self.library_path.rglob("*.png"))

        if all_materials:
            import random
            return random.sample(all_materials, min(count, len(all_materials)))

        return []

    def _load_library_index(self) -> Dict[str, List[str]]:
        """
        加载素材库索引

        Returns:
            索引字典
        """
        index_file = self.library_path / "index.json"

        if index_file.exists():
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"加载索引失败: {e}")

        return {}

    def _save_library_index(self) -> None:
        """保存素材库索引"""
        index_file = self.library_path / "index.json"

        try:
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(self.library_index, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"保存索引失败: {e}")

    def rebuild_library_index(self) -> None:
        """重建素材库索引"""
        self.logger.info("开始重建素材库索引...")

        new_index = {}

        # 扫描所有素材文件
        for image_path in self.library_path.rglob("*.jpg"):
            # 从路径和文件名提取关键词
            category = image_path.parent.name
            filename = image_path.stem

            keywords = [category]

            # 从文件名提取关键词
            name_parts = filename.replace('-', '_').split('_')
            keywords.extend([part.lower() for part in name_parts if len(part) > 2])

            # 添加到索引
            for keyword in keywords:
                if keyword not in new_index:
                    new_index[keyword] = []
                if str(image_path) not in new_index[keyword]:
                    new_index[keyword].append(str(image_path))

        self.library_index = new_index
        self._save_library_index()

        self.logger.info(f"索引重建完成，共索引 {len(new_index)} 个关键词")

    def get_library_stats(self) -> Dict[str, Any]:
        """
        获取素材库统计信息

        Returns:
            统计信息字典
        """
        total_images = len(list(self.library_path.rglob("*.jpg"))) + \
                      len(list(self.library_path.rglob("*.png")))

        categories = [d.name for d in self.library_path.iterdir() if d.is_dir()]

        stats = {
            'total_images': total_images,
            'total_keywords': len(self.library_index),
            'categories': len(categories),
            'category_names': categories,
            'library_path': str(self.library_path)
        }

        return stats

    def print_library_stats(self) -> None:
        """打印素材库统计信息"""
        stats = self.get_library_stats()

        print("\n" + "=" * 60)
        print("📚 素材库统计")
        print("=" * 60)
        print(f"总图片数: {stats['total_images']}")
        print(f"索引关键词数: {stats['total_keywords']}")
        print(f"分类数: {stats['categories']}")
        print(f"分类名称: {', '.join(stats['category_names'][:10])}")
        if len(stats['category_names']) > 10:
            print(f"          ... 还有 {len(stats['category_names']) - 10} 个分类")
        print(f"路径: {stats['library_path']}")
        print("=" * 60 + "\n")
