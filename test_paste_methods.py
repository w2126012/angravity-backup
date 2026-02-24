#!/usr/bin/env python3
"""
诊断脚本: 测试在工单系统中粘贴"稍等"的各种方法
"""

import time
import pyautogui
import pyperclip

print("=" * 60)
print("诊断: 测试粘贴\"稍等\"的各种方法")
print("=" * 60)
print()
print("⚠️  请先:")
print("  1. 手动打开工单系统")
print("  2. 确保输入框可见")
print("  3. 手动点击输入框使其获得焦点")
print()
input("准备好后按Enter继续...")
print()
print("5秒后将尝试各种粘贴方法...")
for i in range(5, 0, -1):
    print(f"{i}...")
    time.sleep(1)
print()

# 复制到剪贴板
pyperclip.copy('稍等')
print(f"剪贴板内容: '{pyperclip.paste()}'")
print()

# 方法1: 直接粘贴
print("方法1: 直接Cmd+V粘贴...")
pyautogui.hotkey('command', 'v')
time.sleep(2)
print("  等待2秒观察...")
print()

# 方法2: Cmd+A全选后粘贴
print("方法2: Cmd+A全选后粘贴...")
pyautogui.hotkey('command', 'a')
time.sleep(0.5)
pyautogui.hotkey('command', 'v')
time.sleep(2)
print("  等待2秒观察...")
print()

# 方法3: 先删除再粘贴
print("方法3: 先Backspace删除再粘贴...")
for _ in range(5):
    pyautogui.press('backspace')
    time.sleep(0.1)
time.sleep(0.5)
pyautogui.hotkey('command', 'v')
time.sleep(2)
print("  等待2秒观察...")
print()

# 方法4: 使用typewrite直接输入
print("方法4: 尝试typewrite直接输入(如果支持)...")
try:
    # pyautogui的typewrite可能不支持中文
    # 但我们可以尝试
    pyautogui.typewrite('shaodeng', interval=0.1)
    time.sleep(2)
    print("  等待2秒观察...")
except Exception as e:
    print(f"  typewrite失败: {e}")
print()

print("=" * 60)
print("测试完成!")
print("=" * 60)
print()
print("请检查工单系统输入框中是否出现了:")
print("1. 方法1的结果")
print("2. 方法2的结果") 
print("3. 方法3的结果")
print("4. 方法4的结果(如果支持)")
print()
print("找到有效的方法后,我们将更新主程序")
print()
