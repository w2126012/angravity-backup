
import time
import cv2
import logging
import subprocess
import numpy as np
import pyautogui
import pytesseract
from utils.window_capture import WindowCapture
from utils.image_processor import ImageProcessor
from utils.automation import AutomationController

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def safe_hotkey(*keys, pause=0.1):
    """
    执行快捷键前先按Escape退出中文输入法,防止组合键失效
    """
    # 先按Escape退出可能存在的中文输入法候选框
    pyautogui.press('escape')
    time.sleep(0.1)
    # 执行快捷键
    pyautogui.hotkey(*keys)
    time.sleep(pause)

def get_active_window_name():
    """获取当前活动窗口的名称"""
    try:
        script = '''
        tell application "System Events"
            set frontApp to name of first application process whose frontmost is true
            return frontApp
        end tell
        '''
        result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True, timeout=2)
        return result.stdout.strip()
    except Exception as e:
        logger.debug(f"获取活动窗口失败: {e}")
        return ""

def is_wecom_active():
    """检查企业微信是否是当前活动窗口"""
    active = get_active_window_name()
    return "企业微信" in active or "WeChat Work" in active

def find_text_location(image_path, target_text, offset_x=0, offset_y=0):
    """
    使用OCR边界框定位目标文字的位置
    
    Args:
        image_path: 截图文件路径
        target_text: 要查找的目标文字
        offset_x: 截图区域相对于屏幕的X偏移量
        offset_y: 截图区域相对于屏幕的Y偏移量
    
    Returns:
        (screen_x, screen_y) 屏幕坐标,如果未找到返回None
    """
    # ⚠️ Retina屏幕缩放因子: 截图是2倍分辨率
    RETINA_SCALE = 2.0
    
    try:
        img = cv2.imread(image_path)
        if img is None:
            logger.warning(f"无法读取图片: {image_path}")
            return None
        
        # 使用image_to_data获取每个文字的边界框
        # 同时使用中文和英文识别以提高准确率
        data = pytesseract.image_to_data(img, lang='chi_sim+eng', output_type=pytesseract.Output.DICT)
        
        n_boxes = len(data['text'])
        found_locations = []
        
        # 定义要匹配的关键词列表(部分匹配)
        keywords = [target_text]
        if target_text == '查看详情':
            keywords = ['查看详情', '查看', '详情', '看详']
        
        for i in range(n_boxes):
            text = data['text'][i].strip()
            conf = int(data['conf'][i]) if data['conf'][i] != '-1' else 0
            
            # 跳过空文本和低置信度
            if not text or conf < 10:  # 降低置信度阈值到10%
                continue
            
            # 检查是否匹配任何关键词
            matched = False
            for kw in keywords:
                if kw in text or text in kw:
                    matched = True
                    break
            
            if matched:
                x = data['left'][i]
                y = data['top'][i]
                w = data['width'][i]
                h = data['height'][i]
                
                # 计算图片内中心点
                img_center_x = x + w // 2
                img_center_y = y + h // 2
                
                # ⚠️ 转换为屏幕坐标 (需要除以Retina缩放因子)
                screen_x = offset_x + int(img_center_x / RETINA_SCALE)
                screen_y = offset_y + int(img_center_y / RETINA_SCALE)
                
                found_locations.append({
                    'text': text,
                    'conf': conf,
                    'box': (x, y, w, h),
                    'img_center': (img_center_x, img_center_y),
                    'screen': (screen_x, screen_y)
                })
                
                logger.info(f"📍 找到'{text}': 置信度={conf}%, 图片中心=({img_center_x},{img_center_y}), 屏幕坐标=({screen_x},{screen_y})")
        
        if found_locations:
            # ⚠️ 选择Y坐标最大的(最底部 = 最新消息)
            # 而不是置信度最高的,因为我们需要点击最新的工单
            best = max(found_locations, key=lambda x: x['screen'][1])  # screen[1]是y坐标
            logger.info(f"✅ 选择点击: {best['text']} at {best['screen']} (最底部/最新, Retina缩放已修正)")
            return best['screen']
        
        # 如果还没找到,打印所有识别到的文字用于调试
        all_texts = [t for t in data['text'] if t.strip()]
        logger.debug(f"OCR识别到的所有文字: {all_texts[:20]}")
        
        return None
        
    except Exception as e:
        logger.error(f"OCR边界框定位失败: {e}")
        return None


