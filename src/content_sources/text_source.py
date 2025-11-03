"""
文本内容源处理器
负责处理文本脚本，将其解析为视频生成所需的结构化数据
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import re


class ScriptSegment:
    """脚本片段类"""

    def __init__(
        self,
        text: str,
        duration: Optional[float] = None,
        scene_type: str = "default",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        初始化脚本片段

        Args:
            text: 文本内容
            duration: 持续时间（秒）
            scene_type: 场景类型
            metadata: 元数据
        """
        self.text = text
        self.duration = duration
        self.scene_type = scene_type
        self.metadata = metadata or {}

    def __repr__(self):
        return f"ScriptSegment(text='{self.text[:30]}...', duration={self.duration})"


class TextSource:
    """文本内容源类"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化文本源

        Args:
            config: 配置字典
        """
        self.config = config
        self.encoding = config.get('encoding', 'utf-8')
        self.split_by_paragraph = config.get('split_by_paragraph', True)

    def load_script(self, file_path: str) -> List[ScriptSegment]:
        """
        加载脚本文件

        Args:
            file_path: 脚本文件路径

        Returns:
            ScriptSegment列表
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"脚本文件不存在: {file_path}")

        with open(file_path, 'r', encoding=self.encoding) as f:
            content = f.read()

        return self.parse_script(content)

    def parse_script(self, content: str) -> List[ScriptSegment]:
        """
        解析脚本内容

        支持多种格式：
        1. 纯文本
        2. 带时间标记的文本 [00:05] 这是文本
        3. 带场景标记的文本 #scene:intro# 这是介绍

        Args:
            content: 脚本内容

        Returns:
            ScriptSegment列表
        """
        segments = []

        if self.split_by_paragraph:
            # 按段落分割
            paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        else:
            # 按行分割
            paragraphs = [line.strip() for line in content.split('\n') if line.strip()]

        for para in paragraphs:
            segment = self._parse_segment(para)
            if segment:
                segments.append(segment)

        return segments

    def _parse_segment(self, text: str) -> Optional[ScriptSegment]:
        """
        解析单个文本片段

        Args:
            text: 文本内容

        Returns:
            ScriptSegment对象
        """
        if not text.strip():
            return None

        duration = None
        scene_type = "default"
        metadata = {}

        # 解析时间标记 [00:05]
        time_match = re.match(r'\[(\d{2}):(\d{2})\]\s*(.*)', text)
        if time_match:
            minutes, seconds, text = time_match.groups()
            duration = int(minutes) * 60 + int(seconds)

        # 解析场景标记 #scene:intro#
        scene_match = re.match(r'#scene:(\w+)#\s*(.*)', text)
        if scene_match:
            scene_type, text = scene_match.groups()

        # 解析元数据 @key=value@
        meta_matches = re.findall(r'@(\w+)=([^@]+)@', text)
        for key, value in meta_matches:
            metadata[key] = value
            text = text.replace(f'@{key}={value}@', '').strip()

        return ScriptSegment(
            text=text.strip(),
            duration=duration,
            scene_type=scene_type,
            metadata=metadata
        )

    def create_from_text(self, text: str) -> List[ScriptSegment]:
        """
        从文本字符串创建脚本片段

        Args:
            text: 文本内容

        Returns:
            ScriptSegment列表
        """
        return self.parse_script(text)

    def save_script(self, segments: List[ScriptSegment], output_path: str) -> None:
        """
        保存脚本到文件

        Args:
            segments: ScriptSegment列表
            output_path: 输出路径
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding=self.encoding) as f:
            for segment in segments:
                line = segment.text

                # 添加时间标记
                if segment.duration:
                    minutes = int(segment.duration // 60)
                    seconds = int(segment.duration % 60)
                    line = f"[{minutes:02d}:{seconds:02d}] {line}"

                # 添加场景标记
                if segment.scene_type != "default":
                    line = f"#scene:{segment.scene_type}# {line}"

                f.write(line + '\n\n')

    def get_total_text(self, segments: List[ScriptSegment]) -> str:
        """
        获取所有片段的完整文本

        Args:
            segments: ScriptSegment列表

        Returns:
            完整文本
        """
        return ' '.join(seg.text for seg in segments)

    def estimate_duration(self, segments: List[ScriptSegment], chars_per_second: float = 3.0) -> float:
        """
        估算总时长

        Args:
            segments: ScriptSegment列表
            chars_per_second: 每秒字符数

        Returns:
            估算的总时长（秒）
        """
        total_duration = 0.0

        for segment in segments:
            if segment.duration:
                total_duration += segment.duration
            else:
                # 根据文本长度估算
                char_count = len(segment.text)
                total_duration += char_count / chars_per_second

        return total_duration
