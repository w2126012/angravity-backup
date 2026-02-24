#!/usr/bin/env python3
"""测试图标检测"""

import cv2
import subprocess
import time

# 1. 截图
print("正在截图...")
subprocess.run(['screencapture', '-x', 'test_screenshot.png'], check=True)
time.sleep(0.2)

# 2. 加载图像
frame = cv2.imread('test_screenshot.png')
if frame is None:
    print("❌ 无法读取截图")
    exit(1)

print(f"✓ 截图尺寸: {frame.shape}")

# 3. 加载图标模板
icon_template = cv2.imread("icon_template.png")
if icon_template is None:
    print("❌ 无法读取icon_template.png")
    exit(1)

print(f"✓ 图标模板尺寸: {icon_template.shape}")

# 4. 裁剪左侧边栏
h, w = frame.shape[:2]
sidebar_width = int(w * 0.4)
sidebar = frame[:, :sidebar_width]
print(f"✓ 侧边栏尺寸: {sidebar.shape}")

# 5. 多尺度模板匹配
scales = [1.0, 0.8, 1.2, 0.9, 1.1, 0.7, 0.6, 0.5]
best_match = None
best_score = 0

for scale in scales:
    if scale != 1.0:
        scaled_w = int(icon_template.shape[1] * scale)
        scaled_h = int(icon_template.shape[0] * scale)
        if scaled_w <= 0 or scaled_h <= 0:
            continue
        template = cv2.resize(icon_template, (scaled_w, scaled_h))
    else:
        template = icon_template
    
    if template.shape[0] > sidebar.shape[0] or template.shape[1] > sidebar.shape[1]:
        continue
    
    try:
        result = cv2.matchTemplate(sidebar, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        print(f"  尺度 {scale:.2f}: 最佳分数 {max_val:.3f} 位置 {max_loc}")
        
        if max_val > best_score:
            best_score = max_val
            best_match = (max_loc[0], max_loc[1], template.shape[1], template.shape[0], scale)
    except Exception as e:
        print(f"  尺度 {scale:.2f}: 错误 {e}")
        continue

print(f"\n{'='*60}")
print(f"最佳匹配分数: {best_score:.3f}")
print(f"{'='*60}")

if best_match:
    x, y, w, h, scale = best_match
    print(f"位置: ({x}, {y})")
    print(f"尺寸: {w}×{h}")
    print(f"缩放: {scale:.2f}")
    
    # 绘制检测结果
    result_img = sidebar.copy()
    cv2.rectangle(result_img, (x, y), (x+w, y+h), (0, 255, 0), 2)
    cv2.putText(result_img, f"Score: {best_score:.3f}", (x, y-10), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    cv2.imwrite('test_icon_detection_result.png', result_img)
    print(f"\n✓ 结果已保存到 test_icon_detection_result.png")
    
    # 判断阈值
    thresholds = [0.6, 0.5, 0.4, 0.3, 0.25]
    print(f"\n阈值测试:")
    for thresh in thresholds:
        status = "✓ 通过" if best_score >= thresh else "✗ 未通过"
        print(f"  {thresh:.2f}: {status}")
else:
    print("❌ 未找到匹配")
