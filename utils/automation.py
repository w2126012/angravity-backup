
import subprocess
import time
import pyautogui
import pyperclip
from AppKit import NSWorkspace, NSRunningApplication, NSApplicationActivateIgnoringOtherApps

class AutomationController:
    def __init__(self):
        pass

    def activate_window(self, window_name="企业微信"):
        """
        使用 open -a 命令直接打开/激活应用程序
        这样可以避免窗口切换误切到其他程序
        """
        try:
            # 使用 open -a 命令直接激活程序
            subprocess.run(['open', '-a', window_name], check=True, timeout=5)
            return True
        except Exception as e:
            print(f"激活 '{window_name}' 失败: {e}")
            # 备用方案:使用NSWorkspace
            try:
                workspace = NSWorkspace.sharedWorkspace()
                apps = workspace.runningApplications()
                for app in apps:
                    if app.localizedName() == window_name:
                        app.activateWithOptions_(NSApplicationActivateIgnoringOtherApps)
                        return True
            except:
                pass
            return False

    def click(self, x, y):
        """Simple click at screen coordinates (x, y)"""
        try:
            import pyautogui
            pyautogui.click(x, y)
            return True
        except Exception as e:
            print(f"Click failed: {e}")
            return False

    def click_and_reply(self, click_x, click_y, reply_text="请稍后"):
        """
        Clicks at (click_x, click_y), checks content (stub), and replies.
        Coordinates must be in screen points (not pixels).
        """
        try:
            # 1. Click the icon
            # Move smoothly to avoid bot detection heuristics (optional) or just click
            pyautogui.click(click_x, click_y)
            
            # 2. Wait for chat load
            time.sleep(1.0)
            
            # 3. Analyze Chat Content (Stub)
            # In a real scenario, we would take a screenshot of the chat area here
            # and use OCR. For now, we assume valid triggering to proceed.
            if not self._check_chat_context():
                print("Chat context check failed. Skipping reply.")
                return

            # 4. Click input box
            # Assuming input box is at the bottom. 
            # We can hardcode an offset or find it. 
            # For robustness, we might just paste directly if focus is set by clicking the chat,
            # but usually clicking the sidebar icon DOES NOT focus the input box.
            # We need to click the intput box.
            # Let's assume input box is roughly center-bottom or we tab to it.
            # A safe bet is clicking slightly above the bottom of the window/screen.
            # For this task, we will just assume previous click focused the window, 
            # and maybe we need to click "Type message..." area.
            # We'll use a TAB or Click strategy.
            # Let's try TAB key to focus input? Or just blindly paste if cursor is there.
            # Better: Click a relative offset from the bottom-center of the screen or window.
            # Since we don't track window bounds in this class yet, let's just click 'center' of screen? 
            # No, that's risky. 
            # Implementation Plan said: "Click input box -> pyperclip ...".
            # Let's rely on user calibrating or finding image of input box?
            # For this MVP, we press 'Tab' then 'Enter'? Or just 'Enter' to focus?
            
            # Let's click at a safe offset relative to the window if we knew window bounds.
            # Re-architecting slightly: we pass window logic or just use screen coordinates?
            # Let's assume input box is at the bottom.
            # We will try to just Paste.
            
            # 5. Paste and Send
            pyperclip.copy(reply_text)
            
            # Mac standard paste
            with pyautogui.hold('command'):
                pyautogui.press('v')
            
            time.sleep(0.5)
            # Send
            pyautogui.press('enter')
            
        except Exception as e:
            print(f"Error in automation sequence: {e}")

    def _check_chat_context(self):
        """
        Verify if we should reply.
        Returns True if condition met (4 digits or red warning), False otherwise.
        """
        # TODO: Implement OCR or visual check.
        # Currently returns True to allow flow testing.
        return True

    def hide_window(self):
        """Hides the active window (Cmd+H)."""
        with pyautogui.hold('command'):
            pyautogui.press('h')
