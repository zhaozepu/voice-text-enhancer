# Voice Text Enhancer.app 使用指南

> macOS 应用版本 - 双击启动，无需终端

---

## 🎉 恭喜！应用已打包成功

应用位置：`dist/VoiceTextEnhancer.app`

---

## 📦 安装步骤

### 1. 移动应用到 Applications

```bash
cp -r dist/VoiceTextEnhancer.app /Applications/
```

或者：
- 在 Finder 中打开 `dist` 文件夹
- 拖动 `VoiceTextEnhancer.app` 到"应用程序"文件夹

### 2. 首次配置

应用会自动在 `~/.voice-text-enhancer/` 创建配置文件。

#### 配置 API Key

```bash
# 编辑环境变量文件
nano ~/.voice-text-enhancer/.env
```

添加你的 DeepSeek API Key：
```
DEEPSEEK_API_KEY=sk-你的API密钥
```

保存并退出（Ctrl+X → Y → Enter）

#### 自定义配置（可选）

```bash
# 编辑配置文件
nano ~/.voice-text-enhancer/config.yaml
```

可以修改：
- 快捷键（默认：右 Option 键）
- 处理模式（默认：typeless 智能结构化）
- 其他选项

### 3. 授予系统权限

⚠️ **必须步骤** - 否则应用无法工作

#### 授予"辅助功能"权限

1. 打开"**系统设置**"
2. 点击"**隐私与安全性**"
3. 选择左侧"**辅助功能**"
4. 点击右下角 **+** 号
5. 找到并添加"**VoiceTextEnhancer**"
6. 确保开关打开 ✓

#### 授予"输入监控"权限

1. 在"隐私与安全性"中
2. 选择左侧"**输入监控**"
3. 同样添加"**VoiceTextEnhancer**"
4. 确保开关打开 ✓

**注意：** 授予权限后，必须完全退出应用并重新启动！

---

## 🚀 使用方法

### 启动应用

**方式一：双击启动**
- 在"应用程序"文件夹中双击 `VoiceTextEnhancer.app`
- 或在 Spotlight 中搜索"VoiceTextEnhancer"

**方式二：自动启动（可选）**
- 系统设置 > 通用 > 登录项
- 添加 VoiceTextEnhancer.app
- 开机自动启动

### 使用流程

```
1. 启动应用（双击或自动启动）
       ↓
2. 应用在后台运行（不显示窗口）
       ↓
3. 在任意输入框输入文本
       ↓
4. 轻按右 Option 键 ⌥
       ↓
5. 自动优化并替换 ✓
```

### 实际示例

1. **打开微信/钉钉/备忘录**
2. **输入文本**（豆包语音或手动）：
   ```
   今天要做三件事第一写文档第二开会第三写代码
   ```
3. **轻按右 Option 键**
4. **自动变成**：
   ```
   今天要做三件事：
   
   1. 写文档
   2. 开会
   3. 写代码
   ```

---

## 🔧 管理应用

### 查看是否运行

```bash
# 查看进程
ps aux | grep VoiceTextEnhancer
```

### 退出应用

应用在后台运行，没有窗口界面。

**退出方法：**
1. 打开"活动监视器"（在"实用工具"中）
2. 搜索"VoiceTextEnhancer"
3. 选中并点击"退出"

或使用命令行：
```bash
pkill -f VoiceTextEnhancer
```

### 查看日志

```bash
# 实时查看
tail -f ~/.voice-text-enhancer/app.log

# 查看最近日志
tail -n 100 ~/.voice-text-enhancer/app.log
```

### 修改配置

```bash
# 编辑配置文件
nano ~/.voice-text-enhancer/config.yaml

# 编辑 API Key
nano ~/.voice-text-enhancer/.env
```

修改后，需要重启应用才能生效。

---

## 🎨 功能特点

### 应用版本优势

✅ **双击启动** - 不需要打开终端  
✅ **后台运行** - 不显示窗口，不占用 Dock  
✅ **开机自启** - 可设置自动启动  
✅ **独立配置** - 配置文件在用户目录  

