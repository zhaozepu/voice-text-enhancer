"""
文本处理核心模块
实现文本获取 → API 处理 → 替换的完整流程
"""
import time
import asyncio
import pyautogui
from loguru import logger

import os
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
        self._cancelled = False

    def cancel(self):
        """取消当前处理任务"""
        if self._processing:
            logger.info("收到取消请求，正在取消任务...")
            self._cancelled = True

    async def process_selected_text(self, with_screenshot: bool = False):
        """
        处理当前选中的文本
        这是主要的处理流程入口

        Args:
            with_screenshot: 为 True 时走"截屏 + 选中文本 → 模型 → 剪贴板"流程，不替换原文
        """
        if self._processing:
            logger.warning("正在处理中，忽略重复触发")
            return

        self._processing = True
        self._cancelled = False  # 重置取消标志

        try:
            if with_screenshot:
                await self._do_process_screenshot()
            else:
                await self._do_process(with_screenshot=False)
        except asyncio.CancelledError:
            logger.info("任务已被用户取消")
            close_fancy_notification()
            await asyncio.sleep(0.1)
            if self.config.get('notifications', {}).get('show_errors', True):
                show_fancy_error("✗ 已取消", duration=1.5)
        except Exception as e:
            logger.exception("处理文本时发生异常")
            if self.config.get('notifications', {}).get('show_errors', True):
                show_error(f"处理失败: {str(e)}")
        finally:
            self._processing = False
            self._cancelled = False

    async def _do_process_screenshot(self):
        """
        截屏 + OCR + 选中文本 → 模型 → 结果直接放入剪贴板（不粘贴回原位置）
        """
        from ..utils.screen_ocr import capture_and_ocr, ScreenCaptureError

        logger.info("开始截屏流程")
        original_clipboard = self.clipboard_mgr.save()
        screenshot_path = None
        screen_text = ""

        try:
            # 1. 截屏 + OCR（保留快门音，作为视觉/听觉反馈）
            try:
                screen_text, screenshot_path = await asyncio.to_thread(capture_and_ocr)
                logger.info(f"屏幕 OCR 文本长度: {len(screen_text)}")
            except ScreenCaptureError as e:
                logger.error(f"{e}")
                close_fancy_notification()
                await asyncio.sleep(0.1)
                show_fancy_error("✗ 缺少屏幕录制权限", duration=3)
                return

            if self._cancelled:
                raise asyncio.CancelledError()

            # 2. 取选中文本（可选：用户没选也能跑，纯靠 OCR 内容）
            selected_text = await self._get_selected_text()
            if not selected_text or not selected_text.strip():
                selected_text = "（用户未选中文本，请基于屏幕 OCR 内容自行判断需要处理的对象）"
            logger.info(f"选中文本长度: {len(selected_text)}")

            if self._cancelled:
                raise asyncio.CancelledError()

            # 3. 调模型（OCR 文本作为上下文前缀）
            enhanced_text = await self._enhance_text(selected_text, screen_text=screen_text)
            if not enhanced_text or not enhanced_text.strip():
                raise ValueError("API 返回了空文本")

            # 4. 把结果放入剪贴板（不粘贴），同时不恢复原剪贴板
            self.clipboard_mgr.copy(enhanced_text)
            await asyncio.sleep(0.2)
            logger.info(f"结果已写入剪贴板，长度: {len(enhanced_text)}")

            close_fancy_notification()
            await asyncio.sleep(0.1)
            if self.config.get('notifications', {}).get('show_completion', True):
                show_fancy_success("✓ 已放入剪贴板，Cmd+V 粘贴", duration=2.5)

        except asyncio.CancelledError:
            close_fancy_notification()
            await asyncio.sleep(0.1)
            show_fancy_error("✗ 已取消", duration=1.5)
            self.clipboard_mgr.restore(original_clipboard)
            raise
        except Exception as e:
            close_fancy_notification()
            await asyncio.sleep(0.1)
            if self.config.get('notifications', {}).get('show_errors', True):
                show_fancy_error(f"处理失败: {e}", duration=3)
            self.clipboard_mgr.restore(original_clipboard)
            raise
        finally:
            if screenshot_path:
                try:
                    os.unlink(screenshot_path)
                except Exception:
                    pass

    async def _do_process(self, with_screenshot: bool = False):
        """
        执行实际的文本处理流程
        """
        logger.info(f"开始处理流程 (with_screenshot={with_screenshot})")
        original_clipboard = self.clipboard_mgr.save()
        logger.info(f"保存原剪贴板，长度: {len(original_clipboard) if original_clipboard else 0}")

        screen_text = ""
        screenshot_path = None

        try:
            selected_text = await self._get_selected_text()
            logger.info(f"获取到的文本: '{selected_text[:50] if selected_text else '(空)'}...'，长度: {len(selected_text) if selected_text else 0}")

            # 文本为空 → 当前不在输入框或输入框为空，静默返回
            if not selected_text or not selected_text.strip():
                logger.info("无文本可处理（光标可能不在输入框），静默跳过")
                return

            # 如果文本很短（≤3字符）且与剪贴板一致，可能是误触，静默跳过
            if len(selected_text.strip()) <= 3 and selected_text == original_clipboard:
                logger.info("文本过短且与剪贴板一致，可能是误触，静默跳过")
                return

            # 文本超长（大概率为误操作，例如全选了整篇文档），不发起 API 请求
            max_length = self.config.get('max_input_length', 5000)
            if len(selected_text) > max_length:
                logger.warning(f"文本长度 {len(selected_text)} 超过上限 {max_length}，疑似误操作，跳过")
                close_fancy_notification()
                await asyncio.sleep(0.1)
                if self.config.get('notifications', {}).get('show_errors', True):
                    show_fancy_error(
                        f"✗ 文本过长（{len(selected_text)}字），疑似误操作",
                        duration=2.5,
                    )
                return

            logger.info(f"获取到选中文本，长度: {len(selected_text)}")

            # 检查是否被取消
            if self._cancelled:
                logger.info("任务在获取文本后被取消")
                raise asyncio.CancelledError()

            # 动效已在快捷键触发时显示，这里直接处理
            enhanced_text = await self._enhance_text(selected_text, screen_text=screen_text)

            # 检查是否被取消
            if self._cancelled:
                logger.info("任务在 API 调用后被取消")
                raise asyncio.CancelledError()

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

            # 清理截屏临时文件
            if screenshot_path:
                try:
                    os.unlink(screenshot_path)
                    logger.info(f"已清理截屏临时文件: {screenshot_path}")
                except Exception:
                    pass

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

    async def _enhance_text(self, text: str, screen_text: str = "") -> str:
        """
        调用 API 增强文本

        Args:
            text: 原始文本
            screen_text: 屏幕 OCR 文本（可选，作为上下文）

        Returns:
            增强后的文本
        """
        active_prompt_name = self.config.get('active_prompt', 'expand')
        prompts = self.config.get('prompts', {})

        if active_prompt_name not in prompts:
            logger.error(f"Prompt '{active_prompt_name}' 不存在，使用默认 expand")
            active_prompt_name = 'expand'

        prompt_template = prompts.get(active_prompt_name, '')

        # 如果有屏幕 OCR 上下文，把它作为额外信息附在用户消息前
        if screen_text and screen_text.strip():
            text = (
                "【当前屏幕 OCR 文本（仅作为上下文参考）】\n"
                f"{screen_text}\n"
                "【需要处理的文本】\n"
                f"{text}"
            )

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
