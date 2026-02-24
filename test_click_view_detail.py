#!/usr/bin/env python3
"""
测试点击"查看详情"按钮
简化流程专门测试OCR定位和点击
"""

import subprocess
import cv2
import pytesseract
import pyautogui
import time

# 获取企微窗口位置
def get_wecom_window():
    script = '''
    tell application "System Events"
        tell process "企业微信"
            set winPos to position of window 1
            set winSize to size of window 1
            set x to item 1 of winPos
            set y to item 2 of winPos
            set w to item 1 of winSize
            set h to item 2 of winSize
            return (x as text) & "," & (y as text) & "," & (w as text) & "," & (h as text)
        end tell
    end tell
    '''
    result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
    print(f"   AppleScript输出: {result.stdout.strip()}")
    if result.stderr:
        print(f"   AppleScript错误: {result.stderr}")
    parts = result.stdout.strip().split(',')
    if len(parts) == 4:
        return int(float(parts[0])), int(float(parts[1])), int(float(parts[2])), int(float(parts[3]))
    return None

# 1. 激活企微
print("1. 激活企业微信...")
subprocess.run(['open', '-a', '企业微信'])
time.sleep(1)

# 2. 获取窗口位置
win = get_wecom_window()
if win:
    x, y, w, h = win
    print(f"2. 窗口位置: ({x}, {y}), 尺寸: {w}x{h}")
else:
    print("❌ 无法获取窗口位置")
    exit(1)

# 3. 截取聊天内容区域
content_x = int(x + w * 0.30)
content_y = y
content_w = int(w * 0.70)
content_h = h

print(f"3. 截取聊天区域: x={content_x}, y={content_y}, w={content_w}, h={content_h}")

subprocess.run([
    'screencapture', '-x', '-R',
    f'{content_x},{content_y},{content_w},{content_h}',
    'test_view_detail.png'
])
time.sleep(0.5)

# 4. OCR识别
print("4. OCR识别...")
img = cv2.imread('test_view_detail.png')
data = pytesseract.image_to_data(img, lang='chi_sim+eng', output_type=pytesseract.Output.DICT)

# 5. 查找"查看详情"
print("5. 查找'查看详情'按钮...")
keywords = ['查看详情', '查看', '详情']
found = []

for i in range(len(data['text'])):
    text = data['text'][i].strip()
    conf = int(data['conf'][i]) if data['conf'][i] != '-1' else 0
    
    if not text or conf < 10:
        continue
    
    for kw in keywords:
        if kw in text or text in kw:
            box_x = data['left'][i]
            box_y = data['top'][i]
            box_w = data['width'][i]
            box_h = data['height'][i]
            
            # 计算图片内中心坐标
            img_center_x = box_x + box_w // 2
            img_center_y = box_y + box_h // 2
            
            print(f"   找到: '{text}' (置信度={conf}%) 边界框=({box_x},{box_y},{box_w},{box_h}) 图片中心=({img_center_x},{img_center_y})")
            # 保存: (text, conf, img_center_x, img_center_y)
            found.append((text, conf, img_center_x, img_center_y))
            break

if not found:
    print("❌ 未找到'查看详情'按钮")
    print("   OCR识别到的文字:", [t for t in data['text'] if t.strip()][:30])
    exit(1)

# 6. 选择最佳匹配并点击
best = max(found, key=lambda x: x[1])  # 选置信度最高

# ⚠️ Retina屏幕修正: 截图是2倍分辨率,需要除以2
# 图片坐标 / 2 = 窗口内相对坐标
# 窗口内相对坐标 + 窗口偏移 = 屏幕坐标
scale = 2.0  # Retina缩放因子
img_center_x = best[2]  # 图片内中心x
img_center_y = best[3]  # 图片内中心y
corrected_x = content_x + int(img_center_x / scale)
corrected_y = content_y + int(img_center_y / scale)

print(f"\n6. 准备点击: '{best[0]}'")
print(f"   图片内坐标: ({img_center_x}, {img_center_y})")
print(f"   修正后屏幕坐标: ({corrected_x}, {corrected_y}) [÷2 + 偏移]")

input("\n按回车键执行点击...")

# 先激活企微窗口
print("   重新激活企业微信...")
subprocess.run(['open', '-a', '企业微信'])
time.sleep(0.5)

# 执行点击 - 使用修正后的坐标
print(f"   点击坐标: ({corrected_x}, {corrected_y})")
pyautogui.click(corrected_x, corrected_y)
print("✅ 已点击!")
print("\n观察是否跳转到了工单系统...")
