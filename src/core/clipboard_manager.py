"""
剪贴板管理模块
提供剪贴板内容的保存和恢复功能
使用 macOS 原生 API 安全处理非文本内容
"""
import pyperclip
from typing import Optional
from loguru import logger


def _safe_paste() -> str:
    """
    安全地从剪贴板读取文本内容
    使用 macOS NSPasteboard API，避免非文本内容导致崩溃
    """
    try:
        from AppKit import NSPasteboard
        pb = NSPasteboard.generalPasteboard()
        # 只获取字符串类型的内容
        text = pb.stringForType_("public.utf8-plain-text")
        if text is None:
            # 尝试其他文本类型
            text = pb.stringForType_("NSStringPboardType")
        if text is None:
            return ""
        return str(text)
    except Exception as e:
        logger.debug(f"NSPasteboard 读取失败，回退到 pyperclip: {e}")
        # 回退到 pyperclip
        try:
            text = pyperclip.paste()
            if not isinstance(text, str):
                return ""
            return text
        except Exception:
            return ""


def _safe_copy(text: str):
    """
    安全地复制文本到剪贴板
    """
    try:
        from AppKit import NSPasteboard
        pb = NSPasteboard.generalPasteboard()
        pb.clearContents()
        pb.setString_forType_(text, "public.utf8-plain-text")
    except Exception as e:
        logger.debug(f"NSPasteboard 写入失败，回退到 pyperclip: {e}")
        # 回退到 pyperclip
        pyperclip.copy(text)


class ClipboardManager:
    """剪贴板管理器"""

    def __init__(self):
        """初始化剪贴板管理器"""
        self._saved_content: Optional[str] = None

    def save(self) -> str:
        """
        保存当前剪贴板内容

        Returns:
            当前剪贴板的内容
        """
        try:
            content = _safe_paste()
            self._saved_content = content
            logger.debug(f"保存剪贴板内容，长度: {len(content) if content else 0}")
            return content
        except Exception as e:
            # 剪贴板可能包含非文本内容（图片、颜色等），静默处理
            logger.warning(f"保存剪贴板失败: {e}")
            self._saved_content = ""
            return ""

    def restore(self, content: Optional[str] = None):
        """
        恢复剪贴板内容

        Args:
            content: 要恢复的内容。如果为 None，则恢复之前保存的内容
        """
        try:
            if content is None:
                content = self._saved_content or ""

            _safe_copy(content)
            logger.debug(f"恢复剪贴板内容，长度: {len(content) if content else 0}")
        except Exception as e:
            logger.error(f"恢复剪贴板失败: {e}")

    def copy(self, text: str):
        """
        复制文本到剪贴板

        Args:
            text: 要复制的文本
        """
        try:
            _safe_copy(text)
            logger.debug(f"复制文本到剪贴板，长度: {len(text)}")
        except Exception as e:
            logger.error(f"复制到剪贴板失败: {e}")
            raise

    def paste(self) -> str:
        """
        从剪贴板粘贴文本

        Returns:
            剪贴板中的文本
        """
        try:
            text = _safe_paste()
            logger.debug(f"从剪贴板读取文本，长度: {len(text) if text else 0}")
            return text
        except Exception as e:
            # 剪贴板可能包含非文本内容（图片、颜色等），静默处理
            logger.warning(f"从剪贴板读取失败: {e}")
            return ""

    def clear(self):
        """清空剪贴板"""
        try:
            _safe_copy("")
            logger.debug("清空剪贴板")
        except Exception as e:
            logger.error(f"清空剪贴板失败: {e}")
