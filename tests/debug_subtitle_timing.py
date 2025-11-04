#!/usr/bin/env python3
"""
检查字幕时间分布和潜在问题
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def analyze_subtitle_timing():
    print("🔍 分析字幕时间分布...")

    try:
        # 模拟实际的视频生成过程
        from src.subtitle import SubtitleGenerator

        # 读取脚本并分割句子
        script_path = Path("examples/sample_script.txt")
        with open(script_path, 'r', encoding='utf-8') as f:
            text = f.read()

        config = {'duration_per_char': 0.3, 'max_chars_per_line': 25}
        generator = SubtitleGenerator(config)
        sentences = generator._split_into_sentences(text)

        # 模拟实际的音频时长（从之前的日志获取）
        actual_durations = [
            3.34, 3.43, 2.66, 2.40, 2.64, 1.56, 1.99, 3.24, 4.58, 1.61,
            2.21, 2.40, 2.98, 5.02, 3.26, 3.65, 1.56, 2.83, 2.30, 3.05,
            1.90, 2.40, 2.64, 3.84, 4.15, 3.62, 3.10, 3.58, 1.80
        ][:len(sentences)]

        # 生成字幕
        subtitle_segments = generator.generate_from_segments(sentences, actual_durations)

        print(f"🎬 分析 {len(subtitle_segments)} 个字幕片段:")

        # 分析时间分布
        very_short = []  # < 0.5秒
        short = []      # 0.5-1秒
        normal = []     # 1-3秒
        long = []       # > 3秒

        prev_end = 0.0
        overlaps = []
        gaps = []

        for i, segment in enumerate(subtitle_segments):
            duration = segment.duration

            if duration < 0.5:
                very_short.append((i, segment))
            elif duration < 1.0:
                short.append((i, segment))
            elif duration <= 3.0:
                normal.append((i, segment))
            else:
                long.append((i, segment))

            # 检查重叠
            if segment.start_time < prev_end - 0.01:
                overlaps.append(f"字幕{i+1}与{i}重叠: {segment.start_time:.2f} < {prev_end:.2f}")

            # 检查间隙
            if i > 0 and segment.start_time > prev_end + 0.1:
                gaps.append(f"字幕{i}与{i+1}之间有间隙: {prev_end:.2f} 到 {segment.start_time:.2f}")

            prev_end = segment.end_time

        print("\n📊 时长分布:")
        print(f"   超短 (<0.5s): {len(very_short)} 个")
        print(f"   短 (0.5-1s): {len(short)} 个")
        print(f"   正常 (1-3s): {len(normal)} 个")
        print(f"   长 (>3s): {len(long)} 个")

        if very_short:
            print("\n⚠️  超短字幕片段:")
            for idx, seg in very_short:
                print(f"   字幕{idx+1}: '{seg.text}' ({seg.duration:.2f}s)")

        if overlaps:
            print("\n❌ 时间重叠:")
            for overlap in overlaps:
                print(f"   {overlap}")

        if gaps:
            print("\nℹ️  时间间隙:")
            for gap in gaps:
                print(f"   {gap}")

        # 检查是否有包含"Python"的字幕
        python_subtitles = []
        for i, segment in enumerate(subtitle_segments):
            if "Python" in segment.text:
                python_subtitles.append((i, segment))

        if python_subtitles:
            print("\n🐍 包含'Python'的字幕:")
            for idx, seg in python_subtitles:
                print(f"   字幕{idx+1}: '{seg.text}' ({seg.start_time:.2f}s - {seg.end_time:.2f}s)")
        else:
            print("\n❓ 没有找到包含'Python'的字幕")

        # 显示前几个字幕的详细信息
        print("\n📋 前10个字幕详情:")
        for i in range(min(10, len(subtitle_segments))):
            seg = subtitle_segments[i]
            print(f"   {i+1:2d}. '{seg.text[:40]}{'...' if len(seg.text) > 40 else ''}' ({seg.start_time:.2f}s - {seg.end_time:.2f}s)")

        print("\n🎉 时间分布分析完成！")
        return True

    except Exception as e:
        print(f"❌ 时间分布分析失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = analyze_subtitle_timing()
    sys.exit(0 if success else 1)
