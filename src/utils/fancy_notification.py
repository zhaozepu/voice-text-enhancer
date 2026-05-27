"""
漂亮的通知系统
使用 macOS 原生通知 + 终端彩色输出
"""
import subprocess
import threading
import time
from typing import Optional
from loguru import logger


class FancyNotification:
    """增强的通知系统"""

    def __init__(self):
        """初始化通知系统"""
        self.is_showing = False
        self.current_thread: Optional[threading.Thread] = None

    def show(self, message: str, notification_type: str = "processing", duration: float = 0):
        """
        显示通知

        Args:
            message: 通知消息
            notification_type: 通知类型 (processing, success, error, info)
            duration: 持续时间（秒），0 表示不自动关闭（仅对 processing 有效）
        """
        # 终端彩色输出
        self._print_colored(message, notification_type)

        # macOS 通知
        self._show_native_notification(message, notification_type)

        # 处理中通知的特殊处理
        if notification_type == 'processing' and duration == 0:
            self.is_showing = True

    def _print_colored(self, message: str, notification_type: str):
        """在终端显示彩色消息"""
        colors = {
            'processing': '\033[94m',  # 蓝色
            'success': '\033[92m',      # 绿色
            'error': '\033[91m',        # 红色
            'info': '\033[96m',         # 青色
        }
        icons = {
            'processing': '⟳',
            'success': '✓',
            'error': '✗',
            'info': 'ℹ',
        }

        color = colors.get(notification_type, '\033[0m')
        icon = icons.get(notification_type, '')
        reset = '\033[0m'

        print(f"{color}{icon} {message}{reset}")

    def _show_native_notification(self, message: str, notification_type: str):
        """显示 macOS 原生通知"""
        try:
            # 标题根据类型不同
            titles = {
                'processing': '正在处理',
                'success': '处理完成',
                'error': '出错了',
                'info': '提示',
            }

            # 音效（仅错误时）
            sound = ' sound name "Basso"' if notification_type == 'error' else ''

            # 副标题（用于添加图标效果）
            icons = {
                'processing': '⟳',
                'success': '✓',
                'error': '✗',
                'info': 'ℹ️',
            }

            title = titles.get(notification_type, '通知')
            icon = icons.get(notification_type, '')

            # 组合消息（图标在消息中）
            full_message = f"{icon} {message}"

            script = f'''
            display notification "{full_message}" with title "Voice Text Enhancer" subtitle "{title}"{sound}
            '''

            subprocess.run(
                ['osascript', '-e', script],
                check=True,
                capture_output=True,
                text=True,
                timeout=2
            )

        except subprocess.TimeoutExpired:
            pass
        except Exception as e:
            logger.debug(f"显示通知失败: {e}")

    def close(self):
        """关闭通知"""
        self.is_showing = False


# 全局通知实例
_notification: Optional[FancyNotification] = None
_processing_indicator: Optional[threading.Thread] = None
_stop_indicator = False


def _show_processing_animation():
    """显示处理中的动画（终端）"""
    global _stop_indicator
    frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    idx = 0

    while not _stop_indicator:
        print(f'\r\033[94m{frames[idx % len(frames)]} 正在处理...\033[0m', end='', flush=True)
        idx += 1
        time.sleep(0.1)

    print('\r' + ' ' * 50 + '\r', end='', flush=True)  # 清除行


def show_fancy_processing(message: str = "正在处理文本..."):
    """显示处理中通知（蓝色，带动画）"""
    global _notification, _processing_indicator, _stop_indicator

    _notification = FancyNotification()
    _notification.show(message, notification_type="processing", duration=0)

    # 启动终端动画
    _stop_indicator = False
    _processing_indicator = threading.Thread(target=_show_processing_animation, daemon=True)
    _processing_indicator.start()


def show_fancy_success(message: str = "处理完成", duration: float = 2.0):
    """显示成功通知（绿色）"""
    global _notification, _stop_indicator

    # 停止处理动画
    _stop_indicator = True
    time.sleep(0.15)

    if _notification:
        _notification.close()

    _notification = FancyNotification()
    _notification.show(message, notification_type="success", duration=duration)


def show_fancy_error(message: str, duration: float = 3.0):
    """显示错误通知（红色）"""
    global _notification, _stop_indicator

    # 停止处理动画
    _stop_indicator = True
    time.sleep(0.15)

    if _notification:
        _notification.close()

    _notification = FancyNotification()
    _notification.show(message, notification_type="error", duration=duration)


def show_fancy_info(message: str, duration: float = 2.0):
    """显示信息通知（浅蓝）"""
    global _notification, _stop_indicator

    # 停止处理动画
    _stop_indicator = True
    time.sleep(0.15)

    if _notification:
        _notification.close()

    _notification = FancyNotification()
    _notification.show(message, notification_type="info", duration=duration)


def close_fancy_notification():
    """关闭当前通知"""
    global _notification, _stop_indicator

    _stop_indicator = True

    if _notification:
        _notification.close()
        _notification = None
