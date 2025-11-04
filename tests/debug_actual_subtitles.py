#!/usr/bin/env python3
"""
检查实际生成的字幕数据
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def analyze_actual_subtitles():
    print("🔍 分析实际生成的字幕数据...")

    try:
        # 模拟实际的字幕生成过程
        from src.subtitle import SubtitleGenerator, SubtitleSegment

        # 读取示例脚本
        script_path = Path("examples/sample_script.txt")
        with open(script_path, 'r', encoding='utf-8') as f:
            text = f.read()

        print("📄 原始脚本内容:")
        print(text[:200] + "..." if len(text) > 200 else text)
        print()

        # 创建字幕生成器
        config = {
            'duration_per_char': 0.3,
            'max_chars_per_line': 25
        }
        generator = SubtitleGenerator(config)

        # 分割句子
        sentences = generator._split_into_sentences(text)
        print(f"📝 分割为 {len(sentences)} 个句子:")

        for i, sentence in enumerate(sentences[:10]):  # 只显示前10个
            print(f"   {i+1:2d}. {sentence[:50]}{'...' if len(sentence) > 50 else ''}")
        if len(sentences) > 10:
            print(f"   ... 还有 {len(sentences) - 10} 个句子")
        print()

        # 模拟音频时长分配（简单估算）
        total_chars = sum(len(s) for s in sentences)
        total_duration = total_chars * 0.3  # 估算总时长

        print(f"📊 总字符数: {total_chars}")
        print(f"⏱️  估算总时长: {total_duration:.1f}秒")

        # 按字符数比例分配时长
        audio_durations = []
        for sentence in sentences:
            duration = (len(sentence) / total_chars) * total_duration
            audio_durations.append(duration)

        print(f"🎵 音频片段数量: {len(audio_durations)}")
        print()

        # 生成字幕片段
        subtitle_segments = generator.generate_from_segments(sentences, audio_durations)

        print(f"🎬 生成的字幕片段 ({len(subtitle_segments)} 个):")
        for i, segment in enumerate(subtitle_segments[:15]):  # 只显示前15个
            print("2d")

        if len(subtitle_segments) > 15:
            print(f"   ... 还有 {len(subtitle_segments) - 15} 个字幕片段")
        print()

        # 检查是否有问题的时间戳
        print("🔍 检查时间戳问题:")
        issues = []
        prev_end = 0.0

        for i, segment in enumerate(subtitle_segments):
            if segment.start_time < prev_end - 0.01:  # 允许0.01秒容差
                issues.append(f"字幕 {i+1}: 开始时间 {segment.start_time:.2f}s < 上一个结束时间 {prev_end:.2f}s")
            if segment.duration < 0.1:
                issues.append(f"字幕 {i+1}: 时长过短 {segment.duration:.2f}s")
            if len(segment.text.strip()) == 0:
                issues.append(f"字幕 {i+1}: 空文本")
            prev_end = segment.end_time

        if issues:
            print("❌ 发现问题:")
            for issue in issues[:10]:  # 只显示前10个问题
                print(f"   {issue}")
            if len(issues) > 10:
                print(f"   ... 还有 {len(issues) - 10} 个问题")
        else:
            print("✅ 没有发现明显的时间戳问题")

        print("\n🎉 字幕数据分析完成！")
        return True

    except Exception as e:
        print(f"❌ 字幕数据分析失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = analyze_actual_subtitles()
    sys.exit(0 if success else 1)
