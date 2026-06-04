"""Escrita dupla — mantém o Postgres como cópia autoritativa sempre-atual.

Após cada escrita no markdown (tasks/CRM/memória), dispara em background um sync
espelho do banco. É **best-effort**: nunca bloqueia nem quebra a escrita markdown
(roda em thread daemon, engole erros, coalescido — no máximo um sync por vez).

Liga sozinho quando o banco está configurado; controle por env:
  DB_DUAL_WRITE=0  -> desliga
  DB_DUAL_WRITE=1  -> liga mesmo sem auto-detecção
"""

from __future__ import annotations

import logging
import os
import threading

logger = logging.getLogger("laboratorio.db.dual_write")

_lock = threading.Lock()
_running = False
_dirty = False


def enabled() -> bool:
    val = os.getenv("DB_DUAL_WRITE", "").strip().lower()
    if val in ("1", "true", "on", "yes"):
        return True
    if val in ("0", "false", "off", "no"):
        return False
    # auto: liga se há banco configurado
    try:
        from laboratorio.db.core import db_enabled

        return db_enabled()
    except Exception:  # noqa: BLE001
        return False


def _run_mirror() -> None:
    from laboratorio.db.markdown_sync import apply_to_db, collect_markdown

    apply_to_db(collect_markdown(), mirror=True)


def _loop() -> None:
    global _running, _dirty
    while True:
        try:
            _run_mirror()
            logger.info("Dual-write: banco sincronizado.")
        except Exception as exc:  # noqa: BLE001 — sync é best-effort
            logger.warning("Dual-write falhou (banco fica até %s atrás): %s", "o próximo sync", exc)
        with _lock:
            if _dirty:
                _dirty = False
                continue
            _running = False
            return


def sync_async() -> None:
    """Agenda um sync do banco em background. Coalescido e tolerante a falha."""
    if not enabled():
        return
    global _running, _dirty
    with _lock:
        if _running:
            _dirty = True  # já tem sync rodando; ele pega o estado atual depois
            return
        _running = True
    threading.Thread(target=_loop, name="dual-write", daemon=True).start()
