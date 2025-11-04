"""
内容源模块
提供文本、素材库、AI生成等多种内容来源
"""

from .text_source import TextSource
from .material_source import MaterialSource
from .auto_material_manager import AutoMaterialManager
from .semantic_matcher import SemanticMatcher
from .image_api import MultiSourceImageAPI

__all__ = [
    'TextSource',
    'MaterialSource',
    'AutoMaterialManager',
    'SemanticMatcher',
    'MultiSourceImageAPI'
]
