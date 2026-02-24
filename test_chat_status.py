#!/usr/bin/env python3
"""测试当前IT工单聊天状态"""

import cv2
import subprocess
import time
from utils.image_processor import ImageProcessor
from utils.automation import AutomationController

print("=" * 60)
print("IT工单聊天状态测试")
print("=" * 60)

bot = AutomationController()
vision = ImageProcessor()

# 激活企业微信
print("\n1. 激活企业微信...")
bot.activate_window("企业微信")
time.sleep(1)

# 截图
print("\n2. 截图...")
subprocess.run(['screencapture', '-x', 'test_current_state.png'], check=True)
time.sleep(0.2)

# 检测状态
print("\n3. 检测IT工单聊天状态...")
frame = cv2.imread('test_current_state.png')
chat_rect, is_active, has_red_dot = vision.find_chat_with_state(frame, "IT服务工单")

print("\n" + "=" * 60)
print("检测结果:")
print("=" * 60)

if chat_rect:
    x, y, w, h = chat_rect
    print(f"✓ 图标位置: ({x}, {y}), 尺寸: {w}×{h}")
    print(f"✓ 聊天状态: {'✅ 已激活(蓝色背景)' if is_active else '⚪ 未激活(白色背景)'}")
    print(f"✓ 红点状态: {'🔴 有红点' if has_red_dot else '⚫ 无红点'}")
    
    print("\n根据当前状态:")
    if is_active and has_red_dot:
        print("  → should_click = False (已在聊天中)")
        print("  → should_process = True (直接处理工单)")
        print("\n⚠️  程序不会点击,因为已经在聊天中了!")
    elif not is_active and has_red_dot:
        print("  → should_click = True (需要点击进入)")
        print("  → should_process = True (然后处理工单)")
        print("\n✓ 程序会点击进入聊天")
    else:
        print("  → 无红点,不会处理")
        
    # 计算点击坐标
    text_center_x = x + w // 2
    text_center_y = y + h // 2
    print(f"\n如果需要点击,坐标是: ({text_center_x}, {text_center_y})")
else:
    print("✗ 未找到IT工单聊天")

print("=" * 60)
