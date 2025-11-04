# 视频生成工厂 - 快速参考指南

## 🚀 快速命令

### 基本生成

```bash
# 使用脚本文件
python3 generate.py --script examples/sample_script.txt

# 使用高级脚本（带标记）
python3 generate.py --script examples/advanced_script.txt

# 直接使用文本
python3 generate.py --text "你的视频内容"

# 指定标题和输出路径
python3 generate.py --script your_script.txt --title "视频标题" --output output/my_video.mp4
```

### 批量生成

```bash
# 批量处理整个目录
python3 generate.py --batch data/scripts
```

### 添加素材

```bash
# 使用图片素材
python3 generate.py --script your_script.txt --materials data/materials
```

## 📝 脚本格式

### 简单格式

```text
这是第一段内容。

这是第二段内容。
可以多行。

这是第三段内容。
```

### 高级格式

```text
#scene:intro# 这是开场

[00:15] 这段在第15秒显示

@topic=教程@ 带元数据的内容

#scene:main# 主要内容
普通文本...

#scene:conclusion# 结束
再见！
```

## 🎨 配置常用修改

### 修改视频分辨率

编辑 `config/default_config.yaml`:

```yaml
video:
  resolution: [1920, 1080]  # 修改为你需要的分辨率
  fps: 30
```

### 更换TTS语音

```yaml
tts:
  engine: "edge-tts"
  voice: "zh-CN-XiaoxiaoNeural"  # 女声-晓晓
  # voice: "zh-CN-YunxiNeural"   # 男声-云希
  # voice: "zh-CN-YunyangNeural" # 男声-云扬
  rate: 1.0  # 语速 (0.5-2.0)
```

### 调整字幕样式

```yaml
subtitle:
  font_size: 48
  font_color: "white"
  stroke_color: "black"
  stroke_width: 2
  position: "bottom"  # top, center, bottom
```

### 添加背景音乐

```yaml
music:
  enabled: true
  volume: 0.2
  default_track: "assets/music/default.mp3"
```

## 📁 目录结构

```
video-factory/
├── examples/          # 示例脚本
│   ├── sample_script.txt
│   └── advanced_script.txt
├── data/
│   ├── scripts/      # 放你的脚本文件
│   └── materials/    # 放图片素材
├── assets/
│   ├── music/        # 放背景音乐
│   └── fonts/        # 放字体文件
├── output/           # 生成的视频输出
└── config/           # 配置文件
```

## 💡 使用技巧

### 1. 准备素材

```bash
# 创建素材目录
mkdir -p data/materials

# 添加图片（JPG、PNG）
# 文件名使用下划线分隔关键词
cp ~/Pictures/nature_mountain.jpg data/materials/
cp ~/Pictures/tech_coding.png data/materials/
```

### 2. 添加背景音乐

```bash
# 添加音乐文件
mkdir -p assets/music
cp ~/Music/background.mp3 assets/music/default.mp3
```

### 3. 批量生成

```bash
# 准备多个脚本
mkdir -p data/scripts
echo "视频1的内容" > data/scripts/video1.txt
echo "视频2的内容" > data/scripts/video2.txt

# 批量生成
python3 generate.py --batch data/scripts
```

## 🔧 常见问题

### Q: 字体错误？

修改配置文件中的字体：

```yaml
subtitle:
  font_name: "Arial"  # 或其他系统字体
```

### Q: TTS速度慢？

检查网络连接，Edge TTS需要访问微软服务器。

### Q: 视频质量不满意？

调整导出质量：

```yaml
export:
  quality: "ultra"  # ultra, high, medium, low
  bitrate: "8000k"
```

### Q: 如何查看生成的视频？

```bash
# macOS
open output/your_video.mp4

# Linux
xdg-open output/your_video.mp4

# 或直接在文件管理器中打开
```

## 📊 生成统计

已成功生成视频：

1. **Python入门教程** (1.4M, 77秒)
2. **高级脚本示例** (1.0M, 57秒)

## 🎯 下一步

1. **尝试添加图片素材**
   - 将图片放入 `data/materials/`
   - 重新生成视频

2. **自定义字幕样式**
   - 修改字体大小、颜色
   - 调整位置

3. **批量生成视频**
   - 准备多个脚本
   - 一次性生成所有视频

4. **探索更多功能**
   - 查看 `examples/USAGE.md`
   - 阅读 `ARCHITECTURE.md`

## 📚 文档索引

- `README.md` - 项目概述
- `QUICKSTART.md` - 快速入门
- `examples/USAGE.md` - 详细使用指南
- `ARCHITECTURE.md` - 系统架构
- `config/default_config.yaml` - 完整配置

---

**提示**: 使用 `--help` 查看所有命令选项

```bash
python3 generate.py --help
```
