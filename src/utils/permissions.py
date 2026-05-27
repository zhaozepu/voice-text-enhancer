"""
macOS 权限检查与请求
"""
import subprocess
from typing import Tuple
from loguru import logger


def check_accessibility() -> bool:
    """
    检查"辅助功能"权限（用于模拟键盘输入）
    通过 AXIsProcessTrusted 检查
    """
    try:
        from ApplicationServices import AXIsProcessTrusted
        return bool(AXIsProcessTrusted())
    except Exception as e:
        logger.warning(f"无法检测辅助功能权限: {e}")
        return False


def _load_iokit():
    """通过 ctypes 加载 IOKit 框架"""
    import ctypes
    iokit = ctypes.CDLL('/System/Library/Frameworks/IOKit.framework/IOKit')
    iokit.IOHIDCheckAccess.argtypes = [ctypes.c_uint32]
    iokit.IOHIDCheckAccess.restype = ctypes.c_int
    iokit.IOHIDRequestAccess.argtypes = [ctypes.c_uint32]
    iokit.IOHIDRequestAccess.restype = ctypes.c_bool
    return iokit


# kIOHIDRequestTypeListenEvent = 1
_REQ_LISTEN_EVENT = 1


def check_input_monitoring() -> bool:
    """
    检查"输入监控"权限（用于全局快捷键监听）
    通过 IOKit.IOHIDCheckAccess
    返回值: 0 = granted, 1 = denied, 2 = unknown
    """
    try:
        iokit = _load_iokit()
        access = iokit.IOHIDCheckAccess(_REQ_LISTEN_EVENT)
        return access == 0
    except Exception as e:
        logger.warning(f"无法检测输入监控权限: {e}")
        return False


def request_input_monitoring() -> bool:
    """
    主动请求"输入监控"权限（首次会触发系统弹窗）
    """
    try:
        iokit = _load_iokit()
        return bool(iokit.IOHIDRequestAccess(_REQ_LISTEN_EVENT))
    except Exception as e:
        logger.warning(f"无法请求输入监控权限: {e}")
        return False


def open_accessibility_settings():
    """打开 系统设置 → 隐私与安全性 → 辅助功能"""
    subprocess.Popen([
        "open",
        "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"
    ])


def open_input_monitoring_settings():
    """打开 系统设置 → 隐私与安全性 → 输入监控"""
    subprocess.Popen([
        "open",
        "x-apple.systempreferences:com.apple.preference.security?Privacy_ListenEvent"
    ])


def get_all_permissions() -> dict:
    """获取所有权限的当前状态"""
    return {
        "accessibility": check_accessibility(),
        "input_monitoring": check_input_monitoring(),
    }
