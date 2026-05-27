#!/usr/bin/env python3
"""
测试漂亮的通知效果
"""
import time
from src.utils.fancy_notification import (
    show_fancy_processing,
    show_fancy_success,
    show_fancy_error,
    show_fancy_info,
    close_fancy_notification
)


def test_all_notifications():
    """测试所有通知类型"""
    print("=" * 50)
    print("测试通知效果")
    print("=" * 50)
    print()

    # 1. 信息通知（蓝色）
    print("1. 显示信息通知（蓝色）...")
    show_fancy_info("工具已启动\n轻按右 Option 即可处理", duration=3)
    time.sleep(4)

    # 2. 处理中通知（蓝色，带旋转动画）
    print("2. 显示处理中通知（蓝色，旋转动画）...")
    show_fancy_processing("正在处理文本，请稍候...")
    time.sleep(3)

    # 关闭处理中通知
    close_fancy_notification()
    time.sleep(0.5)

    # 3. 成功通知（绿色）
    print("3. 显示成功通知（绿色）...")
    show_fancy_success("✓ 文本处理完成", duration=2)
    time.sleep(3)

    # 4. 错误通知（红色）
    print("4. 显示错误通知（红色）...")
    show_fancy_error("处理失败：网络连接错误", duration=3)
    time.sleep(4)

    print()
    print("=" * 50)
    print("测试完成！")
    print("=" * 50)


def test_workflow():
    """测试完整工作流程"""
    print("=" * 50)
    print("模拟完整工作流程")
    print("=" * 50)
    print()

    print("步骤 1: 显示启动通知...")
    show_fancy_info("工具已启动", duration=2)
    time.sleep(3)

    print("步骤 2: 用户按快捷键，显示处理中...")
    show_fancy_processing("正在处理文本，请稍候...")
    time.sleep(5)  # 模拟 API 调用

    print("步骤 3: 处理完成，显示成功通知...")
    close_fancy_notification()
    time.sleep(0.3)
    show_fancy_success("✓ 文本处理完成", duration=2)
    time.sleep(3)

    print()
    print("=" * 50)
    print("工作流程测试完成！")
    print("=" * 50)


if __name__ == "__main__":
    print()
    print("选择测试模式:")
    print("1. 测试所有通知类型")
    print("2. 测试完整工作流程")
    print()

    choice = input("请选择 (1 或 2): ").strip()

    if choice == "1":
        test_all_notifications()
    elif choice == "2":
        test_workflow()
    else:
        print("无效选择，默认运行完整测试")
        test_all_notifications()
