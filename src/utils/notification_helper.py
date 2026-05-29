#!/usr/bin/env python3
"""
独立的通知助手进程
在主线程运行 pywebview，显示 Lottie 动画通知
"""
import sys
import os
import json
import threading
from pathlib import Path


def get_lottie_path() -> Path:
    """获取 Lottie 动画文件路径（兼容打包模式）"""
    # 打包后的路径
    if getattr(sys, 'frozen', False):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).parent.parent.parent
    return base / 'assets' / 'loading.json'


def get_html(lottie_data: str) -> str:
    """生成 HTML 内容 - 彩色 CSS 动效，透明背景，无框无字

    lottie_data 参数保留以兼容旧调用，但当前不再使用 Lottie。
    """
    return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

        html, body {
            width: 100%;
            height: 100%;
            background: transparent;
            overflow: hidden;
        }

        .anim-box {
            position: fixed;
            top: 0;
            left: 50%;
            transform: translateX(-50%) translateY(-10px);
            width: 100px;
            height: 100px;
            opacity: 0;
            transition: opacity 0.3s ease, transform 0.3s ease;
            pointer-events: none;
        }

        .anim-box.show {
            opacity: 1;
            transform: translateX(-50%) translateY(0);
        }

        /* 彩色环：用 conic-gradient 生成绚丽渐变，再用 mask 抠出环形 */
        .ring {
            position: absolute;
            inset: 8px;
            border-radius: 50%;
            background: conic-gradient(
                from 0deg,
                #ff006e,
                #fb5607,
                #ffbe0b,
                #06ffa5,
                #3a86ff,
                #8338ec,
                #ff006e
            );
            -webkit-mask: radial-gradient(circle, transparent 56%, #000 58%);
            mask: radial-gradient(circle, transparent 56%, #000 58%);
            filter: drop-shadow(0 0 6px rgba(255, 100, 200, 0.5))
                    drop-shadow(0 0 10px rgba(80, 180, 255, 0.35));
            animation: spin 1.4s linear infinite;
        }

        /* 内层反向旋转的高光弧 */
        .ring::after {
            content: '';
            position: absolute;
            inset: 8px;
            border-radius: 50%;
            background: conic-gradient(
                from 90deg,
                rgba(255,255,255,0.9) 0deg,
                rgba(255,255,255,0) 60deg,
                rgba(255,255,255,0) 360deg
            );
            -webkit-mask: radial-gradient(circle, transparent 50%, #000 52%, #000 70%, transparent 72%);
            mask: radial-gradient(circle, transparent 50%, #000 52%, #000 70%, transparent 72%);
            animation: spin-reverse 0.9s linear infinite;
            mix-blend-mode: screen;
        }

        /* 中央柔光点 */
        .core {
            position: absolute;
            top: 50%;
            left: 50%;
            width: 18px;
            height: 18px;
            transform: translate(-50%, -50%);
            border-radius: 50%;
            background: radial-gradient(circle, #ffffff 0%, rgba(255,255,255,0.6) 40%, rgba(255,255,255,0) 70%);
            animation: pulse 1.4s ease-in-out infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        @keyframes spin-reverse {
            to { transform: rotate(-360deg); }
        }

        @keyframes pulse {
            0%, 100% { opacity: 0.7; transform: translate(-50%, -50%) scale(0.85); }
            50%     { opacity: 1.0; transform: translate(-50%, -50%) scale(1.15); }
        }
    </style>
</head>
<body>
    <div class="anim-box" id="anim-box">
        <div class="ring"></div>
        <div class="core"></div>
    </div>

    <script>
        let hideTimer = null;

        function showAnimation(duration) {
            if (hideTimer) {
                clearTimeout(hideTimer);
                hideTimer = null;
            }

            const box = document.getElementById('anim-box');
            requestAnimationFrame(() => {
                box.classList.add('show');
            });

            if (duration > 0) {
                hideTimer = setTimeout(hideAnimation, duration * 1000);
            }
        }

        function hideAnimation() {
            const box = document.getElementById('anim-box');
            box.classList.remove('show');
        }

        window.showAnimation = showAnimation;
        window.hideAnimation = hideAnimation;
    </script>
</body>
</html>
"""


def read_lottie_data() -> str:
    """读取 Lottie 动画数据"""
    path = get_lottie_path()
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    return '{}'


def get_screen_size():
    """获取屏幕尺寸"""
    try:
        from AppKit import NSScreen
        screen = NSScreen.mainScreen()
        frame = screen.visibleFrame()
        return int(frame.size.width), int(frame.size.height), int(frame.origin.x), int(frame.origin.y)
    except Exception:
        return 1920, 1080, 0, 0


def _apply_window_config_on_main_thread():
    """
    在主线程上执行实际的窗口配置（NSWindow 操作必须在主线程）
    """
    try:
        from AppKit import (
            NSApp,
            NSWindowCollectionBehaviorCanJoinAllSpaces,
            NSWindowCollectionBehaviorStationary,
            NSWindowCollectionBehaviorFullScreenAuxiliary,
            NSWindowCollectionBehaviorIgnoresCycle,
        )

        SCREEN_SAVER_LEVEL = 1000

        behavior = (
            NSWindowCollectionBehaviorCanJoinAllSpaces
            | NSWindowCollectionBehaviorStationary
            | NSWindowCollectionBehaviorFullScreenAuxiliary
            | NSWindowCollectionBehaviorIgnoresCycle
        )

        windows = list(NSApp.windows()) if NSApp else []
        for win in windows:
            try:
                title = str(win.title()) if win.title() else ''
            except Exception:
                title = ''
            if title == 'Notification':
                win.setCollectionBehavior_(behavior)
                win.setLevel_(SCREEN_SAVER_LEVEL)
                win.setIgnoresMouseEvents_(True)
                return True
    except Exception as e:
        print(f"_apply_window_config_on_main_thread: {e}", file=sys.stderr)
    return False


def configure_window_for_fullscreen():
    """
    把 pywebview 的 NSWindow 配置成可在所有 Space（含全屏 Space）显示。
    使用 GCD 调度到主线程执行（NSWindow 操作必须在主线程）。
    """
    import time
    try:
        from Foundation import NSObject
        import objc

        # 创建一个 helper 对象，用于在主线程上执行配置
        class _ConfigHelper(NSObject):
            def applyConfig_(self, _):
                _apply_window_config_on_main_thread()

        helper = _ConfigHelper.alloc().init()

        # 轮询：在主线程上调用，直到窗口创建完成
        for _ in range(100):
            time.sleep(0.05)
            # performSelectorOnMainThread 是线程安全的，会把调用调度到主线程
            try:
                helper.performSelectorOnMainThread_withObject_waitUntilDone_(
                    "applyConfig:", None, True
                )
                # 检查是否成功（窗口已找到并配置）
                from AppKit import NSApp
                if NSApp:
                    windows = list(NSApp.windows())
                    for win in windows:
                        try:
                            title = str(win.title()) if win.title() else ''
                        except Exception:
                            title = ''
                        if title == 'Notification':
                            return
            except Exception:
                continue
    except Exception as e:
        print(f"configure_window_for_fullscreen: {e}", file=sys.stderr)


def hide_dock_icon():
    """将当前进程设置为 Accessory（不在 Dock 显示图标）"""
    try:
        from AppKit import NSApplication
        # NSApplicationActivationPolicyAccessory = 1
        NSApplication.sharedApplication().setActivationPolicy_(1)
    except Exception as e:
        print(f"hide_dock_icon: {e}", file=sys.stderr)


def main():
    """主函数 - 在主线程运行 webview"""
    import webview

    hide_dock_icon()

    lottie_data = read_lottie_data()
    html = get_html(lottie_data)

    screen_w, screen_h, screen_x, screen_y = get_screen_size()
    win_w, win_h = 160, 160
    # 屏幕水平居中、贴齐顶部（菜单栏下方）
    x = screen_x + (screen_w - win_w) // 2
    y = screen_y + screen_h - win_h

    window = webview.create_window(
        'Notification',
        html=html,
        width=win_w,
        height=win_h,
        x=x,
        y=y,
        resizable=False,
        frameless=True,
        easy_drag=False,
        on_top=True,
        transparent=True,
    )

    # 后台线程：窗口创建后配置跨 Space + 屏保级别（覆盖全屏应用）
    threading.Thread(target=configure_window_for_fullscreen, daemon=True).start()

    def stdin_listener():
        """监听 stdin 命令"""
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                cmd = json.loads(line)
                action = cmd.get('action')

                if action == 'show':
                    duration = cmd.get('duration', 0)
                    window.evaluate_js(f"showAnimation({duration})")

                elif action == 'hide':
                    window.evaluate_js("hideAnimation()")

                elif action == 'quit':
                    window.destroy()
                    os._exit(0)

            except Exception as e:
                print(f"NOTIFICATION_ERROR: {e}", file=sys.stderr)

    listener = threading.Thread(target=stdin_listener, daemon=True)
    listener.start()

    webview.start(debug=False)


if __name__ == '__main__':
    main()
