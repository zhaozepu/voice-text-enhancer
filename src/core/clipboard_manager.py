"""
剪贴板管理模块
提供剪贴板内容的保存和恢复功能
"""
import pyperclip
from typing import Optional
from loguru import logger


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
            content = pyperclip.paste()
            self._saved_content = content
            logger.debug(f"保存剪贴板内容，长度: {len(content) if content else 0}")
            return content
        except Exception as e:
            logger.error(f"保存剪贴板失败: {e}")
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

            pyperclip.copy(content)
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
            pyperclip.copy(text)
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
            text = pyperclip.paste()
            logger.debug(f"从剪贴板读取文本，长度: {len(text) if text else 0}")
            return text
        except Exception as e:
            logger.error(f"从剪贴板读取失败: {e}")
            return ""

    def clear(self):
        """清空剪贴板"""
        try:
            pyperclip.copy("")
            logger.debug("清空剪贴板")
        except Exception as e:
            logger.error(f"清空剪贴板失败: {e}")
