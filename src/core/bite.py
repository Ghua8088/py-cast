import os
import sys
import json
import time
import platform
import shutil
from pathlib import Path
from typing import List, Dict
from pytron import App
import threading

# Local imports
from src.utils.icon_handler import get_icon_url
from src.core.scanner import Scanner
from src.core.searcher import Searcher
from src.core.executor import Executor
from src.core.indexer import Indexer
from src.core.plugins import PluginManager
from src.core.brain import Brain
from src.utils.theme_engine import get_wallpaper_path, get_adaptive_color


class Bite:
    def __init__(self, app: App):
        self.app = app
        self.platform = platform.system()
        self.recent_ids = []
        self.resolved_icons = {}
        self.active_context = None

        # Paths
        config_home = (
            Path(os.environ.get("APPDATA"))
            if self.platform == "Windows"
            else Path.home() / ".config"
        )
        self.config_dir = config_home / "Bite"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.workflow_dir = self.config_dir / "workflows"
        self.workflow_dir.mkdir(parents=True, exist_ok=True)
        self.config_path = self.config_dir / "config.json"

        # Initialize data and clipboard
        self.user_data = self._load_config()
        self.clipboard_history = self.user_data.get("clipboard_history", [])
        self._last_clipboard = self.clipboard_history[0]["content"] if self.clipboard_history else ""

        # Modules
        self.scanner = Scanner(self)
        self.searcher = Searcher(self)
        self.executor = Executor(self)
        self.indexer = Indexer(self)
        self.brain = Brain(self)
        self.plugins = PluginManager(self)
        self.plugins.load_plugins()

        # Initial Data
        self.base_registry = self._get_base_registry()
        self.installed_apps = self.scanner.scan_applications()
        self.workflows = self.scanner.scan_workflows(self.workflow_dir)

        # Background Tasks
        threading.Thread(target=self.scanner.clipboard_monitor, daemon=True).start()
        threading.Thread(target=self.scanner.system_monitor, daemon=True).start()
        self.indexer.start_indexing()

    def _get_base_registry(self):
        reg = [
            {
                "id": "google",
                "name": "Search Google",
                "type": "search",
                "url": "https://google.com/search?q=",
                "cat": "Web",
                "icon": "globe",
            },
            {
                "id": "yt",
                "name": "Search YouTube",
                "type": "search",
                "url": "https://www.youtube.com/results?search_query=",
                "cat": "Web",
                "icon": "youtube",
            },
            {
                "id": "gh",
                "name": "Search GitHub",
                "type": "search",
                "url": "https://github.com/search?q=",
                "cat": "Web",
                "icon": "github",
            },
            {
                "id": "weather",
                "name": "Check Weather",
                "type": "search",
                "url": "https://www.google.com/search?q=weather+",
                "cat": "Web",
                "icon": "sun",
            },
            {
                "id": "dict",
                "name": "Dictionary",
                "type": "search",
                "url": "https://www.google.com/search?q=define+",
                "cat": "Web",
                "icon": "book",
            },
            {
                "id": "trans",
                "name": "Translate",
                "type": "search",
                "url": "https://translate.google.com/?sl=auto&tl=en&text=",
                "cat": "Web",
                "icon": "languages",
            },
            {
                "id": "scratch",
                "name": "Scratchpad",
                "action": "open_scratch",
                "desc": "Quick notes and thoughts",
                "cat": "Productivity",
                "icon": "edit-3",
            },
            {
                "id": "open_lab",
                "name": "Python Lab",
                "action": "open_lab",
                "desc": "Write & Run Python Scripts",
                "cat": "Dev",
                "icon": "code",
            },
            {
                "id": "clean",
                "name": "Kill All Python",
                "action": "kill_py",
                "desc": "Task Cleanup",
                "cat": "System",
                "icon": "zap",
            },
            {
                "id": "empty_trash",
                "name": "Empty Trash",
                "action": "empty_trash",
                "desc": "Clear system bin",
                "cat": "System",
                "icon": "trash",
            },
            {
                "id": "refresh_theme",
                "name": "Refresh Adaptive Theme",
                "desc": "Sync accent colors with your current wallpaper",
                "action": "refresh_theme",
                "cat": "System",
                "icon": "palette",
                "keep_open": True,
            },
            {
                "id": "vol_up",
                "name": "Volume Up",
                "action": "vol_up",
                "desc": "Increment sound",
                "cat": "System",
                "icon": "vol_up",
            },
            {
                "id": "vol_down",
                "name": "Volume Down",
                "action": "vol_down",
                "desc": "Decrement sound",
                "cat": "System",
                "icon": "vol_down",
            },
            {
                "id": "mute",
                "name": "Toggle Mute",
                "action": "mute",
                "desc": "Silence audio",
                "cat": "System",
                "icon": "mute",
            },
            {
                "id": "browse_wf",
                "name": "Browse all Workflows",
                "type": "term_autofill",
                "new_query": "wf:",
                "desc": "List all Python scripts",
                "cat": "Workflows",
                "icon": "zap",
            },
            {
                "id": "wf_folder",
                "name": "Open Workflows Folder",
                "action": "open_wf",
                "desc": "Add .py scripts here",
                "cat": "System",
                "icon": "folder",
            },
            {
                "id": "ip",
                "name": "My External IP",
                "action": "show_ip",
                "desc": "Check network identity",
                "cat": "System",
                "icon": "globe",
            },
            {
                "id": "restart_explorer",
                "name": "Restart Explorer",
                "action": "restart_explorer",
                "desc": "Fix UI glitches",
                "cat": "System",
                "icon": "refresh-cw",
            },
            {
                "id": "settings",
                "name": "Settings",
                "action": "settings",
                "desc": "Manage Shortcuts",
                "cat": "System",
                "icon": "settings",
            },
            {
                "id": "help",
                "name": "How to use Bite?",
                "action": "help",
                "desc": "Tips & Tricks",
                "cat": "Help",
                "icon": "help",
            },
            {
                "id": "reindex",
                "name": "Force Re-index Files",
                "action": "force_reindex",
                "desc": "Deep scan for file changes",
                "cat": "System",
                "icon": "refresh-cw",
            },
            {
                "id": "chatgpt",
                "name": "Open ChatGPT",
                "type": "search",
                "url": "https://chat.openai.com/?q=",
                "desc": "OpenAI Chat",
                "cat": "AI",
                "icon": "bot",
            },
            {
                "id": "claude",
                "name": "Open Claude",
                "type": "search",
                "url": "https://claude.ai/new?q=",
                "desc": "Anthropic Chat",
                "cat": "AI",
                "icon": "cpu",
            },
            {
                "id": "gemini",
                "name": "Open Gemini",
                "type": "search",
                "url": "https://gemini.google.com/app?q=",
                "desc": "Google AI",
                "cat": "AI",
                "icon": "sparkles",
            },
            {
                "id": "grok",
                "name": "Open Grok",
                "type": "search",
                "url": "https://twitter.com/i/grok?q=",
                "desc": "xAI Chat",
                "cat": "AI",
                "icon": "rocket",
            },
            {
                "id": "perplexity",
                "name": "Open Perplexity",
                "type": "search",
                "url": "https://www.perplexity.ai/search?q=",
                "desc": "AI Search Engine",
                "cat": "AI",
                "icon": "search",
            },
        ]

        if self.platform == "Windows":
            reg.extend(
                [
                    {
                        "id": "calc",
                        "name": "Calculator",
                        "path": "calc.exe",
                        "desc": "Standard Calc",
                        "cat": "Apps",
                        "icon": "calculator",
                    },
                    {
                        "id": "note",
                        "name": "Notepad",
                        "path": "notepad.exe",
                        "desc": "Quick Notes",
                        "cat": "Apps",
                        "icon": "file-text",
                    },
                    {
                        "id": "term",
                        "name": "Terminal",
                        "path": "powershell.exe",
                        "desc": "PowerShell",
                        "cat": "Apps",
                        "icon": "terminal",
                    },
                    {
                        "id": "lock",
                        "name": "Lock Screen",
                        "action": "lock",
                        "desc": "Secure PC",
                        "cat": "System",
                        "icon": "lock",
                    },
                    {
                        "id": "sleep",
                        "name": "Sleep",
                        "action": "sleep",
                        "desc": "Energy Saving",
                        "cat": "System",
                        "icon": "moon",
                    },
                ]
            )
        elif self.platform == "Darwin":
            reg.extend(
                [
                    {
                        "id": "calc",
                        "name": "Calculator",
                        "path": "/System/Applications/Calculator.app",
                        "desc": "Calculator",
                        "cat": "Apps",
                        "icon": "calculator",
                    },
                    {
                        "id": "term",
                        "name": "Terminal",
                        "path": "/System/Applications/Utilities/Terminal.app",
                        "desc": "Terminal",
                        "cat": "Apps",
                        "icon": "terminal",
                    },
                    {
                        "id": "lock",
                        "name": "Lock Screen",
                        "action": "lock",
                        "desc": "Secure Mac",
                        "cat": "System",
                        "icon": "lock",
                    },
                ]
            )
        elif self.platform == "Linux":
            reg.extend(
                [
                    {
                        "id": "term",
                        "name": "Terminal",
                        "path": "gnome-terminal",
                        "desc": "Terminal",
                        "cat": "Apps",
                        "icon": "terminal",
                    }
                ]
            )
        return reg

    def _load_config(self):
        defaults = {
            "pins": [],
            "shortcuts": [],
            "snippets": [],
            "aliases": {
                "downloads": os.path.join(os.path.expanduser("~"), "Downloads"),
                "desktop": os.path.join(os.path.expanduser("~"), "Desktop"),
                "documents": os.path.join(os.path.expanduser("~"), "Documents")
            },
            "mnemonics": {},
            "clipboard_history": [],
            "scratchpad": "Welcome to your scratchpad! Type here to keep notes...",
            "settings": {
                "theme_color": "#5e5ce6",
                "start_on_boot": False,
                "hide_footer": False,
                "excluded_folders": [
                    "node_modules", ".git", ".vscode", "venv", "env", "__pycache__", "dist", "build"
                ]
            }
        }
        if self.config_path.exists():
            try:
                data = json.loads(self.config_path.read_text())
                # Deep merge defaults for settings
                for k, v in defaults.items():
                    if k not in data:
                        data[k] = v
                    elif k == "settings" and isinstance(data[k], dict):
                        for sk, sv in v.items():
                            if sk not in data[k]:
                                data[k][sk] = sv
                return data
            except:
                pass
        return defaults

    def update_settings(self, new_settings):
        self.user_data["settings"].update(new_settings)
        self._save_config()
        # Apply startup setting if it was changed
        if "start_on_boot" in new_settings:
            try:
                self.app.set_start_on_boot(new_settings["start_on_boot"])
            except Exception as e:
                print(f"Bite: Failed to set startup preference: {e}")
        return self.user_data["settings"]

    def get_settings(self):
        return self.user_data.get("settings", {})

    def record_selection(self, query: str, item_id: str):
        if not query or not item_id:
            return
        
        # Clean query: lowercase and stripped
        q = query.lower().strip()
        if len(q) < 1:
            return
            
        mnemonics = self.user_data.get("mnemonics", {})
        # Store as { query: { item_id: count } }
        if q not in mnemonics:
            mnemonics[q] = {}
        
        if item_id not in mnemonics[q]:
            mnemonics[q][item_id] = 0
            
        mnemonics[q][item_id] += 1
        
        # Clean up: only keep top 3 per query to save space
        if len(mnemonics[q]) > 3:
            sorted_items = sorted(mnemonics[q].items(), key=lambda x: x[1], reverse=True)
            mnemonics[q] = dict(sorted_items[:3])
            
        self.user_data["mnemonics"] = mnemonics
        self._save_config()
        
        # Neural Learning: Link this action to the current context
        self.brain.record_event(item_id)

    def record_clipboard(self, content: str):
        if not content or content == self._last_clipboard:
            return
        
        self._last_clipboard = content
        entry = {"content": content, "time": time.strftime("%H:%M:%S"), "date": time.strftime("%Y-%m-%d")}
        
        # Avoid duplicates in history
        self.clipboard_history = [c for c in self.clipboard_history if c["content"] != content]
        self.clipboard_history.insert(0, entry)
        self.clipboard_history = self.clipboard_history[:50] # Keep more history
        
        self.user_data["clipboard_history"] = self.clipboard_history
        self.app.state.clipboard = self.clipboard_history
        self._save_config()

    def _save_config(self):
        self.config_path.write_text(json.dumps(self.user_data))

    def update_scratchpad(self, content):
        self.user_data["scratchpad"] = content
        self._save_config()
        return True

    def get_python_scratch(self):
        return self.user_data.get("python_scratch", "# Type your Python code here\nprint('Hello from Bite Python Lab!')\n")

    def save_python_scratch(self, code):
        self.user_data["python_scratch"] = code
        self._save_config()
        return True

    def promote_lab_to_workflow(self, name, code):
        # Clean name for filename
        filename = name.lower().replace(" ", "_")
        if not filename.endswith(".py"):
            filename += ".py"
        
        wf_path = self.workflow_dir / filename
        try:
            # Add a bit of metadata to the file
            header = f"# Bite Workflow: {name}\n# Created via Python Lab\n\n"
            wf_path.write_text(header + code)
            
            # Re-scan workflows so it appears in search immediately
            self.workflows = self.scanner.scan_workflows(self.workflow_dir)
            return {"success": True, "path": str(wf_path)}
        except Exception as e:
            return {"error": str(e)}

    def run_python_scratch(self, code):
        self.save_python_scratch(code)
        # Create a temp file to run
        temp_path = self.config_dir / "lab_scratch.py"
        temp_path.write_text(code)
        
        # Use the same logic as workflow execution
        python_exe = sys.executable
        if not python_exe.lower().endswith("python.exe"):
            for cmd in ["python3", "python", "py"]:
                if shutil.which(cmd):
                    python_exe = shutil.which(cmd)
                    break
        
        import subprocess
        try:
            # We run it and capture output or just run it? 
            # Subprocess Popen is better for non-blocking
            subprocess.Popen(
                [python_exe, str(temp_path)],
                creationflags=(
                    subprocess.CREATE_NEW_CONSOLE
                    if self.platform == "Windows"
                    else 0
                ),
            )
            return {"success": True}
        except Exception as e:
            return {"error": str(e)}

    def toggle_pin(self, item_id: str):
        if not item_id:
            return False
        if item_id in self.user_data["pins"]:
            self.user_data["pins"].remove(item_id)
        else:
            self.user_data["pins"].append(item_id)
        self._save_config()
        return True

    def create_workflow(self, name):
        filename = name.lower().replace(" ", "_") + ".py"
        path = self.workflow_dir / filename
        if path.exists():
            return {"error": "Workflow already exists"}
        template = f"# Bite Workflow: {name}\nimport os\ndef main(): os.system('msg * \"Executed!\"')\nif __name__ == '__main__': main()"
        try:
            path.write_text(template)
            self.workflows = self.scanner.scan_workflows(self.workflow_dir)
            return {"success": True, "path": str(path)}
        except Exception as e:
            return {"error": str(e)}

    def select_workflow(self):
        """Opens a native file dialog via Pytron to select a .py file and adds it to workflows."""
        file_path = self.app.dialog_open_file(
            title="Select Python Workflow Script", file_types=[("Python Files", "*.py")]
        )

        if not file_path:
            return {"error": "No file selected"}

        try:
            # Handle list return if pytron returns it that way
            if isinstance(file_path, list):
                if not file_path:
                    return {"error": "No file selected"}
                file_path = file_path[0]

            source_path = Path(file_path)
            dest_path = self.workflow_dir / source_path.name

            if dest_path.exists():
                return {
                    "error": f"Workflow '{source_path.name}' already exists in Bite."
                }

            shutil.copy(str(file_path), str(dest_path))
            self.workflows = self.scanner.scan_workflows(self.workflow_dir)

            return {
                "success": True,
                "name": source_path.stem.replace("_", " ").title(),
                "path": str(dest_path),
            }
        except Exception as e:
            return {"error": str(e)}

    def select_folder_for_alias(self):
        """Opens a native folder dialog and returns the selected path."""
        # Temporarily disable always_on_top so the dialog isn't hidden behind the main window
        # We can also just hide the window to be safe and clean
        if self.app.windows:
            self.app.windows[0].hide()
            
        folder_path = self.app.dialog_open_folder(title="Select Folder for Alias")
        
        if self.app.windows:
            self.app.windows[0].show()
            
        if not folder_path:
            return {"error": "No folder selected"}
        
        # Handle list return if pytron returns it that way
        if isinstance(folder_path, list):
            if not folder_path:
                return {"error": "No folder selected"}
            folder_path = folder_path[0]
            
        return {"path": str(folder_path)}

    def get_results(self, query):
        return self.searcher.get_results(query)

    def execute(self, item, query=""):
        return self.executor.execute(item, query)

    def _cross_platform_open(self, path):
        return self.executor.cross_platform_open(path)

    def get_external_ip(self):
        try:
            import urllib.request

            with urllib.request.urlopen("https://ident.me", timeout=3) as r:
                return r.read().decode("utf8")
        except:
            return "Unknown"

    def resolve_aliases(self, text: str) -> str:
        """Universal alias resolver for @path shortcuts."""
        if not text or "@" not in text:
            return text
            
        # Combine both alias stores
        all_aliases = self.user_data.get("aliases", {}).copy()
        path_aliases = self.user_data.get("path_aliases", {})
        all_aliases.update(path_aliases)
        
        # Sort by key length descending to prevent partial matches of shorter aliases
        sorted_keys = sorted(all_aliases.keys(), key=len, reverse=True)
        
        expanded = text
        for k in sorted_keys:
            alias = k if k.startswith("@") else f"@{k}"
            target = all_aliases[k].rstrip("\\/")
            
            # Replace @alias/ or @alias\ with target\
            if f"{alias}/" in expanded:
                expanded = expanded.replace(f"{alias}/", f"{target}\\")
            elif f"{alias}\\" in expanded:
                expanded = expanded.replace(f"{alias}\\", f"{target}\\")
            elif expanded.endswith(alias):
                # Ensure it's a whole word or start of string
                idx = expanded.rfind(alias)
                if idx == 0 or expanded[idx-1] == " ":
                    expanded = expanded[:idx] + target
            elif f" {alias} " in expanded:
                expanded = expanded.replace(f" {alias} ", f" {target} ")
            elif expanded.startswith(f"{alias} "):
                expanded = expanded.replace(f"{alias} ", f"{target} ", 1)
            elif expanded == alias:
                expanded = target
                
        return expanded

    def get_adaptive_theme(self):
        path = get_wallpaper_path()
        color = get_adaptive_color(path)
        return {"accent": color or "#3b82f6"} # Default to blue if fails

    # Settings Helpers
    def add_shortcut(self, k, n, u):
        self.user_data["shortcuts"] = [s for s in self.user_data["shortcuts"] if s["id"] != k]
        
        # Check if u is multi-command (contains NEWLINES or ;)
        commands = []
        if "\n" in u:
            commands = [cmd.strip() for cmd in u.split("\n") if cmd.strip()]
        elif ";" in u and not (u.startswith("http") and "query=" in u): # Basic guard for URLs
            commands = [cmd.strip() for cmd in u.split(";") if cmd.strip()]
            
        if len(commands) > 1:
            self.user_data["shortcuts"].append({
                "id": k, "name": n, "type": "multi", 
                "commands": commands, "cat": "Custom", "icon": "layers",
                "desc": f"Runs {len(commands)} commands"
            })
        else:
            # Simple heuristic for web URLs
            cmd = commands[0] if commands else u
            is_web = cmd.startswith("http") or cmd.startswith("www.") or ("." in cmd and " " not in cmd and "/" not in cmd) or ("." in cmd.split("/")[0] if "/" in cmd else False)
            
            if is_web:
                if not cmd.startswith("http"): cmd = "https://" + cmd
                self.user_data["shortcuts"].append({
                    "id": k, "name": n, "type": "search", 
                    "url": cmd, "cat": "Custom", "icon": "globe"
                })
            else:
                # Treat as shell command or file path
                self.user_data["shortcuts"].append({
                    "id": k, "name": n, "type": "shell", 
                    "path": cmd, "cat": "Custom", "icon": "terminal",
                    "shell": True
                })
            
        self._save_config()
        return self.user_data["shortcuts"]

    def remove_shortcut(self, k):
        self.user_data["shortcuts"] = [
            s for s in self.user_data["shortcuts"] if s["id"] != k
        ]
        self._save_config()
        return self.user_data["shortcuts"]

    def get_user_shortcuts(self):
        return self.user_data.get("shortcuts", [])

    def add_snippet(self, n, c):
        self.user_data["snippets"].append(
            {
                "id": f"snip_{int(time.time()) if 'time' in globals() else 123}",
                "name": n,
                "content": c,
            }
        )
        self._save_config()
        return self.user_data["snippets"]

    def remove_snippet(self, sid):
        self.user_data["snippets"] = [
            s for s in self.user_data["snippets"] if s["id"] != sid
        ]
        self._save_config()
        return self.user_data["snippets"]

    def get_user_snippets(self):
        return self.user_data.get("snippets", [])

    def add_path_alias(self, k, p):
        if "path_aliases" not in self.user_data: self.user_data["path_aliases"] = {}
        self.user_data["path_aliases"][k] = p
        self._save_config()
        return self.user_data["path_aliases"]

    def remove_path_alias(self, k):
        if "path_aliases" in self.user_data:
            if k in self.user_data["path_aliases"]:
                del self.user_data["path_aliases"][k]
                self._save_config()
        return self.user_data.get("path_aliases", {})

    def _create_file_result(self, entry, desc, tags=None):
        # ALWAYS force a real icon for file/search results to ensure OS logos show up
        icon_url = get_icon_url(self, entry.path, force=True)
        display_desc = f"{desc} {entry.path}" if desc else entry.path
        return {
            "id": f"file_{entry.path}",
            "name": entry.name,
            "path": entry.path,
            "desc": display_desc,
            "cat": "Files",
            "tags": tags,
            "icon": icon_url or ("folder" if entry.is_dir() else "file"),
            "resolve_path": entry.path if not icon_url and not entry.is_dir() else None,
            "type": "file",
            "is_img": bool(icon_url),
            "is_dir": entry.is_dir()
        }

    def _get_drives(self):
        import psutil

        try:
            return [
                p.mountpoint
                for p in psutil.disk_partitions()
                if "fixed" in p.opts or "rw" in p.opts
            ]
        except:
            return ["C:\\"] if self.platform == "Windows" else ["/"]
