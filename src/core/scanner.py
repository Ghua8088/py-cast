import os
import platform
import re
import time
import psutil
import pyperclip
from pathlib import Path
from typing import List, Dict
from src.utils.icon_handler import get_icon_url

try:
    if platform.system() == "Windows":
        import win32gui
        import win32process
except ImportError:
    pass


class Scanner:
    def __init__(self, bite_instance):
        self.bite = bite_instance
        self.platform = platform.system()

    def scan_applications(self) -> List[Dict]:
        apps = []
        try:
            if self.platform == "Windows":
                base_paths = [
                    os.path.join(
                        os.environ.get("ProgramData", ""),
                        r"Microsoft\Windows\Start Menu\Programs",
                    ),
                    os.path.join(
                        os.environ.get("APPDATA", ""),
                        r"Microsoft\Windows\Start Menu\Programs",
                    ),
                ]
                for base in base_paths:
                    if not os.path.exists(base):
                        continue
                    for root, dirs, files in os.walk(base):
                        for file in files:
                            if file.lower().endswith(".lnk"):
                                try:
                                    full_path = os.path.join(root, file)
                                    name = os.path.splitext(file)[0]
                                    icon_url = get_icon_url(
                                        self.bite, full_path, force=True
                                    )
                                    apps.append(
                                        {
                                            "id": f"app_{full_path}",
                                            "name": name,
                                            "path": full_path,
                                            "desc": "Application",
                                            "cat": "Apps",
                                            "icon": icon_url or "app",
                                            "resolve_path": (
                                                None if icon_url else full_path
                                            ),
                                            "type": "lnk",
                                            "is_img": bool(icon_url),
                                        }
                                    )
                                except:
                                    pass
            elif self.platform == "Darwin":
                search_paths = ["/Applications", os.path.expanduser("~/Applications")]
                for base in search_paths:
                    if not os.path.exists(base):
                        continue
                    for entry in os.scandir(base):
                        if entry.name.endswith(".app"):
                            name = entry.name.replace(".app", "")
                            apps.append(
                                {
                                    "id": f"app_{entry.path}",
                                    "name": name,
                                    "path": entry.path,
                                    "desc": "Application",
                                    "cat": "Apps",
                                    "icon": "app",
                                    "type": "app",
                                    "is_img": False,
                                }
                            )
            elif self.platform == "Linux":
                search_paths = [
                    "/usr/share/applications",
                    os.path.expanduser("~/.local/share/applications"),
                ]
                for base in search_paths:
                    if not os.path.exists(base):
                        continue
                    for entry in os.scandir(base):
                        if entry.name.endswith(".desktop"):
                            try:
                                with open(entry.path, "r", errors="ignore") as f:
                                    content = f.read()
                                    if "NoDisplay=true" in content:
                                        continue
                                    name_match = re.search(
                                        r"^Name=(.*)", content, re.MULTILINE
                                    )
                                    name = (
                                        name_match.group(1)
                                        if name_match
                                        else entry.name
                                    )
                                    apps.append(
                                        {
                                            "id": f"app_{entry.path}",
                                            "name": name,
                                            "path": entry.path,
                                            "desc": "Application",
                                            "cat": "Apps",
                                            "icon": "app",
                                            "type": "desktop",
                                            "is_img": False,
                                        }
                                    )
                            except:
                                pass
        except Exception as e:
            print(f"Scan Error: {e}")
        return apps

    def scan_workflows(self, workflow_dir: Path) -> List[Dict]:
        workflows = []
        if not workflow_dir.exists():
            return []
        try:
            for entry in os.scandir(workflow_dir):
                if entry.name.endswith(".py"):
                    name = entry.name[:-3].replace("_", " ").title()
                    icon_path = workflow_dir / (entry.name[:-3] + ".png")
                    icon_url = (
                        get_icon_url(self.bite, str(icon_path))
                        if icon_path.exists()
                        else None
                    )
                    workflows.append(
                        {
                            "id": f"wf_{entry.path}",
                            "name": name,
                            "path": entry.path,
                            "desc": "Python Workflow",
                            "cat": "Workflows",
                            "icon": icon_url or "zap",
                            "resolve_path": (
                                str(icon_path)
                                if not icon_url and icon_path.exists()
                                else None
                            ),
                            "is_img": bool(icon_url),
                            "type": "workflow",
                        }
                    )
        except Exception as e:
            print(f"Workflow Scan Error: {e}")
        return workflows

    def clipboard_monitor(self):
        if self.platform == "Windows":
            try:
                import pythoncom
                pythoncom.CoInitialize()
            except:
                pass
        
        while True:
            try:
                curr = pyperclip.paste()
                if curr:
                    self.bite.record_clipboard(curr)
            except:
                pass
            time.sleep(1.5)

    def get_active_window(self) -> Dict:
        """Universal active window tracker for context injection."""
        try:
            if self.platform == "Windows":
                hwnd = win32gui.GetForegroundWindow()
                title = win32gui.GetWindowText(hwnd)
                if not title: return None
                
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                proc = psutil.Process(pid)
                return {
                    "title": title,
                    "process": proc.name().lower(),
                    "pid": pid
                }
            elif self.platform == "Darwin":
                # Fallback for macOS context via AppleScript or similar
                return None
            elif self.platform == "Linux":
                return None
        except:
            return None
        return None

    def system_monitor(self):
        # Cache psutil calls
        while True:
            try:
                cpu = psutil.cpu_percent(interval=None)
                mem = psutil.virtual_memory().percent
                bat = psutil.sensors_battery()
                battery = bat.percent if bat else None
                
                # Context Awareness: What is the user doing right now?
                active_context = self.get_active_window()
                self.bite.active_context = active_context

                # Use a dict update to prevent overwriting other state keys if any
                self.bite.app.state.sys_info = {
                    "cpu": cpu,
                    "mem": mem,
                    "battery": battery,
                    "time": time.strftime("%H:%M"),
                    "active_win": active_context.get("title") if active_context else None,
                    "indexing": getattr(self.bite.indexer, "is_indexing", False),
                }
            except:
                pass
            time.sleep(4)
