"""
系统测试脚本
用于验证各模块是否正常工作
"""

import sys
import os
from pathlib import Path

# 添加项目根目录和src到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

# 切换到项目根目录
os.chdir(project_root)

def test_imports():
    """测试模块导入"""
    print("测试模块导入...")

    try:
        from config_loader import ConfigLoader
        print("  ✓ config_loader")

        from utils import setup_logger
        print("  ✓ utils")

        from content_sources import TextSource, MaterialSource
        print("  ✓ content_sources")

        from audio import TTSEngine, AudioMixer
        print("  ✓ audio")

        from subtitle import SubtitleGenerator, SubtitleRenderer
        print("  ✓ subtitle")

        from video_engine import VideoCompositor, VideoEffects
        print("  ✓ video_engine")

        from tasks import TaskQueue, VideoTask, BatchProcessor
        print("  ✓ tasks")

        print("\n✓ 所有模块导入成功!\n")
        return True

    except Exception as e:
        print(f"\n✗ 模块导入失败: {e}\n")
        return False


def test_config():
    """测试配置加载"""
    print("测试配置加载...")

    try:
        from config_loader import ConfigLoader

        config = ConfigLoader("config/default_config.yaml")
        print(f"  ✓ 配置文件加载成功")
        print(f"  - 视频分辨率: {config.get('video.resolution')}")
        print(f"  - TTS引擎: {config.get('tts.engine')}")
        print(f"  - 字幕启用: {config.get('subtitle.enabled')}")

        print("\n✓ 配置测试通过!\n")
        return True

    except Exception as e:
        print(f"\n✗ 配置测试失败: {e}\n")
        return False


def test_text_source():
    """测试文本源"""
    print("测试文本源处理...")

    try:
        from content_sources import TextSource

        text_source = TextSource({'encoding': 'utf-8', 'split_by_paragraph': True})

        # 测试文本解析
        test_text = """
        这是第一段测试文本。

        这是第二段测试文本。

        这是第三段测试文本。
        """

        segments = text_source.create_from_text(test_text)
        print(f"  ✓ 解析了 {len(segments)} 个文本片段")

        # 测试时长估算
        duration = text_source.estimate_duration(segments)
        print(f"  ✓ 估算时长: {duration:.2f}秒")

        print("\n✓ 文本源测试通过!\n")
        return True

    except Exception as e:
        print(f"\n✗ 文本源测试失败: {e}\n")
        return False


def test_subtitle():
    """测试字幕生成"""
    print("测试字幕生成...")

    try:
        from subtitle import SubtitleGenerator

        config = {
            'duration_per_char': 0.3,
            'max_chars_per_line': 25
        }

        sub_gen = SubtitleGenerator(config)

        # 测试字幕生成
        text = "这是一段测试文本，用于生成字幕。"
        segments = sub_gen.generate_from_text(text, audio_duration=10.0)

        print(f"  ✓ 生成了 {len(segments)} 个字幕片段")
        print(f"  - 第一个片段: {segments[0].text}")
        print(f"  - 时间: {segments[0].start_time:.2f}s - {segments[0].end_time:.2f}s")

        print("\n✓ 字幕测试通过!\n")
        return True

    except Exception as e:
        print(f"\n✗ 字幕测试失败: {e}\n")
        return False


def test_task_queue():
    """测试任务队列"""
    print("测试任务队列...")

    try:
        from tasks import TaskQueue, VideoTask, TaskStatus
        import uuid

        queue = TaskQueue()

        # 创建测试任务
        task = VideoTask(
            task_id=str(uuid.uuid4()),
            script_text="测试脚本",
            status=TaskStatus.PENDING
        )

        queue.add_task(task)
        print(f"  ✓ 添加任务: {task.task_id[:8]}...")

        # 获取任务
        retrieved = queue.get_task(task.task_id)
        print(f"  ✓ 获取任务: {retrieved.status.value}")

        # 更新状态
        queue.update_task_status(task.task_id, TaskStatus.COMPLETED)
        print(f"  ✓ 更新状态: {queue.get_task(task.task_id).status.value}")

        # 统计
        stats = queue.get_statistics()
        print(f"  ✓ 队列统计: {stats}")

        print("\n✓ 任务队列测试通过!\n")
        return True

    except Exception as e:
        print(f"\n✗ 任务队列测试失败: {e}\n")
        return False


def main():
    """主测试函数"""
    print("=" * 50)
    print("视频生成工厂 - 系统测试")
    print("=" * 50)
    print()

    tests = [
        ("模块导入", test_imports),
        ("配置加载", test_config),
        ("文本源处理", test_text_source),
        ("字幕生成", test_subtitle),
        ("任务队列", test_task_queue),
    ]

    results = []

    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"测试 '{name}' 发生异常: {e}")
            results.append((name, False))

    # 总结
    print("=" * 50)
    print("测试总结")
    print("=" * 50)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"  {status} - {name}")

    print()
    print(f"总计: {passed}/{total} 测试通过")

    if passed == total:
        print("\n✓ 所有测试通过！系统运行正常。")
        return 0
    else:
        print(f"\n✗ {total - passed} 个测试失败。请检查错误信息。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
