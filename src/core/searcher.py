import os
import re
from pathlib import Path
from typing import List, Dict
from src.utils.icon_handler import get_icon_url


class Searcher:
    def __init__(self, bite_instance):
        self.bite = bite_instance
        self.platform = bite_instance.platform

    def get_results(self, query: str) -> List[Dict]:
        query = query.lower().strip()
        pinned_ids = self.bite.user_data.get("pins", [])

        # 1. Registry & Shortcuts
        registry_matches = self._match_registry(query, pinned_ids)

        # 2. Apps
        app_matches = self._match_apps(
            query, pinned_ids, [r["name"] for r in registry_matches]
        )

        # 3. Files
        file_matches = self._search_files(query) if query else []
        for f in file_matches:
            if query and query in f["name"].lower():
                f["score"] = 60 if f["name"].lower().startswith(query) else 20
            else:
                f["score"] = 10

        # 4. Clipboard
        clip_matches = []
        if "clip" in query or len(query) > 2:
            for c in self.bite.clipboard_history:
                if query in c["content"].lower() or "clip" in query:
                    clip_matches.append(
                        {
                            "id": f"clip_{hash(c['content'])}",
                            "name": f"Clip: {c['content'][:40]}...",
                            "content": c["content"],
                            "cat": "Clipboard",
                            "icon": "clipboard",
                            "action": "paste",
                        }
                    )

        # 5. Calculator
        math_results = self._match_math(query)

        # 6. Terminal Commands
        term_matches = self._match_terminal(query)

        # 7. Snippets
        snippet_matches = []
        for snip in self.bite.user_data.get("snippets", []):
            if (
                not query
                or query in snip["name"].lower()
                or query in snip["content"].lower()
            ):
                it = snip.copy()
                it.update({"cat": "Snippets", "icon": "scissors", "action": "paste"})
                it["score"] = 90 if query and query in snip["name"].lower() else 40
                snippet_matches.append(it)

        # 7. Workflows
        workflow_matches = []
        for wf in self.bite.workflows:
            name_lower = wf["name"].lower()
            if not query:
                workflow_matches.append(wf)
                continue
            if query in name_lower:
                it = wf.copy()
                it["score"] = 85 if name_lower.startswith(query) else 45
                workflow_matches.append(it)

        all_res = (
            math_results
            + registry_matches
            + app_matches
            + file_matches
            + clip_matches[:5]
            + term_matches
            + snippet_matches
            + workflow_matches
        )

        # Web Fallback
        has_exact = any(item.get("score", 0) >= 90 for item in all_res)
        if query and not has_exact and len(query) > 1:
            is_search_cmd = any(
                item.get("type") == "search" and query.startswith(item["id"])
                for item in registry_matches
            )
            if not is_search_cmd:
                all_res.append(
                    {
                        "id": "web_search",
                        "name": f"Search Web for '{query}'",
                        "type": "search",
                        "url": "https://google.com/search?q=",
                        "cat": "Search",
                        "icon": "search",
                        "score": 85,
                    }
                )

        pinned = [r for r in all_res if r.get("pinned")]
        others = [r for r in all_res if not r.get("pinned")]

        if not query:
            recents = []
            for rid in self.bite.recent_ids:
                if rid in pinned_ids:
                    continue
                match = next((x for x in all_res if x["id"] == rid), None)
                if match:
                    it = match.copy()
                    it["cat"] = "Recents"
                    recents.append(it)
            others = recents + others

        cat_map = {
            "System": -5,
            "Recents": -3,
            "Productivity": -2.5,
            "Workflows": -2,
            "Calc": -1,
            "Search": 0,
            "Web": 0.1,
            "Terminal": 0.5,
            "AI": 1,
            "Custom": 2,
            "Apps": 3,
            "Help": 4,
            "Files": 5,
            "Clipboard": 6,
        }
        others.sort(
            key=lambda x: (
                cat_map.get(x.get("cat"), 10),
                -x.get("score", 0),
                x.get("name", ""),
            )
        )

        return pinned + others[:40]

    def _match_registry(self, query, pinned_ids):
        matches = []
        full_registry = self.bite.base_registry + self.bite.user_data.get(
            "shortcuts", []
        )
        for item in full_registry:
            it = item.copy()
            it["pinned"] = it["id"] in pinned_ids
            name_lower = it["name"].lower()
            kid = it["id"].lower()

            score = -1
            if not query:
                score = 0
            elif query == kid or query == name_lower:
                score = 100
            elif name_lower.startswith(query):
                score = 80
            elif query.startswith(kid + " "):
                score = 90
            elif " " + query in name_lower or name_lower.startswith(query + " "):
                score = 90
            elif query in name_lower:
                score = 50
            elif query in it.get("desc", "").lower():
                score = 30

            if score >= 0:
                it["score"] = score
                matches.append(it)
        return matches

    def _match_terminal(self, query):
        if not query.startswith("t:"): return []
        cmd = query[2:].strip()
        if not cmd:
              return [{
                  "id": "term_hint", "name": "Terminal Mode", "desc": "Type a command to run in terminal",
                  "cat": "Terminal", "icon": "terminal", "score": 100
              }]
        
        # Path tabbing support: If the command looks like it might contain a path
        path_query = ""
        parts = cmd.split()
        if parts:
            last_part = parts[-1]
            if "\\" in last_part or "/" in last_part or (len(last_part) >= 2 and last_part[1] == ":"):
                path_query = last_part

        results = [{
            "id": "run_term", "name": f"> {cmd}", "desc": "Run in Terminal",
            "cat": "Terminal", "icon": "terminal", "action": "run_term_cmd", "cmd": cmd, "score": 100
        }]
        
        if path_query:
            path_results = self._search_files(path_query)
            for pr in path_results:
                # Transform file result into a terminal autofill result
                new_cmd = " ".join(parts[:-1]) + " " + pr["path"]
                results.append({
                    "id": f"term_path_{pr['id']}", "name": f"> {new_cmd}", "path": pr["path"], "is_dir": pr.get("is_dir"),
                    "desc": f"Autofill path: {pr['path']}", "cat": "Terminal", "icon": pr["icon"], "type": "term_autofill", "new_query": f"t: {new_cmd}", "score": 80
                })
        
        return results

    def _match_apps(self, query, pinned_ids, existing_names):
        matches = []
        for app in self.bite.installed_apps:
            name_lower = app["name"].lower()
            if not query:
                if app["id"] in pinned_ids:
                    it = app.copy()
                    it.update({"pinned": True, "score": 0})
                    matches.append(it)
                continue
            if query in name_lower and app["name"] not in existing_names:
                it = app.copy()
                it["pinned"] = it["id"] in pinned_ids
                it["score"] = (
                    95
                    if name_lower == query
                    else (75 if name_lower.startswith(query) else 40)
                )
                matches.append(it)
        return matches

    def _match_math(self, query):
        try:
            allowed = set("0123456789+-*/().% ")
            if (
                query
                and set(query).issubset(allowed)
                and any(c.isdigit() for c in query)
            ):
                if not query.strip().isdigit():
                    res = str(eval(query, {"__builtins__": None}))
                    return [
                        {
                            "id": "calc_res",
                            "name": f"= {res}",
                            "content": res,
                            "desc": f"Result of '{query}'",
                            "cat": "Calc",
                            "icon": "calculator",
                            "action": "paste",
                            "score": 100,
                        }
                    ]
        except:
            pass
        return []

    def _search_files(self, query: str) -> List[Dict]:
        results = []
        if len(query) < 2:
            return []

        # Path Navigation
        if (
            (len(query) >= 2 and query[1] == ":")
            or query.startswith("/")
            or query.startswith("\\")
        ):
            target_dir = query if os.path.isdir(query) else os.path.dirname(query)
            partial = os.path.basename(query) if not os.path.isdir(query) else ""
            if os.path.isdir(target_dir):
                try:
                    with os.scandir(target_dir) as entries:
                        for entry in entries:
                            if partial.lower() in entry.name.lower():
                                results.append(self.bite._create_file_result(entry, ""))
                                if len(results) > 50:
                                    break
                except:
                    pass
            return results

        # Index Search
        try:
            indexed_results = self.bite.indexer.search(query)
            for item in indexed_results:
                # Mock an entry-like object for _create_file_result
                class MockEntry:
                    def __init__(self, path, name, is_dir):
                        self.path = path
                        self.name = name
                        self._is_dir = is_dir

                    def is_dir(self):
                        return self._is_dir

                results.append(
                    self.bite._create_file_result(
                        MockEntry(item["path"], item["name"], item["is_dir"]), ""
                    )
                )
        except Exception as e:
            print(f"Search index error: {e}")

        return results
