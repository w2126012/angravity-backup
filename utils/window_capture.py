
import Quartz
import Quartz.CoreGraphics as CG
import numpy as np
import cv2
from AppKit import NSScreen

class WindowCapture:
    def __init__(self, window_name="企业微信"):
        self.window_name = window_name
        self.window_id = None
        self.scale_factor = self._get_screen_scale_factor()

    def _get_screen_scale_factor(self):
        """Get the Retina scale factor (usually 2.0 on Retina, 1.0 otherwise)."""
        # Since we might focus on the main screen for simplicity or iterate screens.
        # For this specific task, capturing the window via Quartz gives full resolution (Retina) pixels.
        # But for coordinates mapping later, we need to know the scale.
        try:
            return NSScreen.mainScreen().backingScaleFactor()
        except:
            return 2.0 # Default fallback to safe retina assumption if fails

    def find_window(self):
        """Finds the window ID for the given window name."""
        # Use OptionAll to ensure we see the window even if occluded or backgrounded
        options = CG.kCGWindowListOptionAll | CG.kCGWindowListExcludeDesktopElements
        window_list = CG.CGWindowListCopyWindowInfo(options, CG.kCGNullWindowID)
        
        candidates = []
        for window in window_list:
            owner_name = window.get('kCGWindowOwnerName', '')
            name = window.get('kCGWindowName', '')
            
            if self.window_name in owner_name:
                 wid = window['kCGWindowNumber']
                 bounds = window.get('kCGWindowBounds', {})
                 width = bounds.get('Width', 0)
                 height = bounds.get('Height', 0)
                 area = width * height
                 
                 candidates.append({
                     'id': wid,
                     'owner': owner_name,
                     'name': name,
                     'bounds': bounds,
                     'area': area
                 })
        
        if not candidates:
            print(f"Window '{self.window_name}' not found.")
            self.window_id = None
            self.window_bounds = None
            return None

        # Sort candidates:
        # 1. Exact Name Match (Bonus) - though often empty
        # 2. Area (Descending) - Main window is usually the largest
        candidates.sort(key=lambda x: (x['name'] == self.window_name, x['area']), reverse=True)
        
        best = candidates[0]
        self.window_id = best['id']
        self.window_bounds = best['bounds']
        print(f"Found window: {best['owner']} - '{best['name']}' ID: {best['id']} Bounds: {best['bounds']}")
        return self.window_id

    def capture(self):
        """Captures the screenshot of the specific window even if backgrounded."""
        if not self.window_id:
            if not self.find_window():
                return None

        # FIXED: Use full screen capture + crop instead of single window capture
        # kCGWindowListOptionIncludingWindow doesn't work reliably on macOS
        # Capture entire screen
        image_ref = CG.CGWindowListCreateImage(
            CG.CGRectNull,
            CG.kCGWindowListOptionOnScreenOnly,
            CG.kCGNullWindowID,
            CG.kCGWindowImageDefault
        )
        
        if not image_ref:
            print("Failed to create full screen image ref.")
            return None

        # Calculate dimensions
        width = CG.CGImageGetWidth(image_ref)
        height = CG.CGImageGetHeight(image_ref)
        
        # Get data provider
        prov = CG.CGImageGetDataProvider(image_ref)
        data = CG.CGDataProviderCopyData(prov)
        
        try:
            img_array = np.frombuffer(data, dtype=np.uint8)
            
            # Reshape: height, width, 4 channels (RGBA/BGRA)
            if len(img_array) != width * height * 4:
                bytes_per_row = CG.CGImageGetBytesPerRow(image_ref)
                if bytes_per_row != width * 4:
                     img_array = img_array.reshape((height, bytes_per_row))
                     img_array = img_array[:, :width*4]
                     img_array = img_array.reshape((height, width, 4))
                else:
                    img_array = img_array.reshape((height, width, 4))
            else:
                 img_array = img_array.reshape((height, width, 4))

            # macOS Quartz returns BGRA format
            # Extract BGR channels
            img_bgr = img_array[:, :, :3]  # Take first 3 channels (BGR), drop alpha
            
            # Crop to window bounds
            # Window bounds are in logical coordinates, need to scale for Retina
            win_x = int(self.window_bounds.get('X', 0) * self.scale_factor)
            win_y = int(self.window_bounds.get('Y', 0) * self.scale_factor)
            win_w = int(self.window_bounds.get('Width', 0) * self.scale_factor)
            win_h = int(self.window_bounds.get('Height', 0) * self.scale_factor)
            
            # Ensure coordinates are within image bounds
            win_x = max(0, min(win_x, width))
            win_y = max(0, min(win_y, height))
            win_w = max(0, min(win_w, width - win_x))
            win_h = max(0, min(win_h, height - win_y))
            
            if win_w == 0 or win_h == 0:
                print(f"Invalid window bounds: x={win_x}, y={win_y}, w={win_w}, h={win_h}")
                return None
            
            # Crop window region
            cropped = img_bgr[win_y:win_y+win_h, win_x:win_x+win_w]
            
            return cropped

        except Exception as e:
            print(f"Error processing captured image: {e}")
            return None
