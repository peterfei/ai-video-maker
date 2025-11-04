#!/usr/bin/env python3
"""
准备复杂测试场景
创建测试图片和长文本脚本
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import random

def create_test_images(output_dir: str, count: int = 15):
    """创建测试图片"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"📸 创建 {count} 张测试图片...")

    # 定义颜色方案
    colors = [
        [(52, 152, 219), (41, 128, 185)],   # 蓝色渐变
        [(231, 76, 60), (192, 57, 43)],      # 红色渐变
        [(46, 204, 113), (39, 174, 96)],     # 绿色渐变
        [(155, 89, 182), (142, 68, 173)],    # 紫色渐变
        [(230, 126, 34), (211, 84, 0)],      # 橙色渐变
        [(52, 73, 94), (44, 62, 80)],        # 深灰色渐变
        [(241, 196, 15), (243, 156, 18)],    # 黄色渐变
        [(26, 188, 156), (22, 160, 133)],    # 青色渐变
    ]

    created_files = []

    for i in range(count):
        # 创建图片
        img = Image.new('RGB', (1920, 1080))
        draw = ImageDraw.Draw(img)

        # 选择颜色
        color_scheme = colors[i % len(colors)]

        # 创建渐变背景
        for y in range(1080):
            ratio = y / 1080
            r = int(color_scheme[0][0] * (1 - ratio) + color_scheme[1][0] * ratio)
            g = int(color_scheme[0][1] * (1 - ratio) + color_scheme[1][1] * ratio)
            b = int(color_scheme[0][2] * (1 - ratio) + color_scheme[1][2] * ratio)
            draw.line([(0, y), (1920, y)], fill=(r, g, b))

        # 添加装饰图形
        for _ in range(10):
            x = random.randint(100, 1820)
            y = random.randint(100, 980)
            size = random.randint(50, 200)
            alpha = random.randint(20, 60)

            # 创建半透明圆形
            circle_img = Image.new('RGBA', (size, size), (255, 255, 255, 0))
            circle_draw = ImageDraw.Draw(circle_img)
            circle_draw.ellipse([0, 0, size, size],
                              fill=(255, 255, 255, alpha))

            # 合并到主图
            img.paste(circle_img, (x, y), circle_img)

        # 添加文字
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 120)
        except:
            font = ImageFont.load_default()

        text = f"Scene {i+1}"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (1920 - text_width) // 2
        y = (1080 - text_height) // 2

        # 文字阴影
        draw.text((x+4, y+4), text, fill=(0, 0, 0, 128), font=font)
        # 主文字
        draw.text((x, y), text, fill=(255, 255, 255), font=font)

        # 保存图片
        filename = f"test_image_{i+1:02d}.jpg"
        filepath = output_path / filename
        img.save(filepath, 'JPEG', quality=90)
        created_files.append(str(filepath))

        if (i + 1) % 5 == 0:
            print(f"  已创建 {i+1}/{count} 张图片")

    print(f"✅ 成功创建 {len(created_files)} 张测试图片")
    return created_files


def create_complex_script(output_file: str):
    """创建复杂的测试脚本（长文本）"""
    script_content = """人工智能技术正在深刻改变我们的世界。
从智能手机到自动驾驶汽车，AI已经渗透到生活的方方面面。
机器学习算法能够从海量数据中发现模式和规律。
深度学习网络模拟人脑神经元的工作方式。
计算机视觉技术让机器能够理解和分析图像内容。
自然语言处理使得人机对话变得越来越自然流畅。
语音识别技术已经达到了接近人类的准确率。
推荐系统能够精准预测用户的兴趣和需求。
AI助手正在成为我们日常工作的得力帮手。
医疗诊断系统帮助医生提高诊断的准确性。
金融风控模型能够实时识别潜在的风险。
智能制造正在推动工业生产的智能化转型。
教育领域的个性化学习系统因材施教。
AI艺术创作展现了机器的创造力。
未来人工智能将在更多领域发挥重要作用。"""

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(script_content, encoding='utf-8')

    lines = script_content.strip().split('\n')
    print(f"📝 创建复杂测试脚本: {output_file}")
    print(f"  - 共 {len(lines)} 个句子")
    print(f"  - 预计视频时长: ~60秒")

    return output_file


def main():
    print("=" * 60)
    print("准备复杂性能测试场景")
    print("=" * 60)

    # 创建测试图片目录
    images_dir = "data/test_materials"
    script_file = "data/scripts/complex_benchmark.txt"

    # 1. 创建测试图片
    print("\n1. 创建测试图片")
    image_files = create_test_images(images_dir, count=15)

    # 2. 创建复杂脚本
    print("\n2. 创建测试脚本")
    script_path = create_complex_script(script_file)

    print("\n" + "=" * 60)
    print("✅ 准备工作完成！")
    print("=" * 60)
    print(f"\n测试素材:")
    print(f"  图片目录: {images_dir} ({len(image_files)} 张)")
    print(f"  脚本文件: {script_path}")
    print(f"\n可以开始性能测试了！")


if __name__ == "__main__":
    main()
