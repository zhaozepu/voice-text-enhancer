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
    """生成 HTML 内容 - 仅 Lottie 动画，透明背景，无框无字"""
    return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/bodymovin/5.9.4/lottie.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

        html, body {
            width: 100%;
            height: 100%;
            background: transparent;
            overflow: hidden;
        }

        .lottie-box {
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 120px;
            height: 120px;
            opacity: 0;
            transition: opacity 0.3s ease;
            pointer-events: none;
        }

        .lottie-box.show {
            opacity: 1;
        }
    </style>
</head>
<body>
    <div class="lottie-box" id="lottie-box"></div>

    <script>
        const LOTTIE_DATA = __LOTTIE_DATA__;
        let lottieAnim = null;
        let hideTimer = null;

        function showAnimation(duration) {
            if (hideTimer) {
                clearTimeout(hideTimer);
                hideTimer = null;
            }

            const box = document.getElementById('lottie-box');
            if (lottieAnim) {
                lottieAnim.destroy();
                lottieAnim = null;
            }
            box.innerHTML = '';

            lottieAnim = lottie.loadAnimation({
                container: box,
                renderer: 'svg',
                loop: true,
                autoplay: true,
                animationData: LOTTIE_DATA
            });

            requestAnimationFrame(() => {
                box.classList.add('show');
            });

            if (duration > 0) {
                hideTimer = setTimeout(hideAnimation, duration * 1000);
            }
        }

        function hideAnimation() {
            const box = document.getElementById('lottie-box');
            box.classList.remove('show');
            setTimeout(() => {
                if (lottieAnim) {
                    lottieAnim.destroy();
                    lottieAnim = null;
                }
                box.innerHTML = '';
            }, 300);
        }

        window.showAnimation = showAnimation;
        window.hideAnimation = hideAnimation;
    </script>
</body>
</html>
""".replace("__LOTTIE_DATA__", lottie_data)


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


def main():
    """主函数 - 在主线程运行 webview"""
    import webview

    lottie_data = read_lottie_data()
    html = get_html(lottie_data)

    screen_w, screen_h, screen_x, screen_y = get_screen_size()
    win_w, win_h = 160, 160
    x = screen_x + screen_w - win_w
    y = screen_y

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
