"""
快捷键监听模块
使用 pynput 监听全局快捷键（支持单键和组合键，支持多个快捷键同时监听）
"""
from pynput import keyboard
from pynput.keyboard import Key
from typing import Callable, Optional, List, Dict, Tuple
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

        # 序列绑定：(first_key_obj, second_key_obj) -> {callback, name, max_gap_sec}
        # 形如 "left_option>right_option" 表示先 tap 第一个键、再 tap 第二个键
        self.sequence_bindings = {}
        # 序列状态：first_key_obj -> last_release_time（最近一次 tap 完成时间）
        self._sequence_pending = {}
        # 序列触发后，吞掉紧随其后的第二个键的单键触发
        self._sequence_consumed_keys = set()
        # 所有序列涉及的键，按下时间记录（不依赖 single_key_bindings）
        self._sequence_press_time = {}

        # 解析所有绑定
        for binding in bindings:
            hotkey_str = binding['hotkey']
            callback = binding['callback']
            name = binding.get('name', hotkey_str)

            if '>' in hotkey_str:
                # 序列绑定：first>second
                parts = [p.strip() for p in hotkey_str.split('>')]
                if len(parts) != 2:
                    logger.error(f"序列快捷键格式错误({hotkey_str}), 应为 'a>b'")
                    continue
                first_key = self._parse_single_key(parts[0])
                second_key = self._parse_single_key(parts[1])
                if first_key is None or second_key is None:
                    logger.error(f"序列快捷键键名解析失败: {hotkey_str}")
                    continue
                self.sequence_bindings[(first_key, second_key)] = {
                    'callback': callback,
                    'name': name,
                    'max_gap': binding.get('max_gap_sec', 0.8),
                }
                logger.info(f"已注册序列绑定: {name} ({hotkey_str})")
            elif hotkey_str in ['right_option', 'right_alt', 'left_option', 'left_alt', 'right_cmd', 'right_ctrl', 'esc']:
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
            # 左 Option：pynput 在 macOS 上左 Option 报为 Key.alt（不是 alt_l）
            'left_option': Key.alt,
            'left_alt': Key.alt,
            'right_cmd': Key.cmd_r,
            'right_ctrl': Key.ctrl_r,
            'esc': Key.esc,
        }
        return key_map.get(key_name)

    def _is_sequence_key(self, key) -> Tuple[bool, bool]:
        """判断该键在序列绑定中扮演的角色，返回 (is_first, is_second)"""
        is_first = any(key == fk for (fk, _) in self.sequence_bindings.keys())
        is_second = any(key == sk for (_, sk) in self.sequence_bindings.keys())
        return is_first, is_second

    def _on_combo_activate(self, callback: Callable, name: str):
        """组合键激活时的回调"""
        logger.info(f"组合键触发: {name}")
        try:
            callback()
        except Exception as e:
            logger.exception(f"回调函数执行失败 ({name}): {e}")

    def _on_press(self, key):
        """按键按下事件"""
        now = time.time()

        # 检查单键绑定
        if key in self.single_key_bindings:
            binding = self.single_key_bindings[key]
            binding['pressed'] = True
            binding['last_press_time'] = now
            logger.info(f"目标键按下: {binding['name']}")

        # 序列键独立记录按下时间（即使该键没有单键绑定）
        is_first, is_second = self._is_sequence_key(key)
        if is_first or is_second:
            self._sequence_press_time[key] = now
            logger.debug(f"序列键按下: {key} @ {now:.3f}")

        # 通知所有组合键对象
        for combo_data in self.combo_key_bindings.values():
            try:
                combo_data['hotkey'].press(self.listener.canonical(key))
            except AttributeError:
                pass

    def _on_release(self, key):
        """按键释放事件"""
        now = time.time()

        # 序列绑定检测：当前 release 是否是某序列的"第二个键"？
        sequence_triggered = False
        for (first_key, second_key), seq in self.sequence_bindings.items():
            if key == second_key:
                # 检查是否在 max_gap 内 tap 过 first_key
                last_first_release = self._sequence_pending.get(first_key)
                # 同时校验 second_key 自身这次也是 tap（按压时长 < 0.5s）
                second_pressed_at = self._sequence_press_time.get(key, 0)
                second_press_duration = now - second_pressed_at if second_pressed_at else 1.0
                if (
                    last_first_release
                    and (now - last_first_release) <= seq['max_gap']
                    and second_press_duration < 0.5
                ):
                    logger.info(f"序列触发: {seq['name']} ({first_key} → {second_key}), 间隔 {now - last_first_release:.3f}s")
                    self._sequence_pending.pop(first_key, None)
                    self._sequence_consumed_keys.add(key)
                    try:
                        seq['callback']()
                    except Exception as e:
                        logger.exception(f"序列回调失败 ({seq['name']}): {e}")
                    sequence_triggered = True
                    break

        # 序列绑定检测：当前 release 是否是某序列的"第一个键"？
        # 仅记录 tap 完成时间，不触发任何单键回调（如果该键也是序列首键）
        is_sequence_first, _ = self._is_sequence_key(key)
        if is_sequence_first and not sequence_triggered:
            # 用独立的按下时间表，不依赖 single_key_bindings
            first_pressed_at = self._sequence_press_time.get(key, 0)
            press_duration = now - first_pressed_at if first_pressed_at else 1.0
            if press_duration < 0.5:
                self._sequence_pending[key] = now
                logger.info(f"序列首键已就绪: {key}, 等待第二键 (≤{0.8}s)")

        # 检查单键绑定
        if key in self.single_key_bindings:
            binding = self.single_key_bindings[key]
            if binding['pressed']:
                release_time = now
                press_duration = release_time - binding['last_press_time']

                # ESC 键总是触发（用于取消任务），其他键只在快速按下释放时触发
                is_esc = (key == Key.esc)
                should_trigger = is_esc or (press_duration < 0.5)

                # 若此次释放刚刚被序列吞掉，则跳过单键触发（避免序列触发后又触发右 Option 的默认动作）
                if key in self._sequence_consumed_keys:
                    self._sequence_consumed_keys.discard(key)
                    should_trigger = False
                # 若此键是某序列的"首键"，本次 tap 应预留给序列；不立即触发其单键回调
                elif is_sequence_first and not sequence_triggered:
                    should_trigger = False

                if should_trigger:
                    logger.debug(f"单键触发: {binding['name']}，按压时长: {press_duration:.3f}秒")
                    try:
                        binding['callback']()
                    except Exception as e:
                        logger.exception(f"回调函数执行失败 ({binding['name']}): {e}")
                else:
                    logger.debug(f"按压时长过长或被序列吞掉({press_duration:.3f}秒)，忽略")

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
