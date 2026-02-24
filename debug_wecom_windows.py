
import Quartz
import Quartz.CoreGraphics as CG

def list_wecom_windows():
    # Use OptionAll to see everything
    options = CG.kCGWindowListOptionAll | CG.kCGWindowListExcludeDesktopElements
    window_list = CG.CGWindowListCopyWindowInfo(options, CG.kCGNullWindowID)
    
    print(f"Searching for '企业微信' in {len(window_list)} windows...")
    
    count = 0
    for window in window_list:
        owner = window.get('kCGWindowOwnerName', '')
        if "企业微信" in owner:
            count += 1
            wid = window.get('kCGWindowNumber', 'N/A')
            name = window.get('kCGWindowName', '')
            bounds = window.get('kCGWindowBounds', {})
            layer = window.get('kCGWindowLayer', 'N/A')
            alpha = window.get('kCGWindowAlpha', 'N/A')
            isOnScreen = window.get('kCGWindowIsOnscreen', 'N/A') # boolean
            
            print(f"ID: {wid} | Name: '{name}' | Layer: {layer} | Bounds: {bounds} | OnScreen: {isOnScreen} | Alpha: {alpha}")

    if count == 0:
        print("No WeCom windows found.")

if __name__ == "__main__":
    list_wecom_windows()
