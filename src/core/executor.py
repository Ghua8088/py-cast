import os
import sys
import subprocess
import ctypes
import shutil
import pyperclip
import psutil
from typing import Dict
from urllib.parse import urlparse


class Executor:
    def __init__(self, bite_instance):
        self.bite = bite_instance
        self.platform = bite_instance.platform

    def cross_platform_open(self, path_or_url):
        if self.platform == "Windows":
            os.startfile(path_or_url)
        elif self.platform == "Darwin":
            subprocess.run(["open", path_or_url])
        elif self.platform == "Linux":
            subprocess.run(["xdg-open", path_or_url])

    def execute(self, item: Dict, query: str = ""):
        try:
            itype = item.get("type")
            path = item.get("path")
            iid = item.get("id")

            # Recents Tracking
            if iid:
                if iid in self.bite.recent_ids:
                    self.bite.recent_ids.remove(iid)
                self.bite.recent_ids.insert(0, iid)
                self.bite.recent_ids = self.bite.recent_ids[:10]

            if item.get("action") == "help":
                self.cross_platform_open("https://pytron-kit.github.io/bite")
                return True

            if itype == "search":
                self._handle_search(item, query)
            elif itype == "shell":
                self._run_shell(item, path if path else item.get("id"))
            elif itype == "workflow":
                if path:
                    # Resolve python interpreter
                    python_exe = sys.executable
                    if not python_exe.lower().endswith("python.exe"):
                        # We are likely in a bundle, try to find system python
                        for cmd in ["python3", "python", "py"]:
                            if shutil.which(cmd):
                                python_exe = shutil.which(cmd)
                                break
                    
                    subprocess.Popen(
                        [python_exe, path],
                        creationflags=(
                            subprocess.CREATE_NO_WINDOW
                            if self.platform == "Windows"
                            else 0
                        ),
                    )
                    self.bite.app.hide()
            elif itype in ["file", "lnk", "app", "desktop"]:
                if path:
                    self.cross_platform_open(path)
                    self.bite.indexer.index_path(path)
            elif "action" in item:
                self._handle_action(item)
            elif path:
                if path.startswith("http"):
                    self.cross_platform_open(path)
                else:
                    self._run_shell(item, path)

            if not item.get("keep_open"):
                self.bite.app.hide()
            return True
        except Exception as e:
            return str(e)

    def _handle_search(self, item, query):
        q = query.strip()
        term = item.get("id", "").lower()
        if q.lower().startswith(term + " "):
            q = q[len(term) :].strip()

        url = item["url"]
        if not q or q.lower() == term:
            p = urlparse(item["url"])
            url = f"{p.scheme}://{p.netloc}"
        else:
            url = item["url"] + q
        self.cross_platform_open(url)

    def _handle_action(self, item):
        act = item["action"]
        path = item.get("path")

        if act == "lock":
            if self.platform == "Windows":
                ctypes.windll.user32.LockWorkStation()
            elif self.platform == "Darwin":
                subprocess.run(["pmset", "displaysleepnow"])
            elif self.platform == "Linux":
                subprocess.run(["xdg-screensaver", "lock"])
        elif act == "sleep":
            if self.platform == "Windows":
                os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
            elif self.platform == "Darwin":
                subprocess.run(["pmset", "sleepnow"])
            elif self.platform == "Linux":
                subprocess.run(["systemctl", "suspend"])
        elif act == "paste":
            pyperclip.copy(item["content"])
        elif act == "kill_py":
            for proc in psutil.process_iter():
                try:
                    if "python" in proc.name().lower():
                        proc.kill()
                except:
                    pass
        elif act == "kill_pid":
            try:
                psutil.Process(int(item["pid"])).kill()
                self.bite.app.notify("Process Killed", f"Terminated {item['name']}", "success")
            except Exception as e:
                self.bite.app.notify("Kill Failed", str(e), "error")
        elif act == "empty_trash":
            self._empty_trash()
        elif act in ["vol_up", "vol_down", "mute"]:
            self._handle_volume(act)
        elif act == "open_wf":
            self.cross_platform_open(str(self.bite.workflow_dir))
        elif act == "show_ip":
            ip = self.bite.get_external_ip()
            self.bite.app.notify("Your External IP", ip)
            pyperclip.copy(ip)
        elif act == "restart_explorer":
            if self.platform == "Windows":
                os.system("taskkill /f /im explorer.exe && start explorer.exe")
        elif act == "force_reindex":
            self.bite.indexer.force_reindex()
        elif act == "new_workflow_ui":
            self.bite.app.emit("pytron:create_workflow_prompt")
        elif act == "run_term_cmd":
            cmd = item.get("cmd", "")
            if self.platform == "Windows":
                 subprocess.Popen(f'start cmd /k "{cmd}"', shell=True)
            elif self.platform == "Darwin":
                 subprocess.run(["osascript", "-e", f'tell application "Terminal" to do script "{cmd}"'])
            elif self.platform == "Linux":
                 subprocess.run(["gnome-terminal", "--", "bash", "-c", f"{cmd}; exec bash"])

        # --- File Context Actions ---
        elif act == "reveal" and path:
            self._reveal_in_explorer(path)
        elif act == "open_term" and path:
            self._open_terminal(path)
        elif act == "ide_code" and path:
            self._open_in_ide(path, "code")

    def _reveal_in_explorer(self, path):
        if self.platform == "Windows":
            subprocess.Popen(f'explorer /select,"{path}"')
        elif self.platform == "Darwin":
            subprocess.run(["open", "-R", path])
        elif self.platform == "Linux":
            # Fallback to opening folder
            folder = os.path.dirname(path) if os.path.isfile(path) else path
            subprocess.run(["xdg-open", folder])

    def _open_terminal(self, path):
        target = os.path.dirname(path) if os.path.isfile(path) else path
        if self.platform == "Windows":
            # Try Windows Terminal, fallback to cmd
            try:
                subprocess.Popen(f'wt -d "{target}"', shell=True)
            except:
                subprocess.Popen(f'start cmd /k "cd /d {target}"', shell=True)
        elif self.platform == "Darwin":
            subprocess.run(["open", "-a", "Terminal", target])
        elif self.platform == "Linux":
            subprocess.run(["gnome-terminal", "--working-directory", target])

    def _open_in_ide(self, path, binary="code"):
        # "code" for VSCode, "cursor" for Cursor, etc.
        try:
            subprocess.Popen([binary, path], shell=(self.platform == "Windows"))
        except:
            self.bite.app.notify(
                "Error", f"Could not launch {binary}. Is it in PATH?", "error"
            )

    def _empty_trash(self):
        if self.platform == "Windows":
            ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 1 | 2 | 4)
        elif self.platform == "Darwin":
            subprocess.run(
                ["osascript", "-e", 'tell application "Finder" to empty trash']
            )

    def _handle_volume(self, act):
        if self.platform == "Windows":
            import win32api
            import win32con

            vks = {
                "vol_up": win32con.VK_VOLUME_UP,
                "vol_down": win32con.VK_VOLUME_DOWN,
                "mute": win32con.VK_VOLUME_MUTE,
            }
            if act == "mute":
                win32api.keybd_event(vks[act], 0)
            else:
                for _ in range(5):
                    win32api.keybd_event(vks[act], 0)
        elif self.platform == "Darwin":
            scripts = {
                "vol_up": "set volume output volume (output volume of (get volume settings) + 5)",
                "vol_down": "set volume output volume (output volume of (get volume settings) - 5)",
                "mute": "set volume with output muted",
            }
            subprocess.run(["osascript", "-e", scripts[act]])

    def _run_shell(self, item, path):
        if self.platform == "Windows":
            subprocess.Popen(path, shell=item.get("shell", False))
        else:
            subprocess.Popen(path.split())
