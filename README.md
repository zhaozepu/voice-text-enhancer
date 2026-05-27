# Voice Text Enhancer 🎙️✨

> 一个 macOS 文本智能增强工具 —— 一键将语音转写或随手输入的草稿，通过 DeepSeek 大模型整理成结构化、专业化的文本。

专为搭配豆包等语音输入法使用而设计：语音转写完成后，**轻按右 Option 键**，工具自动全选输入框文本 → 调用 AI 优化 → 替换回原位置，全程无需鼠标。

---

## ✨ 功能亮点

- 🍎 **菜单栏常驻** —— 顶部菜单栏 ✨ 图标，状态实时显示
- 🪟 **图形化设置面板** —— 可视化配置 API Key 和权限，无需编辑配置文件
- 🛡️ **自动权限引导** —— 启动时自动检测并请求所需权限
- ⌨️ **单键触发** —— 默认轻按右 Option，无需组合键
- 🤖 **AI 智能整理** —— 基于 DeepSeek，自动纠错、优化、Markdown 结构化
- 🎯 **自动全选** —— 无需手动选中文本，按一下就处理
- 🎨 **Lottie 动效提示** —— 处理过程中右下角透明浮层动画
- 📦 **打包成 .app** —— PyInstaller 一键构建，可分发

---

## 🎬 使用场景

- 📝 豆包等语音输入法转写后的文本润色
- 🗒️ 快速整理会议记录、灵感笔记
- 📧 邮件草稿专业化改写
- 💬 社交媒体内容润色
- 📄 任意输入框中的文字结构化（自动转 Markdown 列表/标题）

---

## 🚀 快速开始

### 系统要求

