"""Notificações proativas Caio → Vitor (delegadas pelo Ronaldo)."""

from __future__ import annotations

import logging
import uuid

from laboratorio.whatsapp.caio_session import is_duplicate_outbound, record_outbound
from laboratorio.whatsapp.client import send_text_message
from laboratorio.whatsapp.logger import log_exchange
from laboratorio.whatsapp.vitor_auth import get_vitor_wa_id

logger = logging.getLogger("laboratorio.whatsapp.notify")


def format_vitor_alert(title: str, detail: str, action: str = "", ref: str = "") -> str:
    lines = ["🔔 Ronaldo (via Caio)", "", title.strip()]
    if detail.strip():
        lines.extend(["", detail.strip()])
    if action.strip():
        lines.extend(["", f"Ação sugerida: {action.strip()}"])
    if ref.strip():
        lines.extend(["", f"Ref: {ref.strip()}"])
    return "\n".join(lines)


def format_vitor_digest(alerts: list[dict[str, str]]) -> str:
    """Um único WhatsApp com N alertas da mesma patrulha/ciclo."""
    if not alerts:
        return ""
    if len(alerts) == 1:
        a = alerts[0]
        return format_vitor_alert(
            a.get("title", ""),
            a.get("detail", ""),
            action=a.get("action", ""),
            ref=a.get("ref", ""),
        )
    lines = [f"🔔 Ronaldo — {len(alerts)} alertas", ""]
    for i, a in enumerate(alerts, 1):
        lines.append(f"{i}. {a.get('title', 'Alerta').strip()}")
        if a.get("detail", "").strip():
            lines.append(a["detail"].strip()[:220])
        if a.get("ref", "").strip():
            lines.append(f"Ref: {a['ref'].strip()}")
        lines.append("")
    return "\n".join(lines).strip()


def _send_vitor_body(body: str, *, msg_prefix: str = "ronaldo-alert", dry_run: bool = False) -> bool:
    wa_id = get_vitor_wa_id()
    msg_id = f"{msg_prefix}-{uuid.uuid4().hex[:12]}"

    if dry_run:
        logger.info("[dry-run] WhatsApp → %s: %s", wa_id, body[:80])
        return True

    if is_duplicate_outbound(wa_id, body, window_sec=300):
        logger.info("Alerta Vitor ignorado (duplicata 5min): %s", body[:60])
        return False

    try:
        send_text_message(wa_id, body)
        record_outbound(wa_id, body)
        log_exchange(
            from_wa_id=wa_id,
            inbound="(notificação proativa Ronaldo)",
            outbound=body,
            message_id=msg_id,
            status="ok:ronaldo_escalacao",
        )
        logger.info("Alerta enviado ao Vitor (%d chars)", len(body))
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


def notify_vitor(
    title: str,
    detail: str = "",
    *,
    action: str = "",
    ref: str = "",
    dry_run: bool = False,
) -> bool:
    """Envia alerta operacional ao Vitor via WhatsApp API."""
    body = format_vitor_alert(title, detail, action=action, ref=ref)
    return _send_vitor_body(body, dry_run=dry_run)


def notify_vitor_digest(
    alerts: list[dict[str, str]],
    *,
    dry_run: bool = False,
) -> bool:
    """Vários alertas no mesmo ciclo → 1 mensagem só."""
    body = format_vitor_digest(alerts)
    if not body:
        return False
    return _send_vitor_body(body, msg_prefix="ronaldo-digest", dry_run=dry_run)
