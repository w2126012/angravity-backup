#!/usr/bin/env python3
"""
测试不同的发送方法
"""

import time
import subprocess
import pyautogui
import pyperclip

print("=" * 60)
print("测试不同的发送方法")
print("=" * 60)
print()
print("⚠️  请先:")
print("  1. 手动打开工单系统")
print("  2. 在输入框中输入一些测试文字")
print()
input("准备好后按Enter继续...")
print()

# 方法1: Enter
print("方法1: 尝试 Enter 键...")
time.sleep(2)
pyautogui.press('enter')
time.sleep(1)
subprocess.run(['screencapture', '-x', 'debug_send_method1_enter.png'], check=False)
print("  截图: debug_send_method1_enter.png")
print()

# 重新输入测试文字
print("请重新在输入框输入测试文字...")
time.sleep(3)

# 方法2: Cmd+Enter
print("方法2: 尝试 Cmd+Enter...")
time.sleep(2)
pyautogui.hotkey('command', 'enter')
time.sleep(1)
subprocess.run(['screencapture', '-x', 'debug_send_method2_cmd_enter.png'], check=False)
print("  截图: debug_send_method2_cmd_enter.png")
print()

# 重新输入测试文字
print("请重新在输入框输入测试文字...")
time.sleep(3)

# 方法3: Ctrl+Enter
print("方法3: 尝试 Ctrl+Enter...")
time.sleep(2)
pyautogui.hotkey('ctrl', 'enter')
time.sleep(1)
subprocess.run(['screencapture', '-x', 'debug_send_method3_ctrl_enter.png'], check=False)
print("  截图: debug_send_method3_ctrl_enter.png")
print()

# 重新输入测试文字
print("请重新在输入框输入测试文字...")
time.sleep(3)

# 方法4: 查找并点击发送按钮
print("方法4: 尝试查找'发送'或'提交'按钮并点击...")
time.sleep(2)

# 先截个图用于OCR查找
subprocess.run(['screencapture', '-x', 'debug_find_send_button.png'], check=False)
time.sleep(0.3)

import cv2
import pytesseract

img = cv2.imread('debug_find_send_button.png')
if img is not None:
    data = pytesseract.image_to_data(img, lang='chi_sim', output_type=pytesseract.Output.DICT)
    
    # 查找"发送"或"提交"按钮
    for i, text in enumerate(data['text']):
        if '发送' in text or '提交' in text or '确定' in text:
            conf = int(data['conf'][i])
            if conf > 50:
                x = data['left'][i] + data['width'][i] // 2
                y = data['top'][i] + data['height'][i] // 2
                print(f"  找到按钮 '{text}' at ({x}, {y}), 置信度={conf}")
                
                # 点击
                pyautogui.click(x, y)
                time.sleep(1)
                subprocess.run(['screencapture', '-x', 'debug_send_method4_click_button.png'], check=False)
                print(f"  已点击,截图: debug_send_method4_click_button.png")
                break

print()
print("=" * 60)
print("✅ 测试完成!")
print("=" * 60)
print()
print("请检查截图,看哪种方法成功发送了:")
print("1. debug_send_method1_enter.png")
print("2. debug_send_method2_cmd_enter.png")
print("3. debug_send_method3_ctrl_enter.png")
print("4. debug_send_method4_click_button.png")
print()
