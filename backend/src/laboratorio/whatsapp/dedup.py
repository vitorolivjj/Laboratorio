"""Dedup de message_id e conteúdo inbound — evita respostas duplicadas (retries Meta)."""

from __future__ import annotations

import hashlib
import json
import threading
from datetime import datetime, timezone

from laboratorio.config import BACKEND_ROOT
from laboratorio.whatsapp.vitor_auth import normalize_wa_id

_DEDUP_FILE = BACKEND_ROOT / "data" / "wa_processed_ids.json"
_CONTENT_FILE = BACKEND_ROOT / "data" / "wa_inbound_content.json"
_MAX_IDS = 5000
_CONTENT_WINDOW_SEC = 120
_LOCK = threading.Lock()


def _load_ids() -> set[str]:
    if not _DEDUP_FILE.is_file():
        return set()
    try:
        data = json.loads(_DEDUP_FILE.read_text(encoding="utf-8"))
        return set(data if isinstance(data, list) else [])
    except (json.JSONDecodeError, OSError):
        return set()


def _save_ids(ids: set[str]) -> None:
    _DEDUP_FILE.parent.mkdir(parents=True, exist_ok=True)
    trimmed = list(ids)[-_MAX_IDS:]
    _DEDUP_FILE.write_text(json.dumps(trimmed, indent=0), encoding="utf-8")


def already_processed(message_id: str) -> bool:
    return message_id in _load_ids()


def mark_processed(message_id: str) -> None:
    with _LOCK:
        ids = _load_ids()
        ids.add(message_id)
        _save_ids(ids)


def _load_content() -> dict:
    if not _CONTENT_FILE.is_file():
        return {}
    try:
        return json.loads(_CONTENT_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save_content(data: dict) -> None:
    _CONTENT_FILE.parent.mkdir(parents=True, exist_ok=True)
    trimmed = dict(list(data.items())[-500:])
    _CONTENT_FILE.write_text(json.dumps(trimmed, indent=0), encoding="utf-8")


def _content_key(wa_id: str, text: str) -> str:
    norm = normalize_wa_id(wa_id)
    body = " ".join((text or "").lower().split())
    return hashlib.sha256(f"{norm}:{body}".encode()).hexdigest()[:20]


def is_duplicate_inbound_content(wa_id: str, text: str, *, window_sec: int = _CONTENT_WINDOW_SEC) -> bool:
    """Meta às vezes reenvia o mesmo texto com message_id diferente."""
    key = _content_key(wa_id, text)
    now = datetime.now(timezone.utc)
    with _LOCK:
        data = _load_content()
        prev = data.get(key)
        if not prev:
            return False
        try:
            ts = datetime.fromisoformat(str(prev).replace("Z", "+00:00"))
            return (now - ts).total_seconds() < window_sec
        except ValueError:
            return False


def mark_inbound_content(wa_id: str, text: str) -> None:
    key = _content_key(wa_id, text)
    with _LOCK:
        data = _load_content()
        data[key] = datetime.now(timezone.utc).isoformat()
        _save_content(data)


def mark_if_new(message_id: str, *, wa_id: str = "", text: str = "") -> bool:
    """Marca atomicamente: True se a mensagem é nova (processar), False se duplicada.

    Deve ser chamado ANTES de gerar a resposta — assim a 2ª entrega da Meta
    (entrega "pelo menos uma vez") é descartada mesmo enquanto a 1ª ainda está
    chamando o LLM (que demora). Evita respostas duplicadas.
    """
    now = datetime.now(timezone.utc)
    with _LOCK:
        if wa_id and text:
            ck = _content_key(wa_id, text)
            content = _load_content()
            prev = content.get(ck)
            if prev:
                try:
                    ts = datetime.fromisoformat(str(prev).replace("Z", "+00:00"))
                    if (now - ts).total_seconds() < _CONTENT_WINDOW_SEC:
                        return False
                except ValueError:
                    pass

        if message_id:
            ids = _load_ids()
            if message_id in ids:
                return False
            ids.add(message_id)
            _save_ids(ids)

        if wa_id and text:
            content = _load_content()
            content[_content_key(wa_id, text)] = now.isoformat()
            _save_content(content)

        return True
