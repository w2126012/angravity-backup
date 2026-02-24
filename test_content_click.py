#!/usr/bin/env python3
"""
测试聊天内容区域的点击坐标
Test script to visualize where the code will click for 'chat content focus'
"""
import pyautogui
import time
import subprocess
import sys

# Get screen size
screen_w, screen_h = pyautogui.size()
print(f"屏幕尺寸: {screen_w}x{screen_h}")

# Calculate target coordinates (same logic as main.py fix)
# Use 70% of width (right side) and 50% of height (center)
target_x = int(screen_w * 0.7)
target_y = int(screen_h * 0.5)

print(f"目标点击坐标: ({target_x}, {target_y})")

# Move mouse to target
print("移动鼠标到目标位置...")
pyautogui.moveTo(target_x, target_y, duration=0.5)
time.sleep(1)

# Capture screenshot WITH CURSOR
print("截图(含鼠标指针)...")
# -C captures cursor
subprocess.run(['screencapture', '-x', '-C', 'debug_cursor_pos.png'])

print("完成。请检查 debug_cursor_pos.png 确认鼠标是否在聊天内容区域的空白处。")
