#!/usr/bin/env python3
"""测试图标检测,看看实际匹配到了什么位置"""

import cv2
import numpy as np

# 读取截图和模板
screenshot = cv2.imread('debug_system_screenshot.png')
icon_template = cv2.imread('icon_template.png')

if screenshot is None or icon_template is None:
    print("❌ 无法读取文件")
    exit(1)

# 裁剪左侧栏
h, w = screenshot.shape[:2]
sidebar_width = int(w * 0.4)
sidebar = screenshot[:, :sidebar_width]

print(f"截图尺寸: {w}x{h}")
print(f"侧边栏宽度: {sidebar_width}")
print(f"模板尺寸: {icon_template.shape[:2][::-1]}")

# 多尺度模板匹配
scales = [0.8, 0.9, 1.0, 1.1, 1.2]
best_match = None
best_val = 0
best_scale = 1.0

for scale in scales:
    new_w = int(icon_template.shape[1] * scale)
    new_h = int(icon_template.shape[0] * scale)
    resized = cv2.resize(icon_template, (new_w, new_h))
    
    result = cv2.matchTemplate(sidebar, resized, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    
    print(f"尺度 {scale}: max_val={max_val:.4f}, 位置={max_loc}")
    
    if max_val > best_val:
        best_val = max_val
        best_match = (max_loc[0], max_loc[1], new_w, new_h)
        best_scale = scale

print(f"\n最佳匹配:")
print(f"  尺度: {best_scale}")
print(f"  匹配度: {best_val:.4f}")
print(f"  位置: {best_match}")
print(f"  阈值: 0.6")
print(f"  是否通过: {'✓' if best_val >= 0.6 else '✗'}")

# 可视化
if best_match:
    x, y, w, h = best_match
    vis = screenshot.copy()
    cv2.rectangle(vis, (x, y), (x+w, y+h), (0, 0, 255), 3)
    cv2.putText(vis, f"Score: {best_val:.3f}", (x, y-10), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    cv2.imwrite('debug_icon_match_test.png', vis)
    print("\n✓ 可视化已保存到 debug_icon_match_test.png")
