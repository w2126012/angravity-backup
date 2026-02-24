#!/usr/bin/env python3
"""在debug_system_screenshot.png上标记检测到的位置"""

import cv2

# 读取截图
img = cv2.imread('debug_system_screenshot.png')

if img is not None:
    # 检测到的位置
    x, y, w, h = 740, 352, 86, 80
    
    # 绘制矩形
    cv2.rectangle(img, (x, y), (x+w, y+h), (0, 0, 255), 3)
    
    # 标记中心点
    center_x = x + w//2
    center_y = y + h//2
    cv2.circle(img, (center_x, center_y), 10, (0, 255, 0), -1)
    
    # 添加文字
    cv2.putText(img, f'({x},{y},{w},{h})', (x, y-10), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    cv2.putText(img, f'Click: ({center_x},{center_y})', (center_x-50, center_y-20), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    
    # 保存
    cv2.imwrite('debug_detected_position.png', img)
    print(f"✓ 已标记检测位置: ({x}, {y}, {w}, {h})")
    print(f"✓ 点击坐标: ({center_x}, {center_y})")
    print("✓ 已保存到 debug_detected_position.png")
else:
    print("❌ 无法读取截图")
