# 快速入门指南

5分钟生成你的第一个视频！

## 步骤 1: 环境准备

### macOS / Linux

```bash
cd video-factory

# 使用快速启动脚本
./run.sh
```

### Windows

```bash
cd video-factory

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

## 步骤 2: 生成第一个视频

### 使用示例脚本

```bash
# macOS/Linux
./run.sh --script examples/sample_script.txt

# Windows
python src\main.py --script examples\sample_script.txt
```

视频将生成到 `output/` 目录。

### 使用自己的文本

```bash
python src/main.py --text "大家好，这是我的第一个自动生成的视频！今天我想分享一些有趣的内容。"
```

## 步骤 3: 添加素材（可选）

1. 准备一些图片（JPG、PNG格式）
2. 放入 `data/materials/` 目录
3. 运行命令：

```bash
python src/main.py \
  --script examples/sample_script.txt \
  --materials data/materials
```

## 步骤 4: 批量生成

1. 在 `data/scripts/` 目录创建多个 `.txt` 文件
2. 运行批量处理：

```bash
python src/main.py --batch data/scripts
```

## 常用命令

```bash
# 指定输出路径
python src/main.py --script examples/sample_script.txt --output my_video.mp4

# 设置视频标题
python src/main.py --script examples/sample_script.txt --title "我的教程"

# 使用自定义配置
python src/main.py --script examples/sample_script.txt --config my_config.yaml
```

## 配置调整

编辑 `config/default_config.yaml` 来修改：

- 视频分辨率
- TTS语音
- 字幕样式
- 背景音乐

详细说明请查看 `examples/USAGE.md`

## 故障排除

### 问题: ModuleNotFoundError

**解决**: 确保已安装所有依赖

```bash
pip install -r requirements.txt
```

### 问题: 字体错误

**解决**: 修改 `config/default_config.yaml` 中的字体设置

```yaml
subtitle:
  font_name: "Arial"  # 或其他系统字体
```

### 问题: TTS 失败

**解决**: 检查网络连接，Edge TTS 需要访问微软服务器

## 下一步

- 查看 `examples/USAGE.md` 了解高级功能
- 自定义配置文件来打造独特风格
- 探索更多配置选项和使用模式

祝你使用愉快！
