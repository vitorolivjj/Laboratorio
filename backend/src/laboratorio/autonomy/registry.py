"""Catálogo de ações — tier auto (executa) ou approval (pede OK)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Tier = Literal["auto", "approval"]


@dataclass(frozen=True)
class ActionSpec:
    id: str
    tier: Tier
    label: str
    approval_kind: str | None = None  # client_message | agent_action | high_cost


ACTIONS: dict[str, ActionSpec] = {
    "log_event": ActionSpec("log_event", "auto", "Registrar evento em logs/eventos.md"),
    "memory_recall": ActionSpec("memory_recall", "auto", "Busca memória semântica"),
    "patrol_check": ActionSpec("patrol_check", "auto", "Patrulha operacional (dry-run)"),
    "notify_vitor": ActionSpec("notify_vitor", "auto", "Alerta operacional ao Vitor"),
    "append_task_note": ActionSpec("append_task_note", "auto", "Nota em arquivo da task"),
    "send_client_message": ActionSpec(
        "send_client_message",
        "approval",
        "Mensagem proativa a cliente (só dentro da janela 24h ou resposta)",
        approval_kind="client_message",
    ),
    "send_client_template": ActionSpec(
        "send_client_template",
        "approval",
        "Template Meta — abertura proativa a lead",
        approval_kind="client_template",
    ),
    "run_graph_pilot": ActionSpec(
        "run_graph_pilot",
        "approval",
        "Executar piloto LangGraph",
        approval_kind="agent_action",
    ),
}


def get_action(action_id: str) -> ActionSpec:
    aid = action_id.strip().lower()
    if aid not in ACTIONS:
        raise KeyError(f"Ação desconhecida: {action_id}. Válidas: {', '.join(ACTIONS)}")
    return ACTIONS[aid]
