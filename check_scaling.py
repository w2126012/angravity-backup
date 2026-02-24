#!/usr/bin/env python3
"""检测显示器缩放因子"""

import subprocess
import pyautogui

# 获取截图尺寸
result = subprocess.run(['sips', '-g', 'pixelWidth', '-g', 'pixelHeight', 'debug_system_screenshot.png'],
                       capture_output=True, text=True)
lines = result.stdout.strip().split('\n')
screenshot_width = int(lines[-2].split(':')[-1].strip())
screenshot_height = int(lines[-1].split(':')[-1].strip())

# 获取屏幕尺寸(pyautogui)
screen_width, screen_height = pyautogui.size()

# 计算缩放因子
scale_x = screenshot_width / screen_width
scale_y = screenshot_height / screen_height

print(f"截图尺寸: {screenshot_width} x {screenshot_height}")
print(f"屏幕尺寸: {screen_width} x {screen_height}")
print(f"缩放因子: X={scale_x:.2f}, Y={scale_y:.2f}")

if scale_x == 2.0:
    print("\n✓ 检测到Retina显示屏(2x缩放)")
    print("  点击坐标需要除以2")
elif scale_x == 1.0:
    print("\n✓ 普通显示屏(无缩放)")
    print("  点击坐标无需转换")
else:
    print(f"\n⚠️ 自定义缩放因子: {scale_x}")
    print(f"  点击坐标需要除以{scale_x}")

# 测试坐标转换
test_screenshot_x = 906
test_screenshot_y = 392
test_click_x = test_screenshot_x / scale_x
test_click_y = test_screenshot_y / scale_y

print(f"\n示例坐标转换:")
print(f"  截图坐标: ({test_screenshot_x}, {test_screenshot_y})")
print(f"  点击坐标: ({test_click_x:.0f}, {test_click_y:.0f})")