- macOS 10.15+
- Python 3.10+
- DeepSeek API Key（[免费申请](https://platform.deepseek.com/api_keys)）

### 安装

```bash
# 1. 克隆并进入项目
git clone <your-repo-url>
cd voice-text-enhancer

# 2. 安装依赖
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. 启动
python3 main.py
```

### 首次使用三步走

启动后菜单栏会出现 **✨** 图标：

1. **点击图标 → 「打开设置…」**
2. **填入 DeepSeek API Key**（在弹出的窗口中），点保存
3. **授予两个系统权限**（窗口里点"打开设置"按钮直达对应面板）：
   - 辅助功能（用于模拟 Cmd+A/C/V）
   - 输入监控（用于监听右 Option 键）

授权后从菜单栏选「重启服务」，或重启应用。

完成后，菜单栏图标显示「● 运行中」，光标停在任意输入框内，**轻按右 Option 键** 即可处理当前文本。

---

## 📦 打包成 macOS 应用

```bash
./build_app.sh
```

构建产物：`dist/VoiceTextEnhancer.app`

将 .app 拖到 `/Applications/` 即可双击启动，后台运行无 Dock 图标。

> ⚠️ **首次运行 .app 后，需要重新在系统设置中授予辅助功能和输入监控权限**（.app 是新的应用身份，权限不会从 Python 进程自动迁移）。

---

## ⚙️ 配置说明

### 修改快捷键

`config.yaml`:

```yaml
hotkey:
  trigger: "right_option"   # 可选: right_option, left_option, right_cmd
```

### 切换处理模式

```yaml
active_prompt: "typeless"   # 可选: typeless, expand, optimize, correct, summarize
```

| 模式 | 行为 |
|------|------|
| `typeless` | **智能结构化**（默认）—— 自动识别要点，转 Markdown 列表/标题 |
| `expand` | 纠错 + 优化 + 扩展细节 |
| `optimize` | 纠错 + 优化表达 |
| `correct` | 仅纠正错别字与语法 |
| `summarize` | 提取要点，精简内容 |

### 自定义 Prompt

```yaml
prompts:
  my_style: |
    你是一个专业的文本编辑助手。
    请按以下规则处理文本：
    ...

active_prompt: "my_style"
```

---

## 🏗️ 技术架构

```
┌────────────────────────────────────────────┐
│  主进程 (rumps / NSApplicationMain)        │
│  ├─ 主线程   菜单栏图标 + 设置窗口托管      │
│  └─ 后台线程 asyncio (hotkey + processor)  │
│              │                             │
│              ├─► subprocess ─► 通知 helper │
│              └─► subprocess ─► 设置窗口    │
└────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              │                               │
              ▼                               ▼
   ┌──────────────────────┐      ┌──────────────────────┐
   │ 通知 helper          │      │ 设置窗口             │
   │ pywebview + Lottie   │      │ pywebview HTML 表单  │
   │ 右下角透明浮层动画    │      │ 权限状态 + API Key   │
   └──────────────────────┘      └──────────────────────┘
```

**为什么这种架构？**
- `rumps` 提供 macOS 菜单栏 + 处理 NSRunLoop（避免「无响应」）
- macOS 要求 Cocoa GUI 必须在主线程，但主线程被 rumps 占用
- 通知动画/设置窗口通过子进程隔离，每个子进程都有自己的主线程
- asyncio 事件循环在后台线程运行，处理快捷键和 API 调用

---

## 📂 项目结构

```
voice-text-enhancer/
├── main.py                       # 入口（也作为 helper 模式入口）
├── app_config.py                 # 打包配置路径管理
├── build_app.sh                  # 一键打包脚本
├── VoiceTextEnhancer.spec        # PyInstaller 配置
├── requirements.txt
├── config.example.yaml           # 配置模板
├── .env.example
│
├── assets/
│   └── loading.json              # Lottie 动画资源
│
├── src/
│   ├── core/
│   │   ├── hotkey_listener.py    # 快捷键监听（支持单键/组合键）
│   │   ├── text_processor.py     # 文本处理主流程
│   │   └── clipboard_manager.py  # 剪贴板保存/恢复
│   ├── api/
│   │   ├── deepseek_client.py    # DeepSeek API 客户端
│   │   └── prompts.py            # Prompt 模板
│   └── utils/
│       ├── config_loader.py      # 配置加载
│       ├── logger.py             # loguru 日志
│       ├── notifications.py      # macOS 系统通知（备用）
│       ├── fancy_notification.py # 终端彩色输出（备用）
│       ├── desktop_notification.py # 桌面浮层通知（IPC 客户端）
│       └── notification_helper.py  # 浮层通知子进程（pywebview + Lottie）
│
└── scripts/
    └── install.sh
```

---

## 🐛 故障排查

| 现象 | 原因 / 解决 |
|------|------------|
| 按快捷键无反应 | 检查"输入监控"权限。打包后的 .app 需要重新授权。 |
| 文字未被全选/复制 | 检查"辅助功能"权限。pyautogui 需要此权限模拟键盘。 |
| 粘贴的内容是旧剪贴板内容 | 应用对剪贴板响应慢，可适当增加 `text_processor.py` 中的 `asyncio.sleep` 延迟。 |
| API 调用失败 | 检查 `.env` 中 `DEEPSEEK_API_KEY` 是否正确，网络是否通畅。 |
| .app 打开后没反应 | 查看 `~/.voice-text-enhancer/app.log`；常见原因是权限未授予。 |

查看日志：

```bash
tail -f ~/.voice-text-enhancer/app.log
```

---

## 🛠️ 开发

```bash
# 测试通知动效
python3 test_desktop_notifications.py

# 运行单元测试
pytest tests/ -v

# 重新打包
./build_app.sh
```

---

## 📜 许可证

MIT License

## 🙏 致谢

- [DeepSeek](https://www.deepseek.com/) — AI 模型
- [pynput](https://github.com/moses-palmer/pynput) — 全局快捷键
- [pyautogui](https://github.com/asweigart/pyautogui) — GUI 自动化
- [pywebview](https://pywebview.flowrl.com/) — 桌面浮层窗口
- [Lottie](https://airbnb.io/lottie/) — 矢量动画格式

---

## 🤝 贡献

欢迎 Issue 和 PR！如果这个工具帮到了你，给个 ⭐ 鼓励一下吧。
