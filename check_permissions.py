#!/usr/bin/env python3
"""
权限检查工具
"""
import subprocess
import sys


def check_accessibility_permission():
    """检查辅助功能权限"""
    print("检查辅助功能权限...")

    # 尝试使用 AppleScript 检查
    script = '''
    tell application "System Events"
        set isEnabled to UI elements enabled
    end tell
    return isEnabled
    '''

    try:
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            enabled = result.stdout.strip().lower() == 'true'
            if enabled:
                print("✓ 辅助功能权限已授予")
                return True
            else:
                print("✗ 辅助功能权限未授予")
                return False
        else:
            print("✗ 无法检查辅助功能权限")
            print(f"  错误: {result.stderr}")
            return False

    except Exception as e:
        print(f"✗ 检查失败: {e}")
        return False


def test_keyboard_simulation():
    """测试键盘模拟"""
    print("\n测试键盘模拟功能...")

    try:
        import pyautogui
        import time

        print("  尝试模拟按键...")
        # 模拟按下并释放 Shift 键（不会影响用户）
        pyautogui.keyDown('shift')
        time.sleep(0.1)
        pyautogui.keyUp('shift')

        print("✓ 键盘模拟功能正常")
        return True

    except Exception as e:
        print(f"✗ 键盘模拟失败: {e}")
        return False


def test_clipboard():
    """测试剪贴板功能"""
    print("\n测试剪贴板功能...")

    try:
        import pyperclip

        # 保存原内容
        original = pyperclip.paste()

        # 测试写入
        test_text = "test-clipboard-access"
        pyperclip.copy(test_text)

        # 测试读取
        result = pyperclip.paste()

        # 恢复原内容
        pyperclip.copy(original)

        if result == test_text:
            print("✓ 剪贴板功能正常")
            return True
        else:
            print("✗ 剪贴板读写不一致")
            return False

    except Exception as e:
        print(f"✗ 剪贴板测试失败: {e}")
        return False


def show_permission_guide():
    """显示权限设置指南"""
    print("\n" + "=" * 60)
    print("权限设置指南")
    print("=" * 60)
    print("\n如果权限检查失败，请按照以下步骤授予权限：")
    print("\n1. 打开 '系统设置' (System Settings)")
    print("2. 进入 '隐私与安全性' (Privacy & Security)")
    print("3. 找到 '辅助功能' (Accessibility)")
    print("4. 点击 + 号，添加以下应用之一：")
    print("   - 终端 (Terminal.app)")
    print("   - Python")
    print("   - 你启动程序的应用")
    print("\n5. 同样在 '输入监控' (Input Monitoring) 中添加")
    print("\n6. 重启程序")
    print("\n注意: 授予权限后，需要完全退出并重新启动程序才能生效")
    print("=" * 60)


def main():
    """主函数"""
    print("=" * 60)
    print("Voice Text Enhancer - 权限检查工具")
    print("=" * 60)
    print()

    results = []

    # 检查辅助功能权限
    results.append(check_accessibility_permission())

    # 测试键盘模拟
    results.append(test_keyboard_simulation())

    # 测试剪贴板
    results.append(test_clipboard())

    print("\n" + "=" * 60)
    print("检查结果汇总")
    print("=" * 60)

    if all(results):
        print("✓ 所有检查通过，工具应该可以正常工作")
        print("\n如果仍然遇到问题，请尝试：")
        print("1. 完全退出并重新启动程序")
        print("2. 重启系统")
        print("3. 查看详细日志: ~/.voice-text-enhancer/app.log")
        return 0
    else:
        print("✗ 部分检查未通过，请按照指南配置权限")
        show_permission_guide()
        return 1


if __name__ == "__main__":
    sys.exit(main())
