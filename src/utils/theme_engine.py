import os
import platform
import colorsys
from PIL import Image

def get_wallpaper_path():
    try:
        if platform.system() == "Windows":
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop")
            path, _ = winreg.QueryValueEx(key, "Wallpaper")
            return path
        elif platform.system() == "Darwin":
            # macOS - AppleScript approach via subprocess
            import subprocess
            cmd = 'tell application "finder" to get posix path of (get desktop picture as alias)'
            path = subprocess.check_output(['osascript', '-e', cmd]).decode('utf-8').strip()
            return path
    except:
        pass
    return None

def get_adaptive_color(image_path):
    if not image_path or not os.path.exists(image_path):
        return None
    
    try:
        with Image.open(image_path) as img:
            img.thumbnail((100, 100))
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Simple dominant color: center crop or average
            # Let's do a weighted average of the middle of the screen
            width, height = img.size
            box = (width // 4, height // 4, 3 * width // 4, 3 * height // 4)
            center_crop = img.crop(box)
            pixels = list(center_crop.getdata())
            
            r_avg = sum(p[0] for p in pixels) / len(pixels)
            g_avg = sum(p[1] for p in pixels) / len(pixels)
            b_avg = sum(p[2] for p in pixels) / len(pixels)
            
            # Convert to HSV to check vibrancy
            h, s, v = colorsys.rgb_to_hsv(r_avg/255, g_avg/255, b_avg/255)
            
            # ELEGANT SOLUTION: If the wallpaper is too dark or too grayscale, 
            # don't try to force a muddy color from it. Fallback to a brand default.
            if v < 0.15 or s < 0.1:
                return "#818cf8" # Signature Bite Indigo
            
            # Normalize for UI ACCENT: 
            # We want these colors to POP against the dark glass background.
            s = max(0.55, min(s, 0.9)) # Ensure it's not washed out
            v = max(0.85, 1.0)        # Force high brightness for legibility
            
            r, g, b = colorsys.hsv_to_rgb(h, s, v)
            return "#{:02x}{:02x}{:02x}".format(int(r*255), int(g*255), int(b*255))
    except:
        return None
