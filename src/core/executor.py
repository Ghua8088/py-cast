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
            # --- Universal Alias Expansion ---
            query = self.bite.resolve_aliases(query)
            iid = item.get("id")

            # Handle Multi-Command execution
            commands = item.get("commands")
            if commands and isinstance(commands, list):
                # We iterate and execute each one
                results = []
                for i, cmd in enumerate(commands):
                    # Skip layout tags if the user left them in
                    if cmd.startswith("layout:"):
                        continue
                        
                    # Create a dummy item for each sub-command
                    sub_item = item.copy()
                    sub_item.pop("commands", None)
                    sub_item["path"] = cmd
                    # Re-detect type for each sub-command
                    cmd_str = str(cmd).strip()
                    if cmd_str.startswith("http"):
                        sub_item["id"] = f"_multi_sub_{i}"
                        sub_item["type"] = "search"
                        sub_item["url"] = cmd_str
                    else:
                        sub_item["type"] = "shell"
                    
                    sub_item["keep_open"] = True
                    results.append(self.execute(sub_item, ""))
                
                # After all commands initiated, hide if needed
                if not item.get("keep_open"):
                    self.bite.app.hide()
                return results

            # Recents Tracking
            if iid:
                if iid in self.bite.recent_ids:
                    self.bite.recent_ids.remove(iid)
                self.bite.recent_ids.insert(0, iid)
                self.bite.recent_ids = self.bite.recent_ids[:10]
                
                # Mnemonic Learning (Quicksilver style)
                if query and len(query.strip()) > 0:
                    self.bite.record_selection(query, iid)

            if item.get("action") == "help":
                self.cross_platform_open("https://pytron-kit.github.io/bite")
                return True

            if itype == "search":
                self._handle_search(item, query)
            elif itype == "shell":
                cmd_base = path if path else item.get("id")
                full_cmd = self._append_query_args(cmd_base, query, item.get("id", ""))
                self._run_shell(item, full_cmd)
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
                    # Treat as raw shell command with potential args
                    full_cmd = self._append_query_args(path, query, item.get("id", ""))
                    self._run_shell(item, full_cmd)

            if not item.get("keep_open") and item.get("action") != "refresh_theme":
                self.bite.app.hide()
            return True
        except Exception as e:
            return str(e)

    def _append_query_args(self, base_cmd: str, full_query: str, item_id: str) -> str:
        """Helper to append query parameters as arguments to a base command."""
        q = full_query.strip()
        # If query matches item_id or starts with it, extract the rest as args
        # e.g. "code d:\path" where item_id is "code"
        if q.lower().startswith(item_id.lower() + " "):
            args = q[len(item_id):].strip()
            return f"{base_cmd} {args}"
        elif q.lower() == item_id.lower():
            return base_cmd
        
        # If the query is unrelated to the trigger (e.g. searching 'cod' matches 'code')
        # we don't append the query as it would just break the command
        return base_cmd

    def _handle_search(self, item, query):
        q = query.strip()
        term = item.get("id", "").lower()
        
        # Determine if this is an explicit keyword search (e.g., "g my_query")
        explicit_search = False
        if q.lower().startswith(term + " "):
            q = q[len(term):].strip()
            explicit_search = True

        url = item.get("url") or item.get("path")
        
        # Logic to decide if we should append the query to the URL:
        # 1. Explicit keyword trigger was used AND there is a query body
        # 2. It's the global "web_search" fallback item
        # 3. But NEVER append if the query is empty or just matches the trigger
        should_append = False
        if explicit_search and q:
            should_append = True
        elif item.get("id") == "web_search" and q:
            should_append = True
            
        target_url = url + q if should_append else url
        self.cross_platform_open(target_url)

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
                self.bite.app.system_notification("Process Killed", f"Terminated {item['name']}")
            except Exception as e:
                self.bite.app.system_notification("Kill Failed", str(e))
        elif act == "empty_trash":
            self._empty_trash()
        elif act in ["vol_up", "vol_down", "mute"]:
            self._handle_volume(act)
        elif act == "open_wf":
            self.cross_platform_open(str(self.bite.workflow_dir))
        elif act == "show_ip":
            ip = self.bite.get_external_ip()
            self.bite.app.system_notification("Your External IP", ip)
            pyperclip.copy(ip)
        elif act == "restart_explorer":
            if self.platform == "Windows":
                os.system("taskkill /f /im explorer.exe && start explorer.exe")
        elif act == "force_reindex":
            self.bite.indexer.force_reindex()
        elif act == "new_workflow_ui":
            self.bite.app.emit("pytron:create_workflow_prompt")
        elif act == "refresh_theme":
            theme = self.bite.get_adaptive_theme()
            self.bite.app.emit("pytron:theme_updated", theme)
        elif act == "run_term_cmd":
            cmd = item.get("cmd", "")
            # Default to User Home for terminal sessions
            cwd = os.path.expanduser("~")
            if self.platform == "Windows":
                 subprocess.Popen(f'start cmd /k "{cmd}"', shell=True, cwd=cwd)
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
            self.bite.app.system_notification(
                "Error", f"Could not launch {binary}. Is it in PATH?"
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
        # Universal Expansion handled via initial execute or here for direct calls
        path = self.bite.resolve_aliases(path)

        # Final Shell Safety: Wrap in quotes if it's a direct path starting with a drive
        if ":" in path and not path.startswith('"'):
            # If the path contains spaces and isn't a complex command line
            if " " in path:
                # Basic check: if it's a 'cd' or similar, we only quote the path part
                parts = path.split(" ", 1)
                if len(parts) > 1 and ":" in parts[1]:
                    path = f'{parts[0]} "{parts[1].strip()}"'
                else:
                    path = f'"{path}"'
        
        # Default to User Home for general shell commands to avoid internal app dirs
        cwd = item.get("cwd") or os.path.expanduser("~")

        if self.platform == "Windows":
            subprocess.Popen(path, shell=item.get("shell", False), cwd=cwd)
        else:
            try:
                subprocess.Popen(path.split(), cwd=cwd)
            except:
                subprocess.Popen(path, shell=True, cwd=cwd)
