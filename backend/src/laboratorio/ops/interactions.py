"""Trace estruturado das interações dos agentes (observabilidade).

Grava cada passo de raciocínio/uso de ferramenta e cada task concluída em
`logs/agent_interactions.jsonl` — para o painel mostrar "o que os agentes estão
fazendo" em tempo real e para depurar quando um agente trava.

Uso típico (ao montar uma Crew):

    from laboratorio.ops import interactions
    crew = Crew(..., **interactions.crew_callbacks("orquestrador"))
"""

from __future__ import annotations

import json
import logging
import threading
from collections import deque
from datetime import datetime, timezone
from typing import Any, Callable

from laboratorio.config import LOGS_DIR

logger = logging.getLogger("laboratorio.interactions")

INTERACTIONS_FILE = LOGS_DIR / "agent_interactions.jsonl"
_LOCK = threading.Lock()
_MAX_TEXT = 600


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _trim(text: str) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= _MAX_TEXT else text[: _MAX_TEXT - 1] + "…"


# Trechos de boilerplate que o CrewAI injeta nos erros de ferramenta — viram
# ruído no trace. Cortamos a partir do primeiro marcador encontrado.
_NOISE_MARKERS = (
    "You ONLY have access to the following tools",
    "Tool Name:",
    "Use the following format",
)


def _strip_noise(text: str) -> str:
    cut = len(text)
    for marker in _NOISE_MARKERS:
        idx = text.find(marker)
        if 0 <= idx < cut:
            cut = idx
    return text[:cut].strip() or text.strip()


def _summarize(obj: Any) -> str:
    """Extrai um texto legível de objetos variados do CrewAI (step/task output)."""
    if obj is None:
        return ""
    for attr in ("raw", "output", "result", "text", "return_values", "log"):
        val = getattr(obj, attr, None)
        if val:
            if isinstance(val, dict):
                val = val.get("output") or val.get("text") or json.dumps(val, ensure_ascii=False)
            return _trim(_strip_noise(str(val)))
    if isinstance(obj, dict):
        return _trim(_strip_noise(str(obj.get("output") or obj.get("text") or json.dumps(obj, ensure_ascii=False))))
    return _trim(_strip_noise(str(obj)))


def _agent_of(obj: Any) -> str:
    for attr in ("agent", "agent_role", "role"):
        val = getattr(obj, attr, None)
        if val:
            return _trim(getattr(val, "role", val))
    return "—"


def record_interaction(
    *,
    kind: str,
    context: str = "",
    agent: str = "",
    tool: str = "",
    detail: str = "",
) -> None:
    """Acrescenta uma linha ao trace. Tolerante a falhas (nunca quebra a crew)."""
    row = {
        "at": _now(),
        "kind": kind,
        "context": context,
        "agent": agent or "—",
        "tool": tool,
        "detail": _trim(detail),
    }
    try:
        with _LOCK:
            INTERACTIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
            with INTERACTIONS_FILE.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    except OSError as exc:
        logger.warning("Falha ao gravar interação: %s", exc)


def recent_interactions(limit: int = 40) -> list[dict]:
    """Últimas N interações (mais recentes primeiro), para o painel/endpoint."""
    if not INTERACTIONS_FILE.is_file():
        return []
    try:
        with INTERACTIONS_FILE.open("r", encoding="utf-8") as fh:
            tail = deque(fh, maxlen=max(1, min(limit, 500)))
    except OSError:
        return []
    rows: list[dict] = []
    for line in tail:
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    rows.reverse()
    return rows


def crew_callbacks(context: str, default_agent: str = "") -> dict[str, Callable]:
    """Retorna {step_callback, task_callback} prontos para `Crew(**...)`.

    default_agent rotula a interação quando o objeto do CrewAI não traz o agente
    (caso de crews de um agente só, como o autopilot e o modo dono).
    """

    def _agent(obj: Any) -> str:
        found = _agent_of(obj)
        return found if found and found != "—" else (default_agent or "—")

    def step_callback(step: Any) -> None:
        tool = _trim(getattr(step, "tool", "") or "")
        detail = _summarize(step)
        record_interaction(
            kind="tool" if tool else "step",
            context=context,
            agent=_agent(step),
            tool=tool,
            detail=detail,
        )

    def task_callback(task_output: Any) -> None:
        record_interaction(
            kind="task",
            context=context,
            agent=_agent(task_output),
            detail=_summarize(task_output),
        )

    return {"step_callback": step_callback, "task_callback": task_callback}
