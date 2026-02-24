#!/usr/bin/env python3
"""
可视化测试 - 在截图上标记OCR识别到的"查看详情"位置
"""

import subprocess
import cv2
import pytesseract
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
    'test_visualize.png'
])
time.sleep(0.5)

# 4. OCR识别
print("4. OCR识别...")
img = cv2.imread('test_visualize.png')
data = pytesseract.image_to_data(img, lang='chi_sim+eng', output_type=pytesseract.Output.DICT)

# 5. 查找并标记"查看详情"
print("5. 查找并标记'查看详情'...")
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
            
            # 在图片上绘制矩形框
            cv2.rectangle(img, (box_x, box_y), (box_x + box_w, box_y + box_h), (0, 0, 255), 2)
            # 标记中心点
            center_x = box_x + box_w // 2
            center_y = box_y + box_h // 2
            cv2.circle(img, (center_x, center_y), 5, (0, 255, 0), -1)
            # 添加文字标签
            cv2.putText(img, f"{text}({conf}%)", (box_x, box_y - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
            
            # 计算屏幕坐标
            screen_x = content_x + center_x
            screen_y = content_y + center_y
            
            print(f"   找到: '{text}' 图片坐标=({center_x},{center_y}) 屏幕坐标=({screen_x},{screen_y})")
            found.append((text, conf, screen_x, screen_y, center_x, center_y))
            break

# 保存标记后的图片
cv2.imwrite('test_visualize_marked.png', img)
print(f"\n6. 已保存标记图片: test_visualize_marked.png")

if found:
    print(f"\n找到 {len(found)} 个匹配项")
    print("请打开 test_visualize_marked.png 查看标记位置是否正确")
else:
    print("❌ 未找到任何匹配")
