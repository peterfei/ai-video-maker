# 自动素材获取功能使用指南

## 功能概述

当 `data/materials` 目录为空或未指定素材目录时，系统会自动从 Unsplash 和 Pexels API 获取与视频内容匹配的素材图片。

## 特性

✅ **智能内容匹配**：根据脚本文本自动提取关键词并搜索相关图片
✅ **多源图库支持**：同时支持 Unsplash 和 Pexels 两个免费图库
✅ **自动下载缓存**：下载的素材会自动保存到本地库，避免重复下载
✅ **语义分析**：支持中文关键词到英文搜索词的智能映射
✅ **无缝集成**：当本地目录为空时自动触发，无需额外操作

## 配置步骤

### 1. 获取API密钥

#### Unsplash API
1. 访问 [Unsplash Developers](https://unsplash.com/developers)
2. 创建应用获取 Access Key

#### Pexels API
1. 访问 [Pexels API](https://www.pexels.com/api/)
2. 注册并获取 API Key

### 2. 配置环境变量

在项目根目录的 `.env` 文件中添加：

```bash
# Unsplash API
UNSPLASH_ACCESS_KEY=your_unsplash_access_key_here

# Pexels API
PEXELS_API_KEY=your_pexels_api_key_here
```

### 3. 配置文件设置

在 `config/default_config.yaml` 中启用自动素材功能：

```yaml
auto_materials:
  enabled: true                    # 启用自动素材管理器
  local_priority: true             # 优先使用本地素材
  auto_download: true              # 自动从API下载
  build_library: true              # 构建素材库索引
  materials_per_segment: 1         # 每个片段的素材数量
  library_path: data/material_library  # 素材库路径

  # API密钥（从环境变量读取）
  unsplash_key: ${UNSPLASH_ACCESS_KEY}
  pexels_key: ${PEXELS_API_KEY}

  # 语义匹配配置
  semantic:
    use_ai: false                  # 是否使用AI提取关键词（需要OpenAI API）
    api_key: ${OPENAI_API_KEY}
    model: gpt-3.5-turbo
```

## 使用示例

### 示例1：空目录自动获取

```bash
# data/materials 目录为空
python3 src/main.py --script data/scripts/nature_video.txt --materials data/materials

# 系统会自动检测目录为空，从API获取与脚本内容匹配的素材
```

### 示例2：未指定素材目录

```bash
# 不指定 --materials 参数
python3 src/main.py --script data/scripts/tech_video.txt

# 如果启用了 auto_materials，系统会自动获取素材
```

### 示例3：使用智能背景音乐功能时

```bash
python3 src/main.py \\
    --script data/scripts/complex_benchmark.txt \\
    --materials data/materials \\
    --auto-music

# 即使 data/materials 为空，也会自动获取素材
```

## 工作流程

```
1. 检查素材目录
   ↓
2. 如果目录为空 → 启动自动素材管理器
   ↓
3. 分析脚本内容
   ├─ 提取关键词（如：山、森林、日落）
   └─ 映射为英文搜索词（mountain, forest, sunset）
   ↓
4. 从本地素材库搜索
   ├─ 找到匹配 → 使用本地素材
   └─ 未找到 → 继续下一步
   ↓
5. 从在线图库搜索
   ├─ Unsplash API
   └─ Pexels API
   ↓
6. 下载图片到缓存目录
   ↓
7. 添加到素材库并建立索引
   ↓
8. 返回素材路径用于视频生成
```

## 关键词映射示例

系统内置了中文到英文的关键词映射：

| 中文关键词 | 英文搜索词 |
|-----------|-----------|
| 山 | mountain, nature, landscape |
| 海 | ocean, sea, water, beach |
| 森林 | forest, tree, nature, woods |
| 城市 | city, urban, building, street |
| 科技 | technology, innovation, digital |
| 办公 | office, business, work |
| 学习 | learning, education, study |
| 成功 | success, achievement, growth |

## 素材库结构

```
data/
├── image_cache/              # API下载的原始图片
│   ├── mountain_abc123.jpg
│   └── forest_def456.jpg
│
└── material_library/         # 分类整理的素材库
    ├── index.json           # 关键词索引
    ├── mountain/            # 按关键词分类
    ├── forest/
    └── city/
```

## 注意事项

### API配额限制

- **Unsplash**：
  - 免费版：50 requests/hour
  - 建议使用缓存避免重复请求

- **Pexels**：
  - 免费版：200 requests/hour
  - 较宽松的使用限制

### 最佳实践

1. **复用素材库**：下载的素材会自动保存，下次可直接使用
2. **关键词优化**：如果搜索结果不理想，可以在配置中添加自定义关键词映射
3. **混合使用**：可以预先准备一些通用素材在 `data/materials`，系统会优先使用
4. **监控日志**：观察日志输出了解素材获取过程

### 故障排查

**问题：未能获取素材**
```bash
# 检查API密钥是否正确配置
cat .env | grep -E 'UNSPLASH|PEXELS'

# 检查网络连接
curl -I https://api.unsplash.com
curl -I https://api.pexels.com
```

**问题：搜索结果不相关**
- 检查脚本内容是否包含明确的视觉化关键词
- 考虑启用 AI 关键词提取（需要 OpenAI API）
- 手动添加关键词映射到配置文件

**问题：API配额耗尽**
- 使用本地素材库
- 等待配额重置（通常按小时计）
- 考虑升级到付费计划

## 测试功能

运行测试脚本验证配置：

```bash
python3 test_auto_materials.py
```

预期输出：
```
============================================================
测试自动素材获取功能
============================================================

配置检查:
  Unsplash API Key: ✓ 已配置
  Pexels API Key: ✓ 已配置
  自动下载: ✓ 启用

开始获取素材...
------------------------------------------------------------
✓ 成功获取 2 个素材

素材列表:
  1. mountain_acc2faa4.jpg
  2. forest_e34e9a2e.jpg
```

## 高级功能

### 使用AI提取关键词

启用 OpenAI 进行更智能的关键词提取：

```yaml
auto_materials:
  semantic:
    use_ai: true
    api_key: ${OPENAI_API_KEY}
    model: gpt-3.5-turbo
```

### 自定义关键词映射

在 `src/content_sources/semantic_matcher.py` 中添加自定义映射：

```python
self.keyword_mappings = {
    '你的关键词': ['english', 'keywords', 'here'],
    # ...
}
```

## 总结

自动素材获取功能让视频生成更加便捷：
- ✅ 无需手动准备素材
- ✅ 智能匹配内容
- ✅ 自动构建素材库
- ✅ 提高制作效率

第一次运行可能需要几秒钟下载素材，后续使用会从本地库快速加载。
