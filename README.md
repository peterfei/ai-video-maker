# AI 视频制作 (AI Video Maker)

一个基于 Python 的自动化视频生成系统，专注于解说/教程类视频的批量生产。

## 核心功能

- 🎬 **多源内容整合**: 支持文本脚本、素材库、AI生成内容的混合使用
- 🎙️ **智能配音**: 基于 TTS 技术自动生成解说音频
- 📝 **精准字幕同步**:
  - ✨ **分段音频生成**: 为每个句子单独生成TTS音频
  - ✨ **实际时长匹配**: 字幕时长完全匹配真实音频时长，避免估算误差
  - ✨ **一句一幕**: 每个句子对应独立字幕片段，实现完美同步
- 🎞️ **平滑转场动画**: 支持淡入淡出等多种转场效果，视觉流畅自然
- 🎵 **智能背景音乐**: AI驱动的背景音乐推荐，自动匹配内容情绪和主题，支持无版权音乐库
- 🚀 **高性能处理**:
  - ⚡ **多线程并行**: 智能资源管理，充分利用多核CPU
  - 🎮 **GPU加速**: 支持CUDA (NVIDIA) 和 MPS (Apple Silicon M1/M2/M3/M4)，视频渲染和特效大幅加速
  - 📊 **性能监控**: 实时统计处理速度和资源使用
- ⚡ **批量生成**: 支持任务队列，批量处理多个视频
- 🛠️ **灵活配置**: 通过配置文件轻松定制视频样式和性能参数

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
│   │   ├── audio_mixer.py       # 音频混合
│   │   ├── music_recommender.py # 🎵 智能音乐推荐
│   │   ├── music_downloader.py  # 🎵 音乐下载器
│   │   ├── music_library.py     # 🎵 音乐库管理
│   │   └── models.py            # 数据模型
│   ├── subtitle/                 # 字幕处理
│   │   ├── __init__.py
│   │   ├── subtitle_gen.py      # 字幕生成
│   │   └── subtitle_render.py   # 字幕渲染
│   ├── video_engine/             # 视频合成引擎
│   │   ├── __init__.py
│   │   ├── compositor.py        # 视频合成器
│   │   ├── effects.py           # 视频效果
│   │   ├── gpu_accelerator.py   # GPU加速器
│   │   └── gpu_effects.py       # GPU特效处理器
│   ├── tasks/                    # 任务管理
│   │   ├── __init__.py
│   │   ├── task_queue.py        # 任务队列
│   │   ├── batch_processor.py   # 传统批处理器
│   │   └── parallel_batch_processor.py # 并行批处理器
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
- **GPU加速**: PyTorch + CUDA (NVIDIA) / MPS (Apple Silicon)
- **TTS引擎**: edge-tts / pyttsx3 / Azure TTS
- **字幕渲染**: PIL + MoviePy
- **并发处理**: Python concurrent.futures
- **任务队列**: Python Queue / Celery (可选)
- **AI集成**: OpenAI API / 本地模型
- **性能监控**: psutil + 自定义指标

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

# 批量生成 (自动启用多线程和GPU加速)
python src/main.py --batch data/scripts/

# 性能基准测试
python scripts/performance_benchmark.py --quick
```

### 5. 开源仓库

- GitHub: https://github.com/peterfei/ai-video-maker

## 🎵 智能背景音乐功能

### 功能特性

- 🤖 **AI内容分析**: 使用OpenAI GPT-4分析视频内容，提取主题、情绪、节奏特征
- 🎼 **多源音乐库**: 集成Jamendo、Pixabay、Freesound等无版权音乐平台
- ⚖️ **版权合规**: 自动验证音乐版权状态，确保100%合规使用
- 💾 **智能缓存**: 本地缓存音乐文件，避免重复下载，支持过期清理
- 🎯 **精准匹配**: 根据内容自动推荐最适合的音乐类型和情绪

### 快速使用

```bash
# 自动选择背景音乐（推荐）
python generate.py --text "这是一个关于人工智能的精彩介绍视频"

# 指定音乐偏好
python generate.py --text "你的视频内容" --music-genre ambient --music-mood calm

# 禁用智能音乐
python generate.py --text "你的视频内容" --no-music
```

### 配置说明

```yaml
music:
  enabled: true          # 启用智能音乐功能
  auto_select: true      # 自动选择背景音乐
  copyright_only: true   # 只使用无版权音乐

  # OpenAI配置 (必需)
  openai:
    api_key: ${OPENAI_API_KEY}
    model: "gpt-4"

  # 可选音乐源API (增强功能)
  sources:
    pixabay:
      api_key_env: "PIXABAY_API_KEY"
    freesound:
      api_key_env: "FREESOUND_API_KEY"
