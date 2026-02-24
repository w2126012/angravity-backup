#!/usr/bin/env python3
"""
详细诊断脚本: 在每个步骤后截图,观察工单系统状态
"""

import time
import subprocess
import pyautogui
import pyperclip

print("=" * 60)
print("详细诊断: 截图观察每个步骤")
print("=" * 60)
print()
print("⚠️  请先:")
print("  1. 手动打开工单系统")
print("  2. 确保工单详情页面已加载完成")
print()
input("准备好后按Enter继续...")
print()
print("3秒后开始...")
for i in range(3, 0, -1):
    print(f"{i}...")
    time.sleep(1)
print()

# 步骤0: 初始状态
print("步骤0: 截取初始状态...")
subprocess.run(['screencapture', '-x', 'debug_step0_initial.png'], check=False)
time.sleep(0.5)

# 复制到剪贴板
pyperclip.copy('稍等')
print(f"剪贴板: '{pyperclip.paste()}'")
print()

# 步骤1: 执行5次Backspace
print("步骤1: 按5次Backspace...")
for i in range(5):
    print(f"  Backspace {i+1}/5")
    pyautogui.press('backspace')
    time.sleep(0.2)
time.sleep(0.5)

print("截图: debug_step1_after_backspace.png")
subprocess.run(['screencapture', '-x', 'debug_step1_after_backspace.png'], check=False)
time.sleep(0.5)
print()

# 步骤2: 粘贴
print("步骤2: 执行粘贴 Cmd+V...")
pyautogui.hotkey('command', 'v')
time.sleep(1)

print("截图: debug_step2_after_paste.png")
subprocess.run(['screencapture', '-x', 'debug_step2_after_paste.png'], check=False)
time.sleep(0.5)
print()

# 步骤3: 发送
print("步骤3: 按Enter发送...")
pyautogui.press('enter')
time.sleep(1)

print("截图: debug_step3_after_send.png")
subprocess.run(['screencapture', '-x', 'debug_step3_after_send.png'], check=False)
time.sleep(0.5)
print()

print("=" * 60)
print("✅ 诊断完成!")
print("=" * 60)
print()
print("请检查以下截图:")
print("1. debug_step0_initial.png - 初始状态")
print("2. debug_step1_after_backspace.png - Backspace后")
print("3. debug_step2_after_paste.png - 粘贴后")
print("4. debug_step3_after_send.png - 发送后")
print()
print("对比这些截图,找出哪个步骤没有按预期工作")
print()
