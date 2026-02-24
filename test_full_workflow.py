#!/usr/bin/env python3
"""
测试完整工单处理流程:
OCR识别工单 → 点击查看详情 → 回复稍等 → 退出
"""

import sys
import os
import time
import subprocess
import pyautogui
import cv2
import pytesseract
import re
import pyperclip

# 添加utils路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils.window_capture import WindowCapture

# Retina屏幕缩放
RETINA_SCALE = 2.0

def find_text_location(image_path, keyword, offset_x=0, offset_y=20):
    """使用OCR查找文本位置"""
    img = cv2.imread(image_path)
    if img is None:
        return None
    
    # 使用中英文OCR
    data = pytesseract.image_to_data(img, lang='chi_sim+eng', output_type=pytesseract.Output.DICT)
    
    for i, text in enumerate(data['text']):
        if keyword in text or text in keyword:
            conf = int(data['conf'][i])
            if conf > 30:  # 降低置信度阈值
                x = int((data['left'][i] + data['width'][i] / 2) / RETINA_SCALE)
                y = int((data['top'][i] + data['height'][i] / 2) / RETINA_SCALE)
                return (x + offset_x, y + offset_y)
    
    return None

print("=" * 60)
print("测试: OCR识别工单 → 点击查看详情 → 回复稍等")
print("=" * 60)
print()
print("⚠️  请先手动:")
print("  1. 打开企微并进入IT服务工单聊天")
print("  2. 确保有工单消息(包含'查看详情'按钮)")
print()
input("准备好后按Enter继续...")
print()
print("倒计时 3 秒...")
for i in range(3, 0, -1):
    print(f"{i}...")
    time.sleep(1)
print()

# 初始化
monitor = WindowCapture(window_name="企业微信")

# ========================================
# 步骤1: 获取窗口并滚动
# ========================================
print("步骤1: 获取窗口边界...")
window_id = monitor.find_window()
win_x, win_y, win_w, win_h = 295, 101, 1009, 666

if hasattr(monitor, 'window_bounds') and monitor.window_bounds:
    win_x = float(monitor.window_bounds.get('X', 295))
    win_y = float(monitor.window_bounds.get('Y', 101))
    win_w = float(monitor.window_bounds.get('Width', 1009))
    win_h = float(monitor.window_bounds.get('Height', 666))

print(f"✓ 窗口: ({win_x}, {win_y}), 尺寸: {win_w}x{win_h}")

# 点击聊天区域获取焦点
chat_x = int(win_x + win_w * 0.80)
chat_y = int(win_y + win_h * 0.50)
pyautogui.click(chat_x, chat_y)
time.sleep(0.2)

# 滚动到最新
print("滚动到最新消息...")
pyautogui.press('end')
time.sleep(1)

# ========================================
# 步骤2: 截图并OCR识别
# ========================================
print("\n步骤2: 截图并OCR识别工单...")
content_x = int(win_x + win_w * 0.30)
content_y = int(win_y)
content_w = int(win_w * 0.70)
content_h = int(win_h)

# 删除旧截图
if os.path.exists('debug_ticket_capture.png'):
    os.remove('debug_ticket_capture.png')

# 截图
subprocess.run([
    'screencapture', '-x', '-R',
    f'{content_x},{content_y},{content_w},{content_h}',
    'debug_ticket_capture.png'
], check=True, timeout=2)
time.sleep(0.3)

# OCR识别
img = cv2.imread('debug_ticket_capture.png')
if img is None:
    print("❌ 无法读取截图")
    sys.exit(1)

text = pytesseract.image_to_string(img, lang='chi_sim')
print(f"OCR文本(前300字符): {text[:300]}")

# 匹配工单
pattern1 = r'(\w+)\s*添加了\s*(\d{5,})'
m1 = re.search(pattern1, text)
pattern2 = r'工单\s*(\d{5,})'
m2 = re.search(pattern2, text)

if m1:
    name, ticket_id = m1.groups()
    print(f"✓ 识别到新工单: ID={ticket_id}, 添加人={name}")
elif m2:
    ticket_id = m2.group(1)
    print(f"✓ 识别到工单提醒: ID={ticket_id}")
else:
    print("❌ 未识别到工单")
    sys.exit(1)

# 检查是否包含"查看详情"
if '查看详情' not in text:
    print("❌ 未找到'查看详情'按钮")
    sys.exit(1)

print("✓ 检测到'查看详情'按钮")

# ========================================
# 步骤3: 点击"查看详情"
# ========================================
print("\n步骤3: 查找并点击'查看详情'按钮...")

# 使用OCR查找"查看详情"位置
detail_positions = []
data = pytesseract.image_to_data(img, lang='chi_sim+eng', output_type=pytesseract.Output.DICT)

for i, txt in enumerate(data['text']):
    if '查看详情' in txt or '详情' in txt:
        conf = int(data['conf'][i])
        if conf > 30:
            x = int((data['left'][i] + data['width'][i] / 2) / RETINA_SCALE)
            y = int((data['top'][i] + data['height'][i] / 2) / RETINA_SCALE)
            detail_positions.append((x, y, conf))
            print(f"  找到候选: ({x}, {y}), 置信度={conf}")

if not detail_positions:
    print("❌ 未找到'查看详情'按钮位置")
    sys.exit(1)

# 选择Y坐标最大的(最下面的,即最新的)
detail_positions.sort(key=lambda p: p[1], reverse=True)
btn_x, btn_y, conf = detail_positions[0]

# 转换为屏幕坐标
screen_x = content_x + btn_x
screen_y = content_y + btn_y

print(f"✓ 选择最新的'查看详情': ({screen_x}, {screen_y})")
print("点击...")
pyautogui.click(screen_x, screen_y)
print("✓ 已点击'查看详情'")

# ========================================
# 步骤4: 等待工单系统加载
# ========================================
print("\n步骤4: 等待工单系统加载(10秒)...")
time.sleep(10)

# ========================================
# 步骤5: 回复"稍等"
# ========================================
print("\n步骤5: 在工单系统中回复'稍等'...")

# 复制到剪贴板
pyperclip.copy('稍等')
print(f"  ✓ 剪贴板: '{pyperclip.paste()}'")

# 点击输入框获取焦点
screen_width, screen_height = pyautogui.size()
input_x = int(screen_width * 0.80)
input_y = int(screen_height * 0.77)
print(f"  点击输入框: ({input_x}, {input_y})")
pyautogui.click(input_x, input_y)
time.sleep(0.5)

# 粘贴 - 使用AppleScript确保Cmd+V可靠执行
print("  粘贴 Cmd+V (AppleScript)...")
subprocess.run(['osascript', '-e', 
    'tell application "System Events" to keystroke "v" using command down'],
    timeout=3)
time.sleep(2)

# 发送 - 使用AppleScript确保Enter可靠执行
print("  发送 Enter (AppleScript)...")
subprocess.run(['osascript', '-e',
    'tell application "System Events" to key code 36'],
    timeout=3)
time.sleep(2)

# ========================================
# 步骤6: 退出工单系统
# ========================================
print("\n步骤6: 按Escape退出工单系统...")
pyautogui.press('escape')

print()
print("=" * 60)
print("✅ 测试完成!")
print("=" * 60)
print()
print("请检查:")
print("1. 工单系统是否收到'稍等'回复")
print("2. 是否成功退出工单系统")
print()
