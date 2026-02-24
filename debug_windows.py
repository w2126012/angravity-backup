
import Quartz
import Quartz.CoreGraphics as CG

def list_windows():
    options = CG.kCGWindowListOptionAll | CG.kCGWindowListExcludeDesktopElements
    window_list = CG.CGWindowListCopyWindowInfo(options, CG.kCGNullWindowID)
    
    print(f"Found {len(window_list)} windows:")
    for i, window in enumerate(window_list):
        owner = window.get('kCGWindowOwnerName', 'N/A')
        name = window.get('kCGWindowName', 'N/A')
        wid = window.get('kCGWindowNumber', 'N/A')
        print(f"[{i}] ID: {wid} | Owner: '{owner}' | Name: '{name}'")

if __name__ == "__main__":
    list_windows()
