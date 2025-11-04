# 预置中文字体功能

## 概述

视频生成工厂现已预置高质量的开源中文字体，开箱即用，无需额外安装字体文件。

## 预置字体

### Noto Sans CJK SC Regular
- **文件**: `assets/fonts/NotoSansCJKsc-Regular.otf`
- **来源**: Google Fonts - Noto Sans CJK
- **许可证**: Apache License 2.0
- **特点**:
  - 现代设计，良好的可读性
  - 完整的中文字符支持
  - 适合视频字幕显示
  - 跨平台兼容性良好

## 自动字体选择

系统会按以下优先级自动选择字体：

1. **项目预置字体** (最高优先级)
   - `assets/fonts/NotoSansCJKsc-Regular.otf`

2. **系统字体回退**
   - `Noto Sans CJK SC`
   - `STHeiti Medium` (macOS)
   - `Microsoft YaHei` (Windows)
   - `SimHei` (Windows)
   - 其他系统字体...

## 使用方法

### 自动使用

运行视频生成时，系统会自动使用最佳可用字体：

```bash
python generate.py --script your_script.txt
```

### 手动指定

如需使用特定字体，可以在配置中指定：

```yaml
# config/default_config.yaml
subtitle:
  font_path: "assets/fonts/NotoSansCJKsc-Regular.otf"
```

## 字体管理

### 查看可用字体

```bash
python generate.py --list-fonts
```

### 预览字体效果

```bash
python generate.py --preview-font "assets/fonts/NotoSansCJKsc-Regular.otf"
```

### 测试字体兼容性

```bash
python generate.py --font-manager
# 选择选项 4: 测试字体兼容性
```

## 技术细节

### 字体验证

系统会对预置字体进行以下验证：
- 文件存在性检查
- 字体文件完整性验证
- 中文字符渲染测试
- MoviePy 和 PIL 兼容性测试

### 字体缓存

- 字体检测结果会被缓存以提高性能
- 缓存会在添加新字体时自动清除

## 测试结果

✅ **字体功能测试通过**
- 预置字体自动选择: ✓
- 中文渲染正确: ✓
- 视频生成成功: ✓
- 跨平台兼容: ✓

**测试视频**: `output/预置字体测试_20251104_144702.mp4`

## 许可证说明

预置字体使用开源许可证，允许商业使用：
- Noto Sans CJK: Apache License 2.0

## 故障排除

### 字体未被识别

1. 检查字体文件是否存在：
   ```bash
   ls -la assets/fonts/
   ```

2. 验证字体文件：
   ```bash
   python generate.py --preview-font "assets/fonts/NotoSansCJKsc-Regular.otf"
   ```

### 中文显示异常

1. 检查系统是否支持中文显示
2. 尝试使用系统字体：
   ```yaml
   subtitle:
     font_fallback:
       - "STHeiti Medium"  # macOS
       - "Microsoft YaHei"  # Windows
   ```

## 未来扩展

- 支持更多字体变体 (Bold, Light 等)
- 添加字体子集优化
- 支持用户自定义字体上传
- 字体效果预览界面
