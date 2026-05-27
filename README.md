# Voice Text Enhancer - 文本增强工具

一个 macOS 工具，通过快捷键将选中的文本发送到 DeepSeek API 进行智能优化和增强，然后自动替换回原位置。

## 功能特点

- **一键增强**：按快捷键即可处理选中文本，无需复制粘贴
- **智能处理**：
  - 纠正语法错误和错别字
  - 优化语句表达
  - 适当添加背景信息和细节
  - 格式化为更专业的风格
- **无缝集成**：自动替换文本，不影响剪贴板
- **进度提示**：处理期间显示动态进度通知
- **多种模式**：支持纠错、优化、扩展、总结等多种处理模式

## 使用场景

- 豆包输入法语音转文字后的文本优化
- 快速整理会议记录或笔记
- 邮件和文档的专业化改写
- 社交媒体内容的润色

## 系统要求

- macOS 10.15 或更高版本
- Python 3.8 或更高版本
- DeepSeek API Key（在 [platform.deepseek.com](https://platform.deepseek.com/api_keys) 获取）

## 安装

### 自动安装（推荐）

```bash
cd /Users/tal/Code/voice-text-enhancer
bash scripts/install.sh
```

### 手动安装

1. **安装依赖**：

```bash
pip install -r requirements.txt
```

2. **配置文件**：

```bash
# 复制配置模板
cp .env.example .env
cp config.example.yaml config.yaml

# 编辑 .env，添加你的 API Key
# DEEPSEEK_API_KEY=sk-your-api-key-here
```

3. **系统权限**：

首次运行时，需要在"系统设置 > 隐私与安全性"中授予以下权限：
- **辅助功能** (Accessibility)：允许模拟键盘输入
- **输入监控** (Input Monitoring)：允许监听全局快捷键

## 使用方法

### 启动程序

```bash
python3 main.py
```

启动后会显示：
```
✓ 工具已启动
✓ 快捷键: <cmd>+<shift>+p
✓ 处理模式: expand

使用方法:
  1. 在输入框中输入或粘贴文本（豆包输入法等）
  2. 光标停留在该输入框内
  3. 直接按快捷键 <cmd>+<shift>+p（自动全选并处理）
  4. 等待处理完成，文本自动替换

💡 提示: 无需手动选中文本，按快捷键即可！
```

### 工作流程

1. **输入文本**：
   - 使用豆包输入法语音转文字，或直接输入/粘贴文本
   - 光标停留在输入框内
   
2. **一键处理**：
   - 直接按快捷键 `Cmd+Shift+P`
   - 工具自动执行：全选 → 复制 → AI处理 → 替换
   - 显示动态进度提示："⠋ 正在处理文本，请稍候..."

3. **自动完成**：
   - 处理完成后，文本自动替换到输入框
   - 显示"✓ 文本处理完成"通知
   - 原剪贴板内容自动恢复

**特点**：
- ✅ 无需手动选中文本
- ✅ 一键全自动处理
- ✅ 不影响剪贴板
- ✅ 实时进度提示

### 示例

**处理前**：
```
这是测试文本有一些错别字和语法问题需要优化
```

**处理后**：
```
这是一段测试文本，其中存在一些错别字和语法问题，需要进行优化处理。
为了提升文本质量，我们可以通过语法检查和拼写纠正来改善表达的准确性和专业性。
```

## 配置

### 修改快捷键

编辑 `config.yaml`：

```yaml
hotkey:
  trigger: "<cmd>+<shift>+e"  # 改为 Cmd+Shift+E
```

### 切换处理模式

编辑 `config.yaml` 中的 `active_prompt`：

```yaml
active_prompt: "optimize"  # 可选: correct, optimize, expand, summarize
```

模式说明：
- **correct**：仅纠正错误，不改变原文
- **optimize**：纠错 + 优化表达
- **expand**：纠错 + 优化 + 适当扩展内容（默认）
- **summarize**：纠错 + 提取要点，精简内容

### 自定义 Prompt

在 `config.yaml` 的 `prompts` 部分添加自定义模板：

```yaml
prompts:
  my_custom:  |
    你是一个专业的文本编辑助手。
    请按照我的要求处理文本...
    
active_prompt: "my_custom"
```

## 故障排除

### 快捷键无法触发

1. 检查"系统设置 > 隐私与安全性 > 输入监控"是否授权
2. 检查快捷键是否与其他应用冲突
3. 尝试在 `config.yaml` 中更换快捷键

### 文本无法替换

1. 检查"系统设置 > 隐私与安全性 > 辅助功能"是否授权
2. 确认在执行前已选中文本
3. 某些应用可能限制模拟输入，尝试在不同应用中测试

### API 调用失败

1. 检查 `.env` 中的 `DEEPSEEK_API_KEY` 是否正确
2. 检查网络连接
3. 查看终端日志了解详细错误信息

### 剪贴板被污染

工具会自动保存和恢复剪贴板，但如果遇到问题：
1. 等待处理完成（不要在处理期间进行复制操作）
2. 增加 `config.yaml` 中的延迟时间

## 项目结构

```
voice-text-enhancer/
├── main.py                    # 主程序入口
├── requirements.txt           # Python 依赖
├── config.yaml                # 配置文件
├── .env                       # API Key（不提交）
│
├── src/
│   ├── core/                  # 核心功能
│   │   ├── hotkey_listener.py   # 快捷键监听
│   │   ├── text_processor.py    # 文本处理
│   │   └── clipboard_manager.py # 剪贴板管理
│   │
│   ├── api/                   # API 集成
│   │   ├── deepseek_client.py   # DeepSeek API 客户端
│   │   └── prompts.py           # Prompt 模板
│   │
│   └── utils/                 # 工具模块
│       ├── config_loader.py     # 配置加载
│       ├── logger.py            # 日志
│       └── notifications.py     # 系统通知
│
└── scripts/
    └── install.sh             # 安装脚本
```

## 开发

### 运行测试

```bash
pytest tests/ -v
```

### 查看日志

```bash
tail -f ~/.voice-text-enhancer/app.log
```

## 常见问题

**Q: 处理速度如何？**  
A: 通常 2-5 秒完成，取决于文本长度和网络状况。

**Q: 是否支持多语言？**  
A: 支持，DeepSeek 可以处理中文、英文等多种语言。

**Q: 会消耗多少 API 额度？**  
A: 每次处理约消耗 100-500 tokens，具体取决于文本长度。

**Q: 能否离线使用？**  
A: 不能，需要调用 DeepSeek API，必须联网。

**Q: 是否保存处理记录？**  
A: 不保存。所有处理都是实时的，不会保存任何文本内容。

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 更新日志

### v1.0.0 (2026-05-27)
- 初始版本
- 支持快捷键触发文本处理
- 集成 DeepSeek API
- 支持多种处理模式
- 动态进度提示
- 自动剪贴板管理

## 致谢

- [DeepSeek](https://www.deepseek.com/) - AI 模型提供商
- [pynput](https://github.com/moses-palmer/pynput) - 键盘监听
- [pyautogui](https://github.com/asweigart/pyautogui) - GUI 自动化
- [httpx](https://www.python-httpx.org/) - HTTP 客户端
