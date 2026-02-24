#!/usr/bin/env python3
"""
简化的OCR测试 - 直接使用screencapture和手动窗口坐标
"""
import time
import logging
import subprocess
import cv2
import pytesseract

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_ocr():
    """测试OCR检测"""
    logger.info("=" * 60)
    logger.info("开始OCR测试")
    logger.info("=" * 60)
    
    # 1. 激活企业微信
    logger.info("激活企业微信...")
    subprocess.run(['osascript', '-e', 'tell application "企业微信" to activate'], check=True)
    time.sleep(2)
    
    # 1.5 关闭可能打开的工单页面
    logger.info("关闭可能打开的工单页面...")
    close_script = '''
    tell application "System Events"
        tell process "企业微信"
            keystroke "w" using command down
        end tell
    end tell
    '''
    try:
        subprocess.run(['osascript', '-e', close_script], check=True, timeout=2)
        logger.info("已执行 Cmd+W")
        time.sleep(1)
    except Exception as e:
        logger.warning(f"Cmd+W 执行失败(可能没有窗口需要关闭): {e}")
    
    # 2. 截取全屏
    screenshot_path = 'test_full_screenshot.png'
    logger.info(f"截取全屏到 {screenshot_path}...")
    subprocess.run(['screencapture', '-x', screenshot_path], check=True)
    time.sleep(0.5)
    
    # 3. 读取截图
    full_img = cv2.imread(screenshot_path)
    if full_img is None:
        logger.error("截图读取失败")
        return False
    
    logger.info(f"截图尺寸: {full_img.shape}")
    
    # 4. 假设企业微信窗口在屏幕中央,裁剪右侧60%作为聊天区域
    # 这里使用整个截图的右侧60%作为测试
    h, w = full_img.shape[:2]
    chat_x = int(w * 0.4)
    chat_roi = full_img[:, chat_x:]
    
    cv2.imwrite('test_chat_roi_original.png', chat_roi)
    logger.info(f"聊天区域尺寸: {chat_roi.shape}")
    logger.info("已保存: test_chat_roi_original.png")
    
    # 5. 图像预处理
    logger.info("-" * 60)
    logger.info("开始图像预处理...")
    
    # 灰度化
    gray = cv2.cvtColor(chat_roi, cv2.COLOR_BGR2GRAY)
    cv2.imwrite('test_gray.png', gray)
    logger.debug("✓ 灰度化完成")
    
    # 二值化
    _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    cv2.imwrite('test_binary.png', binary)
    logger.debug("✓ 二值化完成")
    
    # 放大2倍
    scaled = cv2.resize(binary, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    cv2.imwrite('test_scaled.png', scaled)
    logger.debug(f"✓ 放大2倍完成, 新尺寸: {scaled.shape}")
    
    # 6. OCR识别
    logger.info("-" * 60)
    logger.info("开始OCR识别...")
    
    custom_config = r'--oem 3 --psm 6 -c preserve_interword_spaces=1'
    ocr_data = pytesseract.image_to_data(scaled, lang='chi_sim', 
                                          config=custom_config,
                                          output_type=pytesseract.Output.DICT)
    
    # 7. 输出所有OCR结果
    logger.info("-" * 60)
    logger.info("OCR识别结果:")
    
    all_texts = []
    for i in range(len(ocr_data['text'])):
        text = ocr_data['text'][i].strip()
        if text:
            conf = ocr_data['conf'][i]
            all_texts.append((text, conf))
    
    logger.info(f"共检测到 {len(all_texts)} 个文字")
    logger.info("")
    
    # 显示前50个结果
    for idx, (text, conf) in enumerate(all_texts[:50]):
        logger.info(f"  [{idx+1}] '{text}' (置信度={conf:.1f})")
    
    if len(all_texts) > 50:
        logger.info(f"  ... 还有 {len(all_texts) - 50} 个结果未显示")
    
    # 8. 搜索"查看详情"
    logger.info("-" * 60)
    logger.info("搜索'查看详情'关键词...")
    
    found = []
    for text, conf in all_texts:
        if '查看详情' in text or '查看' in text or '详情' in text or '查' in text or '详' in text:
            found.append((text, conf))
            logger.info(f"  ✓ 找到候选: '{text}', 置信度={conf:.1f}")
    
    if not found:
        logger.warning("❌ 未找到任何'查看详情'相关的关键词")
        logger.warning("请检查以下调试图像:")
        logger.warning("  - test_full_screenshot.png")
        logger.warning("  - test_chat_roi_original.png")
        logger.warning("  - test_gray.png")
        logger.warning("  - test_binary.png")
        logger.warning("  - test_scaled.png")
        return False
    else:
        logger.info(f"✅ 共找到 {len(found)} 个候选关键词")
        return True


if __name__ == "__main__":
    success = test_ocr()
    logger.info("=" * 60)
    if success:
        logger.info("✅ 测试成功！OCR可以检测到'查看详情'相关文字")
    else:
        logger.error("❌ 测试失败，OCR未能检测到'查看详情'")
    logger.info("=" * 60)
