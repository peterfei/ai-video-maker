"""
AI内容生成器 (可选模块)
使用AI生成视频脚本和内容建议
"""

from typing import List, Dict, Any, Optional
import os


class AISource:
    """AI内容生成类"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化AI源

        Args:
            config: 配置字典
        """
        self.config = config
        self.enabled = config.get('enabled', False)
        self.provider = config.get('provider', 'openai')
        self.model = config.get('model', 'gpt-4')
        self.api_key = config.get('api_key', os.getenv('OPENAI_API_KEY'))

        if self.enabled and not self.api_key:
            raise ValueError("AI功能已启用，但未提供API密钥")

    def generate_script(
        self,
        topic: str,
        target_duration: int = 60,
        style: str = "educational"
    ) -> str:
        """
        生成视频脚本

        Args:
            topic: 主题
            target_duration: 目标时长（秒）
            style: 风格 (educational, entertaining, professional)

        Returns:
            生成的脚本文本
        """
        if not self.enabled:
            raise RuntimeError("AI功能未启用")

        prompt = self._build_script_prompt(topic, target_duration, style)

        # 这里应该调用实际的AI API
        # 示例实现
        if self.provider == 'openai':
            return self._call_openai(prompt)
        else:
            raise NotImplementedError(f"不支持的AI提供商: {self.provider}")

    def _build_script_prompt(self, topic: str, duration: int, style: str) -> str:
        """
        构建脚本生成提示词

        Args:
            topic: 主题
            duration: 时长
            style: 风格

        Returns:
            提示词
        """
        word_count = duration * 2  # 假设每秒2个单词

        prompt = f"""
请为以下主题生成一个{duration}秒的视频解说脚本：

主题: {topic}
风格: {style}
字数: 约{word_count}字
要求:
- 内容清晰、结构完整
- 适合语音播报
- 包含引入、主体和总结
- 通俗易懂

请直接返回脚本内容，不需要其他说明。
"""
        return prompt

    def _call_openai(self, prompt: str) -> str:
        """
        调用OpenAI API

        Args:
            prompt: 提示词

        Returns:
            生成的文本
        """
        try:
            import openai
            openai.api_key = self.api_key

            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的视频脚本撰写者。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.7
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            raise RuntimeError(f"调用OpenAI API失败: {str(e)}")

    def suggest_keywords(self, topic: str, count: int = 5) -> List[str]:
        """
        为主题生成关键词建议

        Args:
            topic: 主题
            count: 关键词数量

        Returns:
            关键词列表
        """
        if not self.enabled:
            return []

        prompt = f"为主题'{topic}'生成{count}个相关的关键词，用于搜索视频素材。只返回关键词列表，用逗号分隔。"

        try:
            response = self._call_openai(prompt)
            keywords = [kw.strip() for kw in response.split(',')]
            return keywords[:count]
        except Exception:
            return []

    def enhance_script(self, original_script: str) -> str:
        """
        优化现有脚本

        Args:
            original_script: 原始脚本

        Returns:
            优化后的脚本
        """
        if not self.enabled:
            return original_script

        prompt = f"""
请优化以下视频脚本，使其更加流畅、专业和吸引人：

{original_script}

优化要求：
- 保持原意不变
- 改善语言表达
- 增强逻辑性
- 适合语音播报

请直接返回优化后的脚本。
"""

        try:
            return self._call_openai(prompt)
        except Exception:
            return original_script
