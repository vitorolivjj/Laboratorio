"""Standby de TASKs Donizete durante PlayDonizete / retorno no StopDonizete."""

from __future__ import annotations

import logging

from laboratorio.config import TASKS_DIR
from laboratorio.ops import parsers
from laboratorio.ops.markdown_io import read_text
from laboratorio.ops.tasks_store import move_task

logger = logging.getLogger("laboratorio.donizete_task_standby")


def _donizete_agent(agents: str) -> bool:
    return "donizete" in (agents or "").lower()


def find_donizete_tasks_in_executando() -> list[dict]:
    content = read_text(TASKS_DIR / "executando.md")
    return [t for t in parsers.parse_executando_tasks(content) if _donizete_agent(t.get("agents") or "")]


def find_tasks_in_standby(task_ids: list[str]) -> list[str]:
    content = read_text(TASKS_DIR / "standby.md")
    present = set(parsers.parsers_count(TASKS_DIR / "standby.md", "## Em standby"))
    return [tid for tid in task_ids if tid in present]


def pause_task_for_busca(task_id: str) -> list[str]:
    """Move uma TASK específica executando → standby."""
    task_id = task_id.strip().upper()
    for task in find_donizete_tasks_in_executando():
        if task["id"].upper() != task_id:
            continue
        try:
            move_task(
                task_id,
                "standby",
                nota="PlayDonizete — captura intermitente (standby)",
            )
            logger.info("Task %s → standby (PlayDonizete)", task_id)
            return [task_id]
        except ValueError as exc:
            logger.warning("Não moveu %s para standby: %s", task_id, exc)
            return []
    # Já em standby ou outro estado — segue sem erro
    return []


def pause_executando_for_busca(*, task_id: str | None = None) -> list[str]:
    """Move TASK(s) Donizete de executando → standby. Com task_id, só essa."""
    if task_id:
        return pause_task_for_busca(task_id)
    moved: list[str] = []
    for task in find_donizete_tasks_in_executando():
        tid = task["id"]
        try:
            move_task(
                tid,
                "standby",
                nota="PlayDonizete — busca intermitente (task em standby)",
            )
            moved.append(tid)
            logger.info("Task %s → standby (PlayDonizete)", tid)
        except ValueError as exc:
            logger.warning("Não moveu %s para standby: %s", tid, exc)
    return moved


def resume_standby_tasks(task_ids: list[str]) -> list[str]:
    """Restaura TASKs listadas de standby → executando."""
    resumed: list[str] = []
    for tid in task_ids:
        try:
            move_task(
                tid,
                "executando",
                nota="StopDonizete — retoma execução após busca WhatsApp",
            )
            resumed.append(tid)
            logger.info("Task %s → executando (StopDonizete)", tid)
        except ValueError as exc:
            logger.warning("Não restaurou %s: %s", tid, exc)
    return resumed
