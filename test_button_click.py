#!/usr/bin/env python3
"""
智能测试脚本 - 先判断是否在工单页面,只在需要时执行Cmd+W
"""
import cv2
import subprocess
import time
import pyautogui
import pytesseract

def activate_and_ensure_chat():
    """激活企业微信并确保在聊天列表"""
    print("激活企业微信窗口...")
    script = '''
        tell application "企业微信" to activate
        delay 0.5
    '''
    subprocess.run(['osascript', '-e', script])
    time.sleep(1)
    print("✓ 企业微信已激活")
    
    # 窗口信息
    win_x = 273
    win_y = 74  
    win_w = 1009
    win_h = 666
    scale = 2.0
    
    max_attempts = 3
    for attempt in range(max_attempts):
        print(f"\n检查当前页面 (尝试 {attempt + 1}/{max_attempts})...")
        
        # 截图检测
        screenshot_path = "debug_check.png"
        subprocess.run(['screencapture', '-x', screenshot_path], check=True)
        time.sleep(0.3)
        
        screenshot = cv2.imread(screenshot_path)
        if screenshot is None:
            print("  截图失败")
            continue
        
        # 裁剪到窗口
        crop_x = int(win_x * scale)
        crop_y = int(win_y * scale)
        crop_w = int(win_w * scale)
        crop_h = int(win_h * scale)
        
        screen_h, screen_w = screenshot.shape[:2]
        if crop_x + crop_w > screen_w or crop_y + crop_h > screen_h:
            print("  窗口超出屏幕")
            continue
        
        window_img = screenshot[crop_y:crop_y+crop_h, crop_x:crop_x+crop_w]
        
        # OCR检测工单关键词
        ocr_text = pytesseract.image_to_string(window_img, lang='chi_sim')
        workbench_keywords = [
            '基本信息', '跟进记录', '工单列表', '工单管理',
            '待处理', '处理中', '提交时间', '转交时间',
            '问题已解决', '项目模块'
        ]
        is_on_workbench = any(kw in ocr_text for kw in workbench_keywords)
        
        if is_on_workbench:
            print(f"  ✓ 检测到工单页面 - 执行 Cmd+W")
            # 使用AppleScript发送Cmd+W,避免输入法干扰
            script = '''
                tell application "System Events"
                    keystroke "w" using command down
                end tell
            '''
            subprocess.run(['osascript', '-e', script])
            time.sleep(1.5)
        else:
            print(f"  ✓ 已在聊天列表")
            return True
    
    print("  ⚠️ 无法确认是否在聊天列表")
    return False

