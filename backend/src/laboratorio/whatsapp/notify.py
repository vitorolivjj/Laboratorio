"""Notificações proativas Caio → Vitor (delegadas pelo Ronaldo)."""

from __future__ import annotations

import logging
import uuid

from laboratorio.whatsapp.client import send_text_message
from laboratorio.whatsapp.logger import log_exchange
from laboratorio.whatsapp.vitor_auth import get_vitor_wa_id

logger = logging.getLogger("laboratorio.whatsapp.notify")


def format_vitor_alert(title: str, detail: str, action: str = "", ref: str = "") -> str:
    lines = [f"🔔 Ronaldo (via Caio)", "", title.strip()]
    if detail.strip():
        lines.extend(["", detail.strip()])
    if action.strip():
        lines.extend(["", f"Ação sugerida: {action.strip()}"])
    if ref.strip():
        lines.extend(["", f"Ref: {ref.strip()}"])
    return "\n".join(lines)


def notify_vitor(
    title: str,
    detail: str = "",
    *,
    action: str = "",
    ref: str = "",
    dry_run: bool = False,
) -> bool:
    """Envia alerta operacional ao Vitor via WhatsApp API."""
    wa_id = get_vitor_wa_id()
    body = format_vitor_alert(title, detail, action=action, ref=ref)
    msg_id = f"ronaldo-alert-{uuid.uuid4().hex[:12]}"

    if dry_run:
        logger.info("[dry-run] WhatsApp → %s: %s", wa_id, title[:80])
        return True

    try:
        send_text_message(wa_id, body)
        log_exchange(
            from_wa_id=wa_id,
            inbound="(notificação proativa Ronaldo)",
            outbound=body,
            message_id=msg_id,
            status="ok:ronaldo_escalacao",
        )
        logger.info("Alerta enviado ao Vitor: %s", title[:80])
        return True
    except Exception:
        logger.exception("Falha ao notificar Vitor via WhatsApp")
        log_exchange(
            from_wa_id=wa_id,
            inbound="(notificação proativa Ronaldo)",
            outbound="",
            message_id=msg_id,
            status="erro:escalacao",
        )
        return False