def main():
    logger.info("Starting WeCom AutoReply Service (Refactored Version)...")
    
    # ✅ 使用绝对路径，避免 nohup 启动时工作目录不一致导致截图写入失败
    import os as _os
    _BASE_DIR = _os.path.dirname(_os.path.abspath(__file__))
    SCREENSHOT_VISION_PATH    = _os.path.join(_BASE_DIR, 'debug_current_vision.png')
    SCREENSHOT_VERIFY_PATH    = _os.path.join(_BASE_DIR, 'debug_verify_chat.png')
    SCREENSHOT_TICKET_PATH    = _os.path.join(_BASE_DIR, 'debug_ticket_capture.png')
    
    # Initialize components
    monitor = WindowCapture(window_name="企业微信")
    vision = ImageProcessor()  # Text-based detection, no templates needed
    bot = AutomationController()
    
    # State: Deduplication Set
    processed_tickets = set()
    
    # 鼠标守护基准坐标: 点击进入聊天前记录, 后续步骤检查是否有用户操作
    mouse_guard_pos = None
    MOUSE_MOVE_THRESHOLD = 50  # 像素: 超过此值视为用户正在操作鼠标
    
    def update_mouse_guard():
        """更新鼠标守护基准为当前鼠标位置"""
        nonlocal mouse_guard_pos
        _p = pyautogui.position()
        mouse_guard_pos = (_p.x, _p.y)
    
    def script_click(x, y, pause=0.3):
        """程序点击: 执行点击后自动更新鼠标守护基准,避免误判"""
        nonlocal mouse_guard_pos
        pyautogui.click(x, y)
        time.sleep(pause)  # 等鼠标停稳
        _p = pyautogui.position()
        mouse_guard_pos = (_p.x, _p.y)  # 更新基准为点击后的新位置
    
    def user_is_using_mouse():
        """检测用户是否在移动鼠标 (相比守护基准坐标)"""
        if mouse_guard_pos is None:
            return False
        cur = pyautogui.position()
        dx = abs(cur.x - mouse_guard_pos[0])
        dy = abs(cur.y - mouse_guard_pos[1])
        moved = dx > MOUSE_MOVE_THRESHOLD or dy > MOUSE_MOVE_THRESHOLD
        if moved:
            logger.info(f"🖱️ 检测到鼠标移动 ({mouse_guard_pos} → {cur.x},{cur.y}), 终止本次自动处理")
        return moved
    
    # Click cooldown to prevent duplicate clicks
    last_click_time = 0
    CLICK_COOLDOWN = 30  # seconds - 等待30秒防止重复点击
    
    # Metrics
    loop_count = 0
    
    # External ticket system keywords (from debug_gongdan_massage1.png, debug_gongdan_massage2.png)
    # 外部工单系统关键词(参考截图)
    EXTERNAL_TICKET_KEYWORDS = [
        '宝冶集团IT服务系统',
        '上海宝冶集团', '工单管理', '钢结构工程公司',
        '基本信息', '跟进记录', '物资履约系统',
        '分包商物资履约平台', '所属路推',
        '主页', '服务目录', '工单',
        '全部', '处理中', '待审批', '跟踪交的', '我关注的',
        '编号', '标题', '所属路推', '项目体系', '优先级',
        '16029', '16020', '16015', '16011', '15973',  # 工单编号
        '问题解决',
        # 断网/安全警告关键词 (from debug_gongdan_massage3.png)
        '访问链接存在安全风险', '安全风险', '该连接不是私密连接',
        '继续访问', '错误信息', 'sbc-mcc.com', 'wx.sbc-mcc.com'
    ]
    
    # WeCom chat keywords (indicates we're in WeCom, NOT external system)
    # 注意: 避免使用过于通用的词(如"消息"),它们可能在外部系统中也出现
    WECOM_CHAT_KEYWORDS = [
        'IT服务工单', '通讯录', '文档', '日程', '会议', 
        '程琦', '孙仁武', '马海涛', '梁永天', '沙小琳',
        '宝冶IT服务系统 消息通知', '您的工单有新的进展', '添加了',
        '刚刚', '分钟前', '小时前', '昨天',
        '消息 通讯录', '智能表格助手', '运维小分队'  # 更具体的组合
    ]
    
    # Workbench keywords for STEP 5 (inside WeCom)
    WORKBENCH_KEYWORDS = [
        '基本信息', '跟进记录', '工单列表', '工单管理',
        '待处理', '处理中', '待审批', '提交时间', '转交时间',
        '问题已解决', '项目模块', '物资履约系统',
        '查看详情', '已完成', '我的待办', '工作台',
        '创建时间', '截止时间', '优先级', '处理人',
        '工单详情', '关闭工单', '标记完成'
    ]
    
    # Chat keywords for verification (STEP 6)
    CHAT_KEYWORDS = ['消息', '通讯录', '刚刚', '分钟前', '小时前']
    
    # 每日重启：记录上次重启日期，避免同一天多次重启
    import datetime
    last_restart_date = None
    
    # Main Loop
    while True:
        try:
            loop_count += 1
            if loop_count % 30 == 0:
                logger.info(f"Monitor running... (Iteration {loop_count}) | Processed IDs: {len(processed_tickets)}")

            # ============================================================
            # 每日凌晨5点自动重启企业微信 (清理遗留工单，防止电脑变卡)
            # ============================================================
            now = datetime.datetime.now()
            today = now.date()
            if now.hour == 13 and last_restart_date != today:
                logger.info("=" * 60)
                logger.info("🔄 每日13点自动重启企业微信...")
                logger.info("=" * 60)
                try:
                    # 强制退出企业微信
                    subprocess.run(['pkill', '-9', '-f', '企业微信'], timeout=5)
                    logger.info("✅ 已关闭企业微信")
                    time.sleep(3)
                    # 重新打开企业微信
                    subprocess.run(['open', '-a', '企业微信'], timeout=5)
                    logger.info("✅ 已重新打开企业微信，等待启动...")
                    time.sleep(15)  # 等待企业微信完全启动
                    # 清空去重集合，避免隔天工单因历史记录被跳过
                    processed_tickets.clear()
                    last_click_time = 0
                    last_restart_date = today
                    logger.info("✅ 已重置状态，继续监控...")
                except Exception as e:
                    logger.error(f"重启企业微信失败: {e}")
                    last_restart_date = today  # 即使失败也标记，避免反复重试
                continue

            # ============================================================
            # STEP 0: 被动截图检测IT服务工单状态
            # 查找"IT服务工单"聊天并检测红点状态
            # ============================================================
            screenshot_path = SCREENSHOT_VISION_PATH
            try:
                # 截取企业微信窗口
                window_id = monitor.find_window()
                if window_id:
                    subprocess.run(['screencapture', '-x', '-l', str(window_id), screenshot_path], 
                                   check=True, timeout=3)
                else:
                    subprocess.run(['screencapture', '-x', screenshot_path], check=True, timeout=2)
                
                time.sleep(0.2)
                frame = cv2.imread(screenshot_path)
                if frame is None:
                    logger.warning("Failed to read screenshot")
                    time.sleep(2)
                    continue
            except Exception as e:
                logger.error(f"Screenshot failed: {e}")
                time.sleep(2)
                continue
            
            # 查找IT服务工单并检测状态
            chat_rect, is_active, has_red_dot = vision.find_chat_with_state(frame, "IT服务工单")
            
            if not chat_rect:
                logger.debug("IT服务工单 chat not found")
                time.sleep(5)
                continue
            
            # ============================================================
            # STEP 1: 决定是否需要操作 (先判断红点状态)
            # ============================================================
            should_click = False
            should_process = False
            
            # Check click cooldown to prevent rapid repeated clicks
            time_since_click = time.time() - last_click_time
            if time_since_click < CLICK_COOLDOWN:
                logger.debug(f"点击冷却中... ({CLICK_COOLDOWN - time_since_click:.1f}s remaining)")
                time.sleep(2)
                continue
            
            if not is_active and has_red_dot:
                # 白色背景 + 红点 → 需要点击进入聊天
                logger.info("=" * 60)
                logger.info("🔴 检测到红点通知!")
                logger.info("📍 状态: 聊天未激活")
                logger.info("👆 操作: 点击进入聊天")
                logger.info("=" * 60)
                should_click = True
                should_process = True
            elif is_active and has_red_dot:
                # 蓝色背景 + 红点 → 已在聊天中有新消息
                logger.info("=" * 60)
                logger.info("🔴 检测到红点通知!")
                logger.info("📍 状态: 聊天已激活")
                logger.info("👆 操作: 直接检测工单(无需点击)")
                logger.info("=" * 60)
                should_click = False
                should_process = True
            else:
                # 无红点 → 跳过
                logger.debug("无红点通知 - 跳过")
                time.sleep(5)
                continue
            
            # ============================================================
            # 检测到红点后,先激活企微并清理环境
            # ============================================================
            # 激活企微窗口
            bot.activate_window("企业微信")
            time.sleep(0.3)
            
            # ============================================================
            # STEP 3, 4, 5: 暂时注释掉 - 调试用
            # ============================================================
            # # STEP 3: 全屏截图检测外部工单系统
            # external_ticket_path = "debug_fullscreen_check.png"
            # try:
            #     subprocess.run(['screencapture', '-x', external_ticket_path], check=True, timeout=2)
            #     time.sleep(0.3)
            #     fullscreen = cv2.imread(external_ticket_path)
            #     
            #     if fullscreen is not None:
            #         ocr_fullscreen = pytesseract.image_to_string(fullscreen, lang='chi_sim')
            #         
            #         has_external = any(kw in ocr_fullscreen for kw in EXTERNAL_TICKET_KEYWORDS)
            #         has_wecom_chat = any(kw in ocr_fullscreen for kw in WECOM_CHAT_KEYWORDS)
            #         
            #         # 检测到外部工单系统 AND 不在企微聊天中 → 关闭
            #         if has_external and not has_wecom_chat:
            #             logger.info("=" * 60)
            #             logger.info("🌐 检测到外部工单系统,执行关闭...")
            #             logger.info("=" * 60)
            #             safe_hotkey('command', 'w')
            #             time.sleep(1.5)
            #             # 重新激活企微
            #             bot.activate_window("企业微信")
            #             time.sleep(0.5)
            #             
            # except Exception as e:
            #     logger.debug(f"全屏检测失败: {e}")
            # 
            # # STEP 4: 企业微信窗口截图(被动检测)
            # system_screenshot_path = "debug_system_screenshot.png"
            # try:
            #     window_id = monitor.find_window()
            #     if window_id:
            #         subprocess.run(['screencapture', '-x', '-l', str(window_id), system_screenshot_path], 
            #                        check=True, timeout=3)
            #     else:
            #         subprocess.run(['screencapture', '-x', system_screenshot_path], check=True, timeout=2)
            #     time.sleep(0.2)
            # except Exception as e:
            #     logger.debug(f"企微窗口截图失败: {e}")
            # 
            # # STEP 5: 检测工作台页面(企微内部)
            # try:
            #     screenshot = cv2.imread(system_screenshot_path)
            #     if screenshot is not None:
            #         ocr_text = pytesseract.image_to_string(screenshot, lang='chi_sim')
            #         
            #         workbench_count = sum(1 for kw in WORKBENCH_KEYWORDS if kw in ocr_text)
            #         chat_count = sum(1 for kw in CHAT_KEYWORDS if kw in ocr_text)
            #         
            #         # 判断条件: 工作台关键词>=2 AND 聊天关键词<5
            #         is_on_workbench = workbench_count >= 2 and chat_count < 5
            #         
            #         if is_on_workbench:
            #             logger.info(f"检测到工作台页面 [工作台:{workbench_count}, 聊天:{chat_count}]")
            #             # 额外检查:确保当前确实不是聊天界面
            #             if chat_count >= 3:
            #                 logger.info("⚠️ 聊天关键词较多,可能是聊天界面,跳过Cmd+W")
            #             else:
            #                 logger.info("执行 Cmd+W 关闭工作台...")
            #                 bot.activate_window("企业微信")
            #                 time.sleep(0.3)
            #                 safe_hotkey('command', 'w')
            #                 time.sleep(1.0)
            # except Exception as e:
            #     logger.debug(f"工作台检测失败: {e}")
            
            # ============================================================
            # STEP 2: 点击进入聊天(如需要)
            # ============================================================
            if should_click:
                x, y, w, h = chat_rect
                logger.info(f"🔍 检测到图标位置: x={x}, y={y}, w={w}, h={h}")
                
                # 计算点击位置(图标中心 - 因为列表顺序不固定,直接点击识别到的图标)
                screenshot_click_x = x + w // 2  # 图标中心X
                screenshot_click_y = y + h // 2  # 图标中心Y
                
                # 获取窗口偏移量和尺寸
                window_x = 295.0  # 使用实际默认值
                window_y = 101.0
                window_w = 1009.0
                window_h = 666.0
                if hasattr(monitor, 'window_bounds') and monitor.window_bounds:
                    window_x = float(monitor.window_bounds.get('X', 295))
                    window_y = float(monitor.window_bounds.get('Y', 101))
                    window_w = float(monitor.window_bounds.get('Width', 1009))
                    window_h = float(monitor.window_bounds.get('Height', 666))
                logger.info(f"📍 窗口: ({window_x}, {window_y}), 尺寸: {window_w}x{window_h}")
                
                # 使用实际缩放比例:截图像素尺寸 / 窗口逻辑尺寸
                screenshot_width = frame.shape[1] if frame is not None else window_w * 2
                scale_factor = screenshot_width / window_w
                
                # 校验缩放因子范围(正常应该在2.0-2.5之间)
                if scale_factor < 1.5 or scale_factor > 3.0:
                    logger.warning(f"⚠️ 缩放因子异常: {scale_factor:.3f}, 使用默认值2.135")
                    scale_factor = 2.135
                
                # 转换到屏幕坐标:截图坐标 / 缩放比例 + 窗口偏移
                click_x = int(screenshot_click_x / scale_factor) + int(window_x)
                click_y = int(screenshot_click_y / scale_factor) + int(window_y)
                
                logger.info(f"📍 截图坐标(图标中心): ({screenshot_click_x}, {screenshot_click_y})")
                logger.info(f"📍 缩放比例: {scale_factor:.3f} ({screenshot_width}/{window_w})")
                logger.info(f"📍 点击坐标: ({click_x}, {click_y})")
                
                # 边界检查:点击位置应该在窗口左侧40%区域内(聊天列表)
                relative_x = click_x - window_x
                if relative_x > window_w * 0.4:
                    logger.warning(f"⚠️ 点击位置异常! 相对X={relative_x:.0f} > 窗口40%")
                    logger.warning("⚠️ 跳过此次点击,防止点到错误聊天")
                    last_click_time = time.time()  # 设置冷却期
                    continue
                
                # 激活并点击
                if bot.activate_window("企业微信"):
                    time.sleep(0.5)
                    script_click(click_x, click_y)
                    logger.info(f"✅ 已点击图标中心 ({click_x}, {click_y}), 🖱️ 守护基准已更新")
                    last_click_time = time.time()  # Set cooldown
                    time.sleep(0.5)

            
            
            # ============================================================
            # STEP 6: 点击后等待进入聊天 (已移除工作台检测,因关键词重叠导致误判)
            # ============================================================
            if should_process:
                # 🖱️ 检查用户是否在使用鼠标
                if user_is_using_mouse():
                    last_click_time = time.time()
                    mouse_guard_pos = None
                    continue
                
                logger.info("等待进入聊天...")
                time.sleep(1.0)  # 给界面切换一点时间
                
                # ============================================================
                # 验证当前聊天是否为IT服务工单
                # ============================================================
                logger.info("验证当前聊天...")
                time.sleep(0.5)
                try:
                    verify_window_id = monitor.find_window()
                    if verify_window_id:
                        subprocess.run(['screencapture', '-x', '-l', str(verify_window_id), SCREENSHOT_VERIFY_PATH],
                                       check=True, timeout=3)
                    else:
                        subprocess.run(['screencapture', '-x', SCREENSHOT_VERIFY_PATH], check=True, timeout=2)
                except Exception as e:
                    logger.warning(f"聊天验证截图失败: {e}, 直接继续处理")
                    verify_screenshot = None
                else:
                    verify_screenshot = cv2.imread(SCREENSHOT_VERIFY_PATH)
                
                if verify_screenshot is not None:
                    verify_text = pytesseract.image_to_string(verify_screenshot, lang='chi_sim')
                    # OCR 经常将 "IT" 识别为 "上T"，所以同时检测两种写法
                    IT_KEYWORDS = ['IT服务工单', '上T服务工单', '宝冶IT服务系统', '宝冶上T服务系统',
                                   '宝冶IT', '上T服务系统', 'IT服务系统']
                    found = any(kw in verify_text for kw in IT_KEYWORDS)
                    if not found:
                        logger.warning(f"⚠️ 当前不是IT服务工单聊天! OCR片段: {verify_text[:100].replace(chr(10),' ')}")
                        logger.warning("⚠️ 跳过处理,设置冷却期")
                        last_click_time = time.time()
                        continue
                    logger.info("✓ 确认在IT服务工单聊天中")
                
                # ============================================================
                # 点击聊天内容区域获取焦点 (使用窗口坐标)
                # ============================================================
                logger.info("点击聊天内容区域获取焦点...")
                
                # 获取企微窗口位置和缩放因子
                window_id = monitor.find_window()
                win_x, win_y, win_w, win_h = 295, 101, 1009, 666  # 默认值
                if hasattr(monitor, 'window_bounds') and monitor.window_bounds:
                    win_x = float(monitor.window_bounds.get('X', 295))
                    win_y = float(monitor.window_bounds.get('Y', 101))
                    win_w = float(monitor.window_bounds.get('Width', 1009))
                    win_h = float(monitor.window_bounds.get('Height', 666))
                
                logger.info(f"窗口位置: ({win_x}, {win_y}), 尺寸: {win_w}x{win_h}")
                
                # 企微窗口布局:
                # - 左侧约5%: 应用图标栏
                # - 左侧约25%: 聊天列表
                # - 右侧约70%: 聊天内容区域
                # 点击位置应该在窗口80%处,确保在聊天内容区域中间
                chat_click_x = int(win_x + win_w * 0.80)  # 调整到80%位置
                chat_click_y = int(win_y + win_h * 0.5)
                logger.info(f"点击聊天内容坐标: ({chat_click_x}, {chat_click_y}) [窗口80%位置]")
                script_click(chat_click_x, chat_click_y)
                time.sleep(0.3)
                
                # 滚动到最新消息 - 只使用End键
                logger.info("滚动到最新消息(End键)...")
                pyautogui.press('end')
                time.sleep(1.0)
                
                # ============================================================
                # 抓取最新工单信息 - 只截取企微聊天内容区域
                # ============================================================
                # 🖱️ 截图前再检查一次鼠标
                if user_is_using_mouse():
                    last_click_time = time.time()
                    mouse_guard_pos = None
                    continue
                
                logger.info("=" * 60)
                logger.info("📋 正在抓取最新工单信息...")
                
                # 计算聊天内容区域的坐标 (企微窗口右侧70%)
                # 企微布局: 左侧5%图标栏 + 25%聊天列表 = 30%, 右侧70%是聊天内容
                content_x = int(win_x + win_w * 0.30)  # 从30%开始
                content_y = int(win_y)
                content_w = int(win_w * 0.70)  # 右侧70%宽度
                content_h = int(win_h)
                
                
                logger.info(f"📸 只截取聊天内容区域: x={content_x}, y={content_y}, w={content_w}, h={content_h}")
                
                # 删除旧截图文件避免写入冲突
                import os
                if _os.path.exists(SCREENSHOT_TICKET_PATH):
                    _os.remove(SCREENSHOT_TICKET_PATH)
                
                # 使用 screencapture -R x,y,w,h 只截取指定区域
                try:
                    result = subprocess.run(
                        ['screencapture', '-x', '-R', 
                         f'{content_x},{content_y},{content_w},{content_h}',
                         SCREENSHOT_TICKET_PATH],
                        check=True, timeout=5, capture_output=True, text=True
                    )
                    time.sleep(0.3)
                    ticket_screenshot = cv2.imread(SCREENSHOT_TICKET_PATH)
                    if ticket_screenshot is None:
                        logger.error(f"❌ 截图文件读取失败: {SCREENSHOT_TICKET_PATH} 不存在或为空")
                        last_click_time = time.time()
                        continue
                except Exception as e:
                    logger.error(f"❌ 工单截图失败: {e}")
                    last_click_time = time.time()
                    continue
                
                if ticket_screenshot is not None:
                    full_text = pytesseract.image_to_string(ticket_screenshot, lang='chi_sim')
                    
                    # 打印OCR结果用于调试
                    logger.info(f"OCR文本(前300字符): {full_text[:300].replace(chr(10), ' ')}")
                    
                    import re
                    
                    # ⚠️ OCR经常将"查看详情"拆成"查"和"看详情"两行
                    # 使用去掉空白的压缩文本来检测，避免误判
                    full_text_compact = re.sub(r'\s+', '', full_text)
                    has_view_detail = '查看详情' in full_text_compact or '查看详情' in full_text
                    logger.info(f"包含'查看详情': {has_view_detail}")
                    
                    # ========================================
                    # 识别工单格式 - 汇总所有候选工单
                    # ========================================
                    
                    # 使用findall获取所有匹配
                    # 格式1: [人名] 添加了 [数字ID] - 新工单
                    pattern1 = r'(\w+)\s*添加了\s*(\d{5,})'
                    matches1 = re.findall(pattern1, full_text)
                    
                    # 格式2: 工单 [数字ID] ... (超时/未响应等) - 工单提醒
                    pattern2 = r'工单\s*(\d{5,})'
                    matches2 = re.findall(pattern2, full_text)
                    
                    # 日志:显示所有检测到的工单
                    if matches1:
                        logger.info(f"检测到新工单: {matches1}")
                    if matches2:
                        logger.info(f"检测到工单提醒: {matches2}")
                    
                    # 汇总所有候选工单(去重,保持顺序)
                    # 新工单优先,然后是提醒工单
                    # ⚠️ 去重key格式: "{ticket_id}_new" 或 "{ticket_id}_reminder"
                    # 这样同一工单的不同类型消息可以独立处理，不互相干扰
                    all_candidates = []
                    seen_dedup_keys = set()
                    for person_name, tid in matches1:
                        dedup_key = f"{tid}_new"
                        if dedup_key not in seen_dedup_keys:
                            seen_dedup_keys.add(dedup_key)
                            all_candidates.append((tid, f"新工单(由{person_name}添加)", dedup_key))
                    for tid in matches2:
                        dedup_key = f"{tid}_reminder"
                        if dedup_key not in seen_dedup_keys:
                            seen_dedup_keys.add(dedup_key)
                            all_candidates.append((tid, "工单提醒", dedup_key))
                    
                    logger.info(f"所有候选工单: {[(t[0], t[1]) for t in all_candidates]}")
                    
                    # ========================================
                    # 遍历候选工单,找到第一个未处理的
                    # ========================================
                    ticket_id = None
                    ticket_type = None
                    ticket_dedup_key = None
                    
                    if all_candidates and has_view_detail:
                        for cand_id, cand_type, cand_key in all_candidates:
                            if cand_key not in processed_tickets:
                                ticket_id = cand_id
                                ticket_type = cand_type
                                ticket_dedup_key = cand_key
                                logger.info(f"✅ 选中未处理工单: ID={ticket_id}, 类型={ticket_type}")
                                break
                            else:
                                logger.info(f"⏭️ 工单 {cand_id}({cand_type}) 已处理,检查下一个...")
                    
                    if ticket_id and has_view_detail:
                        # 记录工单并处理
                        processed_tickets.add(ticket_dedup_key)  # 用组合key去重
                        logger.info(f"✅ 检测到新消息: {ticket_type} (ID: {ticket_id})")
                        logger.info("=" * 40)
                        logger.info("开始处理工单...")
                        
                        # 🖱️ 点击查看详情前最后检查一次鼠标
                        if user_is_using_mouse():
                            # 已加入processed_tickets，避免重复处理需回退
                            processed_tickets.discard(ticket_dedup_key)
                            last_click_time = time.time()
                            mouse_guard_pos = None
                            break
                        
                        # ========================================
                        # 点击"查看详情"按钮 → 跳转到工单系统
                        # 使用OCR边界框定位精确点击
                        # ========================================
                        logger.info("🔗 步骤1: 使用OCR边界框定位'查看详情'按钮...")
                        
                        # 使用之前截取的聊天内容区域图片进行定位
                        # content_x, content_y 是截图区域的屏幕偏移量
                        view_detail_pos = find_text_location(
                            SCREENSHOT_TICKET_PATH, 
                            '查看详情',
                            offset_x=content_x,
                            offset_y=content_y
                        )
                        
                        if view_detail_pos:
                            link_x, link_y = view_detail_pos
                            logger.info(f"✅ OCR定位成功,点击坐标: ({link_x}, {link_y})")
                            script_click(link_x, link_y)
                        else:
                            # 如果OCR定位失败,使用备用固定坐标
                            logger.warning("⚠️ OCR定位失败,使用备用固定坐标...")
                            link_x = int(win_x + win_w * 0.75)
                            link_y = int(win_y + win_h * 0.70)
                            logger.info(f"备用点击坐标: ({link_x}, {link_y}) [窗口75%, 70%]")
                            script_click(link_x, link_y)
                        
                        # 等待10秒让工单系统加载
                        logger.info("⏳ 等待10秒让工单系统加载...")
                        time.sleep(10)
                        
                        # 回复"稍等"
                        logger.info("📝 回复'稍等'...")
                        import pyperclip
                        
                        # 复制到剪贴板
                        pyperclip.copy('稍等')
                        logger.info(f"   剪贴板: '{pyperclip.paste()}'")
                        
                        # 点击输入框获取焦点
                        screen_width, screen_height = pyautogui.size()
                        input_x = int(screen_width * 0.80)
                        input_y = int(screen_height * 0.77)
                        logger.info(f"   点击输入框: ({input_x}, {input_y})")
                        script_click(input_x, input_y)
                        time.sleep(0.5)
                        
                        # 粘贴 - 使用AppleScript确保Cmd+V可靠执行
                        logger.info("   粘贴 Cmd+V (AppleScript)...")
                        subprocess.run(['osascript', '-e', 
                            'tell application "System Events" to keystroke "v" using command down'],
                            timeout=3)
                        time.sleep(2)
                        
                        # 发送 - 使用AppleScript确保Enter可靠执行
                        logger.info("   发送 Enter (AppleScript)...")
                        subprocess.run(['osascript', '-e',
                            'tell application "System Events" to key code 36'],
                            timeout=3)
                        time.sleep(2)
                        
                        # 退出工单系统
                        logger.info("   退出 Escape...")
                        pyautogui.press('escape')
                        time.sleep(0.5)
                        logger.info("✅ 已回复'稍等'并退出工单")
                        
                        # 设置冷却期防止重复处理
                        last_click_time = time.time()
                        logger.info("✅ 已设置冷却期,防止重复处理")
                    elif all_candidates and all(ckey in processed_tickets for _, _, ckey in all_candidates):
                        # 所有候选工单都已处理
                        logger.info(f"⏭️ 所有候选工单均已处理,跳过")
                    else:
                        # 未匹配到有效工单格式
                        logger.warning("❌ 未匹配到有效工单格式 (需要: [人名]添加了[ID] 或 工单[ID])")
                        # 设置冷却期防止重复点击
                        last_click_time = time.time()
                        logger.info("   已设置冷却期,等待下一个真实通知")
                
                logger.info("=" * 60)
            
            # 循环间隔
            time.sleep(2)
            
        except KeyboardInterrupt:
            logger.info("Received stop signal, exiting...")
            break
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(5)

if __name__ == "__main__":
    main()
