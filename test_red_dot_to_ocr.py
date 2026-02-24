#!/usr/bin/env python3
"""
简化测试: 假设已在IT服务工单聊天页面,直接测试抓取工单
"""

import sys
import os
import time
import subprocess
import pyautogui
import cv2
import pytesseract
import re

# 添加utils路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils.window_capture import WindowCapture

print("=" * 60)
print("测试: 抓取工单信息")
print("=" * 60)
print()
print("⚠️  请先手动:")
print("  1. 打开企微")
print("  2. 进入IT服务工单聊天")
print("  3. 确保有新工单消息")
print()
input("准备好后按Enter继续...")
print()
print("倒计时 5 秒,请切换到企微窗口...")
for i in range(5, 0, -1):
    print(f"{i}...")
    time.sleep(1)
print()

# 初始化
monitor = WindowCapture(window_name="企业微信")

# 步骤1: 获取窗口边界
print("步骤1: 获取窗口边界...")
window_id = monitor.find_window()
win_x, win_y, win_w, win_h = 295, 101, 1009, 666

if hasattr(monitor, 'window_bounds') and monitor.window_bounds:
    win_x = float(monitor.window_bounds.get('X', 295))
    win_y = float(monitor.window_bounds.get('Y', 101))
    win_w = float(monitor.window_bounds.get('Width', 1009))
    win_h = float(monitor.window_bounds.get('Height', 666))

print(f"✓ 窗口: ({win_x}, {win_y}), 尺寸: {win_w}x{win_h}")

# 步骤2: 点击聊天内容区域
print("\n步骤2: 点击聊天内容区域获取焦点...")
chat_x = int(win_x + win_w * 0.80)
chat_y = int(win_y + win_h * 0.50)
print(f"点击: ({chat_x}, {chat_y})")
pyautogui.click(chat_x, chat_y)
time.sleep(0.2)

# 步骤3: 滚动到最新
print("\n步骤3: 滚动到最新消息...")
pyautogui.press('end')
time.sleep(1)

# 步骤4: 截取聊天内容区域
print("\n步骤4: 截取聊天内容区域...")
content_x = int(win_x + win_w * 0.30)
content_y = int(win_y)
content_w = int(win_w * 0.70)
content_h = int(win_h)

print(f"截图区域: x={content_x}, y={content_y}, w={content_w}, h={content_h}")

# 删除旧文件
if os.path.exists('debug_ticket_capture.png'):
    os.remove('debug_ticket_capture.png')

# 截图
result = subprocess.run([
    'screencapture', '-x', '-R',
    f'{content_x},{content_y},{content_w},{content_h}',
    'debug_ticket_capture.png'
], capture_output=True, text=True)

if result.returncode != 0:
    print(f"❌ 截图失败: {result.stderr}")
    sys.exit(1)

time.sleep(0.3)
print("✓ 截图完成: debug_ticket_capture.png")

# 步骤5: OCR识别
print("\n步骤5: OCR识别...")
img = cv2.imread('debug_ticket_capture.png')

if img is None:
    print("❌ 无法读取截图")
    sys.exit(1)

print("✓ 读取截图成功")
text = pytesseract.image_to_string(img, lang='chi_sim')

print("\n" + "=" * 60)
print("OCR结果(完整):")
print("=" * 60)
print(text)
print("=" * 60)

# 步骤6: 匹配工单
print("\n步骤6: 匹配工单...")

# 格式1: [人名] 添加了 [ID]
pattern1 = r'(\w+)\s*添加了\s*(\d{5,})'
m1 = re.search(pattern1, text)

# 格式2: 工单 [ID]
pattern2 = r'工单\s*(\d{5,})'
m2 = re.search(pattern2, text)

has_detail = '查看详情' in text

print(f"包含'查看详情': {has_detail}")

if m1:
    name, tid = m1.groups()
    print(f"✓ 格式1匹配: 新工单 ID={tid}, 添加人={name}")
elif m2:
    tid = m2.group(1)
    print(f"✓ 格式2匹配: 工单提醒 ID={tid}")
else:
    print("❌ 未匹配到工单")
    print("\n尝试查找所有数字:")
    numbers = re.findall(r'\d{5,}', text)
    if numbers:
        print(f"找到的数字: {numbers}")
    else:
        print("没有找到5位以上的数字")

print("\n" + "=" * 60)
print("✅ 测试完成")
print("=" * 60)
print("\n请查看:")
print("1. debug_ticket_capture.png - 截图内容")
print("2. 上面的OCR结果 - 是否正确识别")
print()
