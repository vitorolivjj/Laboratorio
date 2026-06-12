"""Kanban API — parse/build tasks/*.md para REST e painel."""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from laboratorio.config import TASKS_DIR
from laboratorio.ops import parsers
from laboratorio.ops.donizete_capture_task import (
    create_capture_task,
    load_capture_config,
    set_task_group_url,
)
from laboratorio.ops.markdown_io import read_text, write_text_atomic
from laboratorio.ops.tasks_store import STATE_FILES, create_task, move_task

logger = logging.getLogger("laboratorio.ops.task_kanban_api")

# Estados “ativos” que o painel pode cancelar/arquivar de uma vez
BULK_CANCEL_STATES = ("executando", "planejando", "standby", "aguardando")


from laboratorio.ops.snapshot_cache import invalidate_maestro_snapshot as _invalidate_snapshot

_BLOCK_RE = re.compile(
    r"^### ([A-Z][A-Z0-9\-]+) — (.+?)\n(.*?)(?=^### |\n---|\n<!--|\Z)",
    re.MULTILINE | re.DOTALL,
)


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _section_text(fname: str, heading: str, *, tasks_dir: Path) -> str:
    content = read_text(tasks_dir / fname)
    if not content:
        return ""
    pattern = rf"{re.escape(heading)}\s*\n(.*?)(?=\n## |\Z)"
    blocks = re.findall(pattern, content, re.DOTALL)
    return "\n".join(blocks) if blocks else content


def _parse_cards(state: str, *, tasks_dir: Path) -> list[dict[str, Any]]:
    fname, heading = STATE_FILES[state]
    block = _section_text(fname, heading, tasks_dir=tasks_dir)
    cards: list[dict[str, Any]] = []
    for m in _BLOCK_RE.finditer(block):
        body = m.group(3)
        tid = m.group(1)
        capture = load_capture_config(tid, tasks_dir=tasks_dir)
        cards.append(
            {
                "id": tid,
                "title": m.group(2).strip(),
                "state": state,
                "objetivo": parsers._field(body, "Objetivo"),
                "prioridade": parsers._field(body, "Prioridade"),
                "agente": parsers._field(body, "Agente responsável")
                or parsers._field(body, "Agente"),
                "status": parsers._field(body, "Status") or state,
                "grupo_fb": (capture or {}).get("group_url") or parsers._field(body, "Grupo FB"),
                "modo_captura": (capture or {}).get("modo") or parsers._field(body, "Modo captura"),
                "is_capture": bool(capture and capture.get("lock_group")),
            }
        )
    return cards


def find_task_state(task_id: str, *, tasks_dir: Path = TASKS_DIR) -> str | None:
    task_id = task_id.strip().upper()
    for state in STATE_FILES:
        fname, heading = STATE_FILES[state]
        ids = parsers.parsers_count(tasks_dir / fname, heading)
        if task_id in ids:
            return state
    return None


def build_kanban_board(*, tasks_dir: Path = TASKS_DIR) -> dict[str, Any]:
    columns: dict[str, list[dict[str, Any]]] = {}
    total = 0
    for state in STATE_FILES:
        cards = _parse_cards(state, tasks_dir=tasks_dir)
        columns[state] = cards
        total += len(cards)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "columns": columns,
        "total": total,
    }


def get_task_detail(task_id: str, *, tasks_dir: Path = TASKS_DIR) -> dict[str, Any]:
    task_id = task_id.strip().upper()
    state = find_task_state(task_id, tasks_dir=tasks_dir)
    doc_path = tasks_dir / f"{task_id}.md"
    markdown = read_text(doc_path)
    if not state and not markdown:
        raise ValueError(f"TASK {task_id} não encontrada.")

    card: dict[str, Any] | None = None
    if state:
        for c in _parse_cards(state, tasks_dir=tasks_dir):
            if c["id"] == task_id:
                card = c
                break

    capture = load_capture_config(task_id, tasks_dir=tasks_dir)
    meta: dict[str, str] = {}
    if markdown:
        for key in ("Status", "Prioridade", "Agente responsável", "Projeto"):
            m = re.search(rf"\|\s*\*\*{re.escape(key)}\*\*\s*\|\s*([^\|]+)", markdown)
            if m:
                meta[key] = m.group(1).strip()

    return {
        "id": task_id,
        "state": state,
        "card": card,
        "markdown": markdown,
        "meta": meta,
        "capture": capture,
        "doc_path": str(doc_path.relative_to(tasks_dir.parent)),
    }


def create_task_api(
    *,
    titulo: str,
    objetivo: str = "",
    agente: str = "",
    prioridade: str = "media",
    contexto: str = "",
    resultado: str = "",
    to_state: str = "backlog",
    tasks_dir: Path = TASKS_DIR,
) -> dict[str, Any]:
    msg = create_task(
        titulo=titulo,
        objetivo=objetivo,
        agente=agente,
        prioridade=prioridade,
        contexto=contexto,
        resultado=resultado,
        tasks_dir=tasks_dir,
    )
    m = re.search(r"(TASK-\d+)", msg)
    task_id = m.group(1) if m else ""
    if task_id and to_state != "backlog":
        move_task(task_id, to_state, tasks_dir=tasks_dir)
    _invalidate_snapshot()
    return {"task_id": task_id, "message": msg, "state": to_state if task_id else "backlog"}


