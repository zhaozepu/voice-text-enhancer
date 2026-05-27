"""
文本处理核心模块
实现文本获取 → API 处理 → 替换的完整流程
"""
import time
import asyncio
import pyautogui
from loguru import logger

from .clipboard_manager import ClipboardManager
from ..api.deepseek_client import DeepSeekClient
from ..utils.notifications import show_info, show_error, show_success
from ..utils.desktop_notification import (
    show_desktop_processing as show_fancy_processing,
    show_desktop_success as show_fancy_success,
    show_desktop_error as show_fancy_error,
    close_desktop_notification as close_fancy_notification,
)


class TextProcessor:
    """文本处理器"""

    def __init__(self, api_client: DeepSeekClient, config: dict):
        """
        初始化文本处理器

        Args:
            api_client: DeepSeek API 客户端
            config: 配置字典
        """
        self.api_client = api_client
        self.config = config
        self.clipboard_mgr = ClipboardManager()
        self._processing = False

    async def process_selected_text(self):
        """
        处理当前选中的文本
        这是主要的处理流程入口
        """
        if self._processing:
            logger.warning("正在处理中，忽略重复触发")
            return

        self._processing = True

        try:
            await self._do_process()
        except Exception as e:
            logger.exception("处理文本时发生异常")
            if self.config.get('notifications', {}).get('show_errors', True):
                show_error(f"处理失败: {str(e)}")
        finally:
            self._processing = False

    async def _do_process(self):
        """
        执行实际的文本处理流程
        """
        logger.info("开始处理流程")
        original_clipboard = self.clipboard_mgr.save()
        logger.info(f"保存原剪贴板，长度: {len(original_clipboard) if original_clipboard else 0}")

        try:
            selected_text = await self._get_selected_text()
            logger.info(f"获取到的文本: '{selected_text[:50] if selected_text else '(空)'}...'，长度: {len(selected_text) if selected_text else 0}")

            if not selected_text or not selected_text.strip():
                logger.warning("未获取到文本或文本为空")
                if self.config.get('notifications', {}).get('show_errors', True):
                    show_fancy_error("请先在输入框中输入文本", duration=3)
                return

            if selected_text == original_clipboard:
                logger.warning("选中的文本与剪贴板内容相同，可能没有实际选中文本")

            logger.info(f"获取到选中文本，长度: {len(selected_text)}")

            # 显示漂亮的处理中通知
            if self.config.get('notifications', {}).get('show_processing', True):
                show_fancy_processing("正在处理文本，请稍候...")

            enhanced_text = await self._enhance_text(selected_text)

            if not enhanced_text or not enhanced_text.strip():
                raise ValueError("API 返回了空文本")

            await self._replace_text(enhanced_text)

            # 关闭处理中通知，显示成功通知
            close_fancy_notification()
            await asyncio.sleep(0.1)

            if self.config.get('notifications', {}).get('show_completion', True):
                show_fancy_success("✓ 文本处理完成", duration=2)

            logger.info("文本处理流程完成")

        except Exception as e:
            # 关闭处理中通知，显示错误通知
            close_fancy_notification()
            await asyncio.sleep(0.1)

            if self.config.get('notifications', {}).get('show_errors', True):
                error_msg = str(e) if str(e) else "处理失败"
                show_fancy_error(f"处理失败: {error_msg}", duration=3)

            raise

        finally:
            # 等待确保所有操作完成再恢复剪贴板（重要！）
            await asyncio.sleep(0.5)
            logger.info("准备恢复原剪贴板")
            self.clipboard_mgr.restore(original_clipboard)
            logger.info("剪贴板已恢复")

    async def _get_selected_text(self) -> str:
        """
        自动全选并获取输入框内的所有文本

        Returns:
            输入框内的文本内容
        """
        logger.info("自动全选输入框内容（模拟 Cmd+A）")

        try:
            # 先全选输入框内的所有内容
            pyautogui.hotkey('command', 'a')
            logger.info("已执行 Cmd+A 全选")

            # 等待全选完成
            await asyncio.sleep(0.2)

            # 复制选中的内容
            pyautogui.hotkey('command', 'c')
            logger.info("已执行 Cmd+C 复制")
        except Exception as e:
            logger.error(f"模拟键盘操作失败: {e}")
            raise

        # 等待复制完成
        await asyncio.sleep(0.3)

        text = self.clipboard_mgr.paste()
        logger.info(f"从剪贴板读取到文本长度: {len(text) if text else 0}")
        return text

    async def _enhance_text(self, text: str) -> str:
        """
        调用 API 增强文本

        Args:
            text: 原始文本

        Returns:
            增强后的文本
        """
        active_prompt_name = self.config.get('active_prompt', 'expand')
        prompts = self.config.get('prompts', {})

        if active_prompt_name not in prompts:
            logger.error(f"Prompt '{active_prompt_name}' 不存在，使用默认 expand")
            active_prompt_name = 'expand'

        prompt_template = prompts.get(active_prompt_name, '')

        logger.info(f"使用 Prompt: {active_prompt_name}")

        enhanced_text = await self.api_client.enhance_text(text, prompt_template)

        return enhanced_text

    async def _replace_text(self, text: str):
        """
        替换输入框中的所有文本

        Args:
            text: 要替换的文本
        """
        logger.info(f"将处理后的文本写入剪贴板，长度: {len(text)}")
        self.clipboard_mgr.copy(text)

        # 等待剪贴板写入完成（重要！）
        await asyncio.sleep(0.5)

        # 验证剪贴板内容
        verify = self.clipboard_mgr.paste()
        logger.info(f"验证剪贴板，长度: {len(verify)}，匹配: {verify == text}")

        if verify != text:
            logger.error("剪贴板内容不匹配，重新写入")
            self.clipboard_mgr.copy(text)
            await asyncio.sleep(0.3)

        # 先全选，确保替换所有内容
        logger.info("全选输入框内容准备替换")
        pyautogui.hotkey('command', 'a')

        await asyncio.sleep(0.2)

        # 粘贴新内容
        logger.info("粘贴处理后的文本")
        pyautogui.hotkey('command', 'v')

        # 等待粘贴完成（重要！）
        await asyncio.sleep(0.5)
        logger.info("粘贴操作完成")
