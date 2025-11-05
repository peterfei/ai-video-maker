#!/usr/bin/env python3
"""
免费音乐下载工具

从公开的免费音乐源下载高质量背景音乐到本地库。
支持的音乐源：
1. Free Music Archive (FMA)
2. ccMixter
3. YouTube Audio Library (需要手动下载)
4. Incompetech (Kevin MacLeod)
"""

import json
import asyncio
import aiohttp
import os
from pathlib import Path
from typing import List, Dict

# 推荐的免费音乐列表（知名的CC授权音乐）
FREE_MUSIC_SOURCES = [
    {
        "title": "Inspiring Cinematic",
        "artist": "Scott Buckley",
        "url": "https://www.scottbuckley.com.au/library/inspiring-cinematic/",
        "genre": "cinematic",
        "mood": ["inspiring", "uplifting"],
        "themes": ["business", "technology", "presentation"],
        "note": "需要从网站手动下载"
    },
    {
        "title": "Meditation Music",
        "artist": "Christopher Lloyd Clarke",
        "url": "https://www.christopherlloydclarke.com/",
        "genre": "ambient",
        "mood": ["calm", "peaceful"],
        "themes": ["meditation", "wellness", "nature"],
        "note": "需要从网站手动下载"
    },
    {
        "title": "Corporate Background",
        "artist": "Bensound",
        "url": "https://www.bensound.com/royalty-free-music/track/creative-minds",
        "genre": "corporate",
        "mood": ["inspiring", "professional"],
        "themes": ["business", "presentation", "corporate"],
        "note": "需要从网站手动下载（需注明出处）"
    },
]

# YouTube Audio Library 推荐
YOUTUBE_AUDIO_LIBRARY_RECOMMENDATIONS = [
    {"name": "Breathe", "mood": "calm", "genre": "ambient"},
    {"name": "Ikson - Stardust", "mood": "happy", "genre": "electronic"},
    {"name": "Vibe With Me", "mood": "energetic", "genre": "hip-hop"},
    {"name": "Cinematic", "mood": "inspiring", "genre": "orchestral"},
]


def print_download_instructions():
    """打印下载说明"""
    print("🎵 免费音乐下载指南")
    print("=" * 70)
    print()
    print("📋 推荐的免费音乐源：")
    print()

    print("1️⃣  **YouTube Audio Library** (推荐)")
    print("   网址: https://studio.youtube.com/channel/UC.../music")
    print("   特点: 完全免费，无需署名，高质量")
    print("   步骤:")
    print("   - 登录 YouTube Studio")
    print("   - 进入「音频库」")
    print("   - 搜索并下载音乐")
    print("   - 保存到 assets/music/ 目录")
    print()

    print("2️⃣  **Free Music Archive (FMA)**")
    print("   网址: https://freemusicarchive.org/")
    print("   特点: 大量免费音乐，需查看具体许可")
    print("   步骤:")
    print("   - 搜索你需要的音乐类型")
    print("   - 筛选 CC-BY 或 CC0 许可")
    print("   - 下载并保存")
    print()

    print("3️⃣  **Incompetech (Kevin MacLeod)**")
    print("   网址: https://incompetech.com/music/")
    print("   特点: 免费使用，需署名")
    print("   步骤:")
    print("   - 按心情/类型浏览")
    print("   - 下载 MP3")
    print("   - 在视频描述中注明：Music by Kevin MacLeod")
    print()

    print("4️⃣  **ccMixter**")
    print("   网址: https://ccmixter.org/")
    print("   特点: CC授权，remix文化")
    print("   步骤:")
    print("   - 搜索 Creative Commons 音乐")
    print("   - 下载并遵守许可要求")
    print()

    print("5️⃣  **Bensound**")
    print("   网址: https://www.bensound.com/")
    print("   特点: 免费使用，需署名")
    print("   步骤:")
    print("   - 浏览不同类别")
    print("   - 下载免费版本")
    print("   - 在视频中注明：Music from Bensound.com")
    print()

    print("=" * 70)
    print()
    print("💡 **推荐下载列表**（按情绪分类）：")
    print()

    categories = {
        "平静/放松": [
            "Piano - Calm",
            "Ambient - Peaceful",
            "Meditation - Serene"
        ],
        "激励/积极": [
            "Corporate - Uplifting",
            "Inspiring - Motivational",
            "Upbeat - Positive"
        ],
        "科技/现代": [
            "Electronic - Modern",
            "Tech - Innovation",
            "Ambient - Futuristic"
        ],
        "自然/放松": [
            "Nature - Calm",
            "Acoustic - Gentle",
            "Spa - Relaxing"
        ]
    }

    for category, tracks in categories.items():
        print(f"📁 {category}:")
        for track in tracks:
            print(f"   • {track}")
        print()

    print("=" * 70)
    print()
    print("📝 **下载后的设置**：")
    print()
    print("1. 将音乐文件保存到：assets/music/")
    print("2. 更新元数据文件：assets/music/music_metadata.json")
    print("3. 运行测试：python tools/test_music_matching.py")
    print()

    print("示例元数据配置：")
    print(json.dumps({
        "filename": "inspiring_corporate.mp3",
        "title": "Inspiring Corporate",
        "artist": "Your Source",
        "genre": "corporate",
        "mood": ["inspiring", "uplifting"],
        "themes": ["business", "technology"],
        "tempo": "medium",
        "tags": ["corporate", "inspiring", "background"],
        "copyright": "creative_commons",
        "attribution": "Music from YourSource.com"
    }, indent=2))
    print()

    print("=" * 70)
    print()
    print("✅ **版权注意事项**：")
    print()
    print("✓ 始终检查音乐的具体许可证")
    print("✓ 如需署名，在视频描述中注明")
    print("✓ 不要用于商业用途（除非许可允许）")
    print("✓ 保存原始许可证文件")
    print()
    print("🎉 下载后，系统将自动使用AI匹配最合适的音乐！")
    print()


def generate_metadata_template():
    """生成元数据模板"""
    template = {
        "filename": "YOUR_MUSIC_FILE.mp3",
        "title": "Music Title",
        "artist": "Artist Name",
        "genre": "ambient",  # ambient, classical, electronic, corporate, cinematic
        "mood": ["calm", "peaceful"],  # calm, inspiring, happy, sad, serious, energetic
        "themes": ["meditation", "nature"],  # meditation, technology, business, education, nature
        "tempo": "slow",  # slow, medium, fast
        "duration": 180,  # 秒
        "tags": ["piano", "instrumental", "background"],
        "copyright": "creative_commons",  # royalty_free, creative_commons, public_domain
        "attribution": "Music from Source.com (if required)",
        "description": "音乐描述"
    }

    output_path = Path("assets/music/metadata_template.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(template, f, indent=2, ensure_ascii=False)

    print(f"✅ 元数据模板已生成: {output_path}")


if __name__ == "__main__":
    print()
    print_download_instructions()
    generate_metadata_template()
