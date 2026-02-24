#!/usr/bin/env python3
"""
测试增强的OCR检测 - 验证图像预处理和调试输出
"""
import time
import logging
import subprocess
import cv2
import numpy as np
import json

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_window_info_via_applescript():
    """使用AppleScript获取企业微信窗口信息"""
    script = '''
    tell application "System Events"
        tell process "企业微信"
            set windowList to windows
            if (count of windowList) > 0 then
                set mainWindow to window 1
                set windowPosition to position of mainWindow
                set windowSize to size of mainWindow
                set x to item 1 of windowPosition
                set y to item 2 of windowPosition
                set w to item 1 of windowSize
                set h to item 2 of windowSize
                return x & "," & y & "," & w & "," & h
            end if
        end tell
    end tell
    '''
    try:
        result = subprocess.run(['osascript', '-e', script], 
                              capture_output=True, text=True, check=True)
        coords = result.stdout.strip().split(',')
        if len(coords) == 4:
            return tuple(map(int, coords))
    except Exception as e:
        logger.error(f"获取窗口信息失败: {e}")
    return None


def activate_wecom():
    """激活企业微信窗口"""
    script = '''
    tell application "企业微信"
        activate
    end tell
    '''
    subprocess.run(['osascript', '-e', script], check=True)
    logger.info("已激活企业微信")
    time.sleep(0.5)


