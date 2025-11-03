"""
素材库管理器
负责管理和选择视频素材（图片、视频片段等）
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import random
from PIL import Image


class Material:
    """素材类"""

    def __init__(
        self,
        path: Path,
        material_type: str,
        duration: Optional[float] = None,
        tags: Optional[List[str]] = None
    ):
        """
        初始化素材

        Args:
            path: 素材文件路径
            material_type: 素材类型 (image/video)
            duration: 持续时间（视频）
            tags: 标签列表
        """
        self.path = path
        self.material_type = material_type
        self.duration = duration
        self.tags = tags or []
        self.metadata = {}

    def __repr__(self):
        return f"Material(path='{self.path.name}', type={self.material_type})"


class MaterialSource:
    """素材库管理类"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化素材库

        Args:
            config: 配置字典
        """
        self.config = config
        self.image_formats = config.get('image_formats', ['.jpg', '.jpeg', '.png', '.webp'])
        self.video_formats = config.get('video_formats', ['.mp4', '.mov', '.avi'])
        self.auto_resize = config.get('auto_resize', True)
        self.materials: List[Material] = []

    def load_materials(self, directory: str) -> List[Material]:
        """
        从目录加载素材

        Args:
            directory: 素材目录路径

        Returns:
            Material列表
        """
        directory = Path(directory)

        if not directory.exists():
            raise FileNotFoundError(f"素材目录不存在: {directory}")

        materials = []

        # 加载图片
        for ext in self.image_formats:
            for file_path in directory.glob(f"*{ext}"):
                material = Material(
                    path=file_path,
                    material_type='image',
                    tags=self._extract_tags_from_filename(file_path.stem)
                )
                materials.append(material)

        # 加载视频
        for ext in self.video_formats:
            for file_path in directory.glob(f"**/*{ext}"):
                material = Material(
                    path=file_path,
                    material_type='video',
                    tags=self._extract_tags_from_filename(file_path.stem)
                )
                materials.append(material)

        self.materials = materials
        return materials

    def _extract_tags_from_filename(self, filename: str) -> List[str]:
        """
        从文件名提取标签

        文件名格式示例: "nature_mountain_sunset.jpg" -> ["nature", "mountain", "sunset"]

        Args:
            filename: 文件名（不含扩展名）

        Returns:
            标签列表
        """
        # 分割下划线和连字符
        tags = filename.replace('-', '_').split('_')
        # 转换为小写并去除空字符串
        tags = [tag.lower() for tag in tags if tag]
        return tags

    def get_materials_by_type(self, material_type: str) -> List[Material]:
        """
        按类型获取素材

        Args:
            material_type: 素材类型 (image/video)

        Returns:
            Material列表
        """
        return [m for m in self.materials if m.material_type == material_type]

    def get_materials_by_tags(self, tags: List[str], match_all: bool = False) -> List[Material]:
        """
        按标签筛选素材

        Args:
            tags: 标签列表
            match_all: 是否需要匹配所有标签

        Returns:
            Material列表
        """
        matched = []

        for material in self.materials:
            if match_all:
                # 匹配所有标签
                if all(tag in material.tags for tag in tags):
                    matched.append(material)
            else:
                # 匹配任意标签
                if any(tag in material.tags for tag in tags):
                    matched.append(material)

        return matched

    def select_materials(
        self,
        count: int,
        material_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        random_selection: bool = True
    ) -> List[Material]:
        """
        选择素材

        Args:
            count: 需要的素材数量
            material_type: 素材类型过滤
            tags: 标签过滤
            random_selection: 是否随机选择

        Returns:
            Material列表
        """
        # 筛选素材
        candidates = self.materials

        if material_type:
            candidates = [m for m in candidates if m.material_type == material_type]

        if tags:
            candidates = self.get_materials_by_tags(tags)

        if not candidates:
            return []

        # 选择素材
        if random_selection:
            # 如果数量不足，允许重复
            if len(candidates) < count:
                return random.choices(candidates, k=count)
            else:
                return random.sample(candidates, min(count, len(candidates)))
        else:
            return candidates[:count]

    def resize_image(
        self,
        image_path: Path,
        target_size: tuple,
        maintain_aspect: bool = True
    ) -> Image.Image:
        """
        调整图片大小

        Args:
            image_path: 图片路径
            target_size: 目标尺寸 (width, height)
            maintain_aspect: 是否保持宽高比

        Returns:
            PIL Image对象
        """
        img = Image.open(image_path)

        if maintain_aspect:
            # 保持宽高比，填充空白
            img.thumbnail(target_size, Image.Resampling.LANCZOS)

            # 创建目标尺寸的背景
            background = Image.new('RGB', target_size, (0, 0, 0))

            # 计算居中位置
            offset = (
                (target_size[0] - img.size[0]) // 2,
                (target_size[1] - img.size[1]) // 2
            )

            background.paste(img, offset)
            return background
        else:
            # 直接缩放
            return img.resize(target_size, Image.Resampling.LANCZOS)

    def get_material_info(self, material: Material) -> Dict[str, Any]:
        """
        获取素材信息

        Args:
            material: Material对象

        Returns:
            素材信息字典
        """
        info = {
            'path': str(material.path),
            'type': material.material_type,
            'tags': material.tags,
            'size': material.path.stat().st_size,
        }

        if material.material_type == 'image':
            try:
                img = Image.open(material.path)
                info['dimensions'] = img.size
                info['format'] = img.format
            except Exception as e:
                info['error'] = str(e)

        return info

    def create_slideshow_sequence(
        self,
        count: int,
        tags: Optional[List[str]] = None
    ) -> List[Material]:
        """
        创建幻灯片序列

        Args:
            count: 图片数量
            tags: 标签过滤

        Returns:
            Material列表
        """
        return self.select_materials(
            count=count,
            material_type='image',
            tags=tags,
            random_selection=True
        )
