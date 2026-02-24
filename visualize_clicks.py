#!/usr/bin/env python3
"""在截图上标记当前点击位置和建议的点击位置"""

import cv2

# 读取截图
img = cv2.imread('debug_system_screenshot.png')

if img is not None:
    # 检测到的图标位置
    x, y, w, h = 740, 352, 86, 80
    
    # 绘制图标框
    cv2.rectangle(img, (x, y), (x+w, y+h), (0, 0, 255), 2)
    cv2.putText(img, 'Icon', (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
    
    # 当前点击位置(偏移50)
    icon_right = x + w  # 826
    current_click_x = icon_right + 50  # 876
    current_click_y = y + h // 2  # 392
    cv2.circle(img, (current_click_x, current_click_y), 8, (0, 165, 255), -1)
    cv2.putText(img, f'Current: ({current_click_x},{current_click_y})', 
                (current_click_x-80, current_click_y-15), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 165, 255), 2)
    
    # 建议的点击位置(从截图看,IT服务工单文字应该在图标右侧约100-120px)
    # 尝试几个不同的偏移量
    offsets = [80, 100, 120, 150]
    colors = [(255, 0, 0), (0, 255, 0), (255, 255, 0), (255, 0, 255)]
    
    for i, offset in enumerate(offsets):
        test_x = icon_right + offset
        test_y = y + h // 2
        cv2.circle(img, (test_x, test_y), 6, colors[i], -1)
        cv2.putText(img, f'+{offset}', (test_x-15, test_y+20), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, colors[i], 1)
    
    # 保存
    cv2.imwrite('debug_click_positions.png', img)
    print(f"✓ 已标记点击位置")
    print(f"  当前点击: ({current_click_x}, {current_click_y}) [偏移+50]")
    print(f"  测试点位: 红色+80, 绿色+100, 黄色+120, 紫色+150")
    print("✓ 已保存到 debug_click_positions.png")
else:
    print("❌ 无法读取截图")
