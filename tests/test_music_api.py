#!/usr/bin/env python3
"""
测试音乐API功能
"""

import asyncio
import sys
from pathlib import Path

# 添加src到路径
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

from audio.music_recommender import MusicRecommender
from audio.models import MusicSearchCriteria


async def test_music_recommendation():
    """测试音乐推荐功能"""
    print("🎵 测试智能背景音乐推荐功能")

    # 配置（模拟）
    config = {
        'api_key': 'your-openai-api-key',  # 需要真实的API key才能测试
        'model': 'gpt-4',
        'temperature': 0.7,
        'max_tokens': 1000,
        'sources': {
            'jamendo': {
                'enabled': True,
                'copyright_status': 'creative_commons',
                'client_id': 'your_jamendo_client_id',
            }
        }
    }

    # 创建推荐器
    try:
        recommender = MusicRecommender(config)
        print("✅ MusicRecommender 初始化成功")
    except Exception as e:
        print(f"❌ MusicRecommender 初始化失败: {e}")
        return

    # 测试内容分析
    test_content = "这是一个关于人工智能技术发展的精彩介绍视频，探讨了机器学习、深度学习和神经网络的前沿进展。"

    print(f"\\n📝 测试内容: {test_content[:50]}...")

    try:
        analysis = await recommender._analyze_content(test_content)
        print("✅ 内容分析成功:")
        print(f"   - 主题: {analysis.get('theme')}")
        print(f"   - 情绪: {analysis.get('mood')}")
        print(f"   - 节奏: {analysis.get('pace')}")
        print(f"   - 音乐类型: {analysis.get('genre_preferences')}")
        print(f"   - 关键词: {analysis.get('keywords')}")
    except Exception as e:
        print(f"❌ 内容分析失败: {e}")
        return

    # 测试音乐搜索
    print("\\n🔍 测试音乐搜索...")

    criteria = MusicSearchCriteria()
    duration = 180  # 3分钟

    try:
        recommendations = await recommender.recommend_music(test_content, duration, criteria)

        if recommendations:
            print(f"✅ 找到 {len(recommendations)} 个音乐推荐")
            for i, rec in enumerate(recommendations[:3], 1):  # 显示前3个
                print(f"   {i}. {rec.title} - {rec.artist}")
                print(f"      类型: {rec.genre}, 情绪: {rec.mood}")
                print(f"      时长: {rec.duration_formatted}")
                print(f"      来源: {rec.source}, 版权: {rec.copyright_status.value}")
                print()
        else:
            print("⚠️  未找到音乐推荐")

    except Exception as e:
        print(f"❌ 音乐搜索失败: {e}")


async def test_jamendo_api():
    """单独测试Jamendo API"""
    print("\\n🎵 测试Jamendo API")

    config = {
        'api_key': 'dummy-key',  # 不需要真实的OpenAI key来测试Jamendo
        'sources': {
            'jamendo': {
                'enabled': True,
                'copyright_status': 'creative_commons',
                'client_id': 'your_jamendo_client_id',
                'api_url': 'https://api.jamendo.com/v3.0/',
            }
        }
    }

    recommender = MusicRecommender(config)

    # 模拟内容分析结果
    content_analysis = {
        'keywords': ['technology', 'ai', 'future'],
        'mood': 'inspiring',
        'genre_preferences': ['electronic', 'ambient']
    }

    try:
        recommendations = await recommender._search_jamendo(
            config['sources']['jamendo'], content_analysis, 180, MusicSearchCriteria()
        )

        if recommendations:
            print(f"✅ Jamendo API 返回 {len(recommendations)} 个结果")
            for rec in recommendations[:2]:
                print(f"   - {rec.title} ({rec.duration:.0f}s)")
        else:
            print("⚠️  Jamendo API 未返回结果")

    except Exception as e:
        print(f"❌ Jamendo API 测试失败: {e}")


if __name__ == "__main__":
    print("🎵 智能背景音乐API测试")
    print("=" * 50)

    # 测试基本功能
    asyncio.run(test_music_recommendation())

    # 测试Jamendo API
    asyncio.run(test_jamendo_api())

    print("\\n" + "=" * 50)
    print("🎵 测试完成")
    print("\\n💡 要使用完整功能，请设置以下环境变量:")
    print("   export OPENAI_API_KEY='your-openai-api-key'")
    print("   export PIXABAY_API_KEY='your-pixabay-api-key'  # 可选")
    print("   export FREESOUND_API_KEY='your-freesound-api-key'  # 可选")
    print("\\n📖 API申请地址:")
    print("   - OpenAI: https://platform.openai.com/api-keys")
    print("   - Pixabay: https://pixabay.com/api/docs/")
    print("   - Freesound: https://freesound.org/apiv2/apply/")
