"""Grafo comercial — tasks PROJ-LP com agent_action."""

from __future__ import annotations

import json
import logging
import re

from langgraph.graph import END, START, StateGraph

from laboratorio.autonomy.gateway import run_action
from laboratorio.graph.llm import chat
from laboratorio.graph.pilot import SYSTEM, node_cost_gate, node_finalize, node_load, node_plan
from laboratorio.graph.state import PilotState

logger = logging.getLogger("laboratorio.graph.commercial")

ACTIONS_HELP = """
Ações disponíveis (JSON array, max 3):
- append_task_note: {"task_id":"LP-PINTOR-002","note":"..."}
- notify_vitor: {"title":"...","detail":"..."}
- send_client_message: {"to_wa_id":"55...","body":"..."}  (pede APROVAR WA)
"""


def node_execute_actions(state: PilotState) -> dict:
    """LLM propõe ações; gateway executa (auto ou approval)."""
    user = (
        f"Task {state['task_id']}: {state.get('task_title','')}\n"
        f"Plano:\n{state.get('plan','')}\n\n"
        f"{ACTIONS_HELP}\n\n"
        "Responda APENAS JSON: {\"actions\": [{\"id\": \"append_task_note\", \"params\": {...}}, ...]}"
    )
    raw, cost = chat(SYSTEM, user, max_tokens=900)
    est = state.get("estimated_cost_usd", 0.0) + cost
    logs: list[str] = []

    try:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        data = json.loads(m.group(0) if m else raw)
        actions = data.get("actions") or []
    except (json.JSONDecodeError, TypeError):
        actions = [
            {
                "id": "append_task_note",
                "params": {
                    "task_id": state["task_id"],
                    "note": f"Grafo comercial: {raw[:200]}",
                },
            }
        ]

    for item in actions[:3]:
        aid = item.get("id", "")
        params = item.get("params") or {}
        try:
            result = run_action(aid, params, requested_by="langgraph_commercial")
            logs.append(f"{aid}: {result.output[:120]}")
        except Exception as exc:
            logs.append(f"{aid}: ERRO {exc}")

    deliverable = state.get("deliverable", "") + "\n\n**Ações:**\n" + "\n".join(f"- {l}" for l in logs)
    return {
        "deliverable": deliverable.strip(),
        "estimated_cost_usd": est,
        "phase": "actions_done",
    }


def build_commercial_graph():
    g = StateGraph(PilotState)
    g.add_node("load", node_load)
    g.add_node("plan", node_plan)
    g.add_node("execute", node_execute_actions)
    g.add_node("cost_gate", node_cost_gate)
    g.add_node("finalize", node_finalize)

    g.add_edge(START, "load")
    g.add_edge("load", "plan")
    g.add_edge("plan", "execute")
    g.add_edge("execute", "cost_gate")
    g.add_edge("cost_gate", "finalize")
    g.add_edge("finalize", END)
    return g
