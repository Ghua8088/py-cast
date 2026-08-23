import os
import json
import sqlite3
import urllib.parse
from pathlib import Path
from typing import List, Dict


class IDEManager:
    """
    Reads recent projects and workspaces directly from VS Code and Cursor state databases (state.vscdb).
    """

    def __init__(self, bite_instance):
        self.bite = bite_instance
        self.platform = bite_instance.platform

    def _get_vscdb_paths(self) -> List[tuple]:
        """Returns list of (EditorName, CommandBinary, DbPath)"""
        results = []
        if self.platform == "Windows":
            appdata = os.environ.get("APPDATA", "")
            if appdata:
                editors = [
                    ("VS Code", "code", os.path.join(appdata, r"Code\User\globalStorage\state.vscdb")),
                    ("VS Code Insiders", "code-insiders", os.path.join(appdata, r"Code - Insiders\User\globalStorage\state.vscdb")),
                    ("Cursor", "cursor", os.path.join(appdata, r"Cursor\User\globalStorage\state.vscdb")),
                    ("VSCodium", "codium", os.path.join(appdata, r"VSCodium\User\globalStorage\state.vscdb")),
                ]
                for name, cmd, p in editors:
                    if os.path.exists(p):
                        results.append((name, cmd, p))
        elif self.platform == "Darwin":
            home = Path.home()
            editors = [
                ("VS Code", "code", home / "Library/Application Support/Code/User/globalStorage/state.vscdb"),
                ("Cursor", "cursor", home / "Library/Application Support/Cursor/User/globalStorage/state.vscdb"),
            ]
            for name, cmd, p in editors:
                if p.exists():
                    results.append((name, cmd, str(p)))
        elif self.platform == "Linux":
            home = Path.home()
            editors = [
                ("VS Code", "code", home / ".config/Code/User/globalStorage/state.vscdb"),
                ("Cursor", "cursor", home / ".config/Cursor/User/globalStorage/state.vscdb"),
            ]
            for name, cmd, p in editors:
                if p.exists():
                    results.append((name, cmd, str(p)))

        return results

    def get_recent_workspaces(self) -> List[Dict]:
        workspaces = []
        seen_paths = set()

        for editor_name, editor_cmd, db_path in self._get_vscdb_paths():
            try:
                # Open read-only SQLite URI to avoid database locking
                uri = f"file:{urllib.parse.quote(os.path.abspath(db_path))}?mode=ro"
                conn = sqlite3.connect(uri, uri=True)
                cursor = conn.cursor()

                cursor.execute("SELECT value FROM ItemTable WHERE key = 'history.recentlyOpenedPathsList'")
                row = cursor.fetchone()
                conn.close()

                if row and row[0]:
                    data = json.loads(row[0])
                    entries = data.get("entries", [])
                    for entry in entries:
                        folder_uri = entry.get("folderUri") or entry.get("workspace", {}).get("configPath") or entry.get("fileUri")
                        if not folder_uri:
                            continue

                        # Parse file URI to real OS path (e.g., file:///d%3A/projects/foo -> D:\projects\foo)
                        parsed = urllib.parse.urlparse(folder_uri)
                        if parsed.scheme == "file":
                            raw_path = urllib.parse.unquote(parsed.path)
                            # On Windows, path looks like /d:/projects/foo -> strip leading slash
                            if self.platform == "Windows" and len(raw_path) > 2 and raw_path[0] == "/" and raw_path[2] == ":":
                                raw_path = raw_path[1:].replace("/", "\\")
                            
                            if raw_path in seen_paths or not os.path.exists(raw_path):
                                continue

                            seen_paths.add(raw_path)
                            name = os.path.basename(raw_path.rstrip("\\/")) or raw_path

                            workspaces.append({
                                "id": f"ide_{hash(raw_path)}",
                                "name": name,
                                "path": raw_path,
                                "desc": f"Recent {editor_name} Workspace ({raw_path})",
                                "cat": "IDE Workspaces",
                                "icon": "code",
                                "type": "ide_workspace",
                                "action": "open_ide",
                                "editor": editor_cmd,
                            })
            except Exception as e:
                print(f"IDEManager: Error reading {editor_name} recent workspaces: {e}")

        return workspaces

    def search_workspaces(self, query: str) -> List[Dict]:
        items = self.get_recent_workspaces()
        if not query:
            return [{**w, "score": 100} for w in items[:25]]

        q = query.lower().strip()
        matches = []
        for w in items:
            name_lower = w["name"].lower()
            path_lower = w["path"].lower()

            score = 0
            if name_lower == q:
                score = 100
            elif name_lower.startswith(q):
                score = 90
            elif q in name_lower:
                score = 75
            elif q in path_lower:
                score = 40

            if score > 0:
                it = w.copy()
                it["score"] = score
                matches.append(it)

        matches.sort(key=lambda x: -x["score"])
        return matches[:20]
