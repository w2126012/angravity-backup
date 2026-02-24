#!/usr/bin/env python3
"""手动激活企业微信并测试图标检测"""

import time
import subprocess
import cv2
from utils.image_processor import ImageProcessor
from utils.automation import AutomationController

print("=" * 60)
print("企业微信图标检测测试")
print("=" * 60)

# 初始化
bot = AutomationController()
vision = ImageProcessor()

# 1. 激活企业微信窗口
print("\n1. 正在激活企业微信窗口...")
success = bot.activate_window("企业微信")
if success:
    print("   ✓ 企业微信已激活")
else:
    print("   ✗ 企业微信激活失败(可能未运行)")
    exit(1)

# 等待窗口切换
time.sleep(1)

# 2. 截图
print("\n2. 正在截图...")
screenshot_path = "test_wecom_screenshot.png"
subprocess.run(['screencapture', '-x', screenshot_path], check=True)
time.sleep(0.2)

# 3. 检测图标和红点
print("\n3. 正在检测'IT服务工单'图标和红点...")
frame = cv2.imread(screenshot_path)
if frame is None:
    print("   ✗ 无法读取截图")
    exit(1)

chat_rect, is_active, has_red_dot = vision.find_chat_with_state(frame, "IT服务工单")

print("\n" + "=" * 60)
print("检测结果:")
print("=" * 60)

if chat_rect:
    x, y, w, h = chat_rect
    print(f"✓ 图标位置: ({x}, {y}), 尺寸: {w}×{h}")
    print(f"✓ 聊天状态: {'已激活(蓝色)' if is_active else '未激活(白色)'}")
    print(f"✓ 红点状态: {'有红点 🔴' if has_red_dot else '无红点'}")
    
    if has_red_dot:
        print("\n🎉 检测到红点!可以触发自动化流程")
        if not is_active:
            print("   → 需要点击进入聊天")
        else:
            print("   → 已在聊天中,直接处理工单")
    else:
        print("\n⚠️  未检测到红点,不会触发自动化流程")
else:
    print("✗ 未找到'IT服务工单'图标")
    print("   可能原因:")
    print("   1. 企业微信窗口未在前台")
    print("   2. 'IT服务工单'不在聊天列表中")
    print("   3. 图标被遮挡或滚动到屏幕外")

print("=" * 60)
print(f"\n截图已保存到: {screenshot_path}")
print("请查看截图确认企业微信窗口状态")
