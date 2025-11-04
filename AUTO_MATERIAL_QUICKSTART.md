# 自动素材功能 - 3分钟快速入门

## ⚡ 超快上手

### 1️⃣ 启用功能 (30秒)

```bash
# 编辑配置文件
nano config/default_config.yaml

# 找到这一行并改为 true
auto_materials:
  enabled: true  # 改这里！
```

### 2️⃣ 第一次使用 (2分钟)

```bash
# 直接生成视频
python3 generate.py --script examples/sample_script.txt
```

系统会：
- ✓ 自动分析脚本
- ✓ 提取关键词
- ✓ 使用规则匹配（无需API）
- ✓ 生成视频

### 3️⃣ 进阶：获取免费API (可选)

想要更多高质量素材？

**Unsplash** (推荐)
```bash
# 1. 访问 https://unsplash.com/developers
# 2. 注册并创建应用
# 3. 获取 Access Key
export UNSPLASH_ACCESS_KEY="你的密钥"
```

**Pexels** (可选)
```bash
# 1. 访问 https://www.pexels.com/api/
# 2. 注册并获取 API Key
export PEXELS_API_KEY="你的密钥"
```

## 🎯 三种使用模式

### 模式 1: 纯本地（无API密钥）

```yaml
auto_materials:
  enabled: true
  auto_download: false  # 不下载
```

特点：
- ✓ 完全免费
- ✓ 使用本地素材库
- ✓ 规则提取关键词

### 模式 2: 混合模式（推荐）

```yaml
auto_materials:
  enabled: true
  auto_download: true   # 自动下载
  build_library: true   # 构建素材库
```

配置任一API密钥即可。

特点：
- ✓ 优先使用本地
- ✓ 自动在线补充
- ✓ 素材持续积累

### 模式 3: AI增强模式（最佳）

```yaml
auto_materials:
  enabled: true
  semantic:
    use_ai: true  # 启用AI
```

需要OpenAI API密钥。

特点：
- ✓ GPT理解内容
- ✓ 最准确的匹配
- ✓ 最佳效果

## 📝 脚本写法技巧

### 基础写法

```text
这是视频的第一段内容。
这是第二段内容。
```

### 高级写法（推荐）

```text
#scene:tech# 欢迎来到编程世界！

今天我们要学习Python。

#scene:nature# 编程就像探索大自然。

每一行代码都是一次新的发现。
```

场景标记会帮助系统更准确地匹配素材。

## 🎬 完整示例

### 示例脚本 (example.txt)

```text
#scene:tech# 人工智能正在改变世界。

从智能手机到自动驾驶，AI无处不在。

#scene:business# 在商业领域，AI提供强大支持。

数据分析、客户服务、市场预测。

#scene:conclusion# 让我们一起拥抱AI时代！
```

### 运行命令

```bash
python3 generate.py --script example.txt
```

### 自动发生的事情

1. **分析脚本**
   ```
   片段1: "人工智能正在改变世界"
   → 关键词: [technology, AI, innovation]
   ```

2. **查找素材**
   ```
   先查本地 → 没有 → 从Unsplash下载 → 保存到素材库
   ```

3. **生成视频**
   ```
   配音 + 素材 + 字幕 = 完整视频
   ```

## 📚 素材库说明

### 自动构建

```
data/material_library/
├── technology/     # 自动分类
├── nature/
├── business/
└── index.json     # 自动索引
```

### 越用越好

- 第1次: 下载3张图
- 第10次: 已有30张图，速度更快
- 第100次: 素材库非常丰富

## ⚙️ 配置速查

```yaml
auto_materials:
  enabled: true              # 主开关
  local_priority: true       # 优先本地
  auto_download: true        # 自动下载
  build_library: true        # 构建库
  library_path: "data/material_library"

  semantic:
    use_ai: false            # AI模式

  unsplash_key: ""           # Unsplash密钥
  pexels_key: ""             # Pexels密钥

  materials_per_segment: 1   # 每段素材数
```

## 🆘 常见问题

**Q: 没有API密钥可以用吗？**
A: 可以！系统会使用规则匹配和本地素材。

**Q: 素材相关度不高？**
A: 在脚本中使用 #scene:xxx# 标记，或启用AI模式。

**Q: 下载速度慢？**
A: 首次下载需要时间，之后会使用本地缓存。

**Q: API有配额限制吗？**
A: Unsplash: 50次/小时，Pexels: 200次/小时（免费版）

**Q: 图片可以商用吗？**
A: 可以！Unsplash和Pexels的图片都是免费商用。

## 📖 更多信息

- 完整文档: `AUTO_MATERIAL_GUIDE.md`
- 示例脚本: `examples/auto_material_demo.txt`
- 配置文件: `config/default_config.yaml`

## ✅ 检查清单

开始使用前确认：

- [ ] 配置文件中 `enabled: true`
- [ ] (可选) 设置API密钥
- [ ] 准备好视频脚本
- [ ] 运行 `python3 generate.py --script your_script.txt`

就这么简单！🚀

---

**提示**: 第一次可能需要下载素材，之后速度会越来越快！
