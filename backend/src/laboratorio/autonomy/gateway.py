"""Porta única para agentes executarem ações com autonomia graduada."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from laboratorio.autonomy.executor import execute
from laboratorio.autonomy.registry import get_action
from laboratorio.whatsapp.approvals import (
    request_agent_action,
    request_client_message,
    request_client_template,
)

logger = logging.getLogger("laboratorio.autonomy.gateway")


@dataclass
class ActionResult:
    action_id: str
    executed: bool
    pending: bool
    approval_id: str | None
    output: str


def run_action(
    action_id: str,
    params: dict[str, Any] | None = None,
    *,
    requested_by: str = "agent",
) -> ActionResult:
    """
    - tier auto: executa e retorna output
    - tier approval: enfileira WhatsApp; executa só após APROVAR
    """
    spec = get_action(action_id)
    params = dict(params or {})

    if spec.tier == "auto":
        out = execute(spec.id, params)
        return ActionResult(spec.id, executed=True, pending=False, approval_id=None, output=out)

    if spec.id == "send_client_message":
        aid = request_client_message(
            params["to_wa_id"],
            params["body"],
            requested_by=requested_by,
        )
        return ActionResult(
            spec.id,
            executed=False,
            pending=True,
            approval_id=aid,
            output=f"Aguardando APROVAR {aid} / RECUSAR {aid}",
        )

    if spec.id == "send_client_template":
        aid = request_client_template(
            params["to_wa_id"],
            params.get("template_name", "abertura_pintor_contato"),
            params.get("body_params") or [],
            language_code=params.get("language_code", "pt_BR"),
            requested_by=requested_by,
        )
        return ActionResult(
            spec.id,
            executed=False,
            pending=True,
            approval_id=aid,
            output=f"Aguardando APROVAR {aid} / RECUSAR {aid} (template Meta)",
        )

    summary = params.get("summary") or spec.label
    aid = request_agent_action(
        spec.id,
        summary,
        params,
        requested_by=requested_by,
    )
    return ActionResult(
        spec.id,
        executed=False,
        pending=True,
        approval_id=aid,
        output=f"Aguardando APROVAR {aid} / RECUSAR {aid}",
    )
