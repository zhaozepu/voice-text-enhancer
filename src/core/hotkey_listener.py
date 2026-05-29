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

        # 同时按下组合：frozenset({key1, key2, ...}) -> {callback, name}
        # 形如 "left_option+right_option" 表示同时按下两个键（仅由我们认识的修饰键组成）
        self.simul_bindings = {}
        # 已触发但还未释放任何一个键的组合（避免长按重复触发）
        self._simul_fired = set()
        # 组合触发时被消费的键，下一次 release 不应再触发其单键回调
        self._simul_consumed_keys = set()
        # 组合冷却期：组合触发后，参与组合的键在该时间戳前的释放都不触发单键回调
        # （避免「先按组合 → 释放一个 → 又按一下 → 释放」被误判为单键触发）
        self._simul_cooldown_until: float = 0.0
        self._simul_cooldown_keys: set = set()
        self.SIMUL_COOLDOWN_SEC = 0.6
        # 当前按住的键集合
        self._keys_down = set()
        # 每个键最近一次"按下"的时间戳。检测同时按下组合时要求各键时间相近，
        # 避免「按住一个 + 几秒后按另一个」或「上一次组合的 release 事件丢失导致状态残留」
        # 之类的场景误触发组合。
        self._key_press_time: dict = {}
        # 同时按下组合的按下时间窗口（秒）：keyset 中各键的最近按下时间互相必须在此窗口内
        self.SIMUL_PRESS_WINDOW_SEC = 0.4

        # 我们能解析为单键的所有名称（用于判断 a+b 是不是"同时组合"而非 pynput 组合键）
        _SIMPLE_KEY_NAMES = {
            'right_option', 'right_alt', 'left_option', 'left_alt',
            'right_cmd', 'right_ctrl', 'esc',
        }

        # 解析所有绑定
        for binding in bindings:
            hotkey_str = binding['hotkey']
            callback = binding['callback']
            name = binding.get('name', hotkey_str)

            # 判断是否是 "key+key"（且每段都是修饰键），如果是 → 同时按下组合
            simul_parts = None
            if '+' in hotkey_str and '<' not in hotkey_str:
                parts = [p.strip() for p in hotkey_str.split('+')]
                if all(p in _SIMPLE_KEY_NAMES for p in parts):
                    simul_parts = parts

            if simul_parts:
                key_objs = [self._parse_single_key(p) for p in simul_parts]
                if any(k is None for k in key_objs):
                    logger.error(f"组合键解析失败: {hotkey_str}")
                    continue
                key_set = frozenset(key_objs)
                self.simul_bindings[key_set] = {
                    'callback': callback,
                    'name': name,
                }
                logger.info(f"已注册同时按下组合: {name} ({hotkey_str})")
            elif hotkey_str in _SIMPLE_KEY_NAMES:
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

    def _key_in_any_combo(self, key) -> bool:
        """该键是否参与任何同时按下组合"""
        return any(key in keyset for keyset in self.simul_bindings.keys())

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

        # 维护当前按住的键集合 + 记录按下时间戳
        # 注意：pynput 在键被按住时不会重复触发 _on_press（除非有 OS key repeat），
        # 所以 _key_press_time 记录的就是「最近一次新按下」的时间。
        was_already_down = key in self._keys_down
        self._keys_down.add(key)
        if not was_already_down:
            self._key_press_time[key] = now

        # 检查单键绑定
        if key in self.single_key_bindings:
            binding = self.single_key_bindings[key]
            binding['pressed'] = True
            binding['last_press_time'] = now
            logger.info(f"目标键按下: {binding['name']} (key={key!r})")

        # 检查同时按下组合：所有键都按住、且本次未触发过、且各键按下时间相近
        for keyset, simul in self.simul_bindings.items():
            if keyset.issubset(self._keys_down) and keyset not in self._simul_fired:
                # 时间窗口校验：所有键的最近按下时间都必须在 SIMUL_PRESS_WINDOW_SEC 内
                press_times = [self._key_press_time.get(k, 0.0) for k in keyset]
                if not press_times or min(press_times) <= 0:
                    logger.debug(f"组合时间戳缺失，跳过: {simul['name']}")
                    continue
                t_max = max(press_times)
                t_min = min(press_times)
                gap = t_max - t_min
                if gap > self.SIMUL_PRESS_WINDOW_SEC:
                    logger.info(
                        f"组合按下时间间隔 {gap:.2f}s 超过窗口 {self.SIMUL_PRESS_WINDOW_SEC}s，"
                        f"忽略: {simul['name']} (可能是事件状态残留)"
                    )
                    # 状态可能残留，主动重置时间戳避免下次再误判
                    for k in keyset:
                        self._key_press_time[k] = now if k == key else 0.0
                    continue
                # 通过校验 → 触发组合
                self._simul_fired.add(keyset)
                # 主动从 _keys_down 中移除参与组合的键，避免「release 事件丢失导致状态残留」
                # 引发后续误触；这样后续要再触发组合必须重新真实地按下两键
                for k in keyset:
                    self._keys_down.discard(k)
                    self._key_press_time.pop(k, None)
                    self._simul_consumed_keys.add(k)
                    self._simul_cooldown_keys.add(k)
                # 进入冷却期
                self._simul_cooldown_until = now + self.SIMUL_COOLDOWN_SEC
                logger.info(
                    f"同时按下组合触发: {simul['name']} "
                    f"({sorted(str(k) for k in keyset)}, gap={gap:.3f}s)"
                )
                try:
                    simul['callback']()
                except Exception as e:
                    logger.exception(f"组合回调失败 ({simul['name']}): {e}")

        # 通知所有组合键对象
        for combo_data in self.combo_key_bindings.values():
            try:
                combo_data['hotkey'].press(self.listener.canonical(key))
            except AttributeError:
                pass

    def _on_release(self, key):
        """按键释放事件"""
        now = time.time()

        # 维护当前按住的键集合 + 清理按下时间戳
        self._keys_down.discard(key)
        self._key_press_time.pop(key, None)

        # 一旦组合中的任意键被释放，复位该组合的"已触发"状态，下次再同时按下可再次触发
        for keyset in list(self._simul_fired):
            if key in keyset:
                self._simul_fired.discard(keyset)

        # 检查单键绑定
        if key in self.single_key_bindings:
            binding = self.single_key_bindings[key]
            if binding['pressed']:
                release_time = now
                press_duration = release_time - binding['last_press_time']

                # ESC 键总是触发（用于取消任务），其他键只在快速按下释放时触发
                is_esc = (key == Key.esc)
                should_trigger = is_esc or (press_duration < 0.5)

                # 若此次释放是组合触发后的"善后释放"，则跳过单键触发
                if key in self._simul_consumed_keys:
                    self._simul_consumed_keys.discard(key)
                    should_trigger = False
                    logger.info(f"被组合吞掉的单键释放: {binding['name']} (key={key!r})")

                # 组合冷却期：组合触发后短时间内的同键单键释放，不触发单键回调
                if (
                    not is_esc
                    and key in self._simul_cooldown_keys
                    and now < self._simul_cooldown_until
                ):
                    should_trigger = False
                    logger.info(
                        f"组合冷却期内，忽略单键释放: {binding['name']} "
                        f"(key={key!r}, 剩余 {self._simul_cooldown_until - now:.2f}s)"
                    )

                if should_trigger:
                    logger.info(f"单键触发: {binding['name']} (key={key!r})，按压时长: {press_duration:.3f}秒")
                    try:
                        binding['callback']()
                    except Exception as e:
                        logger.exception(f"回调函数执行失败 ({binding['name']}): {e}")
                else:
                    logger.debug(f"按压时长过长或被组合吞掉({press_duration:.3f}秒)，忽略 key={key!r}")

                binding['pressed'] = False

        # 冷却期结束后清理冷却标记
        if self._simul_cooldown_until and now >= self._simul_cooldown_until:
            self._simul_cooldown_keys.clear()
            self._simul_cooldown_until = 0.0

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
