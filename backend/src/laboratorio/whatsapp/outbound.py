"""Envio WhatsApp com políticas de aprovação (Fase 0)."""

from __future__ import annotations

from typing import Any

from laboratorio.whatsapp.approvals import send_proactive_client_message
from laboratorio.whatsapp.client import send_text_message
from laboratorio.whatsapp.vitor_auth import is_vitor_authorized, normalize_wa_id


def send_to_recipient(
    to_wa_id: str,
    body: str,
    *,
    proactive: bool = False,
    requested_by: str = "agent",
) -> dict[str, Any]:
    """
    - proactive=False: resposta inbound (Caio atendimento) — envia direto.
    - proactive=True: agente iniciou — passa pela trava de aprovação.
    """
    if not proactive:
        result = send_text_message(to_wa_id, body)
        return {"pending": False, "sent": True, "api_response": result}

    if is_vitor_authorized(normalize_wa_id(to_wa_id)):
        result = send_text_message(to_wa_id, body)
        return {"pending": False, "sent": True, "api_response": result}

    return send_proactive_client_message(to_wa_id, body, requested_by=requested_by)
