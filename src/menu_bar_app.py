"""
菜单栏应用主入口（rumps）

主线程跑 rumps 主循环（macOS NSApplicationMain），
后台线程跑 asyncio（hotkey listener + text processor）
"""
import os
import sys
import asyncio
import threading
import subprocess
from pathlib import Path
from typing import Optional

import rumps
from loguru import logger

from src.core.hotkey_listener import HotkeyListener
from src.core.text_processor import TextProcessor
from src.api.deepseek_client import DeepSeekClient
from src.utils.config_loader import ConfigLoader
from src.utils.logger import setup_logger
from src.utils.permissions import (
    check_accessibility,
    check_input_monitoring,
    open_accessibility_settings,
    open_input_monitoring_settings,
    request_input_monitoring,
)
from src.utils.user_config import read_api_key, has_api_key, get_user_dir
from src.utils.desktop_notification import (
    shutdown_notification,
    show_desktop_processing,
    close_desktop_notification,
)


def get_settings_helper_script() -> Path:
    """获取设置窗口 helper 脚本路径"""
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS) / 'src' / 'utils' / 'settings_window.py'
    return Path(__file__).parent / 'utils' / 'settings_window.py'


class BackgroundWorker:
    """后台 asyncio 工作线程"""

    def __init__(self, on_status_change=None):
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.thread: Optional[threading.Thread] = None
        self.hotkey_listener: Optional[HotkeyListener] = None
        self.api_client: Optional[DeepSeekClient] = None
        self.processor: Optional[TextProcessor] = None
        self.config: Optional[dict] = None
        self.on_status_change = on_status_change
        self._running = False

    def start(self):
        """启动后台线程"""
        if self._running:
            return
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        """后台线程入口"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        try:
            self.loop.run_until_complete(self._async_main())
        except Exception as e:
            logger.exception(f"后台任务异常: {e}")
        finally:
            self.loop.close()

    async def _async_main(self):
        """异步主任务"""
        try:
            # 始终从用户目录加载配置（开发和打包模式统一）
            from app_config import initialize_config
            try:
                config_file, env_file = initialize_config()
            except FileNotFoundError:
                # 打包模式资源缺失或开发模式首次运行：尝试从项目目录复制
                from app_config import get_user_config_dir
                import shutil
                user_dir = get_user_config_dir()
                project_root = Path(__file__).parent.parent
                if not (user_dir / 'config.yaml').exists():
                    src = project_root / 'config.example.yaml'
                    if src.exists():
                        shutil.copy(src, user_dir / 'config.yaml')
                if not (user_dir / '.env').exists():
                    (user_dir / '.env').touch()
                config_file = str(user_dir / 'config.yaml')
                env_file = str(user_dir / '.env')

            config_loader = ConfigLoader(config_path=config_file, env_path=env_file)
            # 在 load 之前先检查 API Key（避免 ConfigLoader 抛 ValueError）
            if not has_api_key():
                logger.warning("API Key 未配置")
                self._notify_status("⚠️ 未配置 API Key（请打开设置）")
                return
            self.config = config_loader.load()

            # 创建 API 客户端
            self.api_client = DeepSeekClient(
                api_key=self.config['api']['key'],
                base_url=self.config['api'].get('base_url', 'https://api.deepseek.com/v1'),
                model=self.config['api'].get('model', 'deepseek-chat'),
                timeout=self.config['api'].get('timeout', 30),
            )
            self.processor = TextProcessor(self.api_client, self.config)

            # 启动 hotkey listener - 支持多个快捷键绑定
            loop = asyncio.get_running_loop()
            bindings = []

            # 从配置中读取所有快捷键绑定（已由ConfigLoader规范化为hotkey_bindings）
            for binding in self.config.get('hotkey_bindings', []):
                hotkey_str = binding['hotkey']
                prompt_name = binding['prompt_name']
                prompt_content = binding['prompt_content']

                # 为每个绑定创建一个闭包回调
                def make_callback(pname, pcontent):
                    def on_hotkey():
                        logger.info(f"快捷键触发: {pname}")

                        # 立即显示处理动效
                        if self.config.get('notifications', {}).get('show_processing', True):
                            show_desktop_processing("正在处理文本，请稍候...")

                        # 临时修改配置中的active_prompt，让processor使用对应的prompt
                        original_active = self.config.get('active_prompt')
                        self.config['active_prompt'] = pname
                        # 临时注入prompt内容
                        if 'prompts' not in self.config:
                            self.config['prompts'] = {}
                        self.config['prompts'][pname] = pcontent

                        asyncio.run_coroutine_threadsafe(
                            self.processor.process_selected_text(), loop
                        )

                        # 恢复原active_prompt（可选）
                        if original_active:
                            self.config['active_prompt'] = original_active
                    return on_hotkey

                bindings.append({
                    'hotkey': hotkey_str,
                    'callback': make_callback(prompt_name, prompt_content),
                    'name': prompt_name
                })

            # 序列绑定（如 left_option > right_option）：触发截屏 + OCR + 文本处理
            for binding in self.config.get('sequence_bindings', []):
                hotkey_str = binding['hotkey']  # 形如 "left_option>right_option"
                prompt_name = binding.get('prompt_name', 'typeless')
                prompt_content = binding.get('prompt_content', '')
                max_gap = binding.get('max_gap_sec', 0.8)

                def make_seq_callback(pname, pcontent):
                    def on_sequence():
                        logger.info(f"序列快捷键触发(带截屏): {pname}")
                        if self.config.get('notifications', {}).get('show_processing', True):
                            show_desktop_processing("正在截屏并处理…")
                        # 临时切 prompt
                        self.config['active_prompt'] = pname
                        if 'prompts' not in self.config:
                            self.config['prompts'] = {}
                        self.config['prompts'][pname] = pcontent
                        asyncio.run_coroutine_threadsafe(
                            self.processor.process_selected_text(with_screenshot=True), loop
                        )
                    return on_sequence

                bindings.append({
                    'hotkey': hotkey_str,
                    'callback': make_seq_callback(prompt_name, prompt_content),
                    'name': f"{prompt_name}(截屏)",
                    'max_gap_sec': max_gap,
                })

            # 添加 ESC 键绑定，用于取消任务
            # 注意：只在有任务正在处理时才生效，避免对其他应用造成干扰
            def on_cancel():
                if self.processor and self.processor._processing:
                    logger.info("ESC 键触发，取消任务")
                    self.processor.cancel()
                    close_desktop_notification()

            bindings.append({
                'hotkey': 'esc',
                'callback': on_cancel,
                'name': '取消任务'
            })

            self.hotkey_listener = HotkeyListener(bindings)
            self.hotkey_listener.start()

            await asyncio.sleep(0.3)

            if self.hotkey_listener.is_running():
                hotkey_names = ', '.join([b['hotkey'] for b in bindings])
                logger.info(f"✓ 监听快捷键: {hotkey_names}")
                self._notify_status(f"● 运行中 ({len(bindings)}个快捷键)")
            else:
                self._notify_status("⚠️ 快捷键监听启动失败")

            self._running = True

            # 保持运行
            while self._running:
                await asyncio.sleep(1)

        except FileNotFoundError as e:
            logger.error(f"配置文件错误: {e}")
            self._notify_status("⚠️ 配置错误")
        except ValueError as e:
            logger.error(f"配置错误: {e}")
            self._notify_status("⚠️ 配置错误")
        except Exception as e:
            logger.exception("后台任务启动失败")
            self._notify_status(f"⚠️ 错误: {e}")

    def _notify_status(self, status: str):
        if self.on_status_change:
            try:
                self.on_status_change(status)
            except Exception:
                pass

    def stop(self):
        """停止后台任务"""
        self._running = False
        if self.hotkey_listener:
            try:
                self.hotkey_listener.stop()
            except Exception:
                pass
        if self.api_client and self.loop and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(self.api_client.close(), self.loop)


class VoiceTextEnhancerApp(rumps.App):
    """菜单栏应用"""

    def __init__(self):
        # 获取图标路径
        icon_path = self._get_icon_path()

        super().__init__(
            name="润色",
            icon=icon_path,  # 使用您提供的 PNG 图标
        )

        # 菜单项（status_item 不设回调即为不可点击）
        self.status_item = rumps.MenuItem("启动中…")

        self.menu = [
            self.status_item,
            None,  # 分隔线
            rumps.MenuItem("打开设置…", callback=self.open_settings),
            rumps.MenuItem("查看日志", callback=self.view_logs),
            rumps.MenuItem("检查权限", callback=self.check_permissions),
            rumps.MenuItem("重启服务", callback=self.restart_service),
        ]

        self.worker: Optional[BackgroundWorker] = None
        self.settings_proc: Optional[subprocess.Popen] = None
        # 初始化为当前权限状态，避免首次 _periodic_check 误判为"刚刚补齐"
        # 而触发重复启动 worker（导致快捷键被监听两次）
        self._last_perms_ok: bool = (
            has_api_key() and check_accessibility() and check_input_monitoring()
        )
        self._restarting: bool = False  # 防止重启过程中再次触发重启

        # 启动后台
        rumps.Timer(self._initial_setup, 0.5).start()
        # 定期检查权限并更新状态
        rumps.Timer(self._periodic_check, 5).start()

    def _get_icon_path(self) -> str:
        """获取菜单栏图标路径（兼容打包模式）"""
        if getattr(sys, 'frozen', False):
            base = Path(sys._MEIPASS)
        else:
            base = Path(__file__).parent.parent
        return str(base / 'assets' / 'menubar_icon.png')

    def _initial_setup(self, sender):
        """启动后立即执行一次初始化"""
        sender.stop()  # 仅执行一次

        # 触发输入监控权限请求（如果尚未授权，会弹出系统对话框）
        try:
            request_input_monitoring()
        except Exception:
            pass

        self.start_background()

    def start_background(self):
        """启动后台 worker"""
        if self.worker:
            self.worker.stop()
        self.worker = BackgroundWorker(on_status_change=self._update_status)
        self.worker.start()

    def _update_status(self, status: str):
        """更新菜单栏状态显示（线程安全）"""
        # rumps 菜单项设置文本本身是线程安全的
        self.status_item.title = status

    def _periodic_check(self, _):
        """定期检查权限和配置状态"""
        acc = check_accessibility()
        inp = check_input_monitoring()
        key = has_api_key()
        all_ok = key and acc and inp

        if not key:
            self.status_item.title = "⚠️ 未配置 API Key"
        elif not acc or not inp:
            missing = []
            if not acc:
                missing.append("辅助功能")
            if not inp:
                missing.append("输入监控")
            self.status_item.title = f"⚠️ 缺少权限: {', '.join(missing)}"
        else:
            # 从「权限缺失」变成「权限齐全」时，自动重启服务让 worker 重启
            if not self._last_perms_ok and not self._restarting:
                logger.info("权限刚刚补齐，自动重启服务")
                self.status_item.title = "● 启动中…"
                self._restarting = True
                # 在后台线程重启，避免阻塞 rumps 主线程
                threading.Thread(target=self._do_restart_service, daemon=True).start()

        self._last_perms_ok = all_ok

    def _do_restart_service(self):
        """重启 worker（不重启整个进程）"""
        try:
            if self.worker:
                self.worker.stop()
                # 给旧 listener 一点时间真正退出，避免两个 listener 同时监听
                import time as _time
                _time.sleep(0.3)
            self.start_background()
        finally:
            self._restarting = False

    def open_settings(self, _):
        """打开设置窗口（独立子进程）"""
        # 检查是否已有窗口在运行
        if self.settings_proc and self.settings_proc.poll() is None:
            # 已运行，尝试激活
            return

        try:
            env = {**os.environ, 'VTE_SETTINGS_MODE': '1'}
            if getattr(sys, 'frozen', False):
                cmd = [sys.executable]
            else:
                cmd = [sys.executable, str(get_settings_helper_script())]

            self.settings_proc = subprocess.Popen(
                cmd, env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception as e:
            logger.error(f"打开设置失败: {e}")
            rumps.notification("打开设置失败", "", str(e))

    def view_logs(self, _):
        """查看日志文件"""
        log_file = get_user_dir() / 'app.log'
        if log_file.exists():
            # 使用默认应用打开日志文件
            subprocess.run(['open', str(log_file)])
        else:
            rumps.alert(
                title="日志文件不存在",
                message="日志文件尚未生成",
                ok="知道了"
            )

    def check_permissions(self, _):
        """手动触发权限检查"""
        acc = check_accessibility()
        inp = check_input_monitoring()

        msgs = []
        if acc:
            msgs.append("✓ 辅助功能已授权")
        else:
            msgs.append("✗ 辅助功能未授权")
        if inp:
            msgs.append("✓ 输入监控已授权")
        else:
            msgs.append("✗ 输入监控未授权")

        rumps.alert(
            title="权限状态",
            message="\n".join(msgs) + "\n\n点击「打开设置…」配置缺失权限",
            ok="知道了"
        )

    def restart_service(self, _):
        """重启整个应用进程（最可靠）"""
        logger.info("重启应用进程")

        # 启动新进程（独立 session，不受当前进程退出影响）
        if getattr(sys, 'frozen', False):
            cmd = [sys.executable]
        else:
            cmd = [sys.executable] + sys.argv

        subprocess.Popen(
            cmd,
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env={**os.environ},
        )

        # 0.5 秒后退出当前进程（让新进程先启动）
        threading.Timer(0.5, self._force_exit).start()

    def _force_exit(self):
        """强制退出，让新进程接管"""
        try:
            self.cleanup()
        except Exception:
            pass
        os._exit(0)

    def cleanup(self):
        """退出前清理（atexit 触发）"""
        logger.info("应用退出，清理资源")
        if self.worker:
            self.worker.stop()
        try:
            shutdown_notification()
        except Exception:
            pass
        if self.settings_proc and self.settings_proc.poll() is None:
            try:
                self.settings_proc.terminate()
            except Exception:
                pass


def _hide_dock_icon():
    """将主进程设置为 Accessory（不在 Dock 显示图标，仅菜单栏）"""
    try:
        from AppKit import NSApplication
        # NSApplicationActivationPolicyAccessory = 1
        NSApplication.sharedApplication().setActivationPolicy_(1)
    except Exception as e:
        logger.warning(f"隐藏 Dock 图标失败: {e}")


def run():
    """启动菜单栏应用"""
    import atexit

    # 初始化日志（用最小配置）
    log_dir = get_user_dir()
    log_file = log_dir / 'app.log'
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    logger.add(str(log_file), level="INFO", rotation="10 MB", retention="7 days")

    # 隐藏 Dock 图标（开发模式也生效；打包模式由 LSUIElement 处理但再设一次无害）
    _hide_dock_icon()

    logger.info("=" * 50)
    logger.info("Voice Text Enhancer 菜单栏应用启动")
    logger.info(f"PID: {os.getpid()}")
    logger.info(f"frozen: {getattr(sys, 'frozen', False)}")
    logger.info("=" * 50)

    app = VoiceTextEnhancerApp()
    atexit.register(app.cleanup)
    app.run()
