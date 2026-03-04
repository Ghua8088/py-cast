import os
import re
import math
import threading
import requests
from pathlib import Path
from typing import List, Dict
from src.utils.icon_handler import get_icon_url


class Searcher:
    def __init__(self, bite_instance):
        self.bite = bite_instance
        self.platform = bite_instance.platform
        
        # Semantic Intent Map (Natural Language to Action IDs)
        self.SEMANTIC_MAP = {
            "trash": ["empty_trash", "recycle", "garbage", "waste", "clean"],
            "restart": ["restart_explorer", "reboot", "refresh", "respawn"],
            "mute": ["mute", "silent", "quiet", "volume", "stfu"],
            "vol_up": ["volume up", "louder", "boost", "turn it up"],
            "vol_down": ["volume down", "quieter", "soften", "turn it down"],
            "ip": ["external ip", "my address", "network", "internet address"],
            "wf_folder": ["workflow folder", "scripts", "tools", "open scripts"],
            "settings": ["config", "preferences", "options", "control panel"],
            "sleep": ["hibernate", "suspend", "nap"],
            "lock": ["secure", "away", "logout"]
        }
        
        # Real-time Currency Cache
        self.currency_rates = {"usd": 1.0, "eur": 1.05, "gbp": 1.25} 
        threading.Thread(target=self._update_currency_rates, daemon=True).start()

    def _update_currency_rates(self):
        """Fetches real-time exchange rates in the background."""
        try:
            # Using a public API (exchange-rate-api is generally free/no-auth for basic use)
            url = "https://api.exchangerate-api.com/v4/latest/USD"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                rates = data.get("rates", {})
                if rates:
                    # Normalize to lowercase and update our cache
                    new_rates = {k.lower(): v for k, v in rates.items()}
                    self.currency_rates.update(new_rates)
                    print(f"Bite Engine: Refreshed {len(new_rates)} live currency rates.")
        except Exception as e:
            print(f"Bite Engine: Currency update failed (Offline fallback active): {e}")

    def _fuzzy_match(self, query: str, target: str) -> int:
        """Returns a score from 0-100 for fuzzy matching."""
        if not query: return 0
        query, target = query.lower(), target.lower()
        if query == target: return 100
        if target.startswith(query): return 90
        if " " + query in target: return 85
        
        # Simple fuzzy jump match (e.g., 'vsc' matches 'Visual Studio Code')
        # Check if all chars in query appear in target in order
        it = iter(target)
        if all(c in it for c in query):
            # Acronym check (e.g. 'vsc')
            words = target.split()
            acronym = "".join(w[0] for w in words if w)
            if acronym.startswith(query):
                return 80
            return 40
        return 0

    def get_results(self, query: str) -> List[Dict]:
        query = query.lower().strip()
        # --- Universal Alias Expansion ---
        query = self.bite.resolve_aliases(query)
        
        pinned_ids = self.bite.user_data.get("pins", [])

        # 0. The "Ghost" Intent (Proactive suggestions for empty query)
        if query == "":
            brain_preds = self.bite.brain.predict()
            ghost_results = []
            
            # Pool all possible items to find matches for predicted IDs
            # We look in shortcuts, installed apps, base registry, and workflows
            all_pool = (self.bite.user_data.get("shortcuts", []) + 
                        self.bite.installed_apps + 
                        self.bite.base_registry + 
                        self.bite.workflows)
            pool_map = {it["id"]: it for it in all_pool}
            
            for pred in brain_preds:
                iid = pred["id"]
                if iid in pool_map:
                    it = pool_map[iid].copy()
                    # High activation score for empty state
                    it["score"] = 1000 + int(pred["score"]) 
                    it["cat"] = f"★ {it.get('cat', 'Suggested')}"
                    it["desc"] = f"Bite Brain predicted your intent"
                    ghost_results.append(it)
            
            if ghost_results:
                return ghost_results[:5]

        # 1. Registry & Shortcuts
        registry_matches = self._match_registry(query, pinned_ids)
        for r in registry_matches:
            if query:
                fuzz = self._fuzzy_match(query, r["name"])
                r["score"] = max(r.get("score", 0), fuzz)

        # 2. Apps
        app_matches = self._match_apps(
            query, pinned_ids, [r["name"] for r in registry_matches]
        )
        for a in app_matches:
            if query:
                fuzz = self._fuzzy_match(query, a["name"])
                a["score"] = max(a.get("score", 0), fuzz)

        # 3. Files
        file_matches = self._search_files(query) if query else []
        for f in file_matches:
            f_tags = f.get("tags") or ""
            if query and query in f["name"].lower():
                f["score"] = 60 if f["name"].lower().startswith(query) else 20
            elif query and any(t.strip() == query for t in f_tags.split(",")):
                # Boost for exact tag match (e.g. searching 'green' find green images)
                f["score"] = 95
                f["learned"] = True # Highlight it
                f["cat"] = "Semantic Search"
            else:
                f["score"] = 10

        # Semantic Intent Boosting
        if query:
            for action_id, phrases in self.SEMANTIC_MAP.items():
                if any(p in query for p in phrases):
                    # Boost matching registry items
                    for item in registry_matches:
                        if item.get("id") == action_id or action_id in item.get("action", ""):
                            item["score"] = item.get("score", 0) + 200
                            item["learned"] = True
                            item["desc"] = f"Intent Match: '{query}'"

        # 4. Clipboard History (Searchable & Persistent)
        clip_matches = []
        is_clip_search = query.startswith("clip")
        
        if is_clip_search or (len(query) > 2):
            search_body = query[4:].strip() if is_clip_search else query
            for c in self.bite.clipboard_history:
                content = c.get("content", "")
                if not search_body or search_body.lower() in content.lower():
                    clip_matches.append({
                        "id": f"clip_{hash(content)}",
                        "name": f"Clip: {content[:50].strip()}...",
                        "desc": f"Copied at {c.get('time', 'Unknown')} on {c.get('date', 'Today')}",
                        "content": content,
                        "cat": "Clipboard",
                        "icon": "clipboard",
                        "action": "paste",
                        "score": 90 if search_body and search_body.lower() in content.lower() else 40
                    })
        
        # 5. Calculator
        math_results = self._match_math(query)

        # 6. Terminal Commands
        term_matches = self._match_terminal(query)

        # 6b. Process Manager
        proc_matches = self._match_processes(query)

        # 6c. Port Manager
        port_matches = self._match_ports(query)

        # 6d. Developer Tools (Hash, Base64, UUID)
        dev_matches = self._match_dev_tools(query)

        # 7. Secure Env Vault (Security & DX)
        vault_matches = []
        if query.startswith("env:"):
            target = query[4:].strip()
            vault = self.bite.user_data.get("env_vault", {})
            if not target:
                vault_matches.append({
                    "id": "vault_hint", "name": "Secure Env Vault", "desc": "Type 'env: [key]' to copy secret (e.g. env: OPENAI_API_KEY)",
                    "cat": "Security", "icon": "lock", "score": 100
                })
            else:
                for k, v in vault.items():
                    if target.lower() in k.lower():
                        vault_matches.append({
                            "id": f"vault_{k}", "name": f"Copy {k}", "content": v,
                            "desc": "•••••••• (Secure storage)", "cat": "Security",
                            "icon": "shield-check", "action": "paste", "score": 100
                        })

        # 8. Snippets
        snippet_matches = []
        for snip in self.bite.user_data.get("snippets", []):
            name = snip.get("name") or ""
            content = snip.get("content") or ""
            if (
                not query
                or query in name.lower()
                or query in content.lower()
            ):
                it = snip.copy()
                it.update({"cat": "Snippets", "icon": "scissors", "action": "paste"})
                it["score"] = 90 if query and query in name.lower() else 40
                snippet_matches.append(it)

        # 7. Workflows
        workflow_matches = []
        for wf in self.bite.workflows:
            name = wf.get("name") or "Unknown Workflow"
            name_lower = name.lower()
            if not query:
                workflow_matches.append(wf)
                continue
            if query in name_lower:
                it = wf.copy()
                it["score"] = 85 if name_lower.startswith(query) else 45
                workflow_matches.append(it)

        # 8. Plugins
        plugin_results = self.bite.plugins.get_plugin_results(query) if query else []

        # 9. Smart Alias Suggestions (Dynamic & Static)
        alias_matches = []
        if query:
            # Combine both alias stores
            all_aliases = self.bite.user_data.get("aliases", {}).copy()
            path_aliases = self.bite.user_data.get("path_aliases", {})
            all_aliases.update(path_aliases)
            
            clean_q = query.lstrip("@")
            for alias_name, target_path in all_aliases.items():
                clean_name = alias_name.lstrip("@")
                if clean_name.lower().startswith(clean_q.lower()):
                    display_name = f"@{clean_name}"
                    alias_matches.append({
                        "id": f"alias_hint_{clean_name}",
                        "name": display_name,
                        "desc": f"Smart Alias for {target_path}",
                        "cat": "Aliases",
                        "icon": "folder",
                        "type": "term_autofill",
                        "new_query": f"{display_name}\\",
                        "score": 100,
                        "learned": True
                    })

        all_res = (
            math_results
            + registry_matches
            + app_matches
            + file_matches
            + clip_matches[:5]
            + term_matches
            + proc_matches
            + port_matches
            + dev_matches
            + snippet_matches
            + workflow_matches
            + plugin_results
            + alias_matches
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
                        "cat": "Fallback",
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

        # Custom Prefixes
        is_wf_search = query.lower().startswith("wf:") or query.lower().startswith("workflow:")
        if is_wf_search:
            # Strip prefix
            prefix = "wf:" if query.lower().startswith("wf:") else "workflow:"
            wf_query = query[len(prefix):].strip().lower()
            
            wf_matches = []
            for wf in self.bite.workflows:
                if not wf_query or wf_query in wf["name"].lower():
                    it = wf.copy()
                    it["score"] = 100 if wf_query and wf["name"].lower().startswith(wf_query) else 50
                    wf_matches.append(it)
            return sorted(wf_matches, key=lambda x: -x["score"])

        # Mnemonic Boosting (Quicksilver style)
        q_clean = query.lower().strip()
        learned = self.bite.user_data.get("mnemonics", {}).get(q_clean, {})
        if learned:
            for res in all_res:
                rid = res.get("id")
                if rid in learned:
                    # Boost significantly based on selection count
                    res["score"] = res.get("score", 0) + 500 + (learned[rid] * 10)
                    res["learned"] = True

        # 9. Neural Contextual Boosting (The "Bite Brain")
        predictions = self.bite.brain.predict()
        if predictions:
            pred_ids = {p["id"]: p["score"] for p in predictions}
            for item in others:
                iid = item.get("id")
                if iid in pred_ids:
                    # Boost by the brain's confidence score
                    item["score"] = item.get("score", 0) + 150 + int(pred_ids[iid])
                    item["desc"] = f"★ Pattern Match: {item.get('desc')}"
                    item["learned"] = True
        
        # 10. Manual Static Fallbacks (For new users)
        active_ctx = self.bite.active_context
        if active_ctx:
            ctx_title = active_ctx.get("title", "").lower()
            ctx_proc = active_ctx.get("process", "").lower()
            for item in others:
                if ("chrome" in ctx_proc or "firefox" in ctx_proc) and item.get("cat") == "Search":
                    item["score"] = item.get("score", 0) + 50
                elif ("code" in ctx_proc) and item.get("cat") in ["Workflows", "Tools"]:
                    item["score"] = item.get("score", 0) + 50

        cat_map = {
            "Aliases": -100,
            "Pinned Favorites": -90,
            "Recents": -80,    # Recents should be high priority
            "Workflows": -10,
            "Files": 0,        # Files should be ABOVE generic apps/tools when searching paths
            "Productivity": 5,
            "Calc": 6,
            "Apps": 10,
            "System": 20,
            "Custom": 25,
            "Tools": 30,
            "Search": 40,
            "Web": 45,
            "Fallback": 100,   # Google Fallback always at the bottom
            "Help": 200,
            "Clipboard": 210,
        }
        others.sort(
            key=lambda x: (
                not x.get("learned", False),  # Learned items ALWAYS first
                cat_map.get(x.get("cat"), 50),
                -x.get("score", 0),
                x.get("name", "").lower(),
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
            name = it.get("name") or it.get("id") or "Unknown"
            kind_id = it.get("id") or "unknown"
            name_lower = name.lower()
            kid = kind_id.lower()

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
        cmd = query[2:].lstrip()
        
        # Expanded command for internal logic
        expanded_cmd = self.bite.resolve_aliases(cmd)

        if not cmd:
              return [{
                  "id": "term_hint", "name": "Terminal Mode", "desc": "Type or paste a path to browse (e.g. 't: C:\\')",
                  "cat": "Terminal", "icon": "terminal", "score": 100
              }]
        
        results = []
        
        # 1. Direct command execution result
        results.append({
            "id": "run_term", "name": f"> {cmd}", "desc": f"Run expanded: {expanded_cmd}",
            "cat": "Terminal", "icon": "terminal", "action": "run_term_cmd", "cmd": expanded_cmd, "score": 100
        })

        # 2. Path Browsing & Autofill
        # Determine if we are looking for a directory listing or a file search
        path_query = cmd.strip("\"'")
        
        is_dir_query = False
        try:
            p = Path(path_query)
            # If path ends with slash or is a drive like 'C:', trigger directory listing
            if path_query.endswith(("\\", "/")) or (len(path_query) == 2 and path_query[1] == ":"):
                is_dir_query = True
                search_root = p if p.is_dir() else p.parent
                search_name = "" # Force empty to list all children
                
                if search_root.exists() and search_root.is_dir():
                    try:
                        count = 0
                        for entry in os.scandir(search_root):
                            if count > 15: break
                            
                            # Ignore hidden items in directory listing
                            if entry.name.startswith("."):
                                continue

                            full_path = entry.path
                            results.append({
                                "id": f"term_browse_{hash(full_path)}",
                                "name": f"> {entry.name}" + ("\\" if entry.is_dir() else ""),
                                "path": full_path,
                                "is_dir": entry.is_dir(),
                                "desc": f"Autofill: {full_path}",
                                "cat": "Terminal",
                                "icon": get_icon_url(self.bite, full_path, force=True) or ("folder" if entry.is_dir() else "file"),
                                "type": "term_autofill",
                                "new_query": f"t: {full_path}" + ("\\" if entry.is_dir() else ""),
                                "score": 95
                            })
                            count += 1
                    except PermissionError: pass
            elif "\\" in path_query or "/" in path_query:
                # Partial path completion: ONLY list files that START with the last part (NO FUZZY)
                search_root = p.parent
                search_name = p.name.lower()
                
                if search_root.exists() and search_root.is_dir():
                    try:
                        count = 0
                        for entry in os.scandir(search_root):
                            if count > 10: break
                            
                            # Ignore hidden items unless searching for them
                            if entry.name.startswith(".") and not search_name.startswith("."):
                                continue

                            if entry.name.lower().startswith(search_name):
                                full_path = entry.path
                                results.append({
                                    "id": f"term_fill_{hash(full_path)}",
                                    "name": f"> {entry.name}" + ("\\" if entry.is_dir() else ""),
                                    "path": full_path,
                                    "is_dir": entry.is_dir(),
                                    "desc": f"Autofill: {full_path}",
                                    "cat": "Terminal",
                                    "icon": get_icon_url(self.bite, full_path, force=True) or ("folder" if entry.is_dir() else "file"),
                                    "type": "term_autofill",
                                    "new_query": f"t: {full_path}" + ("\\" if entry.is_dir() else ""),
                                    "score": 90
                                })
                                count += 1
                    except PermissionError: pass
        except Exception: pass

        return results
        
        return results

    def _match_processes(self, query):
        if not query.startswith("kill "):
            return []
            
        term = query[5:].strip().lower()
        if not term:
            return [{
                "id": "proc_hint", "name": "Kill Process", "desc": "Type process name to kill (e.g., 'kill node')",
                "cat": "System", "icon": "zap", "score": 100
            }]

        import psutil
        results = []
        try:
            for p in psutil.process_iter(['pid', 'name', 'memory_info']):
                try:
                    name = p.info['name']
                    if name and term in name.lower():
                        mem_mb = p.info['memory_info'].rss / (1024 * 1024)
                        results.append({
                            "id": f"kill_{p.info['pid']}",
                            "name": f"Kill {name}",
                            "desc": f"PID: {p.info['pid']} - RAM: {mem_mb:.1f} MB",
                            "cat": "System",
                            "icon": "zap",
                            "action": "kill_pid",
                            "pid": p.info['pid'],
                            "score": 95 if name.lower() == term else 85
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
        except:
            pass
            
        return sorted(results, key=lambda x: -x["score"])[:15]

    def _match_ports(self, query):
        if not query.startswith("port"):
            return []
            
        term = query[4:].strip()
        import psutil
        
        # 1. No port specified -> Show all listening ports (Security Audit)
        if not term:
            results = []
            try:
                for conn in psutil.net_connections(kind='inet'):
                    if conn.status == psutil.CONN_LISTEN:
                        try:
                            p = psutil.Process(conn.pid)
                            results.append({
                                "id": f"listen_{conn.laddr.port}",
                                "name": f"Listening: {conn.laddr.port} ({p.name()})",
                                "desc": f"PID {conn.pid} | Click to copy/explore",
                                "cat": "Security", "icon": "shield", "action": "paste", "content": str(conn.laddr.port),
                                "score": 90
                            })
                        except: pass
            except: pass
            return results or [{"id":"no_ports","name":"No Active Ports","desc":"Zero open listening ports found.","cat":"Security","icon":"shield-check","score":100}]

        if not term.isdigit():
            return []

        target_port = int(term)
        import psutil
        results = []
        try:
            for conn in psutil.net_connections(kind='inet'):
                if conn.laddr and conn.laddr.port == target_port and conn.status == psutil.CONN_LISTEN:
                    try:
                        p = psutil.Process(conn.pid)
                        name = p.name()
                        results.append({
                            "id": f"kill_port_{conn.pid}",
                            "name": f"Free Port {target_port} ({name})",
                            "desc": f"Kill {name} (PID: {conn.pid}) using port {target_port}",
                            "cat": "System",
                            "icon": "zap",
                            "action": "kill_pid",
                            "pid": conn.pid,
                            "score": 100
                        })
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        pass
        except:
            pass
            
        if not results:
             return [{
                "id": "port_empty", "name": f"Port {target_port} is free", "desc": "No process is listening on this port",
                "cat": "System", "icon": "check", "score": 100
            }]

        return results

    def _match_dev_tools(self, query):
        if not query: return []
        results = []
        q = query.lower()

        # UUID Generator
        if q.startswith("uuid"):
            import uuid
            new_uuid = str(uuid.uuid4())
            results.append({
                "id": "uuid_gen", "name": new_uuid, "desc": "Random UUID v4",
                "content": new_uuid, "cat": "Custom", "icon": "cpu", "action": "paste", "score": 100
            })

        # Hash Generator
        if q.startswith("hash ") and len(query) > 5:
            text = query[5:]
            import hashlib
            h_md5 = hashlib.md5(text.encode()).hexdigest()
            h_sha256 = hashlib.sha256(text.encode()).hexdigest()
            
            results.append({
                "id": "hash_sha256", "name": h_sha256, "desc": f"SHA256 Hash of '{text}'",
                "content": h_sha256, "cat": "Dev", "icon": "lock", "action": "paste", "score": 100
            })
            results.append({
                "id": "hash_md5", "name": h_md5, "desc": f"MD5 Hash of '{text}'",
                "content": h_md5, "cat": "Dev", "icon": "lock", "action": "paste", "score": 95
            })

        # Base64 Encode / Decode
        if q.startswith("b64 ") and len(query) > 4:
            text = query[4:]
            import base64
            # Try decode first, if it fails or is short, offer encode
            try:
                decoded = base64.b64decode(text).decode('utf-8')
                results.append({
                    "id": "b64_dec", "name": decoded, "desc": "Base64 Decoded",
                    "content": decoded, "cat": "Dev", "icon": "terminal", "action": "paste", "score": 100
                })
            except:
                pass
            
            encoded = base64.b64encode(text.encode('utf-8')).decode('utf-8')
            results.append({
                "id": "b64_enc", "name": encoded, "desc": "Base64 Encoded",
                "content": encoded, "cat": "Dev", "icon": "terminal", "action": "paste", "score": 90
            })
        
        # Timer: timer: 5m, timer: 10, t: 30s
        timer_q = None
        if q.startswith("timer:"):
            timer_q = q[6:].strip()
        elif q.startswith("t:") and any(c.isdigit() for c in q[2:]):
            timer_q = q[2:].strip()
            # Ensure it's not a path like t: c:\
            if ":" in timer_q and not timer_q[1] == ":": pass 
            elif timer_q.startswith(("/", "\\")): timer_q = None

        if timer_q:
            match = re.search(r'(\d+)\s*([msh])?', timer_q)
            if match:
                val = int(match.group(1))
                unit = match.group(2) or 'm' # Default to minutes
                unit_name = "minutes" if unit == 'm' else "seconds" if unit == 's' else "hours"
                seconds = val * 60 if unit == 'm' else val if unit == 's' else val * 3600
                
                results.append({
                    "id": f"timer_{seconds}",
                    "name": f"Set Timer: {val} {unit_name}",
                    "desc": f"Start countdown for {val} {unit_name} ({seconds}s)",
                    "cat": "Tools",
                    "icon": "alarm-clock",
                    "action": "start_timer",
                    "seconds": seconds,
                    "score": 100
                })

        # Color Preview
        if (q.startswith("#") and (len(q) == 4 or len(q) == 7)) or q.startswith("rgb("):
             results.append({
                "id": "color_preview", "name": f"Color: {q.upper()}", "desc": "Click to copy HEX",
                "content": q, "cat": "Dev", "icon": "palette", "action": "paste", "score": 100,
                "preview_color": q
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
            # Unit Conversion Support (e.g., "10km to miles")
            unit_match = re.match(r"(\d+\.?\d*)\s*([a-zA-Z]+)\s+(?:to|in)\s+([a-zA-Z]+)", query)
            if unit_match:
                val, from_unit, to_unit = unit_match.groups()
                res = self._convert_units(float(val), from_unit, to_unit)
                if res:
                    return [{
                        "id": "unit_res", "name": f"= {res}", "content": res,
                        "desc": f"{val} {from_unit} in {to_unit}", "cat": "Calc",
                        "icon": "zap", "action": "paste", "score": 100,
                    }]

            # Math Safety & Functions
            allowed_chars = set("0123456789+-*/().%^ abcdefghijklmnopqrstuvwxyz")
            if (
                query 
                and set(query.lower()).issubset(allowed_chars) 
                and any(c.isdigit() for c in query)
            ):
                # Basic math safety (eval is okay here because of restricted context)
                safe_dict = {
                    "__builtins__": None,
                    "abs": abs, "pow": pow, "round": round, "sqrt": math.sqrt,
                    "sin": math.sin, "cos": math.cos, "tan": math.tan,
                    "log": math.log, "log10": math.log10, "exp": math.exp,
                    "pi": math.pi, "e": math.e, "rad": math.radians, "deg": math.degrees
                }
                
                query_prep = query.replace("^", "**").lower()
                # If using trig functions, user likely expects radians but let's be safe
                res = eval(query_prep, safe_dict)
                if isinstance(res, (int, float)):
                    formatted_res = f"{res:,}" if isinstance(res, int) else f"{res:g}"
                    return [
                        {
                            "id": "calc_res",
                            "name": f"= {formatted_res}",
                            "content": str(res),
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

    def _convert_units(self, val, f, t):
        f, t = f.lower().strip(), t.lower().strip()
        
        # Unit Alias Map
        aliases = {
            "km": "km", "kilometers": "km", "kilometer": "km",
            "m": "m", "meters": "m", "meter": "m",
            "cm": "cm", "centimeters": "cm", "centimeter": "cm",
            "mm": "mm", "millimeters": "mm", "millimeter": "mm",
            "mi": "mi", "miles": "mi", "mile": "mi",
            "ft": "ft", "feet": "ft", "foot": "ft",
            "in": "in", "inches": "in", "inch": "in",
            "yd": "yd", "yards": "yd", "yard": "yd",
            "kg": "kg", "kilograms": "kg", "kilogram": "kg",
            "g": "g", "grams": "g", "gram": "g",
            "lb": "lb", "pounds": "lb", "pound": "lb", "lbs": "lb",
            "oz": "oz", "ounces": "oz", "ounce": "oz",
            "kmh": "kmh", "km/h": "kmh", "kph": "kmh",
            "mph": "mph", "miles/hour": "mph",
            "usd": "usd", "dollar": "usd", "dollars": "usd",
            "eur": "eur", "euro": "eur", "euros": "eur",
            "gbp": "gbp", "pound_sterling": "gbp",
        }
        
        f = aliases.get(f, f)
        t = aliases.get(t, t)

        # Base Scales (grouped by category)
        units = {
            "km": 1000, "m": 1, "cm": 0.01, "mm": 0.001, "mi": 1609.34, "ft": 0.3048, "in": 0.0254, "yd": 0.9144,
            "kg": 1000, "g": 1, "mg": 0.001, "lb": 453.592, "oz": 28.3495,
            "kmh": 1, "mph": 1.60934,
        }
        
        # Inject real-time currency rates into the unit map
        # Note: These are all relative to USD (base 1)
        units.update(self.currency_rates)
        
        # Temperature
        if f in ["c", "celsius"] and t in ["f", "fahrenheit"]:
            return f"{(val * 9/5) + 32:g} °F"
        if f in ["f", "fahrenheit"] and t in ["c", "celsius"]:
            return f"{(val - 32) * 5/9:g} °C"

        if f in units and t in units:
            # Using real-time ratios (Base USD)
            res = (val / units[f]) * units[t] if f in self.currency_rates else (val * units[f]) / units[t]
            
            # Special formatting for currency
            if t in self.currency_rates:
                return f"{res:,.2f} {t.upper()}"
                
            return f"{res:g} {t}"
        
        return None

    def _search_files(self, query: str) -> List[Dict]:
        results = []
        if len(query) < 2:
            return []

        resolved_query = query
        if query.startswith("@"):
            raw_aliases = self.bite.user_data.get("aliases", {}).copy()
            path_aliases = self.bite.user_data.get("path_aliases", {})
            raw_aliases.update(path_aliases)
            
            # Normalize keys to be lowercase and without @ prefix
            aliases = { (k[1:] if k.startswith("@") else k).lower(): v for k, v in raw_aliases.items() }
            
            parts = query.replace("/", "\\").split("\\", 1)
            alias_name = parts[0][1:].lower()
            if alias_name in aliases:
                resolved_dir = aliases[alias_name]
                if len(parts) > 1:
                    resolved_query = os.path.join(resolved_dir, parts[1])
                else:
                    resolved_query = resolved_dir + os.sep
            else:
                # Provide hints for available aliases
                matching = [k for k in aliases if k.startswith(alias_name)]
                for m in matching:
                    results.append({
                        "id": f"alias_hint_{m}",
                        "name": f"@{m}",
                        "desc": f"Smart Alias for {aliases[m]}",
                        "cat": "Aliases",
                        "icon": "folder",
                        "type": "term_autofill",
                        "new_query": f"@{m}\\",
                        "score": 100
                    })
                return results

        # Path Navigation
        if (
            (len(resolved_query) >= 2 and resolved_query[1] == ":")
            or resolved_query.startswith("/")
            or resolved_query.startswith("\\")
        ):
            target_dir = resolved_query if os.path.isdir(resolved_query) else os.path.dirname(resolved_query)
            partial = os.path.basename(resolved_query) if not os.path.isdir(resolved_query) else ""
            
            if os.path.isdir(target_dir):
                target_entries = []
                try:
                    with os.scandir(target_dir) as entries:
                        for entry in entries:
                            name_lower = entry.name.lower()
                            partial_lower = partial.lower()
                            
                            # Ignore hidden items unless explicitly searching for them
                            if entry.name.startswith(".") and not partial_lower.startswith("."):
                                continue
                                
                            score = 0
                            if name_lower.startswith(partial_lower):
                                score = 100
                            elif partial_lower in name_lower:
                                # Keep 'contains' but give it a much lower priority
                                score = 20
                                
                            if score > 0:
                                res = self.bite._create_file_result(entry, "")
                                res["score"] = score
                                target_entries.append(res)
                                if len(target_entries) > 100:
                                    break
                except:
                    pass
                
                # Internal sort for the path navigation part to ensure startswith wins immediately
                target_entries.sort(key=lambda x: (-x["score"], x["name"].lower()))
                return target_entries
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
                        MockEntry(item["path"], item["name"], item["is_dir"]), "", tags=item.get("tags")
                    )
                )
        except Exception as e:
            print(f"Search index error: {e}")

        return results
