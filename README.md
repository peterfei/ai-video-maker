# 视频生成工厂 (Video Factory)

一个基于 Python 的自动化视频生成系统，专注于解说/教程类视频的批量生产。

## 核心功能

- 🎬 **多源内容整合**: 支持文本脚本、素材库、AI生成内容的混合使用
- 🎙️ **智能配音**: 基于 TTS 技术自动生成解说音频
- 📝 **自动字幕**: 自动生成并渲染字幕
- 🎵 **背景音乐**: 智能添加背景音乐，自动调节音量
- ⚡ **批量生成**: 支持任务队列，批量处理多个视频
- 🛠️ **灵活配置**: 通过配置文件轻松定制视频样式

## 项目结构

```
video-factory/
├── src/                          # 源代码目录
│   ├── content_sources/          # 内容源管理
│   │   ├── __init__.py
│   │   ├── text_source.py       # 文本/脚本处理
│   │   ├── material_source.py   # 素材库管理
│   │   └── ai_source.py         # AI内容生成
│   ├── audio/                    # 音频处理
│   │   ├── __init__.py
│   │   ├── tts_engine.py        # TTS引擎
│   │   └── audio_mixer.py       # 音频混合
│   ├── subtitle/                 # 字幕处理
│   │   ├── __init__.py
│   │   ├── subtitle_gen.py      # 字幕生成
│   │   └── subtitle_render.py   # 字幕渲染
│   ├── video_engine/             # 视频合成引擎
│   │   ├── __init__.py
│   │   ├── compositor.py        # 视频合成器
│   │   └── effects.py           # 视频效果
│   ├── tasks/                    # 任务管理
│   │   ├── __init__.py
│   │   ├── task_queue.py        # 任务队列
│   │   └── batch_processor.py   # 批处理器
│   ├── __init__.py
│   └── main.py                   # 主程序入口
├── assets/                       # 资源文件
│   ├── templates/                # 视频模板
│   ├── music/                    # 背景音乐库
│   └── fonts/                    # 字体文件
├── output/                       # 输出目录
├── data/                         # 数据目录
│   ├── scripts/                  # 文本脚本
│   └── materials/                # 素材文件
├── config/                       # 配置文件
│   ├── default_config.yaml      # 默认配置
│   └── template_styles.yaml     # 模板样式
├── examples/                     # 示例文件
├── tests/                        # 测试文件
├── requirements.txt              # 依赖列表
└── README.md                     # 项目说明

```

## 技术栈

- **视频处理**: MoviePy + FFmpeg
- **TTS引擎**: edge-tts / pyttsx3 / Azure TTS
- **字幕渲染**: PIL + MoviePy
- **任务队列**: Python Queue / Celery (可选)
- **AI集成**: OpenAI API / 本地模型

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置系统

编辑 `config/default_config.yaml` 设置你的偏好。

### 3. 准备内容

将视频脚本放入 `data/scripts/`，素材文件放入 `data/materials/`。

### 4. 运行生成

```bash
# 生成单个视频
python src/main.py --script data/scripts/example.txt

# 批量生成
python src/main.py --batch data/scripts/
```

## 工作流程

1. **内容准备**: 从脚本、素材库或AI生成内容
2. **音频生成**: TTS将文本转换为语音，添加背景音乐
3. **字幕制作**: 根据脚本时间轴生成字幕
4. **视频合成**: 整合视频画面、音频、字幕
5. **批量处理**: 队列化处理多个任务

## 配置示例

```yaml
# 视频设置
video:
  resolution: [1920, 1080]
  fps: 30
  duration: auto

# TTS设置
tts:
  engine: edge-tts
  voice: zh-CN-XiaoxiaoNeural
  rate: 1.0

# 字幕设置
subtitle:
  font_size: 48
  font_color: white
  position: bottom

# 音乐设置
music:
  enabled: true
  volume: 0.3
```

## 开发路线图

- [x] 项目架构设计
- [ ] 核心模块实现
- [ ] TTS集成
- [ ] 字幕系统
- [ ] 视频合成引擎
- [ ] 批量处理系统
- [ ] Web UI (可选)

## 许可证

MIT License