def test_ocr_detection():

    """测试增强的OCR检测"""
    logger.info("=" * 60)
    logger.info("开始测试增强的OCR检测")
    logger.info("=" * 60)
    
    # 1. 激活企业微信
    activate_wecom()
    time.sleep(1)
    
    # 2. 获取窗口信息
    win_info = get_window_info_via_applescript()
    if not win_info:
        logger.error("未找到企业微信窗口")
        return False
    
    win_x, win_y, win_w, win_h = win_info
    logger.info(f"企业微信窗口: x={win_x}, y={win_y}, w={win_w}, h={win_h}")
    
    # 3. 使用screencapture截取全屏
    screenshot_path = '/tmp/test_screenshot.png'
    subprocess.run(['screencapture', '-x', screenshot_path], check=True)
    logger.info(f"已截取全屏: {screenshot_path}")
    
    # 4. 读取并裁剪到企业微信窗口
    full_img = cv2.imread(screenshot_path)
    if full_img is None:
        logger.error("截图读取失败")
        return False
    
    # 计算缩放比例（Retina显示屏）
    screen_h, screen_w = full_img.shape[:2]
    scale = screen_h / 1080  # 假设屏幕高度
    logger.info(f"截图尺寸: {screen_w}x{screen_h}, 缩放比例: {scale:.2f}")
    
    # 裁剪企业微信窗口
    x1 = int(win_x * scale)
    y1 = int(win_y * scale)
    x2 = int((win_x + win_w) * scale)
    y2 = int((win_y + win_h) * scale)
    
    window_img = full_img[y1:y2, x1:x2]
    if window_img.size == 0:
        logger.error("窗口裁剪失败")
        return False
    
    cv2.imwrite('test_debug_window.png', window_img)
    logger.info(f"已保存企业微信窗口: test_debug_window.png, 尺寸: {window_img.shape}")
    
    # 5. 裁剪聊天区域（右侧60%）
    h, w = window_img.shape[:2]
    chat_x = int(w * 0.4)
    chat_roi = window_img[:, chat_x:]
    
    cv2.imwrite('test_debug_chat_roi_original.png', chat_roi)
    logger.info(f"已保存原始聊天区域: test_debug_chat_roi_original.png, 尺寸: {chat_roi.shape}")
    
    # 6. 图像预处理
    logger.info("-" * 60)
    logger.info("开始图像预处理...")
    
    # 6.1 灰度化
    gray = cv2.cvtColor(chat_roi, cv2.COLOR_BGR2GRAY)
    cv2.imwrite('test_debug_gray.png', gray)
    logger.debug("✓ 灰度化完成")
    
    # 6.2 二值化
    _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    cv2.imwrite('test_debug_binary.png', binary)
    logger.debug("✓ 二值化完成 (阈值=150)")
    
    # 6.3 放大2倍
    scaled = cv2.resize(binary, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    cv2.imwrite('test_debug_scaled.png', scaled)
    logger.debug(f"✓ 放大2倍完成, 新尺寸: {scaled.shape}")
    
    # 7. OCR识别
    logger.info("-" * 60)
    logger.info("开始OCR识别...")
    
    import pytesseract
    custom_config = r'--oem 3 --psm 6 -c preserve_interword_spaces=1'
    ocr_data = pytesseract.image_to_data(scaled, lang='chi_sim', 
                                          config=custom_config,
                                          output_type=pytesseract.Output.DICT)
    
    # 8. 输出所有OCR结果
    logger.info("-" * 60)
    logger.info("OCR识别结果:")
    
    all_texts = []
    for i in range(len(ocr_data['text'])):
        text = ocr_data['text'][i].strip()
        if text:
            conf = ocr_data['conf'][i]
            x = ocr_data['left'][i]
            y = ocr_data['top'][i]
            w_text = ocr_data['width'][i]
            h_text = ocr_data['height'][i]
            all_texts.append((text, conf, x, y, w_text, h_text))
    
    logger.info(f"共检测到 {len(all_texts)} 个文字")
    logger.info("")
    
    # 显示前30个结果
    for idx, (text, conf, x, y, w_text, h_text) in enumerate(all_texts[:30]):
        logger.info(f"  [{idx+1}] 文字='{text}', 置信度={conf:.1f}, 位置=({x}, {y}), 尺寸=({w_text}x{h_text})")
    
    if len(all_texts) > 30:
        logger.info(f"  ... 还有 {len(all_texts) - 30} 个结果未显示")
    
    # 9. 搜索"查看详情"
    logger.info("-" * 60)
    logger.info("搜索'查看详情'关键词...")
    
    found_keywords = []
    for text, conf, x, y, w_text, h_text in all_texts:
        if '查看详情' in text or '查看' in text or '详情' in text or '查' in text or '详' in text:
            found_keywords.append((text, conf, x, y, w_text, h_text))
            logger.info(f"  ✓ 找到候选: '{text}', 置信度={conf:.1f}")
    
    if not found_keywords:
        logger.warning("❌ 未找到任何'查看详情'相关的关键词")
        logger.warning("请检查以下调试图像:")
        logger.warning("  - test_debug_window.png (完整窗口)")
        logger.warning("  - test_debug_chat_roi_original.png (聊天区域原图)")
        logger.warning("  - test_debug_gray.png (灰度化)")
        logger.warning("  - test_debug_binary.png (二值化)")
        logger.warning("  - test_debug_scaled.png (放大2倍)")
        return False
    else:
        logger.info(f"✅ 共找到 {len(found_keywords)} 个候选关键词")
        
        # 选择置信度最高且最完整的
        best_match = None
        for text, conf, x, y, w_text, h_text in found_keywords:
            if conf > 10:
                if best_match is None or len(text) > len(best_match[0]):
                    best_match = (text, conf, x, y, w_text, h_text)
        
        if best_match:
            text, conf, x, y, w_text, h_text = best_match
            # 坐标缩放回原始尺寸
            actual_x = x // 2
            actual_y = y // 2
            actual_w = w_text // 2
            actual_h = h_text // 2
            
            btn_x_in_window = chat_x + actual_x + actual_w // 2
            btn_y_in_window = actual_y + actual_h // 2
            
            logger.info(f"✅ 最佳匹配: '{text}', 置信度={conf:.1f}")
            logger.info(f"   窗口内坐标: ({btn_x_in_window}, {btn_y_in_window})")
            
            # 在原始窗口图像上标记位置
            marked_img = window_img.copy()
            cv2.circle(marked_img, (btn_x_in_window, btn_y_in_window), 10, (0, 255, 0), 3)
            cv2.rectangle(marked_img, 
                         (chat_x + actual_x, actual_y),
                         (chat_x + actual_x + actual_w, actual_y + actual_h),
                         (0, 0, 255), 2)
            cv2.imwrite('test_debug_marked.png', marked_img)
            logger.info("✅ 已保存标记图像: test_debug_marked.png")
            
            return True
        else:
            logger.warning("❌ 找到关键词但置信度都低于10")
            return False


if __name__ == "__main__":
    success = test_ocr_detection()
    if success:
        logger.info("=" * 60)
        logger.info("✅ 测试成功！OCR可以检测到'查看详情'")
        logger.info("=" * 60)
    else:
        logger.info("=" * 60)
        logger.error("❌ 测试失败，OCR未能检测到'查看详情'")
        logger.info("=" * 60)
