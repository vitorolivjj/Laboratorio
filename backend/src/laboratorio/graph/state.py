"""Estado do grafo piloto."""

from __future__ import annotations

from typing import TypedDict


class PilotState(TypedDict, total=False):
    task_id: str
    task_title: str
    task_body: str
    objective: str
    semantic_context: str
    plan: str
    deliverable: str
    estimated_cost_usd: float
    approval_id: str
    phase: str
    error: str
