#!/usr/bin/env python3
"""
设置窗口（独立进程 + pywebview）
显示权限状态、API Key 配置
"""
import sys
import os
import json
from pathlib import Path


def get_user_dir() -> Path:
    d = Path.home() / '.voice-text-enhancer'
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_env_file() -> Path:
    return get_user_dir() / '.env'


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


HTML = """
<!DOCTYPE html>
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
            padding: 28px 32px;
            -webkit-user-select: none;
        }
        h1 {
            font-size: 22px;
            font-weight: 600;
            margin-bottom: 6px;
        }
        .subtitle {
            color: #86868b;
            font-size: 13px;
            margin-bottom: 24px;
        }
        .card {
            background: white;
            border-radius: 12px;
            padding: 18px 20px;
            margin-bottom: 14px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        .card-title {
            font-size: 15px;
            font-weight: 600;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .perm-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #f0f0f0;
        }
        .perm-row:last-child { border-bottom: none; }
        .perm-info {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .badge {
            display: inline-block;
            padding: 3px 10px;
            border-radius: 10px;
            font-size: 11px;
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
        .perm-name { font-size: 14px; }
        .perm-desc { font-size: 12px; color: #86868b; margin-top: 2px; }
        button {
            font-family: inherit;
            font-size: 13px;
            padding: 6px 14px;
            border-radius: 8px;
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
        button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        input[type="password"], input[type="text"] {
            width: 100%;
            padding: 10px 12px;
            border-radius: 8px;
            border: 1px solid #d2d2d7;
            font-size: 13px;
            font-family: ui-monospace, monospace;
            margin-bottom: 8px;
            outline: none;
        }
        input:focus { border-color: #007aff; }
        .input-actions {
            display: flex;
            gap: 8px;
            justify-content: flex-end;
        }
        .hint {
            font-size: 12px;
            color: #86868b;
            margin-top: 6px;
        }
        .hint a { color: #007aff; text-decoration: none; }
        .toast {
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%) translateY(100px);
            background: rgba(0,0,0,0.85);
            color: white;
            padding: 10px 20px;
            border-radius: 8px;
            font-size: 13px;
            opacity: 0;
            transition: all 0.3s;
            pointer-events: none;
        }
        .toast.show {
            opacity: 1;
            transform: translateX(-50%) translateY(0);
        }
        .footer {
            text-align: center;
            color: #86868b;
            font-size: 11px;
            margin-top: 18px;
        }
    </style>
</head>
<body>
    <h1>Voice Text Enhancer</h1>
    <div class="subtitle">设置 · 权限 · API Key</div>

    <div class="card">
        <div class="card-title">🔐 系统权限</div>
        <div class="perm-row">
            <div class="perm-info">
                <div>
                    <div class="perm-name">辅助功能 <span class="badge" id="badge-acc">检测中</span></div>
                    <div class="perm-desc">允许模拟键盘输入（Cmd+A、Cmd+C、Cmd+V）</div>
                </div>
            </div>
            <button onclick="openAccessibility()">打开设置</button>
        </div>
        <div class="perm-row">
            <div class="perm-info">
                <div>
                    <div class="perm-name">输入监控 <span class="badge" id="badge-input">检测中</span></div>
                    <div class="perm-desc">允许监听全局快捷键（右 Option）</div>
                </div>
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
        <div class="hint">从 <a href="javascript:void(0)" onclick="openDeepseek()">platform.deepseek.com</a> 获取，仅保存在本地 ~/.voice-text-enhancer/.env</div>
    </div>

    <div class="footer">轻按右 Option 键即可处理当前输入框文本</div>

    <div class="toast" id="toast"></div>

    <script>
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

        window.addEventListener('pywebviewready', () => {
            refreshPermissions();
            loadApiKey();
            // 每 2 秒刷新一次权限状态
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
        width=520,
        height=560,
        resizable=False,
        js_api=api,
    )
    webview.start(debug=False)


if __name__ == '__main__':
    main()
