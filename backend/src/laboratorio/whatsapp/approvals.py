"""Aprovação do Vitor por WhatsApp — trava para ações sensíveis (Fase 0)."""

from __future__ import annotations

import json
import logging
import os
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Literal

from laboratorio.config import LOGS_DIR, load_env
from laboratorio.whatsapp.client import (
    WhatsAppApiError,
    render_template_body,
    send_template_message,
    send_text_message,
)
from laboratorio.whatsapp.logger import log_exchange
from laboratorio.whatsapp.vitor_auth import get_vitor_wa_id, is_vitor_authorized, normalize_wa_id

logger = logging.getLogger("laboratorio.whatsapp.approvals")

STATE_FILE = LOGS_DIR / "approvals_pending.json"
Decision = Literal["approve", "reject"]

_APPROVAL_CMD = re.compile(
    r"^\s*(aprovar|recusar|approve|reject)\s+([A-F0-9]{4})\s*$",
    re.IGNORECASE,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _short_id() -> str:
    return uuid.uuid4().hex[:4].upper()


def _load_state() -> dict[str, dict[str, Any]]:
    if not STATE_FILE.is_file():
        return {}
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def _save_state(state: dict[str, dict[str, Any]]) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def cost_threshold_usd() -> float:
    load_env()
    raw = os.getenv("APPROVAL_COST_THRESHOLD_USD", "1.0").strip()
    try:
        return max(0.0, float(raw))
    except ValueError:
        return 1.0


def cost_requires_approval(estimated_usd: float) -> bool:
    return estimated_usd >= cost_threshold_usd()


def parse_owner_decision(text: str) -> tuple[Decision, str] | None:
    """Detecta 'APROVAR A1B2' ou 'RECUSAR A1B2' (só resposta dedicada)."""
    m = _APPROVAL_CMD.match(text.strip())
    if not m:
        return None
    verb, aid = m.group(1).lower(), m.group(2).upper()
    action: Decision = "approve" if verb in ("aprovar", "approve") else "reject"
    return action, aid


def _format_request(kind: str, short_id: str, summary: str) -> str:
    kind_label = {
        "client_message": "Mensagem a cliente",
        "client_template": "Template Meta (abertura proativa)",
        "high_cost": "Gasto alto",
        "agent_action": "Ação do agente",
        "evolution_batch": "Autoevolução (resumo diário)",
    }.get(kind, kind)
    return (
        f"🔔 Preciso da sua aprovação [{short_id}]\n"
        f"{kind_label}: {summary}\n\n"
        f"Responda: APROVAR {short_id} ou RECUSAR {short_id}"
    )


def _notify_vitor_request(body: str, short_id: str) -> None:
    wa = get_vitor_wa_id()
    send_text_message(wa, body)
    log_exchange(
        from_wa_id=wa,
        inbound="(pedido de aprovação)",
        outbound=body,
        message_id=f"approval-req-{short_id}",
        status="ok:approval_request",
    )


def _create_pending(
    *,
    kind: str,
    summary: str,
    payload: dict[str, Any],
    requested_by: str = "agent",
) -> str:
    short_id = _short_id()
    while short_id in _load_state():
        short_id = _short_id()

    state = _load_state()
    state[short_id] = {
        "id": short_id,
        "kind": kind,
        "status": "pending",
        "summary": summary,
        "payload": payload,
        "requested_by": requested_by,
        "created_at": _now_iso(),
    }
    _save_state(state)

    request_msg = _format_request(kind, short_id, summary)
    _notify_vitor_request(request_msg, short_id)
    logger.info("Aprovação pendente %s (%s)", short_id, kind)
    return short_id


def request_client_message(
    to_wa_id: str,
    body: str,
    *,
    requested_by: str = "agent",
) -> str:
    """Enfileira envio proativo a cliente — notifica Vitor e retorna ID pendente."""
    to_norm = normalize_wa_id(to_wa_id)
    if is_vitor_authorized(to_norm):
        raise ValueError("Canal Vitor não usa trava de mensagem a cliente")

    preview = body.strip()
    if len(preview) > 120:
        preview = preview[:117] + "..."
    summary = f"Enviar ao cliente +{to_norm[-11:]}: \"{preview}\""
    return _create_pending(
        kind="client_message",
        summary=summary,
        payload={"to_wa_id": to_norm, "body": body.strip()},
        requested_by=requested_by,
    )


def request_client_template(
    to_wa_id: str,
    template_name: str,
    body_params: list[str],
    *,
    language_code: str = "pt_BR",
    requested_by: str = "agent",
) -> str:
    """Enfileira template Meta aprovado — única forma de abrir conversa proativa."""
    from laboratorio.whatsapp.templates import get_template

    to_norm = normalize_wa_id(to_wa_id)
    if is_vitor_authorized(to_norm):
        raise ValueError("Canal Vitor não usa trava de mensagem a cliente")

    spec = get_template(template_name)
    if len(body_params) != len(spec.body_params):
        raise ValueError(
            f"Template {template_name} exige {len(spec.body_params)} params: {spec.body_params}"
        )

    preview = spec.meta_body
    for i, val in enumerate(body_params, start=1):
        preview = preview.replace(f"{{{{{i}}}}}", val)
    if len(preview) > 120:
        preview = preview[:117] + "..."
    summary = f"Template [{template_name}] → +{to_norm[-11:]}: \"{preview}\""
    return _create_pending(
        kind="client_template",
        summary=summary,
        payload={
            "to_wa_id": to_norm,
            "template_name": spec.name,
            "body_params": body_params,
            "language_code": language_code,
        },
        requested_by=requested_by,
    )


def request_evolution_batch(
    *,
    summary: str,
    proposals: list[dict[str, Any]],
    digest_date: str,
    requested_by: str = "evolution_daily",
) -> str:
    """Lote de propostas do resumo diário — aplica só após APROVAR."""
    n = len(proposals)
    short_summary = f"Resumo {digest_date}: {n} proposta(s). {summary[:100]}"
    return _create_pending(
        kind="evolution_batch",
        summary=short_summary,
        payload={
            "digest_date": digest_date,
            "summary": summary,
            "proposals": proposals,
        },
        requested_by=requested_by,
    )


def request_agent_action(
    action_id: str,
    summary: str,
    params: dict[str, Any],
    *,
    requested_by: str = "agent",
) -> str:
    """Pede OK antes de executar ação catalogada (Fase 3)."""
    return _create_pending(
        kind="agent_action",
        summary=f"{summary} [{action_id}]",
        payload={"action_id": action_id, "params": params},
        requested_by=requested_by,
    )


def request_high_cost(
    description: str,
    estimated_usd: float,
    *,
    action_key: str,
    requested_by: str = "agent",
) -> str:
    """Pede OK antes de ação com custo estimado acima do limiar."""
    summary = f"{description} (~US$ {estimated_usd:.2f}, limiar US$ {cost_threshold_usd():.2f})"
    return _create_pending(
        kind="high_cost",
        summary=summary,
        payload={
            "description": description,
            "estimated_usd": estimated_usd,
            "action_key": action_key,
        },
        requested_by=requested_by,
    )


def _execute_pending(item: dict[str, Any]) -> str:
    kind = item.get("kind")
    payload = item.get("payload") or {}

    if kind == "client_message":
        to_wa = payload.get("to_wa_id", "")
        body = payload.get("body", "")
        if not to_wa or not body:
            raise ValueError("Payload de mensagem incompleto")
        send_text_message(to_wa, body)
        log_exchange(
            from_wa_id=to_wa,
            inbound="(envio proativo aprovado)",
            outbound=body,
            message_id=f"approval-send-{item['id']}",
            status="ok:client_message_approved",
        )
        return f"✓ Mensagem enviada ao cliente +{to_wa[-11:]}"

    if kind == "client_template":
        to_wa = payload.get("to_wa_id", "")
        template_name = payload.get("template_name", "")
        body_params = payload.get("body_params") or []
        language_code = payload.get("language_code", "pt_BR")
        if not to_wa or not template_name:
            raise ValueError("Payload de template incompleto")
        try:
            send_template_message(
                to_wa,
                template_name,
                language_code=language_code,
                body_params=body_params,
            )
            preview = f"[template:{template_name}] " + " · ".join(body_params)
            status = "ok:client_template_approved"
            detail = f"✓ Template [{template_name}] enviado ao cliente +{to_wa[-11:]}"
        except WhatsAppApiError as exc:
            if exc.meta_code != 132001:
                raise
            body = render_template_body(template_name, body_params)
            send_text_message(to_wa, body)
            preview = body
            status = "ok:client_template_fallback_text"
            detail = (
                f"✓ Template [{template_name}] não encontrado na Meta (132001) — "
                f"enviado como texto (janela 24h) para +{to_wa[-11:]}"
            )
        from laboratorio.whatsapp.caio_session import mark_script_sent, record_outbound

        mark_script_sent(to_wa, "abertura")
        dedup_body = (
            body
            if status == "ok:client_template_fallback_text"
            else render_template_body(template_name, body_params)
        )
        record_outbound(to_wa, dedup_body)
        log_exchange(
            from_wa_id=to_wa,
            inbound="(template proativo aprovado)",
            outbound=preview,
            message_id=f"approval-template-{item['id']}",
            status=status,
        )
        return detail

    if kind == "high_cost":
        key = payload.get("action_key", "?")
        return (
            f"✓ Gasto aprovado — pode executar: {payload.get('description', key)[:80]}\n"
            f"Ref: {key}"
        )

    if kind == "agent_action":
        from laboratorio.autonomy.executor import execute

        action_id = payload.get("action_id", "")
        params = payload.get("params") or {}
        if not action_id:
            raise ValueError("action_id ausente no payload")
        out = execute(action_id, params)
        return f"✓ Ação executada: {action_id}\n{out[:500]}"

    if kind == "evolution_batch":
        from laboratorio.evolution.digest import apply_evolution_batch

        return "✓ Autoevolução aplicada:\n" + apply_evolution_batch(item)

    raise ValueError(f"Tipo de aprovação desconhecido: {kind}")


def handle_owner_decision(action: Decision, approval_id: str) -> str:
    """Processa APROVAR/RECUSAR do Vitor. Retorna texto de resposta."""
    aid = approval_id.upper()
    state = _load_state()
    item = state.get(aid)
    if not item:
        return f"ID {aid} não encontrado ou já expirou."
    if item.get("status") != "pending":
        return f"ID {aid} já foi {item.get('status')}."

    if action == "reject":
        item["status"] = "rejected"
        item["resolved_at"] = _now_iso()
        state[aid] = item
        _save_state(state)
        logger.info("Aprovação %s recusada", aid)
        return f"✗ Recusado [{aid}] — nada foi executado."

    try:
        result_detail = _execute_pending(item)
    except WhatsAppApiError as exc:
        logger.exception("Falha Meta ao executar aprovação %s", aid)
        code = f" (Meta #{exc.meta_code})" if exc.meta_code else ""
        return f"Erro Meta [{aid}]: {exc}{code}"
    except Exception as exc:
        logger.exception("Falha ao executar aprovação %s", aid)
        return f"Erro ao executar [{aid}]: {exc}"

    item["status"] = "approved"
    item["resolved_at"] = _now_iso()
    state[aid] = item
    _save_state(state)
    logger.info("Aprovação %s concedida", aid)
    return f"✓ Aprovado [{aid}]\n{result_detail}"


_QUEUE_APPROVE_RE = re.compile(
    r"^\s*aprovar\s+fila\s+([\d,\s]+)\s*$",
    re.IGNORECASE,
)


def _apply_queue_proposals(prop_ids: list[int]) -> str:
    from laboratorio.evolution.apply import apply_proposals
    from laboratorio.evolution.propose import list_pending_proposals, mark_proposal_applied

    pending = {int(p["id"]): p for p in list_pending_proposals(limit=100)}
    selected = [pending[i] for i in prop_ids if i in pending]
    if not selected:
        return "Nenhuma proposta pendente com esses IDs na fila."
    batch = [
        {
            "id": p["id"],
            "target": p.get("target", "aprendizados"),
            "title": p.get("title", ""),
            "body": p.get("body", ""),
        }
        for p in selected
    ]
    results = apply_proposals(batch)
    for p in selected:
        mark_proposal_applied(prop_id=int(p["id"]))
    return "✓ Fila aplicada:\n" + "\n".join(results)


def try_handle_approval_message(text: str) -> str | None:
    """Se for comando de aprovação, processa e retorna resposta; senão None."""
    qm = _QUEUE_APPROVE_RE.match(text.strip())
    if qm:
        ids = [int(x) for x in re.findall(r"\d+", qm.group(1))]
        if ids:
            return _apply_queue_proposals(ids)

    parsed = parse_owner_decision(text)
    if not parsed:
        return None
    action, aid = parsed
    return handle_owner_decision(action, aid)


def send_proactive_client_template(
    to_wa_id: str,
    template_name: str,
    body_params: list[str],
    *,
    language_code: str = "pt_BR",
    requested_by: str = "agent",
) -> dict[str, Any]:
    """Abertura proativa via template Meta aprovado."""
    approval_id = request_client_template(
        to_wa_id,
        template_name,
        body_params,
        language_code=language_code,
        requested_by=requested_by,
    )
    return {
        "pending": True,
        "approval_id": approval_id,
        "message": (
            f"Aguardando sua aprovação no WhatsApp [{approval_id}]. "
            "Responda APROVAR ou RECUSAR."
        ),
    }


def send_proactive_client_message(
    to_wa_id: str,
    body: str,
    *,
    requested_by: str = "agent",
) -> dict[str, Any]:
    """
    Envio proativo a lead/cliente (não resposta inbound).
    Retorna {pending: True, approval_id} — envio real só após OK do Vitor.
    """
    approval_id = request_client_message(to_wa_id, body, requested_by=requested_by)
    return {
        "pending": True,
        "approval_id": approval_id,
        "message": (
            f"Aguardando sua aprovação no WhatsApp [{approval_id}]. "
            "Responda APROVAR ou RECUSAR."
        ),
    }
