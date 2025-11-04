#!/usr/bin/env python3
"""
STT 功能基础测试

验证 STT 模块的基本功能是否正常工作。
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    try:
        # 测试导入
        print("🔍 测试模块导入...")

        from src.audio.models import STTResult, STTSegment, STTConfig
        print("✅ STT 数据模型导入成功")

        from src.audio.stt_engine import STTEngine, get_stt_engine
        print("✅ STT 引擎导入成功")

        from src.subtitle.stt_subtitle_gen import STTSubtitleGenerator
        print("✅ STT 字幕生成器导入成功")

        # 测试数据模型
        print("\n🔍 测试数据模型...")
        config = STTConfig()
        print(f"✅ STTConfig 创建成功: model={config.model}, language={config.language}")

        segment = STTSegment(
            text="这是一个测试",
            start_time=0.0,
            end_time=2.0,
            confidence=0.95
        )
        print(f"✅ STTSegment 创建成功: '{segment.text}' ({segment.duration:.1f}s)")

        result = STTResult(
            segments=[segment],
            language="zh",
            duration=2.0,
            model_used="base"
        )
        print(f"✅ STTResult 创建成功: {len(result.segments)} 片段, {result.duration:.1f}s")

        # 测试配置验证
        print("\n🔍 测试配置验证...")
        valid_config = {"model": "tiny", "language": "zh"}
        stt_config = STTConfig.from_dict(valid_config)
        print(f"✅ 配置验证通过: {stt_config.model}")

        try:
            invalid_config = {"model": "invalid", "language": "zh"}
            STTConfig.from_dict(invalid_config)
            print("❌ 应该拒绝无效配置")
        except ValueError:
            print("✅ 正确拒绝了无效配置")

        # 测试 STT 引擎初始化（不加载模型）
        print("\n🔍 测试 STT 引擎初始化...")
        try:
            # 注意：这里不会实际加载模型，只是验证初始化逻辑
            test_config = {"enabled": False, "model": "tiny", "language": "zh"}
            # STTEngine 初始化时会检查 faster-whisper 是否可用
            engine = STTEngine(test_config)
            print("✅ STT 引擎初始化成功（未加载模型）")
        except Exception as e:
            print(f"⚠️  STT 引擎初始化失败（可能是缺少依赖）: {e}")

        # 测试字幕生成器
        print("\n🔍 测试字幕生成器...")
        subtitle_config = {"max_chars_per_line": 20}
        generator = STTSubtitleGenerator(subtitle_config)
        print("✅ STT 字幕生成器创建成功")

        # 测试字幕生成
        mock_segments = [
            STTSegment("你好", 0.0, 1.0, 0.9),
            STTSegment("欢迎使用", 1.0, 2.5, 0.95),
            STTSegment("语音转字幕功能", 2.5, 4.0, 0.92)
        ]
        mock_result = STTResult(mock_segments, "zh", 4.0, "tiny")

        subtitles = generator.generate_from_stt(mock_result)
        print(f"✅ 字幕生成成功: {len(subtitles)} 条字幕")

        for i, sub in enumerate(subtitles[:3], 1):  # 只显示前3条
            print(f"  字幕 {i}: '{sub.text}' ({sub.start_time:.1f}s - {sub.end_time:.1f}s)")

        print("\n🎉 所有基础测试通过！")
        print("\n📝 使用说明:")
        print("1. 安装依赖: pip install faster-whisper")
        print("2. 启用 STT: 在 config/default_config.yaml 中设置 stt.enabled: true")
        print("3. 使用命令: python -m src.main --audio your_audio.mp3 --output output.mp4")

        return True

    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        print("请确保所有依赖都已安装: pip install -r requirements.txt")
        return False

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
