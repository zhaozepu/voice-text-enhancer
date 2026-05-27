"""
快捷键监听模块
使用 pynput 监听全局快捷键（支持单键和组合键）
"""
from pynput import keyboard
from pynput.keyboard import Key
from typing import Callable, Optional
from loguru import logger
import time


class HotkeyListener:
    """快捷键监听器"""

    def __init__(self, hotkey_combination: str, callback: Callable):
        """
        初始化快捷键监听器

        Args:
            hotkey_combination: 快捷键组合
                - 组合键格式: '<cmd>+<shift>+p'
                - 单键格式: 'right_option', 'left_option', 'right_cmd' 等
            callback: 触发时执行的回调函数
        """
        self.hotkey_combination = hotkey_combination
        self.callback = callback
        self.listener = None
        self.hotkey = None
        self.is_single_key = False
        self.target_key = None
        self.last_press_time = 0
        self.key_pressed = False

        # 检测是否是单键模式
        if hotkey_combination in ['right_option', 'right_alt', 'right_cmd', 'right_ctrl']:
            self.is_single_key = True
            self.target_key = self._parse_single_key(hotkey_combination)
            logger.info(f"单键模式已配置: {hotkey_combination}")
        else:
            # 组合键模式
            try:
                self.hotkey = keyboard.HotKey(
                    keyboard.HotKey.parse(hotkey_combination),
                    self._on_activate
                )
                logger.info(f"组合键已配置: {hotkey_combination}")
            except Exception as e:
                logger.error(f"快捷键配置错误: {e}")
                raise ValueError(f"快捷键格式错误: {hotkey_combination}")

    def _parse_single_key(self, key_name: str) -> Optional[Key]:
        """
        解析单键名称为 Key 对象

        Args:
            key_name: 键名称

        Returns:
            Key 对象
        """
        key_map = {
            'right_option': Key.alt_r,
            'right_alt': Key.alt_r,
            'left_option': Key.alt,
            'left_alt': Key.alt,
            'right_cmd': Key.cmd_r,
            'right_ctrl': Key.ctrl_r,
        }
        return key_map.get(key_name)

    def _on_activate(self):
        """快捷键激活时的回调"""
        logger.info("快捷键被触发")
        try:
            self.callback()
        except Exception as e:
            logger.exception(f"回调函数执行失败: {e}")

    def _on_press(self, key):
        """按键按下事件"""
        if self.is_single_key:
            # 单键模式
            if key == self.target_key:
                self.key_pressed = True
                self.last_press_time = time.time()
                logger.debug(f"目标键按下: {key}")
        else:
            # 组合键模式
            try:
                self.hotkey.press(self.listener.canonical(key))
            except AttributeError:
                pass

    def _on_release(self, key):
        """按键释放事件"""
        if self.is_single_key:
            # 单键模式：按下后快速释放触发（防止长按误触）
            if key == self.target_key and self.key_pressed:
                release_time = time.time()
                press_duration = release_time - self.last_press_time

                # 只在快速按下释放时触发（< 0.5秒），防止长按误触
                if press_duration < 0.5:
                    logger.debug(f"目标键释放，按压时长: {press_duration:.3f}秒")
                    self._on_activate()
                else:
                    logger.debug(f"按压时长过长({press_duration:.3f}秒)，忽略")

                self.key_pressed = False
        else:
            # 组合键模式
            try:
                self.hotkey.release(self.listener.canonical(key))
            except AttributeError:
                pass

    def start(self):
        """启动监听"""
        if self.listener is not None:
            logger.warning("监听器已经在运行")
            return

        self.listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release
        )

        self.listener.start()
        logger.info("快捷键监听已启动")

    def stop(self):
        """停止监听"""
        if self.listener is None:
            logger.warning("监听器未运行")
            return

        self.listener.stop()
        self.listener = None
        logger.info("快捷键监听已停止")

    def is_running(self) -> bool:
        """
        检查监听器是否正在运行

        Returns:
            是否正在运行
        """
        return self.listener is not None and self.listener.is_alive()
