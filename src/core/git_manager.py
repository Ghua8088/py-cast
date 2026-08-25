import os
import re
import threading
from pathlib import Path
from typing import List, Dict, Optional


class GitManager:
    """
    Lightweight, zero-dependency Git repository scanner and parser.
    Directly reads .git/HEAD and .git/config without launching external subprocesses.
    """

    def __init__(self, bite_instance):
        self.bite = bite_instance
        self.repos: List[Dict] = []
        self._lock = threading.Lock()
        self._cache_time = 0

    def get_search_roots(self) -> List[str]:
        roots = []
        # 1. Custom user-configured project roots from settings
        custom_roots = self.bite.user_data.get("settings", {}).get("project_roots", [])
        for r in custom_roots:
            if os.path.exists(r) and r not in roots:
                roots.append(r)

        # 2. Universal user home developer directories
        home = Path.home()
        standard_dirs = [
            "projects", "Projects", "source", "repos", "workspace", "Workspace",
            "Developer", "dev", "Dev", "Documents", "Desktop"
        ]
        for d in standard_dirs:
            p = home / d
            if p.exists() and str(p) not in roots:
                roots.append(str(p))

        # 3. Dynamic drive root scan for standard dev folders on all connected drives (Windows)
        if self.bite.platform == "Windows":
            try:
                import string
                from ctypes import windll
                bitmask = windll.kernel32.GetLogicalDrives()
                for letter in string.ascii_uppercase:
                    if bitmask & 1:
                        drive_path = f"{letter}:\\"
                        for sub in ["projects", "repos", "source", "workspace", "dev"]:
                            candidate = os.path.join(drive_path, sub)
                            if os.path.exists(candidate) and candidate not in roots:
                                roots.append(candidate)
                    bitmask >>= 1
            except Exception:
                pass

        return roots

    def scan_repos(self, max_depth: int = 3) -> List[Dict]:
        """Scans directories for .git repositories with shallow depth traversal."""
        discovered = []
        roots = self.get_search_roots()

        for root in roots:
            if not os.path.isdir(root):
                continue
            
            try:
                # Check if root itself is a git repo
                if os.path.exists(os.path.join(root, ".git")):
                    repo_info = self._parse_repo(root)
                    if repo_info:
                        discovered.append(repo_info)
                    continue

                for dirpath, dirnames, _ in os.walk(root):
                    # Compute relative depth
                    rel_path = os.path.relpath(dirpath, root)
                    depth = 0 if rel_path == "." else len(Path(rel_path).parts)
                    
                    if ".git" in dirnames:
                        repo_info = self._parse_repo(dirpath)
                        if repo_info:
                            discovered.append(repo_info)
                        # Don't descend into subdirectories of a git repo (except submodules if needed)
                        dirnames.clear()
                        continue

                    # Don't descend into junk folders
                    dirnames[:] = [
                        d for d in dirnames 
                        if not d.startswith(".") 
                        and d.lower() not in {"node_modules", "dist", "build", "env", "venv", "__pycache__", "target", "vendor"}
                    ]

                    if depth >= max_depth:
                        dirnames.clear()
            except Exception as e:
                print(f"GitManager scan error at {root}: {e}")

        with self._lock:
            self.repos = discovered

        return discovered

    def _parse_repo(self, repo_path: str) -> Optional[Dict]:
        """Parses branch name, remote URL, and repo name directly from .git metadata."""
        try:
            git_dir = os.path.join(repo_path, ".git")
            if os.path.isfile(git_dir):
                # Git submodule / worktree .git file pointer
                with open(git_dir, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read().strip()
                    if content.startswith("gitdir:"):
                        git_dir = os.path.abspath(os.path.join(repo_path, content.split("gitdir:", 1)[1].strip()))

            if not os.path.isdir(git_dir):
                return None

            name = os.path.basename(os.path.abspath(repo_path))

            # 1. Parse active branch from .git/HEAD
            branch = "HEAD"
            head_file = os.path.join(git_dir, "HEAD")
            if os.path.exists(head_file):
                with open(head_file, "r", encoding="utf-8", errors="ignore") as f:
                    head_content = f.read().strip()
                    if head_content.startswith("ref: refs/heads/"):
                        branch = head_content.replace("ref: refs/heads/", "")
                    elif len(head_content) == 40:
                        branch = head_content[:7]  # Detached commit hash

            # 2. Parse remote origin URL from .git/config
            remote_url = ""
            github_url = ""
            config_file = os.path.join(git_dir, "config")
            if os.path.exists(config_file):
                with open(config_file, "r", encoding="utf-8", errors="ignore") as f:
                    config_content = f.read()
                    # Look for [remote "origin"] section URL
                    match = re.search(r'\[remote\s+"origin"\][^\[]*url\s*=\s*(.*)', config_content, re.IGNORECASE)
                    if match:
                        remote_url = match.group(1).strip()
                        # Convert git@github.com:user/repo.git to https://github.com/user/repo
                        if remote_url.startswith("git@"):
                            clean = remote_url.replace(":", "/").replace("git@", "https://")
                            if clean.endswith(".git"):
                                clean = clean[:-4]
                            github_url = clean
                        elif remote_url.startswith("http"):
                            clean = remote_url
                            if clean.endswith(".git"):
                                clean = clean[:-4]
                            github_url = clean

            # 3. Check clean/dirty state indicator via .git/index timestamp comparison
            is_dirty = False
            index_file = os.path.join(git_dir, "index")
            if os.path.exists(index_file):
                # Quick proxy: if repo folder was touched much later than index
                try:
                    index_mtime = os.path.getmtime(index_file)
                    folder_mtime = os.path.getmtime(repo_path)
                    if folder_mtime - index_mtime > 300:
                        is_dirty = True
                except:
                    pass

            return {
                "id": f"repo_{hash(repo_path)}",
                "name": name,
                "path": repo_path,
                "branch": branch,
                "remote_url": remote_url,
                "github_url": github_url,
                "is_dirty": is_dirty,
                "is_dir": True,
                "desc": f"{branch} • {'modified' if is_dirty else 'clean'} • {repo_path}",
                "cat": "Git Repositories",
                "icon": "github" if "github" in remote_url.lower() else "folder",
                "type": "git_repo",
                "action": "open_ide",
            }
        except Exception:
            return None

    def search_repos(self, query: str) -> List[Dict]:
        """Searches cached repos, refreshing asynchronously if empty."""
        with self._lock:
            current_repos = list(self.repos)

        if not current_repos:
            # Trigger background scan
            threading.Thread(target=self.scan_repos, daemon=True).start()

        if not query:
            return [{**r, "score": 100} for r in current_repos[:25]]

        q = query.lower().strip()
        matches = []
        for r in current_repos:
            name_lower = r["name"].lower()
            branch_lower = r["branch"].lower()
            path_lower = r["path"].lower()

            score = 0
            if name_lower == q:
                score = 100
            elif name_lower.startswith(q):
                score = 90
            elif q in name_lower:
                score = 75
            elif q in branch_lower or q in path_lower:
                score = 50

            if score > 0:
                item = r.copy()
                item["score"] = score
                matches.append(item)

        matches.sort(key=lambda x: -x["score"])
        return matches
