import os
import sqlite3
import threading
import time
import platform
from pathlib import Path
from typing import List, Dict


class Indexer:
    def __init__(self, bite_instance):
        self.bite = bite_instance
        self.db_path = bite_instance.config_dir / "index.db"
        self.stop_event = threading.Event()
        self._conn = None
        self._init_db()

        self.exclude_dirs = {
            "windows", "program files", "program files (x86)", "appdata",
            "node_modules", ".git", ".svn", ".hg", "system volume information",
            "$recycle.bin", "recycler", "trash", ".trash", "tmp", "cache", "logs", 
            "private", "run", "dev", "proc", "sys", "boot", "snapshots"
        }
        self.exclude_exts = {
            ".pyc",
            ".pyo",
            ".pyd",
            ".obj",
            ".dll",
            ".exe",
            ".sys",
            ".tmp",
            ".log",
            ".bak",
            ".swp",
            ".class",
            ".metadata",
        }

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        # WAL mode for better concurrency
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")

        # Files table for metadata
        conn.execute("""
            CREATE TABLE IF NOT EXISTS files (
                path TEXT PRIMARY KEY,
                name TEXT,
                mtime REAL,
                is_dir INTEGER,
                last_seen REAL
            )
        """)

        # Migration: Add last_seen if missing
        try:
            cursor = conn.execute("PRAGMA table_info(files)")
            columns = [row[1] for row in cursor.fetchall()]
            if "last_seen" not in columns:
                conn.execute("ALTER TABLE files ADD COLUMN last_seen REAL")
                conn.commit()
                print("Bite Indexer: Migrated database to include 'last_seen'")
        except: pass

        conn.execute("""
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        conn.commit()

        # Purge data from excluded directories (e.g., Recycle Bin)
        try:
            trash_patterns = ["%$recycle.bin%", "%recycler%", "%trash%", "%appdata%", "%node_modules%"]
            for pattern in trash_patterns:
                # Need to use LOWER() for cross-platform case-insensitive purge
                conn.execute("DELETE FROM files WHERE LOWER(path) LIKE ?", (pattern,))
            conn.commit()
            print(f"Bite Indexer: Purged {len(trash_patterns)} categories of junk from DB.")
        except Exception as e:
            print(f"Bite Indexer: Purge error: {e}")

        # FTS5 table for fast searching
        try:
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS files_fts USING fts5(
                    name,
                    path UNINDEXED,
                    content='files',
                    content_rowid='rowid'
                )
            """)
        except sqlite3.OperationalError:
            # Fallback if FTS5 is not available (though it usually is in modern Python)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS files_fts (
                    name TEXT,
                    path TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_name ON files_fts(name)")

        # Triggers to keep FTS in sync
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS files_ai AFTER INSERT ON files BEGIN
                INSERT INTO files_fts(rowid, name) VALUES (new.rowid, new.name);
            END;
        """)
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS files_ad AFTER DELETE ON files BEGIN
                INSERT INTO files_fts(files_fts, rowid, name) VALUES('delete', old.rowid, old.name);
            END;
        """)
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS files_au AFTER UPDATE ON files BEGIN
                INSERT INTO files_fts(files_fts, rowid, name) VALUES('delete', old.rowid, old.name);
                INSERT INTO files_fts(rowid, name) VALUES (new.rowid, new.name);
            END;
        """)

        conn.commit()
        conn.close()

    def get_connection(self):
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def start_indexing(self):
        self.is_indexing = False
        threading.Thread(target=self._index_loop, daemon=True).start()

    def _index_loop(self):
        # Initial wait for app to stabilize
        time.sleep(5)

        while not self.stop_event.is_set():
            try:
                # Conservative Check: Only index if last scan was > 24 hours ago
                conn = sqlite3.connect(self.db_path)
                res = conn.execute("SELECT value FROM metadata WHERE key='last_full_scan'").fetchone()
                last_scan = float(res[0]) if res else 0
                conn.close()
                
                if time.time() - last_scan > (24 * 60 * 60):
                     self.is_indexing = True
                     self._run_indexing()
                     
                     # Update last scan time
                     conn = sqlite3.connect(self.db_path)
                     conn.execute("INSERT OR REPLACE INTO metadata (key, value) VALUES ('last_full_scan', ?)", (str(time.time()),))
                     conn.commit()
                     conn.close()
            except Exception as e:
                print(f"Indexing Error: {e}")
            finally:
                self.is_indexing = False

            # Check every hour if we need to run
            for _ in range(60 * 60):
                if self.stop_event.is_set():
                    break
                time.sleep(1)

    def _run_indexing(self):
        print("Bite Indexer: Starting background crawl...")
        start_time = time.time()

        # Priority Roots: User folders first
        priority_roots = [
            str(Path.home() / "Desktop"),
            str(Path.home() / "Documents"),
            str(Path.home() / "Downloads"),
            str(Path.home() / "Videos"),
            str(Path.home() / "Pictures"),
        ]
        
        system_roots = []
        if platform.system() == "Windows":
            system_roots = self.bite._get_drives()
        else:
            system_roots = ["/"]

        # Deduplicate and prioritize
        all_roots = []
        for r in priority_roots:
            if os.path.exists(r) and r not in all_roots:
                all_roots.append(r)
        
        for r in system_roots:
            if os.path.exists(r) and r not in all_roots:
                all_roots.append(r)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Performance tuning for the session
        cursor.execute("PRAGMA cache_size = -2000")  # 2MB cache

        batch = []
        count = 0
        current_scan_time = time.time()

        # Merged exclusions
        user_excludes = self.bite.user_data.get("settings", {}).get("excluded_folders", [])
        active_excludes = self.exclude_dirs.union(set(user_excludes))
        
        active_excludes.update({
            ".git", ".svn", ".vs", ".vscode", "__pycache__", 
            "node_modules", "dist", "build", "env", "venv", "AppData"
        })

        for root in all_roots:
            if self.stop_event.is_set():
                break
            
            for base, dirs, files in os.walk(root):
                if self.stop_event.is_set():
                    break
                
                # Filter directories (Case-Insensitive)
                dirs[:] = [d for d in dirs if d.lower() not in active_excludes and not d.startswith('.')]

                # Batch entries - only update FTS if modified
                for d in dirs:
                    full_path = os.path.join(base, d)
                    try:
                        mtime = os.path.getmtime(full_path)
                        batch.append((full_path, d, mtime, 1, current_scan_time))
                        count += 1
                    except: continue
                
                for f in files:
                    if f.startswith(".") or os.path.splitext(f)[1].lower() in self.exclude_exts:
                        continue
                        
                    full_path = os.path.join(base, f)
                    try:
                        mtime = os.path.getmtime(full_path)
                        batch.append((full_path, f, mtime, 0, current_scan_time))
                        count += 1
                    except: continue

                if len(batch) >= 1000:
                    cursor.executemany("""
                        INSERT INTO files (path, name, mtime, is_dir, last_seen) 
                        VALUES (?, ?, ?, ?, ?)
                        ON CONFLICT(path) DO UPDATE SET
                            last_seen = excluded.last_seen,
                            name = CASE WHEN mtime != excluded.mtime THEN excluded.name ELSE name END,
                            is_dir = CASE WHEN mtime != excluded.mtime THEN excluded.is_dir ELSE is_dir END,
                            mtime = excluded.mtime
                    """, batch)
                    conn.commit()
                    batch = []
                    time.sleep(0.15)

        if batch:
            cursor.executemany("""
                INSERT INTO files (path, name, mtime, is_dir, last_seen) 
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(path) DO UPDATE SET
                    last_seen = excluded.last_seen,
                    name = CASE WHEN mtime != excluded.mtime THEN excluded.name ELSE name END,
                    is_dir = CASE WHEN mtime != excluded.mtime THEN excluded.is_dir ELSE is_dir END,
                    mtime = excluded.mtime
            """, batch)
            conn.commit()

        # Cleanup stale entries (no longer seen in this scan)
        if not self.stop_event.is_set():
            cursor.execute(
                "DELETE FROM files WHERE last_seen < ?", (current_scan_time - 10,)
            )
            conn.commit()

            # Optimization Phase (The "Magic" part)
            print("Bite Indexer: Optimizing database file...")
            cursor.execute("PRAGMA optimize")
            cursor.execute("VACUUM")

        print(
            f"Bite Indexer: Crawl finished. Indexed {count} items in {time.time() - start_time:.2f}s"
        )
        conn.close()

    def force_reindex(self):
        """Manually trigger a full re-index."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("DELETE FROM metadata WHERE key='last_full_scan'")
        conn.commit()
        conn.close()
        # The background loop will pick this up in its next check, 
        # but we can also trigger the start_indexing again or wake it up.
        # For now, deleting the key is enough for next check.
        self.bite.app.notify("Bite Indexer", "Full re-index queued for the background.")

    def index_path(self, path: str):
        """Surgically index a specific folder (Neighborhood Pulse)."""
        target = Path(path)
        if not target.exists(): return
        
        # If it's a file, index the parent folder
        folder = target.parent if target.is_file() else target
        print(f"Bite Indexer: Neighborhood Pulse on {folder}")
        
        def _run_quick():
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                current_time = time.time()
                batch = []
                
                # Single level scan
                with os.scandir(folder) as entries:
                    for entry in entries:
                        if entry.name.startswith(".") or os.path.splitext(entry.name)[1].lower() in self.exclude_exts:
                            continue
                        batch.append((entry.path, entry.name, entry.stat().st_mtime, 1 if entry.is_dir() else 0, current_time))
                
                if batch:
                    cursor.executemany("""
                        INSERT INTO files (path, name, mtime, is_dir, last_seen) 
                        VALUES (?, ?, ?, ?, ?)
                        ON CONFLICT(path) DO UPDATE SET
                            last_seen = excluded.last_seen,
                            name = CASE WHEN mtime != excluded.mtime THEN excluded.name ELSE name END,
                            is_dir = CASE WHEN mtime != excluded.mtime THEN excluded.is_dir ELSE is_dir END,
                            mtime = excluded.mtime
                    """, batch)
                    conn.commit()
                conn.close()
            except: pass
            
        threading.Thread(target=_run_quick, daemon=True).start()

    def search(self, query: str, limit: int = 40) -> List[Dict]:
        if not query:
            return []

        conn = self.get_connection()
        query_safe = query.replace("'", "''")

        # Layer 1: FTS Exact/Prefix Match (Fastest & Best)
        try:
            res = conn.execute(f"""
                SELECT f.path, f.name, f.is_dir, 1 as rank_group
                FROM files f
                JOIN files_fts ff ON f.rowid = ff.rowid
                WHERE files_fts MATCH '"{query_safe}" OR {query_safe}*'
                ORDER BY rank
                LIMIT {limit}
            """).fetchall()
            if len(res) >= 10:
                return [dict(r) for r in res]
        except sqlite3.OperationalError:
            res = []

        # Layer 2: Fuzzy Sequence Match (The "pyc" -> "py-cast" logic)
        # We turn "abc" into "%a%b%c%"
        fuzzy_query = "%" + "%".join(list(query)) + "%"

        fuzzy_res = conn.execute(
            """
            SELECT path, name, is_dir, 2 as rank_group FROM files 
            WHERE name LIKE ? 
            ORDER BY 
                CASE 
                    WHEN name LIKE ? THEN 0 -- Starts with
                    WHEN name LIKE ? THEN 1 -- Substring
                    ELSE 2 
                END, 
                length(name) ASC
            LIMIT ?
        """,
            (fuzzy_query, f"{query}%", f"%{query}%", limit),
        ).fetchall()

        # Combine and deduplicate
        seen = {r["path"] for r in res}
        combined = [dict(r) for r in res]
        for r in fuzzy_res:
            if r["path"] not in seen:
                combined.append(dict(r))

        # Life Check: Filter out deleted files
        final_results = []
        for r in combined:
            if os.path.exists(r["path"]):
                final_results.append(r)
            else:
                 # Bonus: Clean up the DB if we catch a dead link
                 try:
                     conn.execute("DELETE FROM files WHERE path = ?", (r["path"],))
                     conn.commit()
                 except: pass
        
        return final_results[:limit]
