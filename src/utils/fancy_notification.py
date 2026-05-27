"""
漂亮的浮层通知
右下角彩色动效提示
"""
import tkinter as tk
from tkinter import ttk
import threading
import time
from typing import Optional
from loguru import logger


class FancyNotification:
    """彩色动效浮层通知"""

    def __init__(self):
        """初始化通知系统"""
        self.window: Optional[tk.Tk] = None
        self.is_showing = False
        self.animation_thread: Optional[threading.Thread] = None
        self.should_close = False

    def show(self, message: str, notification_type: str = "processing", duration: int = 0):
        """
        显示通知

        Args:
            message: 通知消息
            notification_type: 通知类型 (processing, success, error, info)
            duration: 持续时间（秒），0 表示不自动关闭
        """
        if self.is_showing:
            logger.warning("通知已经在显示中")
            return

        self.should_close = False

        # 在主线程中创建窗口
        thread = threading.Thread(
            target=self._create_window,
            args=(message, notification_type, duration),
            daemon=True
        )
        thread.start()

    def _create_window(self, message: str, notification_type: str, duration: int):
        """创建通知窗口"""
        try:
            self.is_showing = True

            # 创建主窗口
            self.window = tk.Tk()
            self.window.title("")

            # 窗口设置
            width = 350
            height = 100

            # 获取屏幕尺寸
            screen_width = self.window.winfo_screenwidth()
            screen_height = self.window.winfo_screenheight()

            # 右下角位置（留 20px 边距）
            x = screen_width - width - 20
            y = screen_height - height - 80  # 80px 给 Dock 留空间

            self.window.geometry(f"{width}x{height}+{x}+{y}")

            # 窗口样式
            self.window.overrideredirect(True)  # 无边框
            self.window.attributes('-topmost', True)  # 置顶
            self.window.attributes('-alpha', 0.95)  # 半透明

            # 颜色主题
            themes = {
                'processing': {
                    'bg': '#4A90E2',  # 蓝色
                    'fg': '#FFFFFF',
                    'accent': '#5BA3F5'
                },
                'success': {
                    'bg': '#52C41A',  # 绿色
                    'fg': '#FFFFFF',
                    'accent': '#73D13D'
                },
                'error': {
                    'bg': '#F5222D',  # 红色
                    'fg': '#FFFFFF',
                    'accent': '#FF4D4F'
                },
                'info': {
                    'bg': '#1890FF',  # 浅蓝
                    'fg': '#FFFFFF',
                    'accent': '#40A9FF'
                }
            }

            theme = themes.get(notification_type, themes['info'])

            # 主容器
            container = tk.Frame(
                self.window,
                bg=theme['bg'],
                highlightthickness=0
            )
            container.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

            # 图标 + 文本容器
            content_frame = tk.Frame(container, bg=theme['bg'])
            content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

            # 左侧：动画图标
            if notification_type == 'processing':
                self.icon_label = tk.Label(
                    content_frame,
                    text="⟳",
                    font=("Arial", 32),
                    bg=theme['bg'],
                    fg=theme['fg']
                )
                self.icon_label.pack(side=tk.LEFT, padx=(0, 15))

                # 启动旋转动画
                self.animation_thread = threading.Thread(
                    target=self._rotate_icon,
                    daemon=True
                )
                self.animation_thread.start()
            elif notification_type == 'success':
                icon_label = tk.Label(
                    content_frame,
                    text="✓",
                    font=("Arial", 32, "bold"),
                    bg=theme['bg'],
                    fg=theme['fg']
                )
                icon_label.pack(side=tk.LEFT, padx=(0, 15))
            elif notification_type == 'error':
                icon_label = tk.Label(
                    content_frame,
                    text="✗",
                    font=("Arial", 32, "bold"),
                    bg=theme['bg'],
                    fg=theme['fg']
                )
                icon_label.pack(side=tk.LEFT, padx=(0, 15))
            else:
                icon_label = tk.Label(
                    content_frame,
                    text="ℹ",
                    font=("Arial", 32),
                    bg=theme['bg'],
                    fg=theme['fg']
                )
                icon_label.pack(side=tk.LEFT, padx=(0, 15))

            # 右侧：文本
            text_label = tk.Label(
                content_frame,
                text=message,
                font=("PingFang SC", 14),
                bg=theme['bg'],
                fg=theme['fg'],
                wraplength=220,
                justify=tk.LEFT
            )
            text_label.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            # 淡入动画
            self._fade_in()

            # 自动关闭
            if duration > 0:
                self.window.after(duration * 1000, self.close)

            self.window.mainloop()

        except Exception as e:
            logger.error(f"创建通知窗口失败: {e}")
        finally:
            self.is_showing = False

    def _rotate_icon(self):
        """旋转图标动画"""
        rotation_chars = ["⟳", "⟲", "⟳", "⟲"]
        index = 0

        try:
            while not self.should_close and self.window:
                if hasattr(self, 'icon_label') and self.icon_label.winfo_exists():
                    self.icon_label.config(text=rotation_chars[index % len(rotation_chars)])
                    index += 1
                    time.sleep(0.2)
                else:
                    break
        except Exception as e:
            logger.debug(f"旋转动画停止: {e}")

    def _fade_in(self):
        """淡入动画"""
        try:
            alpha = 0.0
            while alpha < 0.95:
                alpha += 0.05
                self.window.attributes('-alpha', alpha)
                self.window.update()
                time.sleep(0.02)
        except Exception:
            pass

    def _fade_out(self):
        """淡出动画"""
        try:
            alpha = 0.95
            while alpha > 0:
                alpha -= 0.05
                self.window.attributes('-alpha', alpha)
                self.window.update()
                time.sleep(0.02)
        except Exception:
            pass

    def close(self):
        """关闭通知"""
        if not self.window:
            return

        self.should_close = True

        try:
            # 淡出动画
            self._fade_out()

            # 关闭窗口
            if self.window:
                self.window.quit()
                self.window.destroy()
                self.window = None
        except Exception as e:
            logger.debug(f"关闭通知窗口: {e}")
        finally:
            self.is_showing = False


# 全局通知实例
_notification: Optional[FancyNotification] = None


def show_fancy_processing(message: str = "正在处理文本..."):
    """显示处理中通知（蓝色，带旋转动画）"""
    global _notification
    _notification = FancyNotification()
    _notification.show(message, notification_type="processing", duration=0)


def show_fancy_success(message: str = "✓ 处理完成", duration: int = 2):
    """显示成功通知（绿色）"""
    global _notification
    if _notification:
        _notification.close()
        time.sleep(0.3)  # 等待关闭

    _notification = FancyNotification()
    _notification.show(message, notification_type="success", duration=duration)


def show_fancy_error(message: str, duration: int = 3):
    """显示错误通知（红色）"""
    global _notification
    if _notification:
        _notification.close()
        time.sleep(0.3)

    _notification = FancyNotification()
    _notification.show(message, notification_type="error", duration=duration)


def show_fancy_info(message: str, duration: int = 2):
    """显示信息通知（浅蓝）"""
    global _notification
    if _notification:
        _notification.close()
        time.sleep(0.3)

    _notification = FancyNotification()
    _notification.show(message, notification_type="info", duration=duration)


def close_fancy_notification():
    """关闭当前通知"""
    global _notification
    if _notification:
        _notification.close()
        _notification = None
