import os
import sys
import subprocess
import threading
import time
import json
import psutil
import pyperclip
import ctypes
import base64
import platform
from pathlib import Path
from pytron import App
import re
from typing import List, Dict, Any
from urllib.parse import urlparse
from io import BytesIO

# --- Native Icon Extraction Engine (Windows Only) ---
try:
    if platform.system() == "Windows":
        import win32api
        import win32gui
        import win32ui
        import win32con
        from PIL import Image

    def get_icon_base64(path):
        """Extracts the exact system icon for a file using Windows Shell API."""
        if platform.system() != "Windows": return None
        try:
            # SHGFI_ICON (0x100) | SHGFI_LARGEICON (0x0) | SHGFI_USEFILEATTRIBUTES (0x10) if needed
            flags = win32con.SHGFI_ICON | win32con.SHGFI_LARGEICON 
            
            # This returns (hIcon, iIcon, dwAttr, displayName, typeName)
            folder_info = win32gui.SHGetFileInfo(path, 0, flags)
            hIcon = folder_info[0]
            
            if not hIcon: return None

            # Create Device Context and bitmap to copy the icon
            hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
            hbmp = win32ui.CreateBitmap()
            
            # Standard large icon size
            cx = win32api.GetSystemMetrics(win32con.SM_CXICON)
            cy = win32api.GetSystemMetrics(win32con.SM_CYICON)
            
            hbmp.CreateCompatibleBitmap(hdc, cx, cy)
            mem_dc = hdc.CreateCompatibleDC()
            mem_dc.SelectObject(hbmp)
            
            # Fill with transparent color key 
            mem_dc.DrawIcon((0, 0), hIcon)
            
            # Convert to PIL
            bmpinfo = hbmp.GetInfo()
            bmpstr = hbmp.GetBitmapBits(True)
            img = Image.frombuffer(
                'RGB',
                (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                bmpstr, 'raw', 'BGRX', 0, 1
            )
            
            # Cleanup GDI objects
            win32gui.DestroyIcon(hIcon)
            mem_dc.DeleteDC()
            win32gui.DeleteObject(hbmp.GetHandle())

            # Save as PNG base64
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            b64 = base64.b64encode(buffer.getvalue()).decode()
            return f"data:image/png;base64,{b64}"

        except Exception as e:
            pass
        return None

except ImportError:
    # print("PyWin32 not installed properly.")
    def get_icon_base64(path): return None


class Bite:
    def __init__(self, app: App):
        self.app = app
        self.clipboard_history = []
        self._last_clipboard = ""
        self.platform = platform.system()
        
        # User Config
        config_home = Path(os.environ.get('APPDATA')) if self.platform == "Windows" else Path.home() / ".config"
        self.config_dir = config_home / 'Bite'
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_path = self.config_dir / 'config.json'
        self.user_data = self._load_config()
        
        # Core Registry
        self.base_registry = self._get_base_registry()
        self.installed_apps = self._scan_applications()
        
        
        threading.Thread(target=self._clipboard_monitor, daemon=True).start()
        threading.Thread(target=self._system_monitor, daemon=True).start()

    def _get_base_registry(self):
        reg = [
            {"id": "google", "name": "Search Google", "type": "search", "url": "https://google.com/search?q=", "cat": "Web", "icon": "\U0001F310"},
            {"id": "yt", "name": "Search YouTube", "type": "search", "url": "https://www.youtube.com/results?search_query=", "cat": "Web", "icon": "\U0001F4FA"},
            {"id": "gh", "name": "Search GitHub", "type": "search", "url": "https://github.com/search?q=", "cat": "Web", "icon": "\U0001F419"},
            
            {"id": "clean", "name": "Kill All Python", "action": "kill_py", "desc": "Task Cleanup", "cat": "System", "icon": "\u26A0"},
            {"id": "settings", "name": "Settings", "action": "settings", "desc": "Manage Shortcuts", "cat": "System", "icon": "\u2699"},
            {"id": "help", "name": "How to use Bite?", "action": "help", "desc": "Tips & Tricks", "cat": "Help", "icon": "\u2753"},
            
            # AI Chat Shortcuts
            {"id": "chatgpt", "name": "Open ChatGPT", "type": "search", "url": "https://chat.openai.com/?q=", "desc": "OpenAI Chat", "cat": "AI", "icon": "\U0001F916"},
            {"id": "claude", "name": "Open Claude", "type": "search", "url": "https://claude.ai/new?q=", "desc": "Anthropic Chat", "cat": "AI", "icon": "\U0001F9E0"},
            {"id": "gemini", "name": "Open Gemini", "type": "search", "url": "https://gemini.google.com/app?q=", "desc": "Google AI", "cat": "AI", "icon": "\u2728"},
            {"id": "grok", "name": "Open Grok", "type": "search", "url": "https://twitter.com/i/grok?q=", "desc": "xAI Chat", "cat": "AI", "icon": "\U0001F680"},
            {"id": "perplexity", "name": "Open Perplexity", "type": "search", "url": "https://www.perplexity.ai/search?q=", "desc": "AI Search Engine", "cat": "AI", "icon": "\U0001F50D"},
        ]
        
        # Platform Specific Defaults
        if self.platform == "Windows":
             reg.extend([
                {"id": "calc", "name": "Calculator", "path": "calc.exe", "desc": "Standard Calc", "cat": "Apps", "icon": "\U0001F9EE"},
                {"id": "note", "name": "Notepad", "path": "notepad.exe", "desc": "Quick Notes", "cat": "Apps", "icon": "\U0001F4DD"},
                {"id": "term", "name": "Terminal", "path": "powershell.exe", "desc": "PowerShell", "cat": "Apps", "icon": "\U0001F4BB"},
                {"id": "lock", "name": "Lock Screen", "action": "lock", "desc": "Secure PC", "cat": "System", "icon": "\U0001F512"},
                {"id": "sleep", "name": "Sleep", "action": "sleep", "desc": "Energy Saving", "cat": "System", "icon": "\U0001F319"},
             ])
        elif self.platform == "Darwin": # macOS
             reg.extend([
                {"id": "calc", "name": "Calculator", "path": "/System/Applications/Calculator.app", "desc": "Calculator", "cat": "Apps", "icon": "\U0001F9EE"},
                {"id": "term", "name": "Terminal", "path": "/System/Applications/Utilities/Terminal.app", "desc": "Terminal", "cat": "Apps", "icon": "\U0001F4BB"},
                {"id": "lock", "name": "Lock Screen", "action": "lock", "desc": "Secure Mac", "cat": "System", "icon": "\U0001F512"},
             ])
        elif self.platform == "Linux":
             reg.extend([
                {"id": "term", "name": "Terminal", "path": "gnome-terminal", "desc": "Terminal", "cat": "Apps", "icon": "\U0001F4BB"},
             ])
             
        return reg

    def _load_config(self):
        defaults = {"pins": [], "shortcuts": []}
        if self.config_path.exists():
            try: 
                data = json.loads(self.config_path.read_text())
                for k, v in defaults.items():
                    if k not in data: data[k] = v
                return data
            except: pass
        return defaults

    def _save_config(self):
        self.config_path.write_text(json.dumps(self.user_data))

    def add_shortcut(self, keyword, name, url):
        self.user_data["shortcuts"] = [s for s in self.user_data["shortcuts"] if s["id"] != keyword]
        if not url.startswith("http"): url = "https://" + url
        self.user_data["shortcuts"].append({
            "id": keyword, "name": name, "type": "search", "url": url,
            "cat": "Custom", "icon": "\U0001F517", "desc": f"Search with '{keyword}'"
        })
        self._save_config()
        return self.user_data["shortcuts"]

    def remove_shortcut(self, keyword):
        self.user_data["shortcuts"] = [s for s in self.user_data["shortcuts"] if s["id"] != keyword]
        self._save_config()
        return self.user_data["shortcuts"]

    def get_user_shortcuts(self):
        return self.user_data.get("shortcuts", [])

    def _scan_applications(self):
        apps = []
        try:
            if self.platform == "Windows":
                # Windows Scanning (.lnk)
                base_paths = [
                    os.path.join(os.environ["ProgramData"], r"Microsoft\Windows\Start Menu\Programs"),
                    os.path.join(os.environ["APPDATA"], r"Microsoft\Windows\Start Menu\Programs")
                ]
                for base in base_paths:
                    if not os.path.exists(base): continue
                    for root, dirs, files in os.walk(base):
                        for file in files:
                            if file.lower().endswith(".lnk"):
                                try:
                                    full_path = os.path.join(root, file)
                                    name = os.path.splitext(file)[0]
                                    icon_b64 = get_icon_base64(full_path)
                                    icon = icon_b64 if icon_b64 else "\U0001F4F1"
                                    apps.append({
                                        "id": f"app_{full_path}", "name": name, "path": full_path,
                                        "desc": "Application", "cat": "Apps", "icon": icon,
                                        "type": "lnk", "is_img": bool(icon_b64)
                                    })
                                except: pass
                                
            elif self.platform == "Darwin": # macOS
                # Scan /Applications and ~/Applications
                search_paths = ["/Applications", os.path.expanduser("~/Applications")]
                for base in search_paths:
                    if not os.path.exists(base): continue
                    for entry in os.scandir(base):
                        if entry.name.endswith(".app"):
                            name = entry.name.replace(".app", "")
                            apps.append({
                                "id": f"app_{entry.path}", "name": name, "path": entry.path,
                                "desc": "Application", "cat": "Apps", "icon": "\U0001F4F1",
                                "type": "app", "is_img": False
                            })

            elif self.platform == "Linux":
                # Scan /usr/share/applications and ~/.local/share/applications
                search_paths = ["/usr/share/applications", os.path.expanduser("~/.local/share/applications")]
                for base in search_paths:
                    if not os.path.exists(base): continue
                    for entry in os.scandir(base):
                        if entry.name.endswith(".desktop"):
                            try:
                                # Parsing .desktop files is safer with a library, but simple fallback:
                                with open(entry.path, 'r', errors='ignore') as f:
                                    content = f.read()
                                    if "NoDisplay=true" in content: continue
                                    name_match = re.search(r"^Name=(.*)", content, re.MULTILINE)
                                    name = name_match.group(1) if name_match else entry.name
                                    apps.append({
                                        "id": f"app_{entry.path}", "name": name, "path": entry.path,
                                        "desc": "Application", "cat": "Apps", "icon": "\U0001F4F1",
                                        "type": "desktop", "is_img": False
                                    })
                            except: pass

        except Exception as e:
            print(f"Scan Error: {e}")
        return apps

    def _clipboard_monitor(self):
        while True:
            try:
                curr = pyperclip.paste()
                if curr and curr != self._last_clipboard:
                    self._last_clipboard = curr
                    self.clipboard_history.insert(0, {"content": curr, "time": time.strftime("%H:%M:%S")})
                    self.clipboard_history = self.clipboard_history[:20]
                    self.app.state.clipboard = self.clipboard_history
            except: pass
            time.sleep(1)

    def _system_monitor(self):
        while True:
            try:
                self.app.state.sys_info = {"cpu": psutil.cpu_percent(), "mem": psutil.virtual_memory().percent}
            except: pass
            time.sleep(2.5)

    def _get_drives(self):
        drives = []
        if self.platform == "Windows":
            try:
                for part in psutil.disk_partitions():
                    if 'fixed' in part.opts or 'rw' in part.opts:
                        drives.append(part.mountpoint)
            except: pass
            if not drives: drives = ["C:\\"]
        else:
            drives = ["/"]
        return drives

    def _create_file_result(self, entry, extra_desc=""):
        return {
            "id": f"file_{entry.path}",
            "name": entry.name,
            "path": entry.path,
            "desc": f"{extra_desc} {entry.path}",
            "cat": "Files",
            "icon": "\U0001F4C1" if entry.is_dir() else "\U0001F4C4",
            "type": "file"
        }

    def _search_files(self, query: str) -> List[Dict]:
        results = []
        query_orig = query
        query_lower = query.lower()
        
        # Mode 1: Regex
        is_regex = False
        regex_pattern = None
        if query_lower.startswith("re:"):
             is_regex = True
             try: regex_pattern = re.compile(query_orig[3:].strip(), re.IGNORECASE)
             except: return []

        # Mode 2: Path Navigation
        # Windows X:\ or Linux /
        is_path_query = (len(query) >= 2 and query[1] == ':') or query.startswith('/') or query.startswith('\\')
        
        if is_path_query:
             target_dir = query
             partial = ""
             if not os.path.exists(target_dir):
                 target_dir = os.path.dirname(query)
                 partial = os.path.basename(query)
             
             if os.path.isdir(target_dir):
                 try:
                     count = 0
                     with os.scandir(target_dir) as entries:
                         for entry in entries:
                             if count > 50: break
                             name = entry.name
                             if partial and partial.lower() not in name.lower(): continue
                             results.append(self._create_file_result(entry, "(Browse)"))
                             count += 1
                 except: pass
                 return results

        # Mode 3: Broad Search
        if len(query) < 2: return []
        
        search_dirs = [
             Path.home() / "Desktop", Path.home() / "Downloads", Path.home() / "Documents"
        ]
        # Add Drives
        for d in self._get_drives():
            search_dirs.append(Path(d))

        count = 0
        seen_paths = set()
        
        for sdir in search_dirs:
            if not os.path.exists(sdir): continue
            try:
                 with os.scandir(sdir) as entries:
                     for entry in entries:
                         if count >= 30: break
                         if entry.path in seen_paths: continue
                         
                         match = False
                         if is_regex and regex_pattern:
                             if regex_pattern.search(entry.name): match = True
                         elif query_lower in entry.name.lower():
                             match = True
                             
                         if match:
                             results.append(self._create_file_result(entry, "Found"))
                             seen_paths.add(entry.path)
                             count += 1
            except: continue
            
        return results

    def toggle_pin(self, item_id: str):
        if not item_id: return False
        if item_id in self.user_data["pins"]:
            self.user_data["pins"].remove(item_id)
        else:
            self.user_data["pins"].append(item_id)
        self._save_config()
        return True

    def get_results(self, query: str) -> List[Dict]:
        query = query.lower().strip()
        results = []
        pinned_ids = self.user_data.get("pins", [])
        
        # 0. Registry
        registry_matches = []
        full_registry = self.base_registry + self.user_data.get("shortcuts", [])
        
        for item in full_registry:
            it = item.copy()
            it["pinned"] = it["id"] in pinned_ids
            q, kid = query, it["id"].lower()
            
            is_match = False
            is_match = False
            # Show defaults if query is empty
            if not q: is_match = True
            elif q == kid: is_match = True
            elif q == kid: is_match = True
            elif q.startswith(kid + " "): is_match = True
            elif q in it["name"].lower(): is_match = True
            elif q in it.get("desc", "").lower(): is_match = True
            
            # Hate Calculator Override
            if q.startswith("ai") and it["id"] == "calc": is_match = False
            
            if is_match: registry_matches.append(it)

        # 1. Apps
        app_matches = []
        for app in self.installed_apps:
            if not query or query in app["name"].lower():
                 if not any(r["name"] == app["name"] for r in registry_matches): 
                     it = app.copy()
                     it["pinned"] = it["id"] in pinned_ids
                     app_matches.append(it)
        
        if not query:
             app_matches = [a for a in app_matches if a.get("pinned")]

        # 2. Files
        file_matches = self._search_files(query) if query else []

        # 3. Clipboard
        clip_matches = []
        if "clip" in query or len(query) > 2:
            for c in self.clipboard_history:
                if query in c["content"].lower() or "clip" in query:
                    clip_matches.append({
                        "id": f"clip_{hash(c['content'])}",
                        "name": f"Clip: {c['content'][:40]}...",
                        "content": c["content"], "cat": "Clipboard",
                        "icon": "\U0001F4CB", "action": "paste"
                    })

        # 4. Calc
        math_results = []
        try:
             allowed = set("0123456789+-*/().% ")
             if query and set(query).issubset(allowed) and any(c.isdigit() for c in query):
                 if not query.strip().isdigit():
                     res = str(eval(query, {"__builtins__": None}))
                     math_results.append({
                         "id": "calc_res", "name": f"= {res}", "content": res,
                         "desc": f"Result of '{query}'", "cat": "Calc", "icon": "\U0001F9EE", "action": "paste"
                     })
        except: pass

        all_res = math_results + registry_matches + app_matches + file_matches + clip_matches[:5]
        pinned = [r for r in all_res if r.get("pinned")]
        others = [r for r in all_res if not r.get("pinned")]
        
        cat_map = {"AI": -1, "Custom": 0, "Apps": 1, "Web": 2, "Calc": 3, "Files": 4, "Clipboard": 5}
        others.sort(key=lambda x: (cat_map.get(x.get("cat"), 9), x['name']))

        return pinned + others[:30] 

    def _cross_platform_open(self, path_or_url):
        if self.platform == 'Windows':
            os.startfile(path_or_url)
        elif self.platform == 'Darwin':
            subprocess.run(['open', path_or_url])
        elif self.platform == 'Linux':
            subprocess.run(['xdg-open', path_or_url])

    def execute(self, item: Dict, query: str = ""):
        try:
            itype = item.get("type")
            path = item.get("path")                                                                                                     
            
            if item.get("action") == "help":
                self._cross_platform_open("https://pytron-kit.github.io/bite")
                return True

            if itype == "search":
                q = query.strip()
                term = item.get("id", "").lower()
                if q.lower().startswith(term + " "): q = q[len(term):].strip()
                
                url = item["url"]
                if not q or q.lower() == term:
                    p = urlparse(item["url"])
                    url = f"{p.scheme}://{p.netloc}"
                else: url = item["url"] + q
                self._cross_platform_open(url)
                
            elif itype in ["file", "lnk", "app", "desktop"]:
                if path: self._cross_platform_open(path)
                
            elif "action" in item:
                act = item["action"]
                if act == "lock":
                    if self.platform == "Windows": ctypes.windll.user32.LockWorkStation()
                    elif self.platform == "Darwin": subprocess.run(['pmset', 'displaysleepnow'])
                    elif self.platform == "Linux": subprocess.run(['xdg-screensaver', 'lock']) # Common
                elif act == "sleep":
                    if self.platform == "Windows": os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
                    elif self.platform == "Darwin": subprocess.run(['pmset', 'sleepnow'])
                    elif self.platform == "Linux": subprocess.run(['systemctl', 'suspend'])
                elif act == "paste":
                    pyperclip.copy(item["content"])
                elif act == "kill_py":
                    for proc in psutil.process_iter():
                        try:
                             if "python" in proc.name().lower(): proc.kill()
                        except: pass

            elif path:
                if path.startswith("http"): self._cross_platform_open(path)
                else: 
                     # Safe execute for random string commands? Be careful.
                     # For legacy compatibility:
                     if self.platform == "Windows":
                          subprocess.Popen(path, shell=item.get("shell", False))
                     else: # Try simple split
                          subprocess.Popen(path.split())

            if not item.get("keep_open"):
                self.app.hide()
            return True
        except Exception as e:
            return str(e)

def main():
    app = App()
    bite = Bite(app)
    app.set_start_on_boot(True)
    app.state.clipboard = []
    
    @app.expose
    def search_items(query: str): return bite.get_results(query)
    @app.expose
    def run_item(item: dict, query: str = ""): return bite.execute(item, query)
    @app.expose
    def toggle_pin(item_id: str): return bite.toggle_pin(item_id)
    
    # Shortcut API
    @app.expose
    def add_shortcut(k, n, u): return bite.add_shortcut(k, n, u)
    @app.expose
    def remove_shortcut(k): return bite.remove_shortcut(k)
    @app.expose
    def get_user_shortcuts(): return bite.get_user_shortcuts()

    # --- Updater Integration ---
    from pytron.updater import Updater
    # Placeholder URL - Replace with your actual update manifest endpoint
    UPDATE_URL = "https://raw.githubusercontent.com/Ghua8088/Bite/main/update.json" 
    updater = Updater()

    @app.expose
    def check_update():
        return updater.check(UPDATE_URL)

    @app.expose
    def install_update(info):
        # Callback to send progress to frontend
        def on_progress(p):
            app.emit('update_progress', p)
        
        return updater.download_and_install(info, on_progress)

    @app.shortcut('Alt+B')
    def toggle_bite():
        if not bite.app.windows: return
        # Cross-platform toggle logic using internal Pytron state if possible?
        # App.hide() and App.show() are cross platform.
        # But we need to know if we are hidden/visible.
        # For now, simplistic boolean toggle could desync.
        # Let's rely on Windows checking for now on Win, and robust fallback on others.
        
        try:
            if bite.platform == "Windows":
                platform_impl = bite.app.windows[0]._platform
                if platform_impl:
                    hwnd = platform_impl._get_hwnd(bite.app.windows[0].w)
                    if ctypes.windll.user32.IsWindowVisible(hwnd): bite.app.hide()
                    else: 
                        bite.app.show()
                        ctypes.windll.user32.SetForegroundWindow(hwnd)
            else:
                # Basic toggle assumption or improved Pytron API needed.
                # Since we don't track state nicely in App yes, just Show always? No, toggle is key.
                # Assuming IsWindowVisible equivalent is harder.
                # For non-Windows, we might just assume Show first. 
                # If we assume 'Alt+Space' is hit, we want to Show if Hidden, or Hide if Focused.
                bite.app.show() # Safe default for now on Mac/Linux
        except: pass

    @app.on_exit
    def shutdown():
        print("Bite Shutting Down...")

    # Custom Tray Setup
    tray = app.setup_tray()
    tray.add_item("Toggle Bite", toggle_bite)
    tray.add_separator()
    tray.add_item("Documentation", lambda: bite._cross_platform_open("https://pytron-kit.github.io/bite"))
    tray.add_item("Quit", app.quit)
    
    app.run()

if __name__ == '__main__': main()
