#!/usr/bin/env python3
"""
测试工单系统输入框位置
在打开工单系统页面后运行此脚本
"""

import pyautogui
import time

print("请先手动打开工单系统页面...")
print("5秒后开始测试...")
time.sleep(5)

# 获取当前鼠标位置
print("\n请将鼠标移动到工单系统的输入框中央...")
print("观察10秒...")

for i in range(10):
    x, y = pyautogui.position()
    print(f"当前鼠标位置: ({x}, {y})")
    time.sleep(1)

# 计算屏幕比例
screen_w, screen_h = pyautogui.size()
x, y = pyautogui.position()
print(f"\n屏幕分辨率: {screen_w}x{screen_h}")
print(f"输入框位置: ({x}, {y})")
print(f"比例: X={x/screen_w*100:.1f}%, Y={y/screen_h*100:.1f}%")
