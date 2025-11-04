# AI Video Maker

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![MoviePy](https://img.shields.io/badge/MoviePy-1.0+-green.svg)](https://zulko.github.io/moviepy/)

An automated video generation system that transforms text scripts into complete videos with AI-powered material search, voice synthesis, and intelligent subtitling.

**Author**: peterfei <peterfeispace@gmail.com>

## 🚀 Key Features

- **🤖 AI-Powered Material Search**: Automatically finds and downloads relevant images from free stock photo APIs (Unsplash, Pexels)
- **🎤 Intelligent Voice Synthesis**: Text-to-speech with multiple voices and languages
- **📝 Smart Subtitling**: Automatic subtitle generation synchronized with audio
- **🎬 Video Composition**: Professional video creation with transitions and effects
- **🎵 Background Music**: Intelligent music mixing and volume control
- **⚡ Batch Processing**: Queue-based batch video generation
- **🔧 Highly Configurable**: Flexible YAML configuration system

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Usage](#-usage)
- [Configuration](#-configuration)
- [Project Structure](#-project-structure)
- [Technical Stack](#-technical-stack)
- [Contributing](#-contributing)
- [License](#-license)

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Clone the repository
git clone https://github.com/peterfei/ai-video-maker.git
cd ai-video-maker

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Generate Your First Video

```bash
# Generate video from sample script
python src/main.py --script examples/sample_script.txt

# Or generate from text directly
python src/main.py --text "Hello world! This is my first AI-generated video."
```

Your video will be saved in the `output/` directory!

## 📦 Installation

### System Requirements

- Python 3.8 or higher
- FFmpeg (automatically installed with MoviePy)
- Internet connection (for TTS and image APIs)

### Dependencies

```bash
pip install -r requirements.txt
```

Key dependencies:
- `moviepy` - Video processing and composition
- `edge-tts` - Microsoft Edge TTS for voice synthesis
- `Pillow` - Image processing
- `requests` - HTTP client for image APIs
- `PyYAML` - Configuration management

## 🎯 Usage

### Basic Usage

```bash
# Generate video from text file
python src/main.py --script path/to/your/script.txt

# Generate video from text string
python src/main.py --text "Your video content here"

# Batch processing
python src/main.py --batch data/scripts/
```

### Advanced Usage

```bash
# Custom output path and title
python src/main.py \
  --script examples/sample_script.txt \
  --output my_video.mp4 \
  --title "My Custom Video"

# Use custom configuration
python src/main.py \
  --script examples/sample_script.txt \
  --config my_config.yaml

# Enable AI material search (requires API keys)
python src/main.py \
  --script examples/auto_material_demo.txt \
  --auto-materials
```

### Script Format

Create text files with your video content:

```
[SCENE: introduction]
Welcome to my tutorial video!

[SCENE: main_content]
Today we'll learn about Python programming.

First, let's install Python from python.org

Then, create your first "Hello World" program:
print("Hello, World!")

[SCENE: conclusion]
Thanks for watching! Don't forget to subscribe.
```

## ⚙️ Configuration

The system uses YAML configuration files. Copy and modify `config/default_config.yaml`:

```yaml
# Video settings
video:
  resolution: [1920, 1080]
  fps: 30
  duration: auto

# TTS settings
tts:
  engine: edge-tts
  voice: zh-CN-XiaoxiaoNeural
  rate: 1.0

# Subtitle settings
subtitle:
  font_size: 48
  font_color: white
  position: bottom

# Auto material search
auto_materials:
  enabled: true
  local_priority: true
  unsplash_key: "your_unsplash_key"
  pexels_key: "your_pexels_key"
```

### API Keys Setup

For AI material search, get API keys from:
- [Unsplash API](https://unsplash.com/developers)
- [Pexels API](https://www.pexels.com/api/)

Add keys to `config/default_config.yaml` or set as environment variables.

## 🏗️ Project Structure

```
ai-video-factory/
├── src/                          # Source code
│   ├── content_sources/          # Content source management
│   │   ├── text_source.py       # Text/script processing
│   │   ├── material_source.py   # Material library management
│   │   ├── ai_source.py         # AI content generation
│   │   ├── image_api.py         # Free image API integration
│   │   ├── semantic_matcher.py  # AI semantic matching
│   │   └── auto_material_manager.py # Auto material management
│   ├── audio/                    # Audio processing
│   │   ├── tts_engine.py        # TTS engine
│   │   └── audio_mixer.py       # Audio mixing
│   ├── subtitle/                 # Subtitle system
│   │   ├── subtitle_gen.py      # Subtitle generation
│   │   └── subtitle_render.py   # Subtitle rendering
│   ├── video_engine/             # Video synthesis engine
│   │   ├── compositor.py        # Video compositor
│   │   └── effects.py           # Video effects
│   ├── tasks/                    # Task management
│   │   ├── task_queue.py        # Task queue
│   │   └── batch_processor.py   # Batch processor
│   ├── config_loader.py          # Configuration loader
│   ├── utils.py                  # Utilities
│   └── main.py                   # Main entry point
├── config/                       # Configuration files
│   └── default_config.yaml      # Default configuration
├── examples/                     # Example files
│   ├── sample_script.txt
│   ├── advanced_script.txt
│   └── usage.md
├── data/                         # Data directory
│   ├── scripts/                  # Text scripts
│   ├── materials/                # Material files
│   ├── material_library/         # Auto-downloaded materials
│   └── image_cache/              # Image cache
├── output/                       # Generated videos
├── assets/                       # Static assets
│   ├── music/                    # Background music
│   ├── fonts/                    # Fonts
│   └── templates/                # Video templates
├── tests/                        # Test files
├── requirements.txt              # Python dependencies
├── generate.py                   # Simple generation script
├── test_system.py                # System testing
└── README.md                     # This file
```

## 🛠️ Technical Stack

### Core Technologies

- **Video Processing**: MoviePy + FFmpeg
- **Voice Synthesis**: Edge TTS / pyttsx3 / Azure TTS
- **Image Processing**: Pillow (PIL)
- **Configuration**: PyYAML
- **Task Management**: Python Queue / Celery (optional)

### AI Integration

- **Image APIs**: Unsplash API, Pexels API
- **Semantic Matching**: Rule-based + OpenAI GPT (optional)
- **Content Generation**: OpenAI API (optional)

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/

# Format code
black src/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [MoviePy](https://zulko.github.io/moviepy/) for video processing
- [Microsoft Edge TTS](https://speech.microsoft.com/) for voice synthesis
- [Unsplash](https://unsplash.com/) and [Pexels](https://www.pexels.com/) for free images
- [OpenAI](https://openai.com/) for AI capabilities

## 📞 Support

- Issues: [GitHub Issues](https://github.com/peterfei/ai-video-maker/issues)
- Documentation: [Wiki](https://github.com/peterfei/ai-video-maker/wiki)
- Discussions: [GitHub Discussions](https://github.com/peterfei/ai-video-maker/discussions)

---

**Made with ❤️ for automated video creation**
