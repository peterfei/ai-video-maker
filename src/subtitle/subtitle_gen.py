"""
字幕生成器
根据文本和时间信息生成字幕
"""

from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pysrt
from datetime import timedelta


class SubtitleSegment:
    """字幕片段类"""

    def __init__(
        self,
        text: str,
        start_time: float,
        end_time: float,
        index: int = 0
    ):
        """
        初始化字幕片段

        Args:
            text: 字幕文本
            start_time: 开始时间（秒）
            end_time: 结束时间（秒）
            index: 索引
        """
        self.text = text
        self.start_time = start_time
        self.end_time = end_time
        self.index = index

    @property
    def duration(self) -> float:
        """获取字幕持续时间"""
        return self.end_time - self.start_time

    def __repr__(self):
        return f"SubtitleSegment({self.start_time:.2f}s-{self.end_time:.2f}s: '{self.text[:20]}...')"


class SubtitleGenerator:
    """字幕生成器类"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化字幕生成器

        Args:
            config: 配置字典
        """
        self.config = config
        self.duration_per_char = config.get('duration_per_char', 0.3)
        self.max_chars_per_line = config.get('max_chars_per_line', 25)

    def generate_from_text(
        self,
        text: str,
        audio_duration: Optional[float] = None
    ) -> List[SubtitleSegment]:
        """
        从文本生成字幕

        Args:
            text: 文本内容
            audio_duration: 音频总时长（秒）

        Returns:
            SubtitleSegment列表
        """
        # 分句
        sentences = self._split_into_sentences(text)

        # 计算每句的时长
        segments = []
        current_time = 0.0

        for i, sentence in enumerate(sentences):
            # 计算字幕持续时间
            char_count = len(sentence)
            duration = char_count * self.duration_per_char

            # 如果提供了总时长，按比例调整
            if audio_duration and i == len(sentences) - 1:
                # 最后一句，确保不超过总时长
                duration = min(duration, audio_duration - current_time)

            segment = SubtitleSegment(
                text=sentence,
                start_time=current_time,
                end_time=current_time + duration,
                index=i + 1
            )

            segments.append(segment)
            current_time += duration

        return segments

    def generate_from_segments(
        self,
        script_segments: List[Any],
        audio_durations: List[float]
    ) -> List[SubtitleSegment]:
        """
        从脚本片段和音频时长生成字幕

        Args:
            script_segments: 脚本片段列表
            audio_durations: 对应的音频时长列表

        Returns:
            SubtitleSegment列表
        """
        if len(script_segments) != len(audio_durations):
            raise ValueError("脚本片段和音频时长数量不匹配")

        subtitle_segments = []
        current_time = 0.0

        for i, (script_seg, duration) in enumerate(zip(script_segments, audio_durations)):
            # 将长文本分割成多行
            lines = self._split_text_into_lines(script_seg.text)

            # 为每行分配时间
            line_duration = duration / len(lines)

            for j, line in enumerate(lines):
                segment = SubtitleSegment(
                    text=line,
                    start_time=current_time,
                    end_time=current_time + line_duration,
                    index=len(subtitle_segments) + 1
                )
                subtitle_segments.append(segment)
                current_time += line_duration

        return subtitle_segments

    def _split_into_sentences(self, text: str) -> List[str]:
        """
        将文本分割成句子

        Args:
            text: 文本

        Returns:
            句子列表
        """
        import re

        # 按句号、问号、感叹号分割
        sentences = re.split(r'[。！？!?]', text)

        # 过滤空句子
        sentences = [s.strip() for s in sentences if s.strip()]

        # 分割过长的句子
        result = []
        for sentence in sentences:
            if len(sentence) > self.max_chars_per_line:
                # 按逗号或顿号分割
                sub_sentences = re.split(r'[，、,]', sentence)
                result.extend([s.strip() for s in sub_sentences if s.strip()])
            else:
                result.append(sentence)

        return result

    def _split_text_into_lines(self, text: str) -> List[str]:
        """
        将文本分割成多行，每行不超过最大字符数

        Args:
            text: 文本

        Returns:
            文本行列表
        """
        if len(text) <= self.max_chars_per_line:
            return [text]

        lines = []
        words = text.split()
        current_line = ""

        for word in words:
            if len(current_line) + len(word) + 1 <= self.max_chars_per_line:
                current_line += word + " "
            else:
                if current_line:
                    lines.append(current_line.strip())
                current_line = word + " "

        if current_line:
            lines.append(current_line.strip())

        return lines

    def save_to_srt(
        self,
        segments: List[SubtitleSegment],
        output_path: str
    ) -> Path:
        """
        保存字幕为SRT格式

        Args:
            segments: SubtitleSegment列表
            output_path: 输出路径

        Returns:
            输出文件路径
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        subs = pysrt.SubRipFile()

        for segment in segments:
            start = self._seconds_to_timedelta(segment.start_time)
            end = self._seconds_to_timedelta(segment.end_time)

            item = pysrt.SubRipItem(
                index=segment.index,
                start=start,
                end=end,
                text=segment.text
            )

            subs.append(item)

        subs.save(str(output_path), encoding='utf-8')

        return output_path

    def load_from_srt(self, srt_path: str) -> List[SubtitleSegment]:
        """
        从SRT文件加载字幕

        Args:
            srt_path: SRT文件路径

        Returns:
            SubtitleSegment列表
        """
        subs = pysrt.open(srt_path, encoding='utf-8')

        segments = []

        for item in subs:
            segment = SubtitleSegment(
                text=item.text,
                start_time=self._timedelta_to_seconds(item.start),
                end_time=self._timedelta_to_seconds(item.end),
                index=item.index
            )
            segments.append(segment)

        return segments

    def _seconds_to_timedelta(self, seconds: float) -> pysrt.SubRipTime:
        """
        将秒数转换为SubRipTime

        Args:
            seconds: 秒数

        Returns:
            SubRipTime对象
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)

        return pysrt.SubRipTime(hours=hours, minutes=minutes, seconds=secs, milliseconds=millis)

    def _timedelta_to_seconds(self, srt_time: pysrt.SubRipTime) -> float:
        """
        将SubRipTime转换为秒数

        Args:
            srt_time: SubRipTime对象

        Returns:
            秒数
        """
        return (
            srt_time.hours * 3600 +
            srt_time.minutes * 60 +
            srt_time.seconds +
            srt_time.milliseconds / 1000.0
        )

    def adjust_timing(
        self,
        segments: List[SubtitleSegment],
        time_offset: float
    ) -> List[SubtitleSegment]:
        """
        调整字幕时间

        Args:
            segments: SubtitleSegment列表
            time_offset: 时间偏移（秒）

        Returns:
            调整后的SubtitleSegment列表
        """
        adjusted = []

        for seg in segments:
            new_seg = SubtitleSegment(
                text=seg.text,
                start_time=seg.start_time + time_offset,
                end_time=seg.end_time + time_offset,
                index=seg.index
            )
            adjusted.append(new_seg)

        return adjusted

    def merge_segments(
        self,
        segments: List[SubtitleSegment],
        max_duration: float = 5.0
    ) -> List[SubtitleSegment]:
        """
        合并短字幕片段

        Args:
            segments: SubtitleSegment列表
            max_duration: 最大合并时长

        Returns:
            合并后的SubtitleSegment列表
        """
        if not segments:
            return []

        merged = []
        current_text = segments[0].text
        current_start = segments[0].start_time
        current_end = segments[0].end_time

        for i in range(1, len(segments)):
            seg = segments[i]
            potential_duration = seg.end_time - current_start

            if potential_duration <= max_duration:
                # 合并
                current_text += " " + seg.text
                current_end = seg.end_time
            else:
                # 保存当前片段，开始新片段
                merged.append(SubtitleSegment(
                    text=current_text,
                    start_time=current_start,
                    end_time=current_end,
                    index=len(merged) + 1
                ))
                current_text = seg.text
                current_start = seg.start_time
                current_end = seg.end_time

        # 添加最后一个片段
        merged.append(SubtitleSegment(
            text=current_text,
            start_time=current_start,
            end_time=current_end,
            index=len(merged) + 1
        ))

        return merged
