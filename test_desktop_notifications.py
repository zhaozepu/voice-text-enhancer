#!/usr/bin/env python3
"""测试桌面浮层通知效果（Lottie 动画）"""
import time
from src.utils.desktop_notification import (
    show_desktop_processing,
    show_desktop_success,
    show_desktop_error,
    show_desktop_info,
    close_desktop_notification,
    shutdown_notification,
)


def test_all():
    """测试所有通知类型"""
    print("=" * 50)
    print("测试桌面浮层通知（Lottie 动画）")
    print("=" * 50)

    print("\n1. 信息通知（蓝色渐变）...")
    show_desktop_info("工具已启动\n轻按右 Option 即可处理", duration=3)
    time.sleep(4)

    print("2. 处理中通知（紫色渐变 + Lottie 动画）...")
    show_desktop_processing("正在处理文本，请稍候...")
    time.sleep(4)

    print("3. 成功通知（绿色渐变 + 脉冲）...")
    show_desktop_success("文本处理完成", duration=2)
    time.sleep(3)

    print("4. 错误通知（红色渐变 + 脉冲）...")
    show_desktop_error("处理失败：网络连接错误", duration=3)
    time.sleep(4)

    print("\n测试完成！")


def test_workflow():
    """测试完整工作流程"""
    print("=" * 50)
    print("模拟完整工作流程")
    print("=" * 50)

    print("\n步骤 1: 启动通知...")
    show_desktop_info("工具已启动", duration=2)
    time.sleep(3)

    print("步骤 2: 处理中（Lottie 动画）...")
    show_desktop_processing("正在处理文本，请稍候...")
    time.sleep(4)

    print("步骤 3: 成功通知...")
    show_desktop_success("文本处理完成", duration=2)
    time.sleep(3)

    print("\n工作流程测试完成！")


if __name__ == "__main__":
    print("\n选择测试:")
    print("1. 测试所有通知类型")
    print("2. 测试完整工作流程")

    try:
        choice = input("\n请选择 (1 或 2): ").strip()
        if choice == "1":
            test_all()
        elif choice == "2":
            test_workflow()
        else:
            test_all()
    finally:
        time.sleep(1)
        shutdown_notification()
