import os
import re
import urllib.parse
import urllib.request
import threading
import base64
from pathlib import Path
from typing import Optional, List


class FaviconCache:
    """
    Lightweight, persistent local favicon cache for websites and bookmarks.
    Prevents repeated network calls, ensures fast offline icon loading, and enhances privacy.
    """

    def __init__(self, cache_dir: Path, app_instance=None):
        self.cache_dir = Path(cache_dir) / "favicons"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.app = app_instance
        self._mem_cache = {}
        self._fetching = set()
        self._lock = threading.Lock()

    def _extract_domain(self, target: str) -> Optional[str]:
        if not target:
            return None
        target = target.strip().lower()
        if "://" in target:
            parsed = urllib.parse.urlparse(target)
            domain = parsed.netloc
        else:
            domain = target.split("/")[0]

        # Strip standard port or www prefix for cleaner domain keys
        domain = re.sub(r":\d+$", "", domain)
        if domain.startswith("www."):
            domain = domain[4:]
        return domain if domain else None

    def get_favicon(self, url_or_domain: str, fetch_if_missing: bool = True) -> str:
        """
        Returns a base64 data URI or pytron local file URL if cached.
        Falls back to online Google proxy URL while silently caching in the background.
        """
        domain = self._extract_domain(url_or_domain)
        if not domain:
            return "globe"

        # 1. Check in-memory cache
        with self._lock:
            if domain in self._mem_cache:
                return self._mem_cache[domain]

        # 2. Check disk cache
        cache_file = self.cache_dir / f"{domain}.png"
        if cache_file.exists() and cache_file.stat().st_size > 100:
            try:
                data = cache_file.read_bytes()
                b64 = base64.b64encode(data).decode("utf-8")
                data_uri = f"data:image/png;base64,{b64}"
                with self._lock:
                    self._mem_cache[domain] = data_uri
                return data_uri
            except Exception:
                pass

        # 3. Fallback online URL & queue background download
        fallback_url = f"https://www.google.com/s2/favicons?domain={domain}&sz=64"
        if fetch_if_missing:
            self._queue_fetch(domain, cache_file)

        return fallback_url

    def _queue_fetch(self, domain: str, cache_file: Path):
        with self._lock:
            if domain in self._fetching:
                return
            self._fetching.add(domain)

        def fetch_worker():
            try:
                url = f"https://www.google.com/s2/favicons?domain={domain}&sz=64"
                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
                )
                with urllib.request.urlopen(req, timeout=3.5) as resp:
                    if resp.status == 200:
                        content = resp.read()
                        if len(content) > 100:  # Validate non-empty valid icon
                            cache_file.write_bytes(content)
                            b64 = base64.b64encode(content).decode("utf-8")
                            data_uri = f"data:image/png;base64,{b64}"
                            with self._lock:
                                self._mem_cache[domain] = data_uri
            except Exception:
                pass
            finally:
                with self._lock:
                    self._fetching.discard(domain)

        threading.Thread(target=fetch_worker, daemon=True).start()

    def warmup_cache_async(self, urls: List[str]):
        """Warms up favicon cache in the background for a list of URLs (e.g. bookmarks)."""
        def worker():
            for u in urls[:50]:
                self.get_favicon(u, fetch_if_missing=True)
        threading.Thread(target=worker, daemon=True).start()
