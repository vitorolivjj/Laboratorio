"""Execução e retomada do piloto LangGraph."""

from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass

from langgraph.checkpoint.sqlite import SqliteSaver

from laboratorio.config import LOGS_DIR, load_env
from laboratorio.graph.pilot import build_pilot_graph
from laboratorio.graph.state import PilotState

logger = logging.getLogger("laboratorio.graph.runner")

CHECKPOINT_DB = LOGS_DIR / "langgraph_pilot.sqlite"


@dataclass
class PilotResult:
    task_id: str
    phase: str
    plan: str
    deliverable: str
    estimated_cost_usd: float
    approval_id: str | None


def _compile_graph(*, commercial: bool = False):
    load_env()
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(CHECKPOINT_DB), check_same_thread=False)
    checkpointer = SqliteSaver(conn)
    if commercial:
        from laboratorio.graph.commercial import build_commercial_graph

        builder = build_commercial_graph()
    else:
        builder = build_pilot_graph()
    return builder.compile(checkpointer=checkpointer)


def _thread_config(task_id: str) -> dict:
    return {"configurable": {"thread_id": task_id.upper()}}


def run_pilot(task_id: str, *, resume: bool = False, commercial: bool = False) -> PilotResult:
    """Executa (ou retoma) o piloto para uma task."""
    tid = task_id.upper()
    graph = _compile_graph(commercial=commercial)
    config = _thread_config(tid)

    if resume:
        snap = graph.get_state(config)
        if not snap or not snap.values:
            raise RuntimeError(f"Sem checkpoint para {tid} — rode sem --resume")
        logger.info("Retomando piloto %s do checkpoint", tid)
        result = graph.invoke(None, config)
    else:
        initial: PilotState = {"task_id": tid, "phase": "start"}
        result = graph.invoke(initial, config)

    return PilotResult(
        task_id=tid,
        phase=result.get("phase", "?"),
        plan=result.get("plan", ""),
        deliverable=result.get("deliverable", ""),
        estimated_cost_usd=float(result.get("estimated_cost_usd") or 0),
        approval_id=result.get("approval_id"),
    )


def resume_pilot(task_id: str, *, commercial: bool = False) -> PilotResult:
    return run_pilot(task_id, resume=True, commercial=commercial)


def run_commercial(task_id: str, *, resume: bool = False) -> PilotResult:
    return run_pilot(task_id, resume=resume, commercial=True)
