"""Fila de propostas de autoevolução — append-only, aplicação só via APROVAR no digest."""

from __future__ import annotations

import json
import re
import unicodedata
from datetime import datetime, timezone

from laboratorio.config import LOGS_DIR

QUEUE_FILE = LOGS_DIR / "evolution_proposals_queue.jsonl"
VALID_TARGETS = frozenset({"aprendizados", "decisoes"})


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _next_id() -> int:
    if not QUEUE_FILE.is_file():
        return 1
    last = 0
    try:
        for line in QUEUE_FILE.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            last = max(last, int(row.get("id") or 0))
    except (OSError, json.JSONDecodeError):
        pass
    return last + 1


def queue_proposal(
    *,
    title: str,
    body: str,
    target: str = "aprendizados",
    source: str = "whatsapp",
    context: str = "",
) -> dict:
    """Registra proposta numerada — não altera memoria/ até APROVAR no digest."""
    target = target.strip().lower()
    if target not in VALID_TARGETS:
        target = "aprendizados"

    prop_id = _next_id()
    entry = {
        "id": prop_id,
        "date": _today(),
        "queued_at": _now(),
        "title": title.strip()[:120],
        "body": body.strip()[:4000],
        "target": target,
        "source": source.strip() or "whatsapp",
        "context": context.strip()[:500],
        "status": "pending",
    }
    QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with QUEUE_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def list_pending_proposals(*, limit: int = 20) -> list[dict]:
    if not QUEUE_FILE.is_file():
        return []
    rows: list[dict] = []
    try:
        for line in QUEUE_FILE.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("status", "pending") == "pending":
                rows.append(row)
    except (OSError, json.JSONDecodeError):
        return []
    return rows[-limit:]


def format_proposal_ack(entry: dict) -> str:
    pid = entry.get("id", "?")
    target = entry.get("target", "aprendizados")
    return (
        f"✓ Proposta #{pid} na fila de autoevolução ({target}).\n"
        "Não aplicada automaticamente — confira no resumo diário e responda APROVAR quando quiser."
    )


def normalize_proposal_title(title: str) -> str:
    nfkd = unicodedata.normalize("NFD", (title or "").lower())
    folded = "".join(c for c in nfkd if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", folded).strip()


def _rewrite_queue_status(prop_id: int, status: str) -> bool:
    if not QUEUE_FILE.is_file():
        return False
    lines_out: list[str] = []
    found = False
    for line in QUEUE_FILE.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if int(row.get("id") or 0) == prop_id:
            row["status"] = status
            row["resolved_at"] = _now()
            found = True
        lines_out.append(json.dumps(row, ensure_ascii=False))
    if found:
        QUEUE_FILE.write_text("\n".join(lines_out) + "\n", encoding="utf-8")
    return found


def mark_proposal_applied(
    prop_id: int | None = None,
    *,
    title: str | None = None,
) -> bool:
    """Marca proposta na fila jsonl como applied (por id ou título normalizado)."""
    if prop_id is not None:
        return _rewrite_queue_status(int(prop_id), "applied")

    norm = normalize_proposal_title(title or "")
    if not norm or not QUEUE_FILE.is_file():
        return False
    for row in _read_all_rows():
        if row.get("status", "pending") != "pending":
            continue
        if normalize_proposal_title(row.get("title", "")) == norm:
            return _rewrite_queue_status(int(row["id"]), "applied")
    return False


def _read_all_rows() -> list[dict]:
    if not QUEUE_FILE.is_file():
        return []
    rows: list[dict] = []
    try:
        for line in QUEUE_FILE.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
    except (OSError, json.JSONDecodeError):
        pass
    return rows


def pending_title_keys() -> set[str]:
    return {
        normalize_proposal_title(p.get("title", ""))
        for p in list_pending_proposals(limit=50)
        if normalize_proposal_title(p.get("title", ""))
    }


def filter_digest_proposals(proposals: list[dict]) -> list[dict]:
    """Remove propostas duplicadas vs fila pending ou já decididas hoje."""
    pending_keys = pending_title_keys()
    state = _load_evolution_state()
    decided_today = set(state.get("decision_titles_today") or [])

    out: list[dict] = []
    for p in proposals:
        key = normalize_proposal_title(p.get("title", ""))
        if not key:
            out.append(p)
            continue
        if key in pending_keys or key in decided_today:
            continue
        if any(
            key in normalize_proposal_title(x) or normalize_proposal_title(x) in key
            for x in pending_keys | decided_today
            if len(x) > 8
        ):
            continue
        out.append(p)
    return out


def record_decision_title_for_digest(titulo: str) -> None:
    """Evita reproposta no digest no mesmo dia após Decisão: no bridge."""
    state = _load_evolution_state()
    today = _today()
    if state.get("decision_day") != today:
        state["decision_day"] = today
        state["decision_titles_today"] = []
    keys: list[str] = list(state.get("decision_titles_today") or [])
    key = normalize_proposal_title(titulo)
    if key and key not in keys:
        keys.append(key)
    state["decision_titles_today"] = keys
    _save_evolution_state(state)


def _load_evolution_state() -> dict:
    path = LOGS_DIR / "evolution_state.json"
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _save_evolution_state(data: dict) -> None:
    path = LOGS_DIR / "evolution_state.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
