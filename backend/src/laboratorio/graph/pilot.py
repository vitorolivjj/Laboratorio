"""Grafo piloto — plan → work → cost gate → finalize."""

from __future__ import annotations

import logging

from langgraph.graph import END, START, StateGraph

from laboratorio.graph.llm import chat
from laboratorio.graph.state import PilotState
from laboratorio.graph.tasks_io import append_pilot_output, load_task, log_event
from laboratorio.memory.context import augment_with_semantic_memory
from laboratorio.whatsapp.approvals import cost_requires_approval, cost_threshold_usd
from laboratorio.whatsapp.notify import notify_vitor

logger = logging.getLogger("laboratorio.graph.pilot")

SYSTEM = """Você é Ronaldo Maestro executando uma task do Laboratório via motor LangGraph (piloto Fase 2).
Responda em português, objetivo, formato markdown leve. Máximo 25 linhas salvo se pedido relatório."""


def node_load(state: PilotState) -> dict:
    tid = state["task_id"]
    task = load_task(tid)
    query = f"{task['title']} {task['objective']}"
    semantic = augment_with_semantic_memory(query, top_k=5)
    return {
        "task_title": task["title"],
        "task_body": task["body"][:4000],
        "objective": task["objective"],
        "semantic_context": semantic,
        "phase": "loaded",
    }


def node_plan(state: PilotState) -> dict:
    user = (
        f"Task {state['task_id']}: {state['task_title']}\n\n"
        f"Objetivo:\n{state['objective']}\n\n"
        f"{state.get('semantic_context', '')}\n\n"
        "Produza um plano numerado (máx. 7 passos) para concluir esta task no piloto."
    )
    plan, cost = chat(SYSTEM, user, max_tokens=800)
    return {
        "plan": plan,
        "estimated_cost_usd": state.get("estimated_cost_usd", 0.0) + cost,
        "phase": "planned",
    }


def node_work(state: PilotState) -> dict:
    user = (
        f"Task {state['task_id']}\nPlano:\n{state['plan']}\n\n"
        "Execute o piloto: gere o **Relatório de validação LangGraph** com seções:\n"
        "1. O que foi validado\n2. Checkpoints\n3. Memória semântica usada\n"
        "4. Próximo passo (Fase 3 skills)\n"
        "Seja concreto — esta entrega vai para o arquivo da task."
    )
    deliverable, cost = chat(SYSTEM, user, max_tokens=1200)
    return {
        "deliverable": deliverable,
        "estimated_cost_usd": state.get("estimated_cost_usd", 0.0) + cost,
        "phase": "worked",
    }


def node_cost_gate(state: PilotState) -> dict:
    est = float(state.get("estimated_cost_usd") or 0)
    out: dict = {"phase": "cost_ok"}
    if cost_requires_approval(est):
        notify_vitor(
            f"Gasto alto — piloto {state['task_id']}",
            f"Estimativa US$ {est:.3f} (limiar US$ {cost_threshold_usd():.2f}). Grafo segue.",
            ref=state["task_id"],
        )
        out["phase"] = "cost_notified"
        logger.info("Gasto alto notificado ao Vitor")
    return out


def node_finalize(state: PilotState) -> dict:
    tid = state["task_id"]
    report = (
        f"**Plano**\n{state.get('plan', '')}\n\n"
        f"**Entrega**\n{state.get('deliverable', '')}\n\n"
        f"**Custo estimado:** US$ {state.get('estimated_cost_usd', 0):.4f} "
        f"(limiar US$ {cost_threshold_usd():.2f})\n"
    )
    if state.get("approval_id"):
        report += f"\n**Aprovação custo:** pendente [{state['approval_id']}]\n"
    append_pilot_output(tid, report)
    log_event(tid, f"Piloto LangGraph concluído · custo ~US$ {state.get('estimated_cost_usd', 0):.4f}")
    return {"phase": "completed"}


def build_pilot_graph():
    g = StateGraph(PilotState)
    g.add_node("load", node_load)
    g.add_node("plan", node_plan)
    g.add_node("work", node_work)
    g.add_node("cost_gate", node_cost_gate)
    g.add_node("finalize", node_finalize)

    g.add_edge(START, "load")
    g.add_edge("load", "plan")
    g.add_edge("plan", "work")
    g.add_edge("work", "cost_gate")
    g.add_edge("cost_gate", "finalize")
    g.add_edge("finalize", END)
    return g
