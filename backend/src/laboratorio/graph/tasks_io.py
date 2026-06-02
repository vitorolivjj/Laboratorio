"""Leitura/escrita de tasks markdown."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from laboratorio.config import LOGS_DIR, TASKS_DIR


def task_file(task_id: str) -> Path:
    p = TASKS_DIR / f"{task_id}.md"
    if not p.is_file():
        p = TASKS_DIR / f"{task_id.upper()}.md"
    if not p.is_file():
        raise FileNotFoundError(f"Task não encontrada: {task_id}")
    return p


def load_task(task_id: str) -> dict[str, str]:
    path = task_file(task_id)
    content = path.read_text(encoding="utf-8")
    title_m = re.search(r"^# [A-Z0-9\-]+ — (.+?)$", content, re.MULTILINE)
    obj_m = re.search(
        r"## Objetivo\s*\n+(.+?)(?=\n## |\Z)", content, re.MULTILINE | re.DOTALL
    )
    return {
        "id": task_id.upper(),
        "path": str(path),
        "title": (title_m.group(1).strip() if title_m else task_id),
        "body": content,
        "objective": (obj_m.group(1).strip() if obj_m else title_m.group(1) if title_m else ""),
    }


def append_pilot_output(task_id: str, report: str) -> None:
    path = task_file(task_id)
    text = path.read_text(encoding="utf-8")
    marker = "## Saída do piloto LangGraph"
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    block = f"\n\n### Execução {stamp}\n\n{report.strip()}\n"
    if marker in text:
        text = text.replace(marker, marker + block)
    else:
        text = text.rstrip() + f"\n\n{marker}\n{block}"
    path.write_text(text, encoding="utf-8")


def log_event(task_id: str, detail: str) -> None:
    path = LOGS_DIR / "eventos.md"
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    block = f"""### {stamp} — [orquestracao] LangGraph piloto {task_id}
- **Agente(s):** ronaldo_maestro · dev
- **Detalhe:** {detail}
- **Ref:** LAB-003 · Fase 2

"""
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    marker = "## Log\n"
    if marker in text:
        text = text.replace(marker, marker + "\n" + block)
    else:
        text = block + text
    path.write_text(text, encoding="utf-8")
