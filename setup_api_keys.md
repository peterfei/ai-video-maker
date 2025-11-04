# 获取免费图库API密钥

## 🌅 Unsplash API (推荐)

### 步骤：

1. **注册账号**
   - 访问: https://unsplash.com/developers
   - 点击 "Register as a developer"

2. **创建应用**
   - 登录后点击 "New Application"
   - 同意条款
   - 填写应用信息：
     - Application name: `Video Factory`
     - Description: `Automatic video generation`

3. **获取密钥**
   - 创建成功后会看到 `Access Key`
   - 复制这个密钥

4. **配置到系统**
   ```bash
   export UNSPLASH_ACCESS_KEY="你的Access_Key"
   ```

### 配额限制
- 免费版: 50次请求/小时
- 足够日常使用

---

## 📷 Pexels API (备用)

### 步骤：

1. **注册账号**
   - 访问: https://www.pexels.com/api/
   - 点击 "Get Started"

2. **获取密钥**
   - 登录后直接在页面上获取 API Key
   - 无需创建应用

3. **配置到系统**
   ```bash
   export PEXELS_API_KEY="你的API_Key"
   ```

### 配额限制
- 免费版: 200次请求/小时
- 更高的配额

---

## ⚡ 快速配置

### 方法1: 临时环境变量 (推荐测试)

```bash
# 在当前终端窗口设置
export UNSPLASH_ACCESS_KEY="你的密钥"
export PEXELS_API_KEY="你的密钥"

# 然后运行视频生成
python3 generate.py --script examples/auto_material_demo.txt
```

### 方法2: 永久配置 (推荐生产)

编辑 ~/.zshrc 或 ~/.bash_profile：

```bash
# 在文件末尾添加
export UNSPLASH_ACCESS_KEY="你的密钥"
export PEXELS_API_KEY="你的密钥"

# 然后重新加载
source ~/.zshrc
```

### 方法3: 直接在配置文件中

编辑 `config/default_config.yaml`:

```yaml
auto_materials:
  unsplash_key: "你的实际密钥"  # 不使用环境变量
  pexels_key: "你的实际密钥"
```

---

## 🎯 测试配置

配置完成后测试：

```bash
# 测试环境变量
echo $UNSPLASH_ACCESS_KEY

# 生成视频测试
python3 generate.py --script examples/auto_material_demo.txt
```

---

## 💡 提示

1. **只需要一个API密钥就能工作**
   - Unsplash 或 Pexels 任选其一
   - 推荐 Unsplash (图片质量更高)

2. **API密钥是免费的**
   - 无需信用卡
   - 无需付费

3. **图片可商用**
   - Unsplash License: 完全免费商用
   - Pexels License: 完全免费商用

4. **素材库会自动积累**
   - 下载的图片会保存到 `data/material_library`
   - 之后使用会越来越快
   - 减少API调用次数
