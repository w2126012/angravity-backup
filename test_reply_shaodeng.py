#!/usr/bin/env python3
"""
测试在工单页面回复'稍等'
使用方法:
1. 手动打开工单系统页面
2. 运行此脚本
3. 脚本会在5秒后自动点击输入框并回复'稍等'
"""

import pyautogui
import pyperclip
import time

print("=" * 60)
print("测试工单页面回复'稍等'")
print("=" * 60)
print()
print("请手动打开工单系统页面...")
print("5秒后将自动执行以下操作:")
print("  1. 点击输入框(屏幕80%, 77%位置)")
print("  2. 粘贴'稍等'")
print("  3. 按Enter发送")
print()
print("倒计时...")

for i in range(5, 0, -1):
    print(f"  {i}秒...")
    time.sleep(1)

print()
print("开始执行!")
print("-" * 60)

# 步骤1: 复制到剪贴板
print("步骤1: 复制'稍等'到剪贴板...")
pyperclip.copy('稍等')
clipboard_content = pyperclip.paste()
print(f"  ✓ 剪贴板内容: '{clipboard_content}'")

# 步骤2: 点击输入框
screen_width, screen_height = pyautogui.size()
input_x = int(screen_width * 0.80)
input_y = int(screen_height * 0.77)
print(f"\n步骤2: 点击输入框位置 ({input_x}, {input_y})")
print(f"  屏幕分辨率: {screen_width}x{screen_height}")
print(f"  点击坐标比例: X=80%, Y=77%")

# 点击3次确保焦点
print("  第1次点击...")
pyautogui.click(input_x, input_y)
time.sleep(0.2)
print("  第2次点击...")
pyautogui.click(input_x, input_y)
time.sleep(0.2)
print("  第3次点击...")
pyautogui.click(input_x, input_y)
time.sleep(0.5)
print("  ✓ 已点击输入框")

# 步骤3: 粘贴
print("\n步骤3: 粘贴内容 (Cmd+V)...")
pyautogui.hotkey('command', 'v')
time.sleep(0.5)
print("  ✓ 已粘贴")

# 步骤4: 发送
print("\n步骤4: 按Enter发送...")
pyautogui.press('enter')
print("  ✓ 已发送")

print()
print("=" * 60)
print("✅ 测试完成!")
print("=" * 60)
print()
print("请检查工单系统是否成功收到'稍等'回复")
print()
