"""
桌面浮层通知（Lottie 动画，透明无框）
通过独立的 helper 进程显示，避免主线程阻塞

当前阶段:
- 处理中: 显示 Lottie 动画
- 成功/错误/信息: 暂时只关闭动画（待补充资源后扩展）
"""
import sys
import os
import json
import subprocess
import atexit
from pathlib import Path
from typing import Optional
from loguru import logger


def get_helper_script() -> Path:
    """获取 helper 脚本路径（兼容打包模式）"""
    if getattr(sys, 'frozen', False):
        # 打包后从 _MEIPASS 加载
        return Path(sys._MEIPASS) / 'src' / 'utils' / 'notification_helper.py'
    return Path(__file__).parent / 'notification_helper.py'


class NotificationProcess:
    """通知进程管理器"""

    def __init__(self):
        self.process: Optional[subprocess.Popen] = None

    def ensure_running(self) -> bool:
        """确保通知进程正在运行"""
        if self.process and self.process.poll() is None:
            return True

        try:
            env = {**os.environ, 'VTE_HELPER_MODE': '1'}

            if getattr(sys, 'frozen', False):
                # 打包模式：调用 .app 自身可执行文件，通过环境变量切换为 helper 模式
                cmd = [sys.executable]
            else:
                # 开发模式：用当前 Python 解释器运行 helper 脚本
                cmd = [sys.executable, str(get_helper_script())]

            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                bufsize=0,
                text=True,
                env=env,
            )
            atexit.register(self.shutdown)
            logger.info(f"通知进程已启动 (PID: {self.process.pid})")
            return True
        except Exception as e:
            logger.error(f"启动通知进程失败: {e}")
            return False

    def send_command(self, cmd: dict) -> bool:
        """发送命令到通知进程"""
        if not self.ensure_running():
            return False

        try:
            line = json.dumps(cmd, ensure_ascii=False) + '\n'
            self.process.stdin.write(line)
            self.process.stdin.flush()
            return True
        except (BrokenPipeError, OSError) as e:
            logger.warning(f"发送命令失败，重启进程: {e}")
            self.process = None
            return False

    def shutdown(self):
        """关闭通知进程（确保子进程一定退出，避免孤儿动效残留）"""
        if not self.process:
            return
        if self.process.poll() is not None:
            self.process = None
            return

        # 先尝试优雅退出
        try:
            self.send_command({'action': 'quit'})
        except Exception:
            pass
        try:
            self.process.wait(timeout=0.8)
        except Exception:
            pass

        # 兜底：terminate
        if self.process.poll() is None:
            try:
                self.process.terminate()
                self.process.wait(timeout=0.5)
            except Exception:
                pass

        # 最后兜底：SIGKILL
        if self.process.poll() is None:
            try:
                self.process.kill()
            except Exception:
                pass

        self.process = None


_notif_process: Optional[NotificationProcess] = None


def _get_process() -> NotificationProcess:
    global _notif_process
    if _notif_process is None:
        _notif_process = NotificationProcess()
    return _notif_process


def show_desktop_processing(message: str = ""):
    """显示处理中动效（Lottie 动画，无文案）"""
    _get_process().send_command({'action': 'show', 'duration': 0})


def show_desktop_success(message: str = "", duration: float = 2.0):
    """成功 - 占位实现：仅关闭动效（待补充资源）"""
    _get_process().send_command({'action': 'hide'})


def show_desktop_error(message: str = "", duration: float = 3.0):
    """错误 - 占位实现：仅关闭动效（待补充资源）"""
    _get_process().send_command({'action': 'hide'})


def show_desktop_info(message: str = "", duration: float = 2.0):
    """信息 - 占位实现：什么也不做（待补充资源）"""
    pass


def close_desktop_notification():
    """关闭当前动效"""
    _get_process().send_command({'action': 'hide'})


def set_dot_count(count: int):
    """更新暂存上下文圆点数量（0 表示隐藏）"""
    try:
        _get_process().send_command({'action': 'dots', 'count': int(count)})
    except Exception as e:
        logger.warning(f"更新圆点失败: {e}")


def shutdown_notification():
    """关闭通知进程（程序退出时调用）"""
    global _notif_process
    if _notif_process:
        _notif_process.shutdown()
        _notif_process = None
