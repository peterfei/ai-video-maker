# 视频生成工厂 - 使用指南

## 快速开始

### 1. 安装依赖

```bash
cd video-factory
pip install -r requirements.txt
```

### 2. 基本使用

#### 生成单个视频

```bash
# 使用脚本文件
python src/main.py --script examples/sample_script.txt --materials data/materials

# 直接使用文本
python src/main.py --text "这是我的视频脚本内容" --output output/my_video.mp4

# 指定标题和输出路径
python src/main.py \
  --script examples/sample_script.txt \
  --title "Python入门教程" \
  --output output/python_tutorial.mp4
```

#### 批量生成视频

```bash
# 批量处理目录中的所有脚本
python src/main.py --batch data/scripts
```

### 3. 准备素材

将图片或视频素材放入素材目录：

```bash
data/materials/
├── image1.jpg
├── image2.png
├── nature_mountain.jpg  # 使用下划线命名可自动提取标签
└── tech_coding.png
```

素材文件命名建议：
- 使用描述性名称
- 用下划线分隔关键词，如 `nature_mountain_sunset.jpg`
- 系统会自动提取标签用于智能匹配

### 4. 编写脚本

#### 简单脚本

创建 `.txt` 文件，直接写入文本：

```text
这是第一段内容。

这是第二段内容。
可以分多行。

这是第三段内容。
```

#### 高级脚本格式

使用特殊标记控制视频生成：

```text
#scene:intro# 这是开场片段

[00:15] 这段内容将在第15秒显示

@duration=5@ 这段内容显示5秒

#scene:main# 这是主要内容
普通文本内容...

#scene:conclusion# 这是结尾部分
感谢观看！
```

**支持的标记：**
- `#scene:名称#` - 场景标记
- `[MM:SS]` - 时间标记
- `@key=value@` - 自定义元数据

## 配置说明

### 修改配置文件

编辑 `config/default_config.yaml` 来自定义设置：

```yaml
# 视频分辨率
video:
  resolution: [1920, 1080]  # 1080p
  fps: 30

# TTS语音设置
tts:
  engine: "edge-tts"
  voice: "zh-CN-XiaoxiaoNeural"  # 女声
  rate: 1.0  # 语速

# 字幕样式
subtitle:
  font_size: 48
  font_color: "white"
  position: "bottom"

# 背景音乐
music:
  enabled: true
  volume: 0.2  # 音乐音量
```

### 可用的TTS语音

Edge TTS 中文语音：
- `zh-CN-XiaoxiaoNeural` - 女声（晓晓）
- `zh-CN-YunxiNeural` - 男声（云希）
- `zh-CN-YunyangNeural` - 男声（云扬）
- `zh-CN-XiaoyiNeural` - 女声（晓伊）

## 高级功能

### 1. 自定义视频模板

在配置文件中定义自己的模板：

```yaml
templates:
  my_template:
    type: "image_slideshow"
    transition: "fade"
    transition_duration: 1.0
    image_duration: 6.0
```

### 2. 添加背景音乐

将音乐文件放入 `assets/music/` 目录：

```bash
assets/music/
├── default.mp3
├── upbeat.mp3
└── calm.mp3
```

在配置中指定：

```yaml
music:
  default_track: "assets/music/calm.mp3"
  volume: 0.25
```

### 3. 批量处理配置

```yaml
batch:
  max_workers: 2  # 并行任务数
  retry_on_error: true
  retry_times: 3
```

### 4. 使用 Python API

```python
from src.main import VideoFactory

# 创建工厂实例
factory = VideoFactory("config/default_config.yaml")

# 生成视频
result = factory.generate_video(
    script_path="examples/sample_script.txt",
    materials_dir="data/materials",
    title="我的视频"
)

if result['success']:
    print(f"视频已生成: {result['output_path']}")
```

## 常见问题

### Q: 视频生成失败，提示找不到字体？

A: 在 macOS 上，修改配置文件中的字体设置：

```yaml
subtitle:
  font_name: "STHeiti Medium"  # macOS 中文字体
```

常用字体：
- macOS: `STHeiti Medium`, `PingFang SC`
- Windows: `Microsoft YaHei`, `SimHei`
- Linux: `WenQuanYi Zen Hei`, `Noto Sans CJK SC`

### Q: TTS 生成速度很慢？

A: Edge TTS 需要网络连接。如果网络不稳定，可以：
1. 使用本地 TTS 引擎 `pyttsx3`
2. 预先生成音频文件后重复使用

### Q: 如何调整视频质量？

A: 在配置文件中设置：

```yaml
export:
  quality: "high"  # ultra, high, medium, low
  bitrate: "8000k"  # 更高的比特率
```

### Q: 批量生成时某些任务失败了怎么办？

A: 查看错误日志：

```bash
# 日志保存在
output/logs/error_<task_id>_<timestamp>.log
```

可以重试失败的任务：

```python
from src.tasks import TaskQueue, BatchProcessor

queue = TaskQueue("output/task_queue.json")
processor = BatchProcessor(queue, config)
processor.retry_failed_tasks()
```

## 性能优化建议

1. **并行处理**: 设置合适的 `max_workers` 值
2. **素材预处理**: 提前调整图片大小到目标分辨率
3. **音频缓存**: 相同文本的语音可以重复使用
4. **质量设置**: 开发测试时使用低质量，最终输出时使用高质量

## 进阶示例

### 示例1: 创建系列教程视频

```bash
# 准备多个脚本文件
data/scripts/
├── lesson01.txt
├── lesson02.txt
└── lesson03.txt

# 批量生成
python src/main.py --batch data/scripts
```

### 示例2: 自定义处理流程

```python
from src.main import VideoFactory
from src.tasks import VideoTask, TaskQueue
import uuid

factory = VideoFactory()
queue = TaskQueue("my_tasks.json")

# 创建多个任务
for i in range(5):
    task = VideoTask(
        task_id=str(uuid.uuid4()),
        script_text=f"这是第{i+1}个视频的内容",
        output_path=f"output/video_{i+1}.mp4"
    )
    queue.add_task(task)

# 处理任务
from src.tasks import BatchProcessor
processor = BatchProcessor(queue, factory.config.get('batch', {}), factory.generate_from_task)
processor.process_all_pending()
```

## 输出文件说明

生成的文件结构：

```
output/
├── video_20240103_143022.mp4  # 最终视频
├── temp/                        # 临时文件（可删除）
│   ├── voice_abc123.mp3
│   └── final_audio_def456.mp3
├── logs/                        # 日志文件
│   └── error_task123_20240103_143022.log
└── task_queue.json             # 任务队列状态
```

## 技巧与最佳实践

1. **脚本编写**
   - 每段文本不要太长（建议50字以内）
   - 使用简单句，避免复杂的长句
   - 段落之间留空行

2. **素材选择**
   - 图片分辨率至少 1920x1080
   - 图片风格保持一致
   - 使用高质量图片

3. **语音优化**
   - 调整语速（rate: 0.9-1.2 较合适）
   - 选择合适的音色
   - 测试不同语音效果

4. **字幕设置**
   - 字体大小根据分辨率调整
   - 确保字幕可读性（颜色对比）
   - 位置不要遮挡重要内容

## 获取帮助

- 查看日志文件了解错误详情
- 检查配置文件格式是否正确
- 确保所有依赖正确安装
- 参考 `examples/` 目录中的示例

祝你使用愉快！
