#!/usr/bin/env python3
"""
设置窗口（独立进程 + pywebview）
显示权限状态、API Key 配置、Prompt 编辑
"""
import sys
import os
import json
import yaml
from pathlib import Path


def get_user_dir() -> Path:
    d = Path.home() / '.voice-text-enhancer'
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_env_file() -> Path:
    return get_user_dir() / '.env'


def get_config_file() -> Path:
    """获取用户配置文件路径"""
    return get_user_dir() / 'config.yaml'


def read_api_key() -> str:
    env = get_env_file()
    if not env.exists():
        return ''
    try:
        for line in env.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if '=' in line and line.startswith('DEEPSEEK_API_KEY='):
                return line.split('=', 1)[1].strip().strip('"').strip("'")
    except Exception:
        pass
    return ''


def write_api_key(api_key: str) -> bool:
    env = get_env_file()
    api_key = api_key.strip()
    try:
        lines = []
        found = False
        if env.exists():
            for line in env.read_text(encoding='utf-8').splitlines():
                if line.strip().startswith('DEEPSEEK_API_KEY='):
                    lines.append(f'DEEPSEEK_API_KEY={api_key}')
                    found = True
                else:
                    lines.append(line)
        if not found:
            lines.append(f'DEEPSEEK_API_KEY={api_key}')
        env.write_text('\n'.join(lines) + '\n', encoding='utf-8')
        os.chmod(env, 0o600)
        return True
    except Exception:
        return False


def check_accessibility() -> bool:
    try:
        from ApplicationServices import AXIsProcessTrusted
        return bool(AXIsProcessTrusted())
    except Exception:
        return False


def check_input_monitoring() -> bool:
    try:
        import ctypes
        iokit = ctypes.CDLL('/System/Library/Frameworks/IOKit.framework/IOKit')
        iokit.IOHIDCheckAccess.argtypes = [ctypes.c_uint32]
        iokit.IOHIDCheckAccess.restype = ctypes.c_int
        return iokit.IOHIDCheckAccess(1) == 0  # 1 = ListenEvent
    except Exception:
        return False


def read_config() -> dict:
    """读取配置文件"""
    config_file = get_config_file()
    if not config_file.exists():
        # 返回默认配置
        return {
            'hotkey_bindings': []
        }
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}

        # 如果是旧格式，转换为新格式
        if 'hotkey_bindings' not in config and 'hotkey' in config:
            hotkey_str = config['hotkey'].get('trigger', 'right_option')
            active_prompt = config.get('active_prompt', 'typeless')
            prompts = config.get('prompts', {})
            prompt_content = prompts.get(active_prompt, '')

            config['hotkey_bindings'] = [
                {
                    'hotkey': hotkey_str,
                    'prompt_name': active_prompt,
                    'prompt_content': prompt_content
                }
            ]

        return config
    except Exception as e:
        print(f"读取配置失败: {e}", file=sys.stderr)
        return {'hotkey_bindings': []}


def write_config(config: dict) -> bool:
    """写入配置文件（仅更新hotkey_bindings）"""
    config_file = get_config_file()
    try:
        # 读取现有配置
        existing = {}
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                existing = yaml.safe_load(f) or {}

        # 更新hotkey_bindings
        existing['hotkey_bindings'] = config.get('hotkey_bindings', [])

        # 写回文件
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.safe_dump(existing, f, allow_unicode=True, default_flow_style=False)

        return True
    except Exception as e:
        print(f"写入配置失败: {e}", file=sys.stderr)
        return False


