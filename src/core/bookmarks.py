import os
import json
import sqlite3
import platform
import threading
from pathlib import Path
from typing import List, Dict


class BookmarksManager:
    """
    Lightweight, zero-overhead browser bookmarks reader for Chromium and Firefox browsers.
    Reads local JSON/SQLite files without browser extensions or external network requests.
    """

    def __init__(self, bite_instance):
        self.bite = bite_instance
        self.platform = bite_instance.platform
        self.bookmarks: List[Dict] = []
        self._lock = threading.Lock()
        self.refresh_bookmarks_async()

    def is_opted_in(self) -> bool:
        """Returns True only if the user explicitly opted-in to bookmarks search in Settings."""
        return bool(self.bite.user_data.get("settings", {}).get("opt_in_bookmarks", False))

    def refresh_bookmarks_async(self):
        if not self.is_opted_in():
            with self._lock:
                self.bookmarks = []
            return
        threading.Thread(target=self._load_all_bookmarks, daemon=True).start()

    def _get_chromium_paths(self) -> List[tuple]:
        """Returns list of (BrowserName, BookmarksFilePath) for Chromium-based browsers."""
        paths = []
        if self.platform == "Windows":
            local_appdata = os.environ.get("LOCALAPPDATA", "")
            if not local_appdata:
                return []

            browsers = {
                "Google Chrome": os.path.join(local_appdata, r"Google\Chrome\User Data\Default\Bookmarks"),
                "Microsoft Edge": os.path.join(local_appdata, r"Microsoft\Edge\User Data\Default\Bookmarks"),
                "Brave": os.path.join(local_appdata, r"BraveSoftware\Brave-Browser\User Data\Default\Bookmarks"),
                "Chromium": os.path.join(local_appdata, r"Chromium\User Data\Default\Bookmarks"),
                "Arc": os.path.join(local_appdata, r"Arc\User Data\Default\Bookmarks"),
                "Vivaldi": os.path.join(local_appdata, r"Vivaldi\User Data\Default\Bookmarks"),
            }
            for name, p in browsers.items():
                if os.path.exists(p):
                    paths.append((name, p))
        elif self.platform == "Darwin":
            home = Path.home()
            browsers = {
                "Google Chrome": home / "Library/Application Support/Google/Chrome/Default/Bookmarks",
                "Microsoft Edge": home / "Library/Application Support/Microsoft Edge/Default/Bookmarks",
                "Brave": home / "Library/Application Support/BraveSoftware/Brave-Browser/Default/Bookmarks",
                "Arc": home / "Library/Application Support/Arc/User Data/Default/Bookmarks",
            }
            for name, p in browsers.items():
                if p.exists():
                    paths.append((name, str(p)))
        elif self.platform == "Linux":
            home = Path.home()
            browsers = {
                "Google Chrome": home / ".config/google-chrome/Default/Bookmarks",
                "Brave": home / ".config/BraveSoftware/Brave-Browser/Default/Bookmarks",
                "Chromium": home / ".config/chromium/Default/Bookmarks",
            }
            for name, p in browsers.items():
                if p.exists():
                    paths.append((name, str(p)))

        return paths

    def _parse_chromium_json(self, browser_name: str, file_path: str) -> List[Dict]:
        results = []
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                data = json.load(f)

            roots = data.get("roots", {})

            def traverse(node, folder=""):
                if not isinstance(node, dict):
                    return
                node_type = node.get("type")
                name = node.get("name", "Untitled")
                if node_type == "url":
                    url = node.get("url", "")
                    if url and not url.startswith("javascript:"):
                        folder_name = folder or "Bookmarks bar"
                        results.append({
                            "id": f"bm_{hash(url)}",
                            "name": name,
                            "url": url,
                            "browser": browser_name.lower(),
                            "folder": folder_name,
                            "desc": f"★ {browser_name} Bookmark ({folder_name})",
                            "cat": "Bookmarks",
                            "icon": "globe",
                            "type": "search",
                            "action": "open_url",
                        })
                elif node_type == "folder":
                    subfolder = f"{folder}/{name}" if folder else name
                    for child in node.get("children", []):
                        traverse(child, subfolder)

            for _, root_node in roots.items():
                traverse(root_node)
        except Exception as e:
            print(f"BookmarksManager: Failed parsing {browser_name} bookmarks: {e}")

        return results

    def _load_all_bookmarks(self):
        if not self.is_opted_in():
            with self._lock:
                self.bookmarks = []
            return

        all_bm = []
        for browser_name, path in self._get_chromium_paths():
            bm_items = self._parse_chromium_json(browser_name, path)
            all_bm.extend(bm_items)

        # Deduplicate by URL
        seen_urls = set()
        unique_bm = []
        for b in all_bm:
            if b["url"] not in seen_urls:
                seen_urls.add(b["url"])
                unique_bm.append(b)

        with self._lock:
            self.bookmarks = unique_bm

    def search_bookmarks(self, query: str) -> List[Dict]:
        # Privacy Check
        if not self.is_opted_in():
            return [{
                "id": "bm_optin_hint",
                "name": "Enable Browser Bookmarks in Settings",
                "desc": "Bookmarks search is disabled by default for privacy. Click to open Settings.",
                "cat": "Bookmarks",
                "icon": "shield",
                "action": "settings",
                "score": 100
            }]

        with self._lock:
            items = list(self.bookmarks)

        if not items:
            self.refresh_bookmarks_async()

        clean_q = query.lower().strip()
        if not clean_q:
            return [{**b, "score": 100} for b in items[:30]]

        tokens = clean_q.split()
        matches = []

        for b in items:
            name_lower = b["name"].lower()
            url_lower = b["url"].lower()
            browser_lower = b.get("browser", "").lower()
            folder_lower = b.get("folder", "").lower()

            combined = f"{name_lower} {browser_lower} {url_lower} {folder_lower}"

            # Check if all tokens match anywhere in the bookmark's metadata
            if all(tok in combined for tok in tokens):
                score = 0
                
                # 1. Exact or prefix match on title
                if name_lower == clean_q:
                    score = 120
                elif name_lower.startswith(clean_q):
                    score = 100
                elif clean_q in name_lower:
                    score = 85
                
                # 2. Browser match (e.g. "brav", "brave", "edge", "chrome")
                elif any(browser_lower.startswith(tok) or tok in browser_lower for tok in tokens):
                    score = 90
                    # Additional boost if other tokens match the title
                    other_tokens = [tok for tok in tokens if not (browser_lower.startswith(tok) or tok in browser_lower)]
                    if other_tokens and any(tok in name_lower for tok in other_tokens):
                        score = 110

                # 3. URL match
                elif clean_q in url_lower:
                    score = 70
                else:
                    score = 60

                it = b.copy()
                it["score"] = score
                matches.append(it)

        matches.sort(key=lambda x: (-x["score"], x["name"].lower()))
        return matches[:35]
