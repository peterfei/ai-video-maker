#!/usr/bin/env python3
"""
测试不同字幕文本的渲染
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_font_rendering():
    print("🔍 测试字体渲染功能...")

    try:
        # 导入MoviePy
        from moviepy.editor import TextClip

        # 测试不同的字幕文本
        test_texts = [
            "Python",  # 纯英文
            "欢迎来到Python编程入门教程！",  # 中英文混合
            "今天我们将学习Python的基础语法。",  # 中文句子
            "变量就像是一个容器",  # 纯中文
            "Hello World",  # 纯英文
            "人工智能",  # 中文短语
        ]

        video_size = (1920, 1080)

        print("🧪 测试不同字幕文本的渲染:")

        for i, text in enumerate(test_texts):
            print(f"\n📝 测试文本 {i+1}: '{text}'")

            success_count = 0

            # 测试不同的方法
            methods = ['label', 'caption']

            for method in methods:
                try:
                    clip = TextClip(
                        text,
                        fontsize=48,
                        font='Arial Unicode MS',
                        color='white',
                        stroke_color='black',
                        stroke_width=2,
                        method=method,
                        size=(video_size[0] * 0.9, None),
                        align='center'
                    )

                    print(f"   ✅ {method}方法: 成功 (大小: {clip.size})")
                    clip.close()
                    success_count += 1

                except Exception as e:
                    print(f"   ❌ {method}方法: 失败 - {str(e)}")

            print(f"   📊 成功率: {success_count}/{len(methods)}")

        print("\n🎉 字体渲染测试完成！")
        return True

    except Exception as e:
        print(f"❌ 字体渲染测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_font_rendering()
    sys.exit(0 if success else 1)
