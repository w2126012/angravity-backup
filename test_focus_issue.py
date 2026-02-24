#!/usr/bin/env python3
"""
诊断: 检查等待10秒后工单系统的焦点状态
"""

import time
import subprocess
import pyautogui
import pyperclip

print("=" * 60)
print("诊断: 检查工单系统加载后的焦点状态")
print("=" * 60)
print()
print("⚠️  操作步骤:")
print("  1. 手动打开企微并进入IT服务工单聊天")
print("  2. 手动点击一个工单的'查看详情'")
print("  3. 立即回到终端")
print()
input("完成上述操作后按Enter...")
print()
print("等待10秒模拟工单系统加载...")
for i in range(10, 0, -1):
    print(f"{i}秒...")
    time.sleep(1)
print()

# 截图当前状态
print("截图当前状态...")
subprocess.run(['screencapture', '-x', 'debug_after_10s.png'], check=False)
print("  保存为: debug_after_10s.png")
print()

# 尝试直接粘贴
print("测试1: 直接粘贴...")
pyperclip.copy('测试1')
pyautogui.hotkey('command', 'v')
time.sleep(1)
subprocess.run(['screencapture', '-x', 'debug_test1_paste.png'], check=False)
print("  截图: debug_test1_paste.png")
print()

time.sleep(2)

# 先点击屏幕中心再粘贴
print("测试2: 先点击屏幕中心,再粘贴...")
screen_width, screen_height = pyautogui.size()
center_x = screen_width // 2
center_y = screen_height // 2
print(f"  点击屏幕中心: ({center_x}, {center_y})")
pyautogui.click(center_x, center_y)
time.sleep(0.5)

pyperclip.copy('测试2')
pyautogui.hotkey('command', 'v')
time.sleep(1)
subprocess.run(['screencapture', '-x', 'debug_test2_click_center.png'], check=False)
print("  截图: debug_test2_click_center.png")
print()

time.sleep(2)

# 先点击输入框位置再粘贴
print("测试3: 先点击输入框位置(80%, 77%),再粘贴...")
input_x = int(screen_width * 0.80)
input_y = int(screen_height * 0.77)
print(f"  点击输入框: ({input_x}, {input_y})")
pyautogui.click(input_x, input_y)
time.sleep(0.5)

pyperclip.copy('测试3')
pyautogui.hotkey('command', 'v')
time.sleep(1)
subprocess.run(['screencapture', '-x', 'debug_test3_click_input.png'], check=False)
print("  截图: debug_test3_click_input.png")
print()

print("=" * 60)
print("✅ 诊断完成!")
print("=" * 60)
print()
print("请检查截图,看哪个测试成功粘贴了:")
print("1. debug_after_10s.png - 等待10秒后的初始状态")
print("2. debug_test1_paste.png - 直接粘贴(无点击)")
print("3. debug_test2_click_center.png - 点击屏幕中心后粘贴")
print("4. debug_test3_click_input.png - 点击输入框后粘贴")
print()
