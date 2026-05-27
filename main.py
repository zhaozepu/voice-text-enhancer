#!/usr/bin/env python3
"""
Voice Text Enhancer - 文本增强工具
主入口程序
"""
import os
import sys

# 打包模式下，作为通知 helper 启动时直接进入 helper 主循环
# （子进程通过环境变量切换模式，避免重新启动整个应用）
if os.environ.get('VTE_HELPER_MODE') == '1':
    from src.utils.notification_helper import main as helper_main
    helper_main()
    sys.exit(0)

import asyncio
from pathlib import Path
from loguru import logger

# 应用配置路径管理（支持打包）
try:
    from app_config import initialize_config
    APP_MODE = 'packaged'
except ImportError:
    APP_MODE = 'dev'

from src.core.hotkey_listener import HotkeyListener
from src.core.text_processor import TextProcessor
from src.api.deepseek_client import DeepSeekClient
from src.utils.config_loader import ConfigLoader
from src.utils.logger import setup_logger
from src.utils.notifications import show_info, show_error
from src.utils.desktop_notification import (
    show_desktop_info as show_fancy_info,
    show_desktop_error as show_fancy_error,
    shutdown_notification,
)


def check_permissions():
    """
    检查必要的系统权限

    Returns:
        是否具有必要权限
    """
    logger.info("检查系统权限...")

    try:
        import pyautogui
        import pyperclip

        test_text = pyperclip.paste()
        logger.debug("剪贴板访问正常")

        logger.info("基础权限检查通过")
        logger.warning(
            "注意: 首次运行需要授予以下权限:\n"
            "  1. 辅助功能权限 (Accessibility) - 允许模拟键盘输入\n"
            "  2. 输入监控权限 (Input Monitoring) - 允许监听全局快捷键\n"
            "如果快捷键无法触发或无法粘贴文本，请在 '系统设置 > 隐私与安全性' 中授予权限"
        )

        return True

    except Exception as e:
        logger.error(f"权限检查失败: {e}")
        return False


async def main():
    """主函数"""
    try:
        print("=" * 50)
        print("Voice Text Enhancer - 文本增强工具")
        print("=" * 50)
        print()

        # 初始化配置文件路径（支持打包）
        if APP_MODE == 'packaged':
            config_file, env_file = initialize_config()
            config_loader = ConfigLoader(config_path=config_file, env_path=env_file)
        else:
            config_loader = ConfigLoader()

        config = config_loader.load()

        setup_logger(config)

        logger.info("文本增强工具启动中...")

        if not check_permissions():
            logger.error("缺少必要的系统权限")
            show_fancy_error("缺少必要的系统权限\n请查看终端输出", duration=5)
            sys.exit(1)

        api_client = DeepSeekClient(
            api_key=config['api']['key'],
            base_url=config['api'].get('base_url', 'https://api.deepseek.com/v1'),
            model=config['api'].get('model', 'deepseek-chat'),
            timeout=config['api'].get('timeout', 30)
        )
        logger.info("API 客户端初始化完成")

        processor = TextProcessor(api_client, config)
        logger.info("文本处理器初始化完成")

        hotkey_trigger = config['hotkey']['trigger']

        # 获取当前正在运行的事件循环
        loop = asyncio.get_running_loop()

        def on_hotkey_triggered():
            """快捷键触发回调"""
            logger.info("快捷键被触发，开始处理文本")
            # 从其他线程提交协程到主事件循环
            asyncio.run_coroutine_threadsafe(processor.process_selected_text(), loop)

        hotkey_listener = HotkeyListener(hotkey_trigger, on_hotkey_triggered)
        hotkey_listener.start()

        active_prompt = config.get('active_prompt', 'expand')
        # 格式化通知消息
        if hotkey_trigger == "right_option":
            hotkey_display_short = "轻按右 Option"
        elif hotkey_trigger == "left_option":
            hotkey_display_short = "轻按左 Option"
        else:
            hotkey_display_short = hotkey_trigger

        # 显示漂亮的启动通知
        show_fancy_info(
            f"工具已启动\n{hotkey_display_short} 即可处理\n模式: {active_prompt}",
            duration=3
        )

        logger.info(f"监听快捷键: {hotkey_trigger}")
        logger.info(f"当前使用 Prompt 模式: {active_prompt}")
        logger.info("工具运行中，按 Ctrl+C 退出...")

        # 格式化快捷键显示
        if hotkey_trigger == "right_option":
            hotkey_display = "右边 Option 键"
        elif hotkey_trigger == "left_option":
            hotkey_display = "左边 Option 键"
        elif hotkey_trigger == "right_cmd":
            hotkey_display = "右边 Command 键"
        else:
            hotkey_display = hotkey_trigger

        print(f"\n✓ 工具已启动")
        print(f"✓ 快捷键: {hotkey_display}")
        print(f"✓ 处理模式: {active_prompt}")
        print(f"\n使用方法:")
        print(f"  1. 在输入框中输入或粘贴文本（豆包输入法等）")
        print(f"  2. 光标停留在该输入框内")
        print(f"  3. 轻按 {hotkey_display}（自动全选并处理）")
        print(f"  4. 等待处理完成，文本自动替换")
        print(f"\n💡 提示: 轻按一下即可，无需长按！")
        print(f"\n按 Ctrl+C 退出")
        print("=" * 50)

        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("收到退出信号")
            print("\n正在退出...")

    except FileNotFoundError as e:
        logger.error(str(e))
        print(f"\n错误: {e}")
        print("\n请按照以下步骤配置:")
        print("  1. 复制 config.example.yaml 为 config.yaml")
        print("  2. 复制 .env.example 为 .env")
        print("  3. 在 .env 中填写 DEEPSEEK_API_KEY")
        sys.exit(1)

    except ValueError as e:
        logger.error(str(e))
        print(f"\n配置错误: {e}")
        sys.exit(1)

    except Exception as e:
        logger.exception("程序异常退出")
        print(f"\n程序异常: {e}")
        sys.exit(1)

    finally:
        if 'hotkey_listener' in locals():
            hotkey_listener.stop()
        if 'api_client' in locals():
            await api_client.close()

        shutdown_notification()
        show_info("文本增强工具已停止")
        logger.info("程序已退出")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n已退出")
        sys.exit(0)
