"""
STT 字幕生成器

将 STT (语音转文字) 结果转换为标准字幕格式，支持时间戳对齐和文本优化。
"""

import re
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from .subtitle_gen import SubtitleGenerator, SubtitleSegment

# Import STT models - using try/except for optional dependency
try:
    from ..audio.models import STTResult, STTSegment
except ImportError:
    # Define dummy classes if audio models not available
    class STTSegment:
        def __init__(self, text, start_time, end_time, confidence):
            self.text = text
            self.start_time = start_time
            self.end_time = end_time
            self.confidence = confidence
            self.duration = end_time - start_time

    class STTResult:
        def __init__(self, segments, language, duration, model_used):
            self.segments = segments
            self.language = language
            self.duration = duration
            self.model_used = model_used


logger = logging.getLogger(__name__)


class STTSubtitleGenerator:
    """
    STT 字幕生成器

    将语音转文字结果转换为适合视频字幕的标准格式。
    支持文本分段、时间戳对齐和字幕质量优化。
    """

    def __init__(self, config: Dict[str, Any]):
        """
        初始化 STT 字幕生成器

        Args:
            config: 字幕配置字典
        """
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # 从配置获取参数
        self.max_chars_per_line = config.get('max_chars_per_line', 25)
        self.stt_segment_merge_threshold = config.get('stt_segment_merge_threshold', 1.5)
        self.stt_min_segment_length = config.get('stt_min_segment_length', 0.5)

        # 创建基础字幕生成器用于文本处理
        self.base_generator = SubtitleGenerator(config)

        self.logger.debug("STT 字幕生成器初始化完成")

    def generate_from_stt(self, stt_result: STTResult) -> List[SubtitleSegment]:
        """
        从 STT 结果生成字幕

        Args:
            stt_result: STT 识别结果

        Returns:
            List[SubtitleSegment]: 字幕片段列表
        """
        if not stt_result.segments:
            self.logger.warning("STT 结果为空，返回空字幕列表")
            return []

        self.logger.info(
            f"开始从 STT 结果生成字幕: {len(stt_result.segments)} 个片段，"
            ".2f"
        )

        # 预处理 STT 片段
        processed_segments = self._preprocess_stt_segments(stt_result.segments)

        # 合并短片段
        merged_segments = self._merge_short_segments(processed_segments)

        # 文本后处理
        cleaned_segments = self._post_process_text(merged_segments)

        # 转换为字幕片段
        subtitle_segments = self._convert_to_subtitle_segments(cleaned_segments)

        # 最终质量检查
        final_segments = self._quality_check(subtitle_segments)

        self.logger.info(f"字幕生成完成: {len(final_segments)} 个字幕片段")

        return final_segments

    def _preprocess_stt_segments(self, stt_segments: List[STTSegment]) -> List[STTSegment]:
        """
        预处理 STT 片段

        Args:
            stt_segments: 原始 STT 片段

        Returns:
            List[STTSegment]: 预处理后的片段
        """
        processed = []

        for segment in stt_segments:
            # 跳过置信度过低的片段
            min_confidence = self.config.get('min_confidence_threshold', 0.3)
            if segment.confidence < min_confidence:
                self.logger.debug(f"跳过低置信度片段: {segment.confidence:.2f} < {min_confidence}")
                continue

            # 跳过时长过短的片段
            if segment.duration < self.stt_min_segment_length:
                self.logger.debug(f"跳过过短片段: {segment.duration:.2f}s < {self.stt_min_segment_length}s")
                continue

            # 清理文本
            cleaned_text = self._clean_segment_text(segment.text)
            if not cleaned_text.strip():
                continue

            # 创建新片段
            processed_segment = STTSegment(
                text=cleaned_text,
                start_time=segment.start_time,
                end_time=segment.end_time,
                confidence=segment.confidence
            )

            processed.append(processed_segment)

        self.logger.debug(f"预处理完成: {len(processed)}/{len(stt_segments)} 个片段保留")
        return processed

    def _clean_segment_text(self, text: str) -> str:
        """
        清理片段文本

        Args:
            text: 原始文本

        Returns:
            str: 清理后的文本
        """
        if not text:
            return ""

        # 移除多余空格
        text = re.sub(r'\s+', ' ', text.strip())

        # 中文标点符号规范化
        text = self._normalize_chinese_punctuation(text)

        # 移除首尾标点（如果需要）
        text = self._trim_punctuation(text)

        return text

    def _normalize_chinese_punctuation(self, text: str) -> str:
        """
        规范化中文标点符号

        Args:
            text: 文本

        Returns:
            str: 规范化后的文本
        """
        # 英文标点转中文标点
        punctuation_map = {
            ',': '，',
            '.': '。',
            '?': '？',
            '!': '！',
            ':': '：',
            ';': '；',
            '(': '（',
            ')': '）',
            '[': '【',
            ']': '】',
            '"': '"',  # 保持英文引号
            "'": "'",  # 保持英文单引号
        }

        for en, zh in punctuation_map.items():
            text = text.replace(en, zh)

        return text

    def _trim_punctuation(self, text: str) -> str:
        """
        移除首尾标点符号（可选）

        Args:
            text: 文本

        Returns:
            str: 处理后的文本
        """
        # 可以配置是否移除首尾标点
        if self.config.get('trim_punctuation', False):
            text = text.strip('，。？！：；""''（）【】')

        return text

    def _merge_short_segments(
        self,
        segments: List[STTSegment],
        max_gap: Optional[float] = None
    ) -> List[STTSegment]:
        """
        合并短片段

        Args:
            segments: STT 片段列表
            max_gap: 最大合并间隔（秒），如果为 None 则使用配置值

        Returns:
            List[STTSegment]: 合并后的片段
        """
        if not segments:
            return []

        if max_gap is None:
            max_gap = self.stt_segment_merge_threshold

        merged = []
        current = segments[0]

        for next_seg in segments[1:]:
            # 检查是否可以合并
            time_gap = next_seg.start_time - current.end_time
            should_merge = (
                time_gap <= max_gap and
                current.duration + next_seg.duration <= self.stt_segment_merge_threshold * 2
            )

            if should_merge:
                # 合并片段
                current = STTSegment(
                    text=current.text + " " + next_seg.text,
                    start_time=current.start_time,
                    end_time=next_seg.end_time,
                    confidence=min(current.confidence, next_seg.confidence)
                )
            else:
                # 保存当前片段，开始新片段
                merged.append(current)
                current = next_seg

        merged.append(current)

        self.logger.debug(f"片段合并完成: {len(merged)}/{len(segments)} 个片段")
        return merged

    def _post_process_text(self, segments: List[STTSegment]) -> List[STTSegment]:
        """
        文本后处理

        Args:
            segments: STT 片段列表

        Returns:
            List[STTSegment]: 处理后的片段
        """
        processed = []

        for segment in segments:
            # 分行处理
            lines = self._split_text_into_lines(segment.text)

            if len(lines) == 1:
                # 单行，直接使用
                processed.append(segment)
            else:
                # 多行，分割为多个片段
                line_segments = self._split_segment_by_lines(segment, lines)
                processed.extend(line_segments)

        return processed

    def _split_text_into_lines(self, text: str) -> List[str]:
        """
        将文本分割成多行

        Args:
            text: 文本

        Returns:
            List[str]: 文本行列表
        """
        return self.base_generator._split_text_into_lines(text)

    def _split_segment_by_lines(
        self,
        segment: STTSegment,
        lines: List[str]
    ) -> List[STTSegment]:
        """
        按行分割片段

        Args:
            segment: 原始片段
            lines: 文本行列表

        Returns:
            List[STTSegment]: 分割后的片段列表
        """
        if len(lines) <= 1:
            return [segment]

        # 按字符数比例分配时间
        total_chars = sum(len(line) for line in lines)
        if total_chars == 0:
            return [segment]

        split_segments = []
        current_time = segment.start_time
        duration_per_char = segment.duration / total_chars

        for line in lines:
            line_duration = len(line) * duration_per_char
            line_segment = STTSegment(
                text=line,
                start_time=current_time,
                end_time=current_time + line_duration,
                confidence=segment.confidence
            )
            split_segments.append(line_segment)
            current_time += line_duration

        return split_segments

    def _convert_to_subtitle_segments(self, stt_segments: List[STTSegment]) -> List[SubtitleSegment]:
        """
        转换为字幕片段

        Args:
            stt_segments: STT 片段列表

        Returns:
            List[SubtitleSegment]: 字幕片段列表
        """
        subtitle_segments = []

        for i, stt_seg in enumerate(stt_segments, 1):
            subtitle_seg = SubtitleSegment(
                text=stt_seg.text,
                start_time=stt_seg.start_time,
                end_time=stt_seg.end_time,
                index=i
            )
            subtitle_segments.append(subtitle_seg)

        return subtitle_segments

    def _quality_check(self, segments: List[SubtitleSegment]) -> List[SubtitleSegment]:
        """
        质量检查和最终处理

        Args:
            segments: 字幕片段列表

        Returns:
            List[SubtitleSegment]: 检查后的片段
        """
        if not segments:
            return []

        # 检查时间戳连续性
        validated_segments = []
        prev_end = 0.0

        for segment in segments:
            # 确保开始时间不早于上一个片段的结束时间
            if segment.start_time < prev_end - 0.1:  # 允许 0.1s 的容差
                self.logger.warning(
                    f"时间戳不连续: 片段 {segment.index} "
                    f"开始时间 {segment.start_time:.2f}s < 上一个结束时间 {prev_end:.2f}s"
                )

            # 确保时长合理
            if segment.duration < 0.1:
                self.logger.warning(f"片段时长过短: {segment.duration:.2f}s")

            validated_segments.append(segment)
            prev_end = segment.end_time

        return validated_segments

    def adjust_timing(
        self,
        segments: List[SubtitleSegment],
        time_offset: float
    ) -> List[SubtitleSegment]:
        """
        调整字幕时间戳

        Args:
            segments: 字幕片段列表
            time_offset: 时间偏移（秒）

        Returns:
            List[SubtitleSegment]: 调整后的片段
        """
        return self.base_generator.adjust_timing(segments, time_offset)

    def save_to_srt(
        self,
        segments: List[SubtitleSegment],
        output_path: str
    ) -> Path:
        """
        保存字幕为 SRT 格式

        Args:
            segments: 字幕片段列表
            output_path: 输出路径

        Returns:
            Path: 输出文件路径
        """
        return self.base_generator.save_to_srt(segments, output_path)

    def __repr__(self) -> str:
        return (
            f"STTSubtitleGenerator("
            f"max_chars_per_line={self.max_chars_per_line}, "
            f"merge_threshold={self.stt_segment_merge_threshold}s"
            f")"
        )