```

### API密钥设置

```bash
# 必需：OpenAI API (用于内容分析)
export OPENAI_API_KEY="your-openai-api-key"

# 可选：扩展音乐源
export PIXABAY_API_KEY="your-pixabay-api-key"
export FREESOUND_API_KEY="your-freesound-api-key"
```

### 详细文档

📖 [智能背景音乐功能完整指南](MUSIC_FEATURE_README.md)

## 🚀 性能优化

### 多线程并行处理

系统支持智能的多线程视频生成：

- **自动资源检测**: 根据CPU核心数和内存自动调整线程数
- **内存感知调度**: 防止内存溢出，确保系统稳定
- **性能监控**: 实时统计处理速度和资源使用
- **优雅降级**: 在资源不足时自动调整处理策略

### GPU加速支持

支持多种GPU后端加速视频处理：

**NVIDIA GPU (CUDA)**
- 自动检测 CUDA GPU 可用性
- 支持硬件编码 (h264_nvenc)
- 智能GPU内存管理
- 适用于 GTX 10系列及更新显卡

**Apple Silicon (MPS)**
- 支持 M1/M2/M3/M4 系列芯片
- 自动识别芯片型号和GPU核心数
- 使用 VideoToolbox 硬件编码
- 统一内存架构，高效资源利用
- M4 基础版: 10核GPU
- M4 Pro: 20核GPU
- M4 Max: 40核GPU

**通用特性**
- **自动检测**: 启动时自动检测最佳GPU后端
- **智能回退**: GPU不可用时自动使用CPU处理
- **内存管理**: 智能GPU内存分配和释放
- **性能提升**: 视频特效和渲染速度显著提升

### 配置性能参数

在 `config/default_config.yaml` 中调整性能设置：

```yaml
performance:
  threading:
    enabled: true          # 启用多线程
    max_workers: auto      # 自动/手动设置线程数
    task_timeout: 3600     # 任务超时时间

  gpu:
    enabled: true          # 启用GPU加速
    device: auto           # 自动选择GPU设备
    backend_priority:      # GPU后端优先级
      - cuda              # NVIDIA GPU优先
      - mps               # Apple Silicon次之
      - cpu               # CPU回退
    memory_limit: 0.8      # GPU内存使用比例
```

### 性能基准测试

运行内置基准测试评估系统性能：

```bash
# 快速测试 (推荐)
python scripts/performance_benchmark.py --quick

# 完整基准测试
python scripts/performance_benchmark.py
```

### 性能提升预期

- **多线程处理**: 批量视频生成速度提升 3-5倍
- **GPU加速**: 视频渲染速度提升 5-10倍
- **智能调度**: 充分利用系统资源，减少等待时间

## 📊 系统要求

### 基础配置
- Python 3.8+
- 4GB+ RAM
- FFmpeg

### 推荐配置 (最佳性能)
- Python 3.8+
- 8GB+ RAM
- 多核CPU (4核心+)
- GPU加速 (推荐以下之一):
  - NVIDIA GPU (GTX 10系列或更新) with CUDA 11.0+
  - Apple Silicon (M1/M2/M3/M4)
- 16GB+ 系统内存

### GPU支持
**NVIDIA GPU**
- CUDA 11.0+
- PyTorch 2.0+
- GTX 10系列或更新显卡

**Apple Silicon**
- macOS 12.0+
- PyTorch 2.0+ (支持MPS)
- M1/M2/M3/M4 系列芯片
- 推荐 16GB+ 统一内存
- 作者: peterfei <peterfeispace@gmail.com>

## 工作流程

1. **内容准备**: 从脚本、素材库或AI生成内容
2. **音频生成**:
   - 智能分句：将脚本按句子分割
   - 分段TTS：为每个句子单独生成音频并测量时长
   - 音频拼接：无缝拼接所有音频片段
   - 背景音乐：混合背景音乐，自动调节音量
3. **字幕制作**: 使用实际音频时长生成精确同步的字幕
4. **视频合成**: 整合视频画面（带转场动画）、音频、字幕
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
- [x] 核心模块实现
- [x] TTS集成（Edge TTS，支持分段生成）
- [x] 字幕系统（精确同步技术）
- [x] 视频合成引擎（转场动画）
- [x] 批量处理系统
- [ ] Web UI (可选)
- [ ] 更多视频模板
- [ ] 性能优化（GPU加速）

## 许可证

MIT License

作者: peterfei <peterfeispace@gmail.com>
