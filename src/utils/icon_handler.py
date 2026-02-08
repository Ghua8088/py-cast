import os
import platform
import ctypes
import base64
import hashlib
from io import BytesIO
from ctypes import wintypes
from PIL import Image


def hicon_to_image(hIcon):
    """Helper to convert HICON to PIL image."""
    user32 = ctypes.windll.user32
    gdi32 = ctypes.windll.gdi32

    hdc_screen = user32.GetDC(0)
    hdc_mem = gdi32.CreateCompatibleDC(hdc_screen)
    cx = user32.GetSystemMetrics(11)  # SM_CXICON
    cy = user32.GetSystemMetrics(12)  # SM_CYICON

    class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [
            ("biSize", wintypes.DWORD),
            ("biWidth", wintypes.LONG),
            ("biHeight", wintypes.LONG),
            ("biPlanes", wintypes.WORD),
            ("biBitCount", wintypes.WORD),
            ("biCompression", wintypes.DWORD),
            ("biSizeImage", wintypes.DWORD),
            ("biXPelsPerMeter", wintypes.LONG),
            ("biYPelsPerMeter", wintypes.LONG),
            ("biClrUsed", wintypes.DWORD),
            ("biClrImportant", wintypes.DWORD),
        ]

    class BITMAPINFO(ctypes.Structure):
        _fields_ = [("bmiHeader", BITMAPINFOHEADER), ("bmiColors", wintypes.DWORD * 3)]

    bmi = BITMAPINFO()
    bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.bmiHeader.biWidth = cx
    bmi.bmiHeader.biHeight = -cy
    bmi.bmiHeader.biPlanes = 1
    bmi.bmiHeader.biBitCount = 32
    bmi.bmiHeader.biCompression = 0

    pixel_data = ctypes.c_void_p()
    hbmp = gdi32.CreateDIBSection(
        hdc_mem, ctypes.byref(bmi), 0, ctypes.byref(pixel_data), None, 0
    )
    old_bmp = gdi32.SelectObject(hdc_mem, hbmp)

    user32.DrawIconEx(hdc_mem, 0, 0, hIcon, cx, cy, 0, None, 0x0003)  # DI_NORMAL

    bits = ctypes.string_at(pixel_data, cx * cy * 4)
    img = Image.frombuffer("RGBA", (cx, cy), bits, "raw", "BGRA", 0, 1)

    # Cleanup
    gdi32.SelectObject(hdc_mem, old_bmp)
    gdi32.DeleteObject(hbmp)
    gdi32.DeleteDC(hdc_mem)
    user32.ReleaseDC(0, hdc_screen)

    return img


def extract_icon_to_png_bytes(path):
    """Extracts a high-quality icon using strictly ctypes to avoid handle conflicts."""
    try:
        if platform.system() != "Windows":
            return None
        if not os.path.exists(path):
            return None

        shell32 = ctypes.windll.shell32
        user32 = ctypes.windll.user32

        class SHFILEINFO(ctypes.Structure):
            _fields_ = [
                ("hIcon", wintypes.HICON),
                ("iIcon", ctypes.c_int),
                ("dwAttributes", wintypes.DWORD),
                ("szDisplayName", wintypes.WCHAR * 260),
                ("szTypeName", wintypes.WCHAR * 80),
            ]

        shfi = SHFILEINFO()
        # 0x100 is SHGFI_ICON, 0x0 is SHGFI_LARGEICON
        res = shell32.SHGetFileInfoW(
            str(path), 0, ctypes.byref(shfi), ctypes.sizeof(shfi), 0x100 | 0x00
        )

        if not res or not shfi.hIcon:
            return None
        hIcon = shfi.hIcon

        img = hicon_to_image(hIcon)
        user32.DestroyIcon(hIcon)

        # Check for empty/transparent results
        extrema = img.getextrema()
        if not extrema or (len(extrema) >= 4 and extrema[3][1] == 0):
            # Fallback: Try ExtractIconEx if SHGetFileInfo fails
            try:
                hIcon_ptr = (wintypes.HICON * 1)()
                shell32.ExtractIconExW(str(path), 0, hIcon_ptr, None, 1)
                if hIcon_ptr[0]:
                    img = hicon_to_image(hIcon_ptr[0])
                    user32.DestroyIcon(hIcon_ptr[0])
            except:
                return None

        buffer = BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()
    except Exception as e:
        print(f"Icon Extract Error: {e}")
        return None


def get_icon_url(app_instance, path, force=False):
    """Resolves a file path to an icon. Returns a Base64 data URI or pytron:// URL."""
    if not path:
        return None
    path_str = str(path)
    path_lower = path_str.lower()
    key = hashlib.md5(path_str.lower().encode()).hexdigest() + ".png"

    if key in app_instance.resolved_icons:
        return app_instance.resolved_icons[key]

    if not force:
        return None

    # 1. Windows Native Extraction
    if platform.system() == "Windows" and path_lower.endswith((".lnk", ".exe")):
        try:
            png_bytes = extract_icon_to_png_bytes(path_str)
            if png_bytes:
                b64 = base64.b64encode(png_bytes).decode("utf-8")
                url = f"data:image/png;base64,{b64}"
                app_instance.resolved_icons[key] = url
                return url
        except:
            pass

    # 2. macOS/Linux Generic Image Handling
    if path_lower.endswith(
        (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico", ".icns")
    ):
        try:
            # For basic files, serving via pytron is faster
            url = app_instance.app.serve_file(path_str)
            app_instance.resolved_icons[key] = url
            return url
        except:
            pass

    # 3. Linux Icon Resolution (Search system paths)
    if platform.system() == "Linux" and not path_str.startswith("/"):
        # If path is just an icon name (from .desktop file)
        for base in ["/usr/share/icons/hicolor/48x48/apps", "/usr/share/pixmaps"]:
            test_path = os.path.join(base, path_str + ".png")
            if os.path.exists(test_path):
                url = app_instance.app.serve_file(test_path)
                app_instance.resolved_icons[key] = url
                return url

    return None
