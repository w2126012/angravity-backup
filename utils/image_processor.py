
import cv2
import numpy as np
import pytesseract
import re

class ImageProcessor:
    def __init__(self, threshold=0.7):
        """
        ImageProcessor for text-based detection.
        No longer uses template matching.
        """
        self.threshold = threshold
        print("[INFO] ImageProcessor initialized with text-based detection strategy.")

    def find_text_location(self, image, target_text="IT服务"):
        """
        Uses OCR to find target text in the image (left sidebar chat list).
        Returns (x, y, w, h) of the text bounding box, or None if not found.
        """
        if image is None or image.size == 0:
            return None
        
        try:
            # Crop to left sidebar (chat list area)
            # Assuming left 40% of window contains the chat list
            h, w = image.shape[:2]
            sidebar_width = int(w * 0.4)
            sidebar = image[:, :sidebar_width]
            
            # Convert to grayscale for better OCR
            gray = cv2.cvtColor(sidebar, cv2.COLOR_BGR2GRAY)
            
            # Use pytesseract to get detailed box information
            # lang='chi_sim' for simplified Chinese
            data = pytesseract.image_to_data(gray, lang='chi_sim', output_type=pytesseract.Output.DICT)
            
            # Debug: Print all detected text
            all_text = [data['text'][i].strip() for i in range(len(data['text'])) if data['text'][i].strip()]
            if all_text:
                print(f"[DEBUG] OCR detected {len(all_text)} text items: {all_text[:10]}")  # Show first 10
                
                # Join all text to see if target appears when combined
                combined = ''.join(all_text)
                print(f"[DEBUG] Combined text (first 100 chars): {combined[:100]}")
            else:
                print("[DEBUG] OCR detected no text in sidebar")
            
            # Strategy 1: Search for "IT服务工单" in combined text (more specific)
            combined_text = ''.join(all_text)
            
            # Try to find the full target first, then fallback to partial match
            # OCR sometimes misrecognizes "IT" as other characters like "盯", "上T", etc.
            search_targets = ["IT服务工单", "服务工单"]  # Fallback to just "服务工单"
            search_target = None
            
            for candidate in search_targets:
                if candidate in combined_text:
                    search_target = candidate
                    break
            
            if search_target:
                # Find the approximate position by locating where the text starts
                target_start_idx = combined_text.index(search_target)
                
                # Find which box contains the start of our target
                char_count = 0
                for i in range(len(data['text'])):
                    text = data['text'][i].strip()
                    if text:
                        if char_count <= target_start_idx < char_count + len(text):
                            # This box contains the start of our target
                            x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                            
                            # Filter: Only accept matches in the upper portion of sidebar (chat list area)
                            # Sidebar height is full window height, chat list is typically top 70%
                            sidebar_h = gray.shape[0]
                            if y < sidebar_h * 0.7:  # Only matches in top 70% of sidebar
                                print(f"[INFO] ✓ Found '{search_target}' in combined text at box {i}, position ({x}, {y})")
                                return (x, y, w, h)
                            else:
                                print(f"[DEBUG] Found '{search_target}' but position ({x}, {y}) is too low (filtered out)")
                        char_count += len(text)
            
            # Strategy 2: Original exact match (fallback)
            n_boxes = len(data['text'])
            for i in range(n_boxes):
                text = data['text'][i].strip()
                
                # Check if this text contains our target
                if target_text in text:
                    # Get bounding box
                    x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                    conf = data['conf'][i]
                    
                    # Apply same position filter
                    sidebar_h = gray.shape[0]
                    if y < sidebar_h * 0.7:
                        print(f"[INFO] ✓ Found '{target_text}' at ({x}, {y}) size ({w}×{h}) confidence: {conf}")
                        return (x, y, w, h)
                    else:
                        print(f"[DEBUG] Found '{target_text}' but position too low (filtered out)")
            
            # If not found in single words, try combining adjacent text
            # Sometimes OCR splits "IT服务工单" into multiple boxes
            combined_text = ""
            start_idx = None
            for i in range(n_boxes):
                text = data['text'][i].strip()
                if text:
                    combined_text += text
                    if start_idx is None:
                        start_idx = i
                    
                    # Check if combined text contains target
                    if target_text in combined_text:
                        # Return bounding box of the first word in the sequence
                        x, y, w, h = data['left'][start_idx], data['top'][start_idx], data['width'][start_idx], data['height'][start_idx]
                        print(f"[INFO] ✓ Found '{target_text}' (combined) at ({x}, {y})")
                        return (x, y, w, h)
                else:
                    # Reset on empty text (new line)
                    combined_text = ""
                    start_idx = None
            
            print(f"[WARNING] ✗ Text '{target_text}' not found in sidebar")
            return None
            
        except Exception as e:
            print(f"[ERROR] OCR failed: {e}")
            return None

 

    def extract_ids_from_chat(self, full_image):
        if full_image is None: return []
        h, w = full_image.shape[:2]
        crop_x = int(w * 0.4)
        crop_y = int(h * 0.5)
        chat_roi = full_image[crop_y:h, crop_x:w]
        
        # DEBUG: Save scan area
        try:
            cv2.imwrite("debug_scan_area.png", chat_roi)
        except Exception as e:
            print(f"[DEBUG] Failed to save debug image: {e}")

        gray = cv2.cvtColor(chat_roi, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        try:
            # print(f"[DEBUG] Scanning for text...")
            text = pytesseract.image_to_string(thresh, lang='chi_sim+eng')
            # print(f"[DEBUG] OCR Raw Text: {text[:50].replace('\n', ' ')}...") 
        except Exception as e:
            print(f"OCR Error: {e}")
            return []
        
        pattern = re.compile(r"添加了\s*(\d{4,})")
        matches = pattern.findall(text)
        unique = list(set(matches))
        if unique:
             print(f"[DEBUG] OCR Found IDs: {unique}")
        return unique

    def find_chat_with_state(self, image, target_text="IT服务工单"):
        """
        Finds the chat icon and detects its state using template matching.
        Returns: (rect, is_active, has_red_dot)
        - rect: (x, y, w, h) of the icon
        - is_active: True if background is blue (chat is active)
        - has_red_dot: True if red notification dot is present
        """
        # Load icon template
        try:
            icon_template = cv2.imread("icon_template.png")
            if icon_template is None:
                print("[ERROR] Failed to load icon_template.png")
                return None, False, False
        except Exception as e:
            print(f"[ERROR] Failed to load icon template: {e}")
            return None, False, False
        
        # Crop to left sidebar (chat list area)
        h, w = image.shape[:2]
        sidebar_width = int(w * 0.4)
        sidebar = image[:, :sidebar_width]
        
        # Multi-scale template matching for icon
        # Collect ALL candidates above threshold, not just the best one
        all_candidates = []
        scales = [1.0, 0.9, 1.1]  # Fewer scales for speed
        threshold = 0.6
        
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
                
                # Find ALL locations above threshold
                locations = np.where(result >= threshold)
                for pt in zip(*locations[::-1]):  # Switch to (x, y) format
                    score = result[pt[1], pt[0]]
                    # Check if this is not too close to an existing candidate
                    too_close = False
                    for existing in all_candidates:
                        if abs(existing['y'] - pt[1]) < 40:  # Same row (within 40px)
                            if existing['score'] >= score:
                                too_close = True
                                break
                            else:
                                # Replace with higher score
                                all_candidates.remove(existing)
                                break
                    
                    if not too_close:
                        all_candidates.append({
                            'x': pt[0],
                            'y': pt[1],
                            'w': template.shape[1],
                            'h': template.shape[0],
                            'scale': scale,
                            'score': score
                        })
            except Exception as e:
                continue
        
        if not all_candidates:
            print(f"[DEBUG] Icon not found, no candidates above threshold {threshold}")
            return None, False, False
        
        # Sort candidates by Y position (top to bottom)
        all_candidates.sort(key=lambda c: c['y'])
        print(f"[DEBUG] Found {len(all_candidates)} icon candidates")
        
        # Load red dot template once
        try:
            red_dot_template = cv2.imread("debug_red_dot_rois.png")
            if red_dot_template is None:
                print("[WARNING] Red dot template not found")
                red_dot_template = None
        except:
            red_dot_template = None
        
        # Check each candidate for red dot, return the first one with red dot
        for candidate in all_candidates:
            icon_x = candidate['x']
            icon_y = candidate['y']
            icon_w = candidate['w']
            icon_h = candidate['h']
            matched_scale = candidate['scale']
            best_score = candidate['score']
            
            print(f"[INFO] Checking candidate at ({icon_x}, {icon_y}), score {best_score:.3f}")
            
            # Detect background color (blue = active)
            sample_points = []
            for offset_y in [0, icon_h // 4, icon_h // 2, icon_h * 3 // 4]:
                sample_x_left = max(0, icon_x - 5)
                sample_y = min(sidebar.shape[0] - 1, icon_y + offset_y)
                if sample_x_left < sidebar.shape[1]:
                    sample_points.append(sidebar[sample_y, sample_x_left])
                sample_x_right = min(sidebar.shape[1] - 1, icon_x + icon_w + 10)
                if sample_x_right < sidebar.shape[1]:
                    sample_points.append(sidebar[sample_y, sample_x_right])
            
            is_active = False
            if sample_points:
                avg_b = sum([bgr[0] for bgr in sample_points]) / len(sample_points)
                avg_g = sum([bgr[1] for bgr in sample_points]) / len(sample_points)
                avg_r = sum([bgr[2] for bgr in sample_points]) / len(sample_points)
                is_active = (avg_b > 150 and avg_r < 180 and avg_g < 180)
            
            # Search for red dot in this candidate's area
            search_x = max(0, icon_x - 30)
            search_y = max(0, icon_y - 30)
            search_w = min(sidebar.shape[1] - search_x, icon_w + 200)
            search_h = min(sidebar.shape[0] - search_y, icon_h + 60)
            
            if search_w <= 0 or search_h <= 0:
                continue
            
            search_roi = sidebar[search_y:search_y+search_h, search_x:search_x+search_w]
            
            # Detect red dot using template matching
            has_red_dot = False
            if red_dot_template is not None:
                for dot_scale in [1.0, 0.8, 1.2]:
                    if dot_scale != 1.0:
                        scaled_w = int(red_dot_template.shape[1] * dot_scale)
                        scaled_h = int(red_dot_template.shape[0] * dot_scale)
                        if scaled_w <= 0 or scaled_h <= 0:
                            continue
                        dot_template = cv2.resize(red_dot_template, (scaled_w, scaled_h))
                    else:
                        dot_template = red_dot_template
                    
                    if dot_template.shape[0] > search_roi.shape[0] or dot_template.shape[1] > search_roi.shape[1]:
                        continue
                    
                    try:
                        result = cv2.matchTemplate(search_roi, dot_template, cv2.TM_CCOEFF_NORMED)
                        _, max_val, _, _ = cv2.minMaxLoc(result)
                        threshold = 0.35 if not is_active else 0.25  # Higher threshold to avoid false positives
                        if max_val > threshold:
                            has_red_dot = True
                            print(f"[INFO] ✓ Red dot detected at candidate ({icon_x}, {icon_y})! Score: {max_val:.3f}")
                            break
                    except:
                        continue
            
            # Fallback: color-based detection
            if not has_red_dot:
                try:
                    hsv_roi = cv2.cvtColor(search_roi, cv2.COLOR_BGR2HSV)
                    lower_red1 = np.array([0, 100, 100])
                    upper_red1 = np.array([10, 255, 255])
                    lower_red2 = np.array([160, 100, 100])
                    upper_red2 = np.array([180, 255, 255])
                    mask1 = cv2.inRange(hsv_roi, lower_red1, upper_red1)
                    mask2 = cv2.inRange(hsv_roi, lower_red2, upper_red2)
                    red_mask = mask1 | mask2
                    red_pixel_count = cv2.countNonZero(red_mask)
                    # Require higher count to avoid false positives from red UI elements
                    if red_pixel_count > 200:
                        has_red_dot = True
                        print(f"[INFO] ✓ Red dot via color at ({icon_x}, {icon_y})! Count: {red_pixel_count}")
                except:
                    pass
            
            # If found red dot, save debug image and return this candidate
            if has_red_dot:
                cv2.imwrite("debug_red_dot_search_area.png", search_roi)
                print(f"[INFO] ✓ Found icon with red dot at ({icon_x}, {icon_y})")
                return (icon_x, icon_y, icon_w, icon_h), is_active, True
        
        # No red dot found in any candidate, return the first (topmost) candidate
        first = all_candidates[0]
        print(f"[DEBUG] No red dot found, returning first candidate at ({first['x']}, {first['y']})")
        return (first['x'], first['y'], first['w'], first['h']), False, False



    def validate_ticket_format(self, image):
        """
        Validates if the chat content contains a valid ticket format.
        Format: [人名] 添加了 [数字ID] [任务名]
        """
        # Scan the right side of the window (chat content area)
        h, w = image.shape[:2]
        chat_x = int(w * 0.4)
        chat_roi = image[:, chat_x:]
        
        # Convert to grayscale
        gray = cv2.cvtColor(chat_roi, cv2.COLOR_BGR2GRAY)
        
        try:
            # OCR the chat content
            text = pytesseract.image_to_string(gray, lang='chi_sim+eng')
            print(f"[DEBUG] Chat content OCR (first 200 chars): {text[:200]}")
            
            # Regex pattern: [人名] 添加了 [数字ID]
            # Example: "余凌晖 添加了 15729 履约密码重制"
            # Handle OCR variations with flexible spacing
            pattern = re.compile(r"(\S+)\s*添加了\s*(\d{4,})")
            match = pattern.search(text)
            
            if match:
                person_name = match.group(1)
                ticket_id = match.group(2)
                print(f"[INFO] ✓ 检测到新工单: {person_name} 添加了 {ticket_id}")
                return True, ticket_id, person_name
            
            # Fallback 1: Try with more flexible pattern (handle newlines/spaces as \s+)
            pattern1b = re.compile(r"([\u4e00-\u9fa5]+)\s*添加了\s*(\d{4,})")
            match1b = pattern1b.search(text)
            if match1b:
                person_name = match1b.group(1)
                ticket_id = match1b.group(2)
                print(f"[INFO] ✓ 检测到新工单(备用): {person_name} 添加了 {ticket_id}")
                return True, ticket_id, person_name
            
            # Fallback 2: 超时提醒消息 [ID] ... 的处理
            pattern2 = re.compile(r"(\d{4,})\s+\S+.*?的处理")
            match2 = pattern2.search(text)
            if match2:
                ticket_id = match2.group(1)
                print(f"[INFO] ✓ 检测到工单提醒: ID={ticket_id}")
                return True, ticket_id, "系统提醒"
            
            # Pattern 3: 超时格式 "工单 [ID] ... 已超过"
            pattern3 = re.compile(r"工单\s+(\d{4,}).*?已超过")
            match3 = pattern3.search(text)
            if match3:
                ticket_id = match3.group(1)
                print(f"[INFO] ✓ 检测到超时工单: ID={ticket_id}")
                return True, ticket_id, "超时提醒"
            
            print(f"[DEBUG] 未找到有效工单格式")
            return False, None, None
                
        except Exception as e:
            print(f"[ERROR] OCR failed in validate_ticket_format: {e}")
            return False, None, None

    def find_blue_button(self, image, button_text="查看详情"):
        """
        Finds the button using template matching.
        Returns: (x, y, w, h) of the button, or None if not found.
        """
        # Load button template
        try:
            button_template = cv2.imread("button_template.png")
            if button_template is None:
                print("[ERROR] Failed to load button_template.png")
                return None
        except Exception as e:
            print(f"[ERROR] Failed to load button template: {e}")
            return None
        
        # Scan the right side of the window (chat content area)
        h, w = image.shape[:2]
        chat_x = int(w * 0.4)
        chat_roi = image[:, chat_x:]
        
        print(f"[DEBUG] Searching for button using template matching...")
        
        # Multi-scale template matching
        best_match = None
        best_score = 0
        scales = [1.0, 0.9, 1.1, 0.8, 1.2]
        
        for scale in scales:
            if scale != 1.0:
                scaled_w = int(button_template.shape[1] * scale)
                scaled_h = int(button_template.shape[0] * scale)
                if scaled_w <= 0 or scaled_h <= 0:
                    continue
                template = cv2.resize(button_template, (scaled_w, scaled_h))
            else:
                template = button_template
            
            if template.shape[0] > chat_roi.shape[0] or template.shape[1] > chat_roi.shape[1]:
                continue
            
            try:
                result = cv2.matchTemplate(chat_roi, template, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                
                if max_val > best_score:
                    best_score = max_val
                    best_match = (max_loc[0], max_loc[1], template.shape[1], template.shape[0], scale)
            except Exception as e:
                continue
        
        if best_score < 0.25:  # Further lowered threshold
            print(f"[DEBUG] Button not found, best score: {best_score:.3f}")
            return None
        
        btn_x, btn_y, btn_w, btn_h, matched_scale = best_match
        # Adjust coordinates to full image (add chat_x offset)
        full_x = chat_x + btn_x
        print(f"[INFO] ✓ Found button at ({full_x}, {btn_y}), size ({btn_w}×{btn_h}), scale {matched_scale:.2f}, score {best_score:.3f}")
        
        return (full_x, btn_y, btn_w, btn_h)
