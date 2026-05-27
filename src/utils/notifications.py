"""
系统通知模块
使用 macOS 通知中心显示消息和进度提示
"""
import subprocess
import threading
import time
from typing import Optional
from loguru import logger


def show_notification(title: str, message: str = "", sound: bool = False):
    """
    显示 macOS 系统通知

    Args:
        title: 通知标题
        message: 通知消息内容
        sound: 是否播放声音
    """
    try:
        sound_param = ' sound name "default"' if sound else ''
        script = f'display notification "{message}" with title "{title}"{sound_param}'

        subprocess.run(
            ['osascript', '-e', script],
            check=True,
            capture_output=True,
            text=True
        )

        logger.debug(f"显示通知: {title} - {message}")
    except subprocess.CalledProcessError as e:
        logger.error(f"显示通知失败: {e}")
    except Exception as e:
        logger.error(f"显示通知异常: {e}")


def show_error(message: str):
    """
    显示错误通知

    Args:
        message: 错误消息
    """
    show_notification("文本增强工具 - 错误", message, sound=True)


def show_success(message: str):
    """
    显示成功通知

    Args:
        message: 成功消息
    """
    show_notification("文本增强工具", message, sound=False)


def show_info(message: str):
    """
    显示信息通知

    Args:
        message: 信息内容
    """
    show_notification("文本增强工具", message, sound=False)


class ProgressIndicator:
    """
    进度提示对话框
    使用 AppleScript 显示一个带进度条的对话框
    """

    def __init__(self, message: str = "正在处理文本..."):
        """
        初始化进度提示

        Args:
            message: 提示消息
        """
        self.message = message
        self._process: Optional[subprocess.Popen] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False

    def start(self):
        """启动进度提示"""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._show_progress, daemon=True)
        self._thread.start()
        logger.debug("进度提示已启动")

    def stop(self):
        """停止进度提示"""
        if not self._running:
            return

        self._running = False

        if self._process and self._process.poll() is None:
            try:
                self._process.terminate()
                self._process.wait(timeout=1)
            except Exception as e:
                logger.error(f"关闭进度提示失败: {e}")

        logger.debug("进度提示已停止")

    def _show_progress(self):
        """
        显示进度对话框（在后台线程中运行）
        使用动画文本来模拟进度
        """
        try:
            animation_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
            frame_idx = 0

            while self._running:
                spinner = animation_frames[frame_idx % len(animation_frames)]
                display_message = f"{spinner} {self.message}"

                script = f'''
                display notification "{display_message}" with title "文本增强工具"
                '''

                try:
                    subprocess.run(
                        ['osascript', '-e', script],
                        check=True,
                        capture_output=True,
                        text=True,
                        timeout=1
                    )
                except subprocess.TimeoutExpired:
                    pass
                except Exception:
                    pass

                frame_idx += 1
                time.sleep(0.5)

        except Exception as e:
            logger.error(f"进度提示异常: {e}")

    def __enter__(self):
        """上下文管理器入口"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.stop()
        return False
