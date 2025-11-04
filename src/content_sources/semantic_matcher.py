"""
AI语义理解引擎
用于提取关键词和理解内容语义，智能匹配素材
"""

import os
import re
from typing import List, Dict, Any, Optional
import json
from pathlib import Path


class SemanticMatcher:
    """语义匹配器"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化语义匹配器

        Args:
            config: 配置字典
        """
        self.config = config
        self.use_ai = config.get('use_ai', False)
        self.api_key = config.get('api_key', os.getenv('OPENAI_API_KEY'))
        self.model = config.get('model', 'gpt-3.5-turbo')

        # 预定义的关键词映射
        self.keyword_mappings = {
            # 技术相关
            '编程': ['coding', 'programming', 'computer', 'technology'],
            '代码': ['code', 'programming', 'developer', 'software'],
            '开发': ['development', 'coding', 'software', 'programming'],
            'Python': ['python', 'programming', 'code', 'software'],
            '人工智能': ['artificial intelligence', 'AI', 'machine learning', 'technology'],
            '数据': ['data', 'analytics', 'statistics', 'information'],

            # 自然风景
            '山': ['mountain', 'nature', 'landscape', 'outdoor'],
            '海': ['ocean', 'sea', 'water', 'beach'],
            '森林': ['forest', 'tree', 'nature', 'woods'],
            '天空': ['sky', 'cloud', 'weather', 'atmosphere'],
            '日落': ['sunset', 'sky', 'evening', 'dusk'],
            '自然': ['nature', 'landscape', 'outdoor', 'scenery'],

            # 城市生活
            '城市': ['city', 'urban', 'building', 'street'],
            '建筑': ['architecture', 'building', 'structure', 'construction'],
            '街道': ['street', 'road', 'urban', 'city'],
            '交通': ['traffic', 'transportation', 'vehicle', 'road'],

            # 商业办公
            '办公': ['office', 'business', 'work', 'workplace'],
            '会议': ['meeting', 'conference', 'business', 'team'],
            '团队': ['team', 'collaboration', 'group', 'people'],
            '商业': ['business', 'corporate', 'professional', 'commerce'],

            # 教育学习
            '学习': ['learning', 'education', 'study', 'knowledge'],
            '教育': ['education', 'school', 'learning', 'teaching'],
            '书': ['book', 'reading', 'literature', 'library'],
            '学生': ['student', 'education', 'learning', 'school'],

            # 科技创新
            '科技': ['technology', 'innovation', 'digital', 'modern'],
            '创新': ['innovation', 'creativity', 'technology', 'modern'],
            '未来': ['future', 'futuristic', 'modern', 'technology'],
            '网络': ['network', 'internet', 'connection', 'digital'],

            # 抽象概念
            '成功': ['success', 'achievement', 'winning', 'growth'],
            '成长': ['growth', 'development', 'progress', 'improvement'],
            '创意': ['creativity', 'idea', 'innovation', 'design'],
            '思考': ['thinking', 'mind', 'idea', 'contemplation'],
        }

    def extract_keywords(self, text: str, max_keywords: int = 5) -> List[str]:
        """
        从文本中提取关键词

        Args:
            text: 输入文本
            max_keywords: 最大关键词数

        Returns:
            关键词列表
        """
        if self.use_ai and self.api_key:
            return self._extract_keywords_with_ai(text, max_keywords)
        else:
            return self._extract_keywords_simple(text, max_keywords)

    def _extract_keywords_simple(self, text: str, max_keywords: int) -> List[str]:
        """
        简单的关键词提取（基于规则）

        Args:
            text: 输入文本
            max_keywords: 最大关键词数

        Returns:
            关键词列表
        """
        keywords = []

        # 检查预定义的关键词
        for chinese_word, english_words in self.keyword_mappings.items():
            if chinese_word in text:
                keywords.extend(english_words[:2])  # 取前2个相关词

        # 去重
        keywords = list(dict.fromkeys(keywords))

        # 如果没有匹配，返回一些通用关键词
        if not keywords:
            keywords = ['abstract', 'background', 'design', 'modern']

        return keywords[:max_keywords]

    def _extract_keywords_with_ai(self, text: str, max_keywords: int) -> List[str]:
        """
        使用AI提取关键词

        Args:
            text: 输入文本
            max_keywords: 最大关键词数

        Returns:
            关键词列表
        """
        try:
            import openai
            openai.api_key = self.api_key

            prompt = f"""
分析以下视频脚本，提取{max_keywords}个最相关的英文关键词，用于搜索配图。
关键词应该是具体的、视觉化的名词，适合用来搜索图片。

脚本内容：
{text}

请直接返回{max_keywords}个英文关键词，用逗号分隔，不需要其他说明。
"""

            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的视频内容分析助手。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.7
            )

            keywords_text = response.choices[0].message.content.strip()
            keywords = [kw.strip() for kw in keywords_text.split(',')]

            return keywords[:max_keywords]

        except Exception as e:
            print(f"AI关键词提取失败，使用简单模式: {e}")
            return self._extract_keywords_simple(text, max_keywords)

    def analyze_script_segments(self, segments: List[Any]) -> List[Dict[str, Any]]:
        """
        分析脚本片段，生成素材需求

        Args:
            segments: 脚本片段列表

        Returns:
            素材需求列表
        """
        material_needs = []

        for i, segment in enumerate(segments):
            # 提取关键词
            keywords = self.extract_keywords(segment.text, max_keywords=3)

            # 根据场景类型调整关键词
            if hasattr(segment, 'scene_type') and segment.scene_type != 'default':
                scene_keywords = self._get_scene_keywords(segment.scene_type)
                keywords = scene_keywords + keywords

            need = {
                'segment_index': i,
                'text': segment.text,
                'scene_type': getattr(segment, 'scene_type', 'default'),
                'keywords': keywords,
                'primary_keyword': keywords[0] if keywords else 'abstract',
                'duration': getattr(segment, 'duration', 5.0)
            }

            material_needs.append(need)

        return material_needs

    def _get_scene_keywords(self, scene_type: str) -> List[str]:
        """
        根据场景类型获取关键词

        Args:
            scene_type: 场景类型

        Returns:
            关键词列表
        """
        scene_mapping = {
            'intro': ['beginning', 'start', 'introduction', 'welcome'],
            'main': ['content', 'information', 'detail', 'focus'],
            'demo': ['demonstration', 'example', 'practice', 'action'],
            'conclusion': ['end', 'summary', 'conclusion', 'finish'],
            'tech': ['technology', 'digital', 'modern', 'innovation'],
            'nature': ['nature', 'landscape', 'outdoor', 'scenery'],
            'business': ['business', 'professional', 'corporate', 'office'],
            'education': ['education', 'learning', 'study', 'knowledge'],
        }

        return scene_mapping.get(scene_type, [])

    def match_local_materials(
        self,
        keywords: List[str],
        local_materials: List[Any],
        count: int = 1
    ) -> List[Any]:
        """
        匹配本地素材

        Args:
            keywords: 关键词列表
            local_materials: 本地素材列表
            count: 需要的数量

        Returns:
            匹配的素材列表
        """
        if not local_materials:
            return []

        # 计算每个素材的匹配分数
        scored_materials = []

        for material in local_materials:
            score = 0

            # 检查标签匹配
            if hasattr(material, 'tags'):
                for keyword in keywords:
                    if keyword.lower() in [tag.lower() for tag in material.tags]:
                        score += 10

            # 检查文件名匹配
            filename = material.path.stem.lower()
            for keyword in keywords:
                if keyword.lower() in filename:
                    score += 5

            if score > 0:
                scored_materials.append((score, material))

        # 按分数排序
        scored_materials.sort(reverse=True, key=lambda x: x[0])

        # 返回最匹配的素材
        return [m for s, m in scored_materials[:count]]

    def generate_search_query(self, keywords: List[str]) -> str:
        """
        生成搜索查询字符串

        Args:
            keywords: 关键词列表

        Returns:
            搜索查询字符串
        """
        # 使用主要关键词
        if keywords:
            return keywords[0]
        else:
            return 'abstract background'

    def save_material_mappings(self, mappings: List[Dict[str, Any]], output_file: str) -> None:
        """
        保存素材映射关系

        Args:
            mappings: 映射关系列表
            output_file: 输出文件路径
        """
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(mappings, f, ensure_ascii=False, indent=2)

    def load_material_mappings(self, input_file: str) -> List[Dict[str, Any]]:
        """
        加载素材映射关系

        Args:
            input_file: 输入文件路径

        Returns:
            映射关系列表
        """
        input_path = Path(input_file)

        if not input_path.exists():
            return []

        with open(input_path, 'r', encoding='utf-8') as f:
            return json.load(f)