HTML = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Voice Text Enhancer 设置</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif;
            background: #f5f5f7;
            color: #1d1d1f;
            padding: 20px 24px;
            -webkit-user-select: none;
            max-height: 100vh;
            overflow-y: auto;
        }
        h1 {
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 4px;
        }
        .subtitle {
            color: #86868b;
            font-size: 12px;
            margin-bottom: 18px;
        }
        .card {
            background: white;
            border-radius: 10px;
            padding: 16px 18px;
            margin-bottom: 12px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        .card-title {
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .perm-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #f0f0f0;
        }
        .perm-row:last-child { border-bottom: none; }
        .badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 8px;
            font-size: 10px;
            font-weight: 600;
        }
        .badge.ok {
            background: #e3f4e6;
            color: #1a8a30;
        }
        .badge.no {
            background: #fdecea;
            color: #c0392b;
        }
        .perm-name { font-size: 13px; }
        .perm-desc { font-size: 11px; color: #86868b; margin-top: 1px; }
        button {
            font-family: inherit;
            font-size: 12px;
            padding: 5px 12px;
            border-radius: 6px;
            border: 1px solid #d2d2d7;
            background: white;
            cursor: pointer;
            transition: all 0.15s;
        }
        button:hover { background: #f5f5f7; }
        button.primary {
            background: #007aff;
            color: white;
            border-color: #007aff;
        }
        button.primary:hover { background: #0051d5; }
        button.danger {
            background: #ff3b30;
            color: white;
            border-color: #ff3b30;
        }
        button.danger:hover { background: #d32f2f; }
        button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        input[type="password"], input[type="text"], select, textarea {
            width: 100%;
            padding: 8px 10px;
            border-radius: 6px;
            border: 1px solid #d2d2d7;
            font-size: 12px;
            font-family: inherit;
            margin-bottom: 6px;
            outline: none;
        }
        textarea {
            font-family: ui-monospace, monospace;
            resize: vertical;
            min-height: 80px;
        }
        input:focus, select:focus, textarea:focus { border-color: #007aff; }
        .input-actions {
            display: flex;
            gap: 6px;
            justify-content: flex-end;
        }
        .hint {
            font-size: 11px;
            color: #86868b;
            margin-top: 4px;
        }
        .hint a { color: #007aff; text-decoration: none; }
        .toast {
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%) translateY(100px);
            background: rgba(0,0,0,0.85);
            color: white;
            padding: 8px 16px;
            border-radius: 6px;
            font-size: 12px;
            opacity: 0;
            transition: all 0.3s;
            pointer-events: none;
        }
        .toast.show {
            opacity: 1;
            transform: translateX(-50%) translateY(0);
        }

        /* 快捷键绑定列表 */
        .binding-list {
            max-height: 240px;
            overflow-y: auto;
        }
        .binding-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 10px;
            border: 1px solid #e5e5ea;
            border-radius: 8px;
            margin-bottom: 8px;
            background: #fafafa;
        }
        .binding-info {
            flex: 1;
        }
        .binding-hotkey {
            font-size: 13px;
            font-weight: 600;
            margin-bottom: 2px;
        }
        .binding-prompt {
            font-size: 11px;
            color: #86868b;
        }
        .binding-actions {
            display: flex;
            gap: 6px;
        }

        /* 模态框 */
        .modal {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.5);
            display: none;
            align-items: center;
            justify-content: center;
            z-index: 1000;
        }
        .modal.show {
            display: flex;
        }
        .modal-content {
            background: white;
            border-radius: 12px;
            padding: 20px;
            width: 90%;
            max-width: 500px;
            max-height: 80vh;
            overflow-y: auto;
        }
        .modal-title {
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 16px;
        }
        .form-group {
            margin-bottom: 14px;
        }
        .form-label {
            display: block;
            font-size: 12px;
            font-weight: 600;
            margin-bottom: 6px;
        }
        .modal-actions {
            display: flex;
            gap: 8px;
            justify-content: flex-end;
            margin-top: 16px;
        }

        .footer {
            text-align: center;
            color: #86868b;
            font-size: 10px;
            margin-top: 12px;
        }
    </style>
</head>
<body>
    <h1>Voice Text Enhancer</h1>
    <div class="subtitle">设置 · 权限 · API Key · 快捷键绑定</div>

    <div class="card">
        <div class="card-title">🔐 系统权限</div>
        <div class="perm-row">
            <div>
                <div class="perm-name">辅助功能 <span class="badge" id="badge-acc">检测中</span></div>
                <div class="perm-desc">允许模拟键盘输入（Cmd+A、Cmd+C、Cmd+V）</div>
            </div>
            <button onclick="openAccessibility()">打开设置</button>
        </div>
        <div class="perm-row">
            <div>
                <div class="perm-name">输入监控 <span class="badge" id="badge-input">检测中</span></div>
                <div class="perm-desc">允许监听全局快捷键</div>
            </div>
            <button onclick="openInputMonitoring()">打开设置</button>
        </div>
        <div class="hint">⚠️ 授权后请重启本应用使其生效</div>
    </div>

    <div class="card">
        <div class="card-title">🔑 DeepSeek API Key</div>
        <input type="password" id="api-key" placeholder="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" />
        <div class="input-actions">
            <button onclick="toggleVisible()" id="toggle-btn">显示</button>
            <button class="primary" onclick="saveKey()">保存</button>
        </div>
        <div class="hint">从 <a href="javascript:void(0)" onclick="openDeepseek()">platform.deepseek.com</a> 获取</div>
    </div>

    <div class="card">
        <div class="card-title">
            <span>⌨️ 快捷键绑定</span>
            <button class="primary" onclick="showAddModal()">添加绑定</button>
        </div>
        <div class="binding-list" id="binding-list">
            <div style="text-align:center;color:#86868b;font-size:12px;padding:20px;">加载中...</div>
        </div>
    </div>

    <div class="footer">配置保存在 ~/.voice-text-enhancer/</div>

    <div class="toast" id="toast"></div>

    <!-- 编辑/添加绑定的模态框 -->
    <div class="modal" id="edit-modal">
        <div class="modal-content">
            <div class="modal-title" id="modal-title">添加快捷键绑定</div>

            <div class="form-group">
                <label class="form-label">快捷键</label>
                <select id="edit-hotkey">
                    <option value="right_option">右 Option</option>
                    <option value="left_option">左 Option</option>
                    <option value="right_cmd">右 Cmd</option>
                    <option value="<cmd>+<shift>+p">Cmd+Shift+P</option>
                    <option value="<cmd>+<alt>+space">Cmd+Alt+Space</option>
                </select>
            </div>

            <div class="form-group">
                <label class="form-label">Prompt 名称</label>
                <input type="text" id="edit-prompt-name" placeholder="例如：智能结构化、纠错模式..." />
            </div>

            <div class="form-group">
                <label class="form-label">Prompt 内容</label>
                <textarea id="edit-prompt-content" placeholder="输入完整的 Prompt 指令..." rows="8"></textarea>
            </div>

            <div class="modal-actions">
                <button onclick="closeModal()">取消</button>
                <button class="primary" onclick="saveBinding()">保存</button>
            </div>
        </div>
    </div>

    <script>
        let editingIndex = -1; // -1 表示新增，>=0 表示编辑现有
        let currentBindings = [];

        function showToast(msg) {
            const t = document.getElementById('toast');
            t.textContent = msg;
            t.classList.add('show');
            setTimeout(() => t.classList.remove('show'), 1800);
        }

        async function refreshPermissions() {
            const status = await window.pywebview.api.get_permissions();
            const accBadge = document.getElementById('badge-acc');
            const inputBadge = document.getElementById('badge-input');
            accBadge.textContent = status.accessibility ? '已授权' : '未授权';
            accBadge.className = 'badge ' + (status.accessibility ? 'ok' : 'no');
            inputBadge.textContent = status.input_monitoring ? '已授权' : '未授权';
            inputBadge.className = 'badge ' + (status.input_monitoring ? 'ok' : 'no');
        }

        async function loadApiKey() {
            const key = await window.pywebview.api.get_api_key();
            document.getElementById('api-key').value = key || '';
        }

        async function saveKey() {
            const key = document.getElementById('api-key').value.trim();
            if (!key) {
                showToast('请输入 API Key');
                return;
            }
            if (!key.startsWith('sk-')) {
                showToast('Key 格式不正确，应以 sk- 开头');
                return;
            }
            const ok = await window.pywebview.api.save_api_key(key);
            showToast(ok ? '已保存 ✓' : '保存失败');
        }

        function toggleVisible() {
            const input = document.getElementById('api-key');
            const btn = document.getElementById('toggle-btn');
            if (input.type === 'password') {
                input.type = 'text';
                btn.textContent = '隐藏';
            } else {
                input.type = 'password';
                btn.textContent = '显示';
            }
        }

        function openAccessibility() {
            window.pywebview.api.open_accessibility();
        }
        function openInputMonitoring() {
            window.pywebview.api.open_input_monitoring();
        }
        function openDeepseek() {
            window.pywebview.api.open_url('https://platform.deepseek.com/api_keys');
        }

        // 加载快捷键绑定列表
        async function loadBindings() {
            const bindings = await window.pywebview.api.get_bindings();
            currentBindings = bindings || [];
            renderBindings();
        }

        function renderBindings() {
            const container = document.getElementById('binding-list');
            if (currentBindings.length === 0) {
                container.innerHTML = '<div style="text-align:center;color:#86868b;font-size:12px;padding:20px;">暂无绑定，点击右上角"添加绑定"</div>';
                return;
            }
            container.innerHTML = currentBindings.map((b, i) => `
                <div class="binding-item">
                    <div class="binding-info">
                        <div class="binding-hotkey">${escapeHtml(b.hotkey)}</div>
                        <div class="binding-prompt">${escapeHtml(b.prompt_name)}</div>
                    </div>
                    <div class="binding-actions">
                        <button onclick="showEditModal(${i})">编辑</button>
                        <button class="danger" onclick="deleteBinding(${i})">删除</button>
                    </div>
                </div>
            `).join('');
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        function showAddModal() {
            editingIndex = -1;
            document.getElementById('modal-title').textContent = '添加快捷键绑定';
            document.getElementById('edit-hotkey').value = 'right_option';
            document.getElementById('edit-prompt-name').value = '';
            document.getElementById('edit-prompt-content').value = '';
            document.getElementById('edit-modal').classList.add('show');
        }

        function showEditModal(index) {
            editingIndex = index;
            const binding = currentBindings[index];
            document.getElementById('modal-title').textContent = '编辑快捷键绑定';
            document.getElementById('edit-hotkey').value = binding.hotkey;
            document.getElementById('edit-prompt-name').value = binding.prompt_name;
            document.getElementById('edit-prompt-content').value = binding.prompt_content;
            document.getElementById('edit-modal').classList.add('show');
        }

        function closeModal() {
            document.getElementById('edit-modal').classList.remove('show');
        }

        async function saveBinding() {
            const hotkey = document.getElementById('edit-hotkey').value;
            const promptName = document.getElementById('edit-prompt-name').value.trim();
            const promptContent = document.getElementById('edit-prompt-content').value.trim();

            if (!promptName) {
                showToast('请输入 Prompt 名称');
                return;
            }
            if (!promptContent) {
                showToast('请输入 Prompt 内容');
                return;
            }

            const binding = {
                hotkey,
                prompt_name: promptName,
                prompt_content: promptContent
            };

            if (editingIndex >= 0) {
                // 编辑现有
                currentBindings[editingIndex] = binding;
            } else {
                // 新增
                currentBindings.push(binding);
            }

            const ok = await window.pywebview.api.save_bindings(currentBindings);
            if (ok) {
                showToast('已保存 ✓');
                closeModal();
                await loadBindings();
            } else {
                showToast('保存失败');
            }
        }

        async function deleteBinding(index) {
            if (!confirm('确定删除这个绑定吗？')) {
                return;
            }
            currentBindings.splice(index, 1);
            const ok = await window.pywebview.api.save_bindings(currentBindings);
            if (ok) {
                showToast('已删除');
                await loadBindings();
            } else {
                showToast('删除失败');
            }
        }

        window.addEventListener('pywebviewready', () => {
            refreshPermissions();
            loadApiKey();
            loadBindings();
            setInterval(refreshPermissions, 2000);
        });
    </script>
</body>
</html>
"""


class API:
    """暴露给 JS 的 API"""

    def get_permissions(self):
        return {
            "accessibility": check_accessibility(),
            "input_monitoring": check_input_monitoring(),
        }

    def get_api_key(self):
        return read_api_key()

    def save_api_key(self, key: str) -> bool:
        return write_api_key(key)

    def get_bindings(self) -> list:
        """获取所有快捷键绑定"""
        config = read_config()
        return config.get('hotkey_bindings', [])

    def save_bindings(self, bindings: list) -> bool:
        """保存快捷键绑定"""
        return write_config({'hotkey_bindings': bindings})

    def open_accessibility(self):
        import subprocess
        subprocess.Popen([
            "open",
            "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"
        ])

    def open_input_monitoring(self):
        import subprocess
        subprocess.Popen([
            "open",
            "x-apple.systempreferences:com.apple.preference.security?Privacy_ListenEvent"
        ])

    def open_url(self, url: str):
        import subprocess
        subprocess.Popen(["open", url])


def main():
    """在主线程运行 webview"""
    import webview

    api = API()
    window = webview.create_window(
        'Voice Text Enhancer 设置',
        html=HTML,
        width=580,
        height=720,
        resizable=False,
        js_api=api,
    )
    webview.start(debug=False)


if __name__ == '__main__':
    main()
