"""Agenda de lembretes Vitor — WhatsApp via Caio."""

from __future__ import annotations

import json
import logging
import re
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from laboratorio.config import LOGS_DIR, TASKS_DIR

logger = logging.getLogger("laboratorio.vitor_schedule")

SCHEDULE_FILE = LOGS_DIR / "vitor_whatsapp_agenda.json"
TZ = ZoneInfo("America/Sao_Paulo")


def _load() -> dict:
    if not SCHEDULE_FILE.is_file():
        return {"items": []}
    try:
        return json.loads(SCHEDULE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"items": []}


def _save(data: dict) -> None:
    SCHEDULE_FILE.parent.mkdir(parents=True, exist_ok=True)
    SCHEDULE_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def list_pending() -> list[dict]:
    data = _load()
    now = datetime.now(timezone.utc)
    out = []
    for item in data.get("items", []):
        if item.get("sent"):
            continue
        try:
            due = datetime.fromisoformat(item["due_at"].replace("Z", "+00:00"))
            if due.tzinfo is None:
                due = due.replace(tzinfo=timezone.utc)
        except (KeyError, ValueError):
            continue
        item = {**item, "due_local": due.astimezone(TZ).strftime("%d/%m %H:%M")}
        out.append(item)
    return sorted(out, key=lambda x: x.get("due_at", ""))


def cancel_item(item_id: str) -> bool:
    data = _load()
    before = len(data.get("items", []))
    data["items"] = [i for i in data.get("items", []) if i.get("id") != item_id and not i.get("sent")]
    _save(data)
    return len(data["items"]) < before


def cancel_all_pending() -> int:
    """Remove lembretes WhatsApp ainda não enviados. Retorna quantidade removida."""
    data = _load()
    items = data.get("items", [])
    kept = [i for i in items if i.get("sent")]
    removed = len(items) - len(kept)
    if removed:
        data["items"] = kept
        _save(data)
    return removed


def add_schedule(*, due_at: datetime, command: str, label: str = "") -> dict:
    if due_at.tzinfo is None:
        due_at = due_at.replace(tzinfo=TZ)
    due_utc = due_at.astimezone(timezone.utc)
    item = {
        "id": uuid.uuid4().hex[:10],
        "due_at": due_utc.isoformat(),
        "command": command.strip(),
        "label": label.strip() or command.strip(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "sent": False,
    }
    data = _load()
    data.setdefault("items", []).append(item)
    _save(data)
    return item


def parse_schedule_request(text: str) -> tuple[datetime, str, str] | None:
    """Retorna (due_at, command, label) ou None."""
    folded = text.strip()
    lower = folded.lower()
    now = datetime.now(TZ)

    # agendar em 30 min: status
    m = re.search(
        r"agendar\s+(?:em\s+)?(\d+)\s*(min(?:utos)?|h(?:oras)?)\s*[:\-]?\s*(.+)",
        lower,
        re.I,
    )
    if m:
        n, unit, cmd = int(m.group(1)), m.group(2), folded[m.start(3) :].strip()
        delta = timedelta(minutes=n) if "min" in unit else timedelta(hours=n)
        return now + delta, cmd, cmd

    # lembrete em 1h status
    m = re.search(
        r"(?:lembre|lembra|lembrete|me avise)\s+(?:em\s+)?(\d+)\s*(min(?:utos)?|h(?:oras)?)\s*[:\-]?\s*(.+)",
        lower,
        re.I,
    )
    if m:
        n, unit, cmd = int(m.group(1)), m.group(2), folded[m.start(3) :].strip()
        delta = timedelta(minutes=n) if "min" in unit else timedelta(hours=n)
        return now + delta, cmd, cmd

    # agendar amanhã 9h: patrulha
    m = re.search(
        r"agendar\s+amanh[aã]\s*(?:as|às)?\s*(\d{1,2})(?::(\d{2}))?\s*[:\-]?\s*(.+)",
        lower,
        re.I,
    )
    if m:
        h, mi = int(m.group(1)), int(m.group(2) or 0)
        cmd = folded[m.start(3) :].strip()
        due = (now + timedelta(days=1)).replace(hour=h, minute=mi, second=0, microsecond=0)
        return due, cmd, cmd

    # agendar 01/06 9h: status
    m = re.search(
        r"agendar\s+(\d{1,2})/(\d{1,2})(?:\s*(?:as|às)\s*(\d{1,2})(?::(\d{2}))?)?\s*[:\-]?\s*(.+)",
        lower,
        re.I,
    )
    if m:
        day, month = int(m.group(1)), int(m.group(2))
        h = int(m.group(3) or 9)
        mi = int(m.group(4) or 0)
        cmd = folded[m.start(5) :].strip()
        year = now.year
        due = datetime(year, month, day, h, mi, tzinfo=TZ)
        if due < now:
            due = due.replace(year=year + 1)
        return due, cmd, cmd

    return None


_TASK_ID_RE = re.compile(
    r"\b((?:LP-PINTOR|LAB|TASK|VITOR)-\d+[A-Z]?)\b",
    re.I,
)


def _extract_task_id(command: str) -> str:
    m = _TASK_ID_RE.search(command or "")
    return m.group(1).upper() if m else ""


def reminder_task_obsolete(command: str) -> tuple[bool, str]:
    """Não cobrar tasks já concluídas, canceladas ou arquivadas."""
    tid = _extract_task_id(command)
    if not tid:
        return False, ""

    task_file = TASKS_DIR / f"{tid}.md"
    if task_file.is_file():
        body = task_file.read_text(encoding="utf-8").lower()
        if "cancelad" in body[:800]:
            return True, f"{tid} cancelada"

    for fname in ("concluidas.md", "arquivado.md"):
        path = TASKS_DIR / fname
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        if re.search(rf"^###\s+{re.escape(tid)}\b", text, re.M | re.I):
            return True, f"{tid} em {fname}"

    return False, ""


def run_due_schedules(processor) -> list[dict]:
    """Executa itens vencidos. `processor(command) -> str` gera a mensagem."""
    data = _load()
    now = datetime.now(timezone.utc)
    sent: list[dict] = []
    for item in data.get("items", []):
        if item.get("sent"):
            continue
        try:
            due = datetime.fromisoformat(item["due_at"].replace("Z", "+00:00"))
            if due.tzinfo is None:
                due = due.replace(tzinfo=timezone.utc)
        except (KeyError, ValueError):
            continue
        if due > now:
            continue

        obsolete, reason = reminder_task_obsolete(item.get("command", ""))
        if obsolete:
            item["sent"] = True
            item["sent_at"] = now.isoformat()
            item["skipped"] = reason
            logger.info("Lembrete ignorado (%s): %s", item.get("id"), reason)
            continue

        try:
            body = processor(item.get("command", "status"))
            item["sent"] = True
            item["sent_at"] = now.isoformat()
            sent.append({"item": item, "body": body})
        except Exception as exc:
            item["error"] = str(exc)
            item["sent"] = True
            sent.append({"item": item, "body": f"Lembrete falhou: {exc}"})
    _save(data)
    return sent