def create_capture_api(
    *,
    group_url: str,
    titulo: str = "",
    to_state: str = "executando",
    tasks_dir: Path = TASKS_DIR,
) -> dict[str, Any]:
    task_id, msg = create_capture_task(group_url, titulo=titulo, tasks_dir=tasks_dir)
    if to_state != "executando":
        move_task(task_id, to_state, tasks_dir=tasks_dir)
    _invalidate_snapshot()
    from laboratorio.ops.donizete_mac_sync import mac_sync_hint_for_task

    return {
        "task_id": task_id,
        "message": msg,
        "state": to_state,
        "group_url": group_url,
        "mac_sync_hint": mac_sync_hint_for_task(task_id),
    }


def move_task_api(
    task_id: str,
    to_state: str,
    nota: str = "",
    *,
    tasks_dir: Path = TASKS_DIR,
    force: bool = False,
) -> dict[str, Any]:
    msg = move_task(task_id, to_state, nota=nota, tasks_dir=tasks_dir, force=force)
    _invalidate_snapshot()
    return {"task_id": task_id.strip().upper(), "message": msg, "to_state": to_state}


def patch_task_api(
    task_id: str,
    *,
    titulo: str | None = None,
    objetivo: str | None = None,
    prioridade: str | None = None,
    grupo_fb: str | None = None,
    tasks_dir: Path = TASKS_DIR,
) -> dict[str, Any]:
    task_id = task_id.strip().upper()
    path = tasks_dir / f"{task_id}.md"
    doc = read_text(path)
    if not doc:
        raise ValueError(f"Arquivo tasks/{task_id}.md não encontrado.")

    changes: list[str] = []
    if titulo:
        doc = re.sub(
            rf"^# {re.escape(task_id)} — .+$",
            f"# {task_id} — {titulo.strip()}",
            doc,
            count=1,
            flags=re.MULTILINE,
        )
        changes.append("titulo")
    if objetivo:
        if "## Objetivo" in doc:
            doc = re.sub(
                r"(## Objetivo\n\n)(.*?)(\n## )",
                rf"\g<1>{objetivo.strip()}\g<3>",
                doc,
                count=1,
                flags=re.DOTALL,
            )
        changes.append("objetivo")
    if prioridade:
        doc = re.sub(
            r"(\| \*\*Prioridade\*\* \| )([^|\n]+)( \|)",
            rf"\g<1>{prioridade.strip()}\g<3>",
            doc,
            count=1,
        )
        changes.append("prioridade")
    write_text_atomic(path, doc)

    if grupo_fb:
        set_task_group_url(task_id, grupo_fb, tasks_dir=tasks_dir)
        changes.append("grupo_fb")

    _invalidate_snapshot()
    return {"task_id": task_id, "updated": changes, "message": f"{task_id} atualizada: {', '.join(changes) or '—'}"}


def _patch_doc_archived(task_id: str, *, tasks_dir: Path) -> None:
    path = tasks_dir / f"{task_id}.md"
    doc = read_text(path)
    if not doc:
        return
    doc2 = re.sub(
        r"(\| \*\*Status\*\* \| )([^|\n]*)( \|)",
        r"\g<1>arquivado (cancelada)\g<3>",
        doc,
        count=1,
    )
    if doc2 == doc and "| **Status** |" not in doc:
        doc2 = doc + "\n| **Status** | arquivado (cancelada) |\n"
    write_text_atomic(path, doc2)


def bulk_archive_active(
    *,
    states: tuple[str, ...] | None = None,
    nota: str = "cancelada e arquivada pelo painel",
    stop_capture: bool = True,
    clear_agenda: bool = True,
    tasks_dir: Path = TASKS_DIR,
) -> dict[str, Any]:
    """Move todas as tasks das colunas ativas para arquivado; para captura e limpa agenda WA."""
    target_states = states or BULK_CANCEL_STATES
    to_move: list[tuple[str, str]] = []
    for state in target_states:
        if state not in STATE_FILES or state in ("arquivado", "concluidas"):
            continue
        fname, heading = STATE_FILES[state]
        for tid in parsers.parsers_count(tasks_dir / fname, heading):
            to_move.append((tid, state))

    moved: list[str] = []
    errors: list[dict[str, str]] = []
    for tid, _from in to_move:
        try:
            move_task(tid, "arquivado", nota=nota, tasks_dir=tasks_dir)
            _patch_doc_archived(tid, tasks_dir=tasks_dir)
            moved.append(tid)
        except ValueError as exc:
            errors.append({"id": tid, "error": str(exc)})

    capture_stopped = False
    if stop_capture:
        try:
            from laboratorio.ops.donizete_runner import capture_active, stop_busca

            if capture_active():
                stop_busca()
                capture_stopped = True
        except Exception as exc:  # noqa: BLE001 — cleanup opcional, não derruba a ação
            logger.warning("Não foi possível parar a captura Donizete: %s", exc)

    agenda_cleared = 0
    if clear_agenda:
        try:
            from laboratorio.whatsapp.vitor_schedule import cancel_all_pending

            agenda_cleared = cancel_all_pending()
        except Exception as exc:  # noqa: BLE001 — cleanup opcional, não derruba a ação
            logger.warning("Não foi possível limpar a agenda: %s", exc)

    _invalidate_snapshot()
    return {
        "moved": moved,
        "moved_count": len(moved),
        "errors": errors,
        "capture_stopped": capture_stopped,
        "agenda_cleared": agenda_cleared,
        "states": list(target_states),
        "message": (
            f"{len(moved)} task(s) arquivada(s)"
            + (" · captura parada" if capture_stopped else "")
            + (f" · {agenda_cleared} lembrete(s) cancelado(s)" if agenda_cleared else "")
        ),
    }