def test_button_click():
    print("="*60)
    print("测试点击'查看详情'按钮")
    print("="*60)
    
    # 激活并确保在聊天列表
    if not activate_and_ensure_chat():
        print("\n警告: 无法确认在聊天列表,继续测试可能失败")
        input("按Enter继续...")
    
    # 点击进入IT服务工单聊天
    print("\n查找并点击'IT服务工单'聊天...")
    icon_template = cv2.imread("icon_template.png")
    if icon_template is None:
        print("❌ icon_template.png 未找到")
        print("跳过聊天点击步骤,假设已在IT服务工单聊天中")
    else:
        # 截图查找图标
        subprocess.run(['screencapture', '-x', 'debug_icon_search.png'], check=True)
        time.sleep(0.3)
        screenshot = cv2.imread('debug_icon_search.png')
        
        win_x = 273
        win_y = 74
        win_w = 1009
        win_h = 666
        scale = 2.0
        
        # 裁剪到窗口左侧(聊天列表区域)
        crop_x = int(win_x * scale)
        crop_y = int(win_y * scale)
        crop_w = int(win_w * scale * 0.3)  # 左侧30%
        crop_h = int(win_h * scale)
        
        sidebar = screenshot[crop_y:crop_y+crop_h, crop_x:crop_x+crop_w]
        
        # 模板匹配查找图标
        result = cv2.matchTemplate(sidebar, icon_template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        if max_val > 0.6:
            icon_x = max_loc[0] + icon_template.shape[1] // 2
            icon_y = max_loc[1] + icon_template.shape[0] // 2
            click_x = win_x + icon_x / scale
            click_y = win_y + icon_y / scale
            
            print(f"✓ 找到IT服务工单图标, 点击位置: ({click_x:.1f}, {click_y:.1f})")
            pyautogui.click(click_x, click_y)
            time.sleep(1)
            print("✓ 已点击进入IT服务工单聊天")
            
            # 5. 移动鼠标到聊天消息区域并滚动到底部
            print("\n滚动到聊天底部...")
            win_x = 273
            win_y = 74
            win_w = 1009
            win_h = 666
            
            # 聊天消息区域在右侧,大约60%宽度,50%高度处
            chat_area_x = win_x + win_w * 0.6
            chat_area_y = win_y + win_h * 0.5
            
            # 移动鼠标到聊天区域
            pyautogui.moveTo(chat_area_x, chat_area_y)
            time.sleep(0.3)
            print(f"✓ 鼠标移动到聊天区域: ({chat_area_x:.1f}, {chat_area_y:.1f})")
            
            # 向下滚动多次确保到底部
            for i in range(10):
                pyautogui.scroll(-5)  # 负数向下滚动
                time.sleep(0.1)
            
            time.sleep(0.5)
            print("✓ 已滚动到聊天底部")
        else:
            print(f"未找到IT服务工单图标 (score: {max_val:.3f})")
            print("假设已在IT服务工单聊天中")
    
    # 使用窗口信息
    win_x = 273
    win_y = 74  
    win_w = 1009
    win_h = 666
    scale = 2.0
    
    print(f"\n使用窗口位置: x={win_x}, y={win_y}, w={win_w}, h={win_h}")
    
    # 截图
    screenshot_path = "debug_button_test.png"
    print("正在截图...")
    subprocess.run(['screencapture', '-x', screenshot_path], check=True)
    time.sleep(0.5)
    
    screenshot = cv2.imread(screenshot_path)
    button_template = cv2.imread("button_template.png")
    
    if screenshot is None:
        print("❌ 截图加载失败")
        return
    if button_template is None:
        print("❌ 按钮模板加载失败")
        return
    
    print(f"✓ 截图尺寸: {screenshot.shape}")
    print(f"✓ 模板尺寸: {button_template.shape}")
    
    # 裁剪到窗口
    crop_x = int(win_x * scale)
    crop_y = int(win_y * scale)
    crop_w = int(win_w * scale)
    crop_h = int(win_h * scale)
    
    screen_h, screen_w = screenshot.shape[:2]
    if crop_x + crop_w > screen_w or crop_y + crop_h > screen_h:
        print("❌ 窗口超出屏幕范围")
        return
    
    window_img = screenshot[crop_y:crop_y+crop_h, crop_x:crop_x+crop_w]
    cv2.imwrite("debug_cropped_window.png", window_img)
    print(f"✓ 窗口图像尺寸: {window_img.shape}")
    print(f"✓ 已保存 debug_cropped_window.png")
    
    # 在右侧搜索按钮
    h, w = window_img.shape[:2]
    chat_x = int(w * 0.4)
    chat_roi = window_img[:, chat_x:]
    print(f"✓ 搜索区域尺寸: {chat_roi.shape}")
    
    # 模板匹配
    print("\n正在匹配按钮...")
    result = cv2.matchTemplate(chat_roi, button_template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    
    print(f"\n匹配结果:")
    print(f"  分数: {max_val:.3f}")
    print(f"  位置: {max_loc}")
    
    if max_val < 0.3:
        print(f"\n❌ 按钮未找到 (score: {max_val:.3f} < 0.3)")
        print("请确保聊天列表中有工单通知显示'查看详情'按钮")
        return
    
    print(f"✓ 找到按钮!")
    
    # 计算按钮中心
    btn_x_in_window = chat_x + max_loc[0] + button_template.shape[1] // 2
    btn_y_in_window = max_loc[1] + button_template.shape[0] // 2
    
    # 转换到屏幕坐标
    btn_click_x = win_x + btn_x_in_window / scale
    btn_click_y = win_y + btn_y_in_window / scale
    
    print(f"\n按钮位置:")
    print(f"  窗口内: ({btn_x_in_window}, {btn_y_in_window})")
    print(f"  屏幕: ({btn_click_x:.1f}, {btn_click_y:.1f})")
    
    # 标记按钮位置
    btn_x = chat_x + max_loc[0]
    btn_y = max_loc[1]
    cv2.rectangle(window_img, (btn_x, btn_y), 
                  (btn_x + button_template.shape[1], btn_y + button_template.shape[0]), 
                  (0, 255, 0), 3)
    cv2.imwrite("debug_button_marked.png", window_img)
    print(f"\n✓ 已保存 debug_button_marked.png")
    
    # 确认点击
    print("\n" + "="*60)
    print(f"准备点击: ({btn_click_x:.1f}, {btn_click_y:.1f})")
    response = input("按 Enter 执行点击 (或输入 n 取消): ")
    
    if response.lower() == 'n':
        print("已取消")
        return
    
    # 点击
    print("正在点击...")
    pyautogui.click(btn_click_x, btn_click_y)
    print(f"✓ 已点击 ({btn_click_x:.1f}, {btn_click_y:.1f})")
    print("\n请检查是否打开了工单详情页面")

if __name__ == "__main__":
    test_button_click()
