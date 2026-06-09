from __future__ import annotations

import threading
import time
from collections import OrderedDict
from typing import Any

_CACHE_REGISTRY: dict[str, "TTLCache"] = {}


class TTLCache:
    def __init__(
        self,
        ttl_seconds: int = 1800,
        max_entries: int = 512,
        enabled: bool = True,
        name: str | None = None,
    ):
        self.ttl_seconds = max(0, int(ttl_seconds))
        self.max_entries = max(1, int(max_entries))
        self.enabled = bool(enabled) and self.ttl_seconds > 0
        self.name = name
        self._store: OrderedDict[str, tuple[float, Any]] = OrderedDict()
        self._lock = threading.RLock()
        self._hits = 0
        self._misses = 0
        self._sets = 0
        self._evictions = 0
        if name:
            _CACHE_REGISTRY[name] = self

    def get(self, key: str):
        if not self.enabled:
            return None
        now = time.time()
        with self._lock:
            item = self._store.get(key)
            if not item:
                self._misses += 1
                return None
            ts, value = item
            if now - ts > self.ttl_seconds:
                self._store.pop(key, None)
                self._misses += 1
                self._evictions += 1
                return None
            self._store.move_to_end(key)
            self._hits += 1
            return value

    def set(self, key: str, value: Any):
        if not self.enabled:
            return
        with self._lock:
            self._store[key] = (time.time(), value)
            self._store.move_to_end(key)
            self._sets += 1
            while len(self._store) > self.max_entries:
                self._store.popitem(last=False)
                self._evictions += 1

    def clear(self):
        with self._lock:
            self._store.clear()

    def prune_expired(self) -> int:
        if not self.enabled:
            return 0
        now = time.time()
        removed = 0
        with self._lock:
            for key, (ts, _) in list(self._store.items()):
                if now - ts > self.ttl_seconds:
                    self._store.pop(key, None)
                    removed += 1
            self._evictions += removed
        return removed

    def stats(self) -> dict[str, int | bool | str | None]:
        self.prune_expired()
        with self._lock:
            total = self._hits + self._misses
            hit_rate_pct = round((self._hits / total * 100.0), 2) if total else 0.0
            return {
                "name": self.name,
                "enabled": self.enabled,
                "ttl_seconds": self.ttl_seconds,
                "max_entries": self.max_entries,
                "entries": len(self._store),
                "hits": self._hits,
                "misses": self._misses,
                "sets": self._sets,
                "evictions": self._evictions,
                "hit_rate_pct": hit_rate_pct,
            }


def cache_registry_stats() -> dict[str, dict[str, int | bool | str | None]]:
    return {name: cache.stats() for name, cache in sorted(_CACHE_REGISTRY.items())}
