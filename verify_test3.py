#!/usr/bin/env python3
"""
验证测试3: 点击输入框位置后粘贴
"""

import time
import subprocess
import pyautogui
import pyperclip

print("=" * 60)
print("验证: 点击输入框(80%, 77%)后粘贴")
print("=" * 60)
print()
print("⚠️  请先:")
print("  1. 手动打开企微并进入IT服务工单聊天")
print("  2. 手动点击一个工单的'查看详情'")
print("  3. 立即回到终端")
print()
input("完成后按Enter...")
print()

print("等待10秒模拟工单系统加载...")
for i in range(10, 0, -1):
    print(f"{i}秒...")
    time.sleep(1)
print()

# 获取屏幕尺寸
screen_width, screen_height = pyautogui.size()
input_x = int(screen_width * 0.80)
input_y = int(screen_height * 0.77)

print(f"点击输入框: ({input_x}, {input_y})")
pyautogui.click(input_x, input_y)
time.sleep(0.5)

print("复制'稍等'到剪贴板...")
pyperclip.copy('稍等')

print("粘贴 Cmd+V...")
pyautogui.hotkey('command', 'v')
time.sleep(1)

print("截图...")
subprocess.run(['screencapture', '-x', 'debug_verify_test3.png'], check=False)
time.sleep(0.5)

print("发送 Enter...")
pyautogui.press('enter')
time.sleep(1)

print("退出 Escape...")
pyautogui.press('escape')

print()
print("=" * 60)
print("✅ 验证完成!")
print("=" * 60)
print()
print("请检查:")
print("1. debug_verify_test3.png - 粘贴后的状态")
print("2. 工单系统是否收到'稍等'回复")
print("3. 是否成功退出工单系统")
print()
