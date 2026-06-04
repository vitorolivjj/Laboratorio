"""Estado curto do Caio por número — evita scripts/outbound duplicados."""

from __future__ import annotations

import hashlib
import json
import threading
from datetime import datetime, timezone

from laboratorio.config import BACKEND_ROOT
from laboratorio.whatsapp.vitor_auth import normalize_wa_id

_SESSION_FILE = BACKEND_ROOT / "data" / "caio_wa_session.json"
_OUTBOUND_DEDUP_SEC = 90
_LOCK = threading.Lock()


def _load() -> dict:
    if not _SESSION_FILE.is_file():
        return {}
    try:
        return json.loads(_SESSION_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save(data: dict) -> None:
    _SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    _SESSION_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _hash_body(body: str) -> str:
    norm = " ".join((body or "").lower().split())
    return hashlib.sha256(norm.encode()).hexdigest()[:16]


def was_script_sent(wa_id: str, script_key: str) -> bool:
    key = normalize_wa_id(wa_id)
    if not key:
        return False
    with _LOCK:
        entry = _load().get(key) or {}
        return script_key in (entry.get("scripts_sent") or [])


def mark_script_sent(wa_id: str, script_key: str) -> None:
    key = normalize_wa_id(wa_id)
    if not key:
        return
    with _LOCK:
        data = _load()
        entry = dict(data.get(key) or {})
        scripts = list(entry.get("scripts_sent") or [])
        if script_key not in scripts:
            scripts.append(script_key)
        entry["scripts_sent"] = scripts[-20:]
        entry["updated_at"] = datetime.now(timezone.utc).isoformat()
        data[key] = entry
        _save(data)


def is_duplicate_outbound(wa_id: str, body: str, *, window_sec: int = _OUTBOUND_DEDUP_SEC) -> bool:
    """True se o mesmo texto foi enviado ao número nos últimos N segundos."""
    key = normalize_wa_id(wa_id)
    text = (body or "").strip()
    if not key or not text:
        return False
    h = _hash_body(text)
    now = datetime.now(timezone.utc)

    with _LOCK:
        data = _load()
        entry = dict(data.get(key) or {})
        last_h = entry.get("last_outbound_hash")
        last_at = entry.get("last_outbound_at")
        if last_h == h and last_at:
            try:
                prev = datetime.fromisoformat(last_at.replace("Z", "+00:00"))
                if (now - prev).total_seconds() < window_sec:
                    return True
            except ValueError:
                pass
    return False


def record_outbound(wa_id: str, body: str) -> None:
    key = normalize_wa_id(wa_id)
    if not key:
        return
    with _LOCK:
        data = _load()
        entry = dict(data.get(key) or {})
        entry["last_outbound_hash"] = _hash_body(body)
        entry["last_outbound_at"] = datetime.now(timezone.utc).isoformat()
        data[key] = entry
        _save(data)
