#!/usr/bin/env python3
"""
Voice Text Enhancer - 文本增强工具
主入口程序

根据环境变量切换三种模式：
- VTE_HELPER_MODE=1   → 通知动效子进程（pywebview + Lottie）
- VTE_SETTINGS_MODE=1 → 设置窗口子进程（pywebview 配置 UI）
- 默认                → 菜单栏应用（rumps）
"""
import os
import sys


def main():
    mode = os.environ.get('VTE_HELPER_MODE') or os.environ.get('VTE_SETTINGS_MODE')

    if os.environ.get('VTE_HELPER_MODE') == '1':
        # 子进程：桌面浮层通知
        from src.utils.notification_helper import main as helper_main
        helper_main()
        return

    if os.environ.get('VTE_SETTINGS_MODE') == '1':
        # 子进程：设置窗口
        from src.utils.settings_window import main as settings_main
        settings_main()
        return

    # 主进程：菜单栏应用
    from src.menu_bar_app import run
    run()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
