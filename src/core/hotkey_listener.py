"""
快捷键监听模块
使用 pynput 监听全局快捷键（支持单键和组合键，支持多个快捷键同时监听）
"""
from pynput import keyboard
from pynput.keyboard import Key
from typing import Callable, Optional, List, Dict
from loguru import logger
import time


class HotkeyListener:
    """快捷键监听器（支持多个快捷键同时监听）"""

    def __init__(self, bindings: List[Dict[str, any]]):
        """
        初始化快捷键监听器

        Args:
            bindings: 快捷键绑定列表，每个元素包含:
                {
                    'hotkey': 'right_option',  # 快捷键字符串
                    'callback': func,           # 触发时的回调函数
                    'name': 'binding_name'      # 绑定名称（用于日志）
                }
        """
        self.bindings = bindings
        self.listener = None

        # 单键绑定状态：key对象 -> {callback, name, pressed, last_press_time}
        self.single_key_bindings = {}

        # 组合键绑定：hotkey_str -> {hotkey对象, callback, name}
        self.combo_key_bindings = {}

        # 解析所有绑定
        for binding in bindings:
            hotkey_str = binding['hotkey']
            callback = binding['callback']
            name = binding.get('name', hotkey_str)

            if hotkey_str in ['right_option', 'right_alt', 'left_option', 'left_alt', 'right_cmd', 'right_ctrl']:
                # 单键模式
                key_obj = self._parse_single_key(hotkey_str)
                if key_obj:
                    self.single_key_bindings[key_obj] = {
                        'callback': callback,
                        'name': name,
                        'pressed': False,
                        'last_press_time': 0
                    }
                    logger.info(f"已注册单键绑定: {name} ({hotkey_str})")
            else:
                # 组合键模式
                try:
                    hotkey_obj = keyboard.HotKey(
                        keyboard.HotKey.parse(hotkey_str),
                        lambda cb=callback, n=name: self._on_combo_activate(cb, n)
                    )
                    self.combo_key_bindings[hotkey_str] = {
                        'hotkey': hotkey_obj,
                        'callback': callback,
                        'name': name
                    }
                    logger.info(f"已注册组合键绑定: {name} ({hotkey_str})")
                except Exception as e:
                    logger.error(f"快捷键配置错误 ({hotkey_str}): {e}")

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

    def _on_combo_activate(self, callback: Callable, name: str):
        """组合键激活时的回调"""
        logger.info(f"组合键触发: {name}")
        try:
            callback()
        except Exception as e:
            logger.exception(f"回调函数执行失败 ({name}): {e}")

    def _on_press(self, key):
        """按键按下事件"""
        # 检查单键绑定
        if key in self.single_key_bindings:
            binding = self.single_key_bindings[key]
            binding['pressed'] = True
            binding['last_press_time'] = time.time()
            logger.info(f"目标键按下: {binding['name']}")

        # 通知所有组合键对象
        for combo_data in self.combo_key_bindings.values():
            try:
                combo_data['hotkey'].press(self.listener.canonical(key))
            except AttributeError:
                pass

    def _on_release(self, key):
        """按键释放事件"""
        # 检查单键绑定
        if key in self.single_key_bindings:
            binding = self.single_key_bindings[key]
            if binding['pressed']:
                release_time = time.time()
                press_duration = release_time - binding['last_press_time']

                # 只在快速按下释放时触发（< 0.5秒），防止长按误触
                if press_duration < 0.5:
                    logger.debug(f"单键触发: {binding['name']}，按压时长: {press_duration:.3f}秒")
                    try:
                        binding['callback']()
                    except Exception as e:
                        logger.exception(f"回调函数执行失败 ({binding['name']}): {e}")
                else:
                    logger.debug(f"按压时长过长({press_duration:.3f}秒)，忽略")

                binding['pressed'] = False

        # 通知所有组合键对象
        for combo_data in self.combo_key_bindings.values():
            try:
                combo_data['hotkey'].release(self.listener.canonical(key))
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
        logger.info(f"快捷键监听已启动，共 {len(self.bindings)} 个绑定")

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
