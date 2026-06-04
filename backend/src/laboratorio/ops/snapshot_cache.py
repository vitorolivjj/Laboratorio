"""Cache do snapshot Maestro — sem dependências pesadas."""

from __future__ import annotations

import threading
import time
from typing import Any

_SNAPSHOT_CACHE: dict[str, Any] = {"data": None, "ts": 0.0}
_SNAPSHOT_LOCK = threading.Lock()


def invalidate_maestro_snapshot() -> None:
    with _SNAPSHOT_LOCK:
        _SNAPSHOT_CACHE["data"] = None
        _SNAPSHOT_CACHE["ts"] = 0.0


def get_snapshot_cache() -> tuple[dict[str, Any] | None, float]:
    with _SNAPSHOT_LOCK:
        return _SNAPSHOT_CACHE["data"], _SNAPSHOT_CACHE["ts"]


def set_snapshot_cache(data: dict[str, Any]) -> None:
    with _SNAPSHOT_LOCK:
        _SNAPSHOT_CACHE["data"] = data
        _SNAPSHOT_CACHE["ts"] = time.monotonic()
