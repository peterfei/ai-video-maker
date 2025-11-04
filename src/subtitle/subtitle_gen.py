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
            audio_duration: 音频总时长（秒），如果提供则按实际时长精确同步

        Returns:
            SubtitleSegment列表
        """
        # 分句
        sentences = self._split_into_sentences(text)

        if not sentences:
            return []

        # 计算每句的时长
        segments = []
        current_time = 0.0

        if audio_duration is not None:
            # 使用精确音频时长进行同步
            # 按字符数比例分配时间
            total_chars = sum(len(sentence) for sentence in sentences)

            if total_chars == 0:
                return []

            for i, sentence in enumerate(sentences):
                char_count = len(sentence)
                # 按字符数比例分配时间
                duration = (char_count / total_chars) * audio_duration

                # 确保最后一段精确到达audio_duration
                if i == len(sentences) - 1:
                    duration = audio_duration - current_time

                segment = SubtitleSegment(
                    text=sentence,
                    start_time=current_time,
                    end_time=current_time + duration,
                    index=i + 1
                )

                segments.append(segment)
                current_time += duration
        else:
            # 向后兼容：使用字符时长估算
            import logging
            logging.warning("未提供audio_duration参数，使用默认时长估算模式")

            for i, sentence in enumerate(sentences):
                # 计算字幕持续时间
                char_count = len(sentence)
                duration = char_count * self.duration_per_char

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
        sentences: List[str],
        audio_durations: List[float]
    ) -> List[SubtitleSegment]:
        """
        从句子列表和对应的音频时长生成字幕

        Args:
            sentences: 句子列表
            audio_durations: 对应的音频时长列表（每个句子的实际TTS时长）

        Returns:
            SubtitleSegment列表

        Raises:
            ValueError: 当句子数量与时长数量不匹配时
        """
        if len(sentences) != len(audio_durations):
            raise ValueError(
                f"句子数量({len(sentences)})与音频时长数量({len(audio_durations)})不匹配"
            )

        import logging
        logger = logging.getLogger(__name__)

        subtitle_segments = []
        current_time = 0.0

        for i, (sentence, duration) in enumerate(zip(sentences, audio_durations)):
            # 验证时长
            if duration <= 0:
                logger.warning(f"句子 {i} 的音频时长为 {duration}，使用最小时长 0.1秒")
                duration = max(0.1, duration)

            # 创建字幕片段（每个句子一个字幕）
            segment = SubtitleSegment(
                text=sentence.strip(),
                start_time=current_time,
                end_time=current_time + duration,
                index=i + 1
            )

            subtitle_segments.append(segment)
            current_time += duration

            logger.debug(
                f"字幕 {i+1}: {sentence[:30]}... "
                f"[{segment.start_time:.2f}s - {segment.end_time:.2f}s] "
                f"(时长: {duration:.2f}s)"
            )

        logger.info(f"生成 {len(subtitle_segments)} 个字幕片段，总时长 {current_time:.2f}秒")

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