### 核心功能

✅ **智能结构化** - 自动识别文本类型并格式化  
✅ **语法纠错** - 自动修正错别字和标点  
✅ **表达优化** - 口语转书面语  
✅ **剪贴板保护** - 不影响正常复制粘贴  
✅ **实时提示** - 动态进度通知  

---

## 🐛 故障排除

### 问题 1: 应用无法打开

**错误提示："无法验证开发者"**

**解决方法：**
1. 打开"系统设置" > "隐私与安全性"
2. 找到"仍要打开"按钮
3. 点击"打开"确认

或使用命令行：
```bash
xattr -cr /Applications/VoiceTextEnhancer.app
```

### 问题 2: 快捷键无反应

**可能原因：**
- 权限未授予
- 应用未运行

**解决方法：**
1. 检查应用是否在运行：
   ```bash
   ps aux | grep VoiceTextEnhancer
   ```

2. 检查权限是否授予（看上面"授予系统权限"）

3. 完全重启应用：
   ```bash
   pkill -f VoiceTextEnhancer
   open /Applications/VoiceTextEnhancer.app
   ```

### 问题 3: 找不到配置文件

**解决方法：**
```bash
# 手动创建配置
mkdir -p ~/.voice-text-enhancer
cd /Users/tal/Code/voice-text-enhancer
cp config.example.yaml ~/.voice-text-enhancer/config.yaml
cp .env.example ~/.voice-text-enhancer/.env

# 编辑 API Key
nano ~/.voice-text-enhancer/.env
```

### 问题 4: API 调用失败

**检查 API Key：**
```bash
cat ~/.voice-text-enhancer/.env | grep DEEPSEEK_API_KEY
```

确保格式正确：
```
DEEPSEEK_API_KEY=sk-你的实际密钥
```

---

## 📱 快捷键配置

### 修改快捷键

编辑配置文件：
```bash
nano ~/.voice-text-enhancer/config.yaml
```

修改这一行：
```yaml
hotkey:
  trigger: "right_option"  # 改成你想要的
```

**可选快捷键：**
- `right_option` - 右 Option 键（默认）
- `left_option` - 左 Option 键
- `right_cmd` - 右 Command 键
- `<cmd>+<alt>+space` - Cmd+Option+空格（组合键）

### 切换处理模式

```yaml
active_prompt: "typeless"  # 智能结构化（推荐）
# active_prompt: "correct"   # 仅纠错
# active_prompt: "optimize"  # 纠错+优化
```

---

## 🔄 更新应用

1. 获取最新代码
2. 重新打包：
   ```bash
   cd /Users/tal/Code/voice-text-enhancer
   ./build_app.sh
   ```
3. 覆盖旧应用：
   ```bash
   rm -rf /Applications/VoiceTextEnhancer.app
   cp -r dist/VoiceTextEnhancer.app /Applications/
   ```

---

## 📋 完整安装清单

- [ ] 应用已移动到 /Applications
- [ ] API Key 已配置（~/.voice-text-enhancer/.env）
- [ ] 辅助功能权限已授予 ✓
- [ ] 输入监控权限已授予 ✓
- [ ] 应用已启动
- [ ] 快捷键测试通过

---

## 💡 使用技巧

### 1. 豆包输入法完美搭配

```
按 Fn 语音输入 → 松开 Fn → 轻按右 Option → 自动优化
```

### 2. 会议记录快速整理

语音输入会议内容 → 按右 Option → 自动结构化为标题+列表

### 3. 批量文本优化

复制多段文本 → 粘贴到输入框 → 按右 Option → 批量优化

---

## 📞 获取帮助

- **查看日志**：`~/.voice-text-enhancer/app.log`
- **配置文件**：`~/.voice-text-enhancer/config.yaml`
- **环境变量**：`~/.voice-text-enhancer/.env`

---

**享受智能文本处理的便利！🎉**

最后更新：2026-05-27  
版本：v1.0.0
