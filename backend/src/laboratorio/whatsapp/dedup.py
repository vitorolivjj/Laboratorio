"""Dedup de message_id para evitar respostas duplicadas (retries Meta)."""

from __future__ import annotations

import json
import threading

from laboratorio.config import BACKEND_ROOT

_DEDUP_FILE = BACKEND_ROOT / "data" / "wa_processed_ids.json"
_MAX_IDS = 5000
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


def mark_if_new(message_id: str) -> bool:
    """Marca atomicamente: True se a mensagem é nova (processar), False se duplicada.

    Deve ser chamado ANTES de gerar a resposta — assim a 2ª entrega da Meta
    (entrega "pelo menos uma vez") é descartada mesmo enquanto a 1ª ainda está
    chamando o LLM (que demora). Evita respostas duplicadas.
    """
    if not message_id:
        return True
    with _LOCK:
        ids = _load_ids()
        if message_id in ids:
            return False
        ids.add(message_id)
        _save_ids(ids)
        return True
