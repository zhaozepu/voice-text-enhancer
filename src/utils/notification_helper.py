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
            width: 64px;
            height: 64px;
            opacity: 0;
            transition: opacity 0.3s ease, transform 0.3s ease;
            pointer-events: none;
        }

        .anim-box.show {
            opacity: 1;
            transform: translateX(-50%) translateY(0);
        }

        /* 彩色环：用 conic-gradient 生成绚丽渐变，再用 mask 抠出细环 */
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
            /* 细环：环厚度约占半径的 7%，并有羽化边 */
            -webkit-mask: radial-gradient(circle closest-side,
                transparent 78%,
                #000 88%,
                #000 96%,
                transparent 100%);
            mask: radial-gradient(circle closest-side,
                transparent 78%,
                #000 88%,
                #000 96%,
                transparent 100%);
            filter: drop-shadow(0 0 5px rgba(255, 100, 200, 0.55))
                    drop-shadow(0 0 9px rgba(80, 180, 255, 0.4));
            animation: spin 1.4s linear infinite;
        }

        /* 反向旋转的白色高光弧（更细） */
        .ring::after {
            content: '';
            position: absolute;
            inset: 0;
            border-radius: 50%;
            background: conic-gradient(
                from 90deg,
                rgba(255,255,255,0.95) 0deg,
                rgba(255,255,255,0) 50deg,
                rgba(255,255,255,0) 360deg
            );
            -webkit-mask: radial-gradient(circle closest-side,
                transparent 82%,
                #000 89%,
                #000 95%,
                transparent 100%);
            mask: radial-gradient(circle closest-side,
                transparent 82%,
                #000 89%,
                #000 95%,
                transparent 100%);
            animation: spin-reverse 1.0s linear infinite;
            mix-blend-mode: screen;
        }

        /* 中央柔光点（呼吸） */
        .core {
            position: absolute;
            top: 50%;
            left: 50%;
            width: 28px;
            height: 28px;
            transform: translate(-50%, -50%);
            border-radius: 50%;
            background: radial-gradient(circle, #ffd6e0 0%, rgba(255,182,200,0.55) 45%, rgba(255,182,200,0.12) 78%, rgba(255,182,200,0) 100%);
            animation: pulse 1.4s ease-in-out infinite;
        }


        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        @keyframes spin-reverse {
            to { transform: rotate(-360deg); }
        }

        @keyframes pulse {
            0%, 100% { opacity: 0.55; transform: translate(-50%, -50%) scale(0.85); }
            50%     { opacity: 0.85; transform: translate(-50%, -50%) scale(1.12); }
        }

        /* 暂存上下文圆点指示 */
        .dots {
            position: fixed;
            top: 76px;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            gap: 6px;
            opacity: 0;
            transition: opacity 0.25s ease;
            pointer-events: none;
            padding: 5px 10px;
            background: rgba(20, 20, 30, 0.55);
            border-radius: 999px;
            backdrop-filter: blur(6px);
            -webkit-backdrop-filter: blur(6px);
        }
        .dots.show { opacity: 1; }
        .dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: radial-gradient(circle at 30% 30%, #ffd6e0 0%, #ff4d8d 60%, #c1004d 100%);
            box-shadow: 0 0 6px rgba(255, 80, 140, 0.7);
            animation: dot-pop 0.35s ease;
        }
        @keyframes dot-pop {
            0%   { transform: scale(0); opacity: 0; }
            60%  { transform: scale(1.3); opacity: 1; }
            100% { transform: scale(1); opacity: 1; }
        }
    </style>
</head>
<body>
    <div class="anim-box" id="anim-box">
        <div class="ring"></div>
        <div class="core"></div>
    </div>

    <div class="dots" id="dots"></div>

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

        function setDotCount(count) {
            const container = document.getElementById('dots');
            const safe = Math.max(0, parseInt(count, 10) || 0);
            container.innerHTML = '';
            for (let i = 0; i < safe; i++) {
                const dot = document.createElement('div');
                dot.className = 'dot';
                // 让最新一个圆点带 pop 动效，其它的复用即可
                container.appendChild(dot);
            }
            if (safe > 0) {
                container.classList.add('show');
            } else {
                container.classList.remove('show');
            }
        }

        window.showAnimation = showAnimation;
        window.hideAnimation = hideAnimation;
        window.setDotCount = setDotCount;
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
    对 helper 子进程的所有 NSWindow 都应用一遍，并强制置顶。
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

        if not NSApp:
            return False

        applied = False
        for win in list(NSApp.windows()):
            win.setCollectionBehavior_(behavior)
            win.setLevel_(SCREEN_SAVER_LEVEL)
            win.setIgnoresMouseEvents_(True)
            # orderFrontRegardless 强制置顶但不抢焦点，能覆盖在全屏应用上
            try:
                win.orderFrontRegardless()
            except Exception:
                pass
            applied = True
        return applied
    except Exception as e:
        print(f"_apply_window_config_on_main_thread: {e}", file=sys.stderr)
    return False


def _apply_window_config_async():
    """从任意线程触发主线程上的窗口配置（用于每次 show 时重应用，确保跨全屏 Space 可见）"""
    try:
        from Foundation import NSObject

        class _Helper(NSObject):
            def apply_(self, _):
                _apply_window_config_on_main_thread()

        h = _Helper.alloc().init()
        h.performSelectorOnMainThread_withObject_waitUntilDone_("apply:", None, False)
    except Exception as e:
        print(f"_apply_window_config_async: {e}", file=sys.stderr)


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


def parent_watchdog():
    """
    监视父进程是否还活着；若父进程已死(PPID 变成 1)或 stdin 关闭，立即退出。
    避免主进程崩溃时 helper 子进程成为孤儿，造成动效一直挂在屏幕上。
    """
    import time
    initial_ppid = os.getppid()
    while True:
        time.sleep(1.0)
        try:
            current_ppid = os.getppid()
        except Exception:
            current_ppid = 1
        # PPID 变成 1 = 父进程已死，被 launchd/init 接管
        if current_ppid == 1 or current_ppid != initial_ppid:
            print("notification_helper: 父进程已退出，自杀", file=sys.stderr)
            os._exit(0)


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

    # 监视父进程，避免成为孤儿动效
    threading.Thread(target=parent_watchdog, daemon=True).start()

    def stdin_listener():
        """监听 stdin 命令；stdin 关闭(父进程死/管道断)立即退出"""
        try:
            for line in sys.stdin:
                line = line.strip()
                if not line:
                    continue
                try:
                    cmd = json.loads(line)
                    action = cmd.get('action')

                    if action == 'show':
                        duration = cmd.get('duration', 0)
                        # 每次 show 时再应用一次窗口配置，确保覆盖在全屏应用之上
                        _apply_window_config_async()
                        window.evaluate_js(f"showAnimation({duration})")

                    elif action == 'hide':
                        window.evaluate_js("hideAnimation()")

                    elif action == 'dots':
                        count = int(cmd.get('count', 0))
                        # 圆点持续可见，需要保证窗口在最上层
                        _apply_window_config_async()
                        window.evaluate_js(f"setDotCount({count})")

                    elif action == 'quit':
                        window.destroy()
                        os._exit(0)

                except Exception as e:
                    print(f"NOTIFICATION_ERROR: {e}", file=sys.stderr)
        except Exception:
            pass
        # stdin 自然结束 = 父进程关闭了管道（通常意味着父进程已退出）
        print("notification_helper: stdin 已关闭，自杀", file=sys.stderr)
        os._exit(0)

    listener = threading.Thread(target=stdin_listener, daemon=True)
    listener.start()

    webview.start(debug=False)


if __name__ == '__main__':
    main()
