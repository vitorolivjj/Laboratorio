"""Log de mensagens WhatsApp (markdown)."""

from __future__ import annotations

from datetime import datetime, timezone

from laboratorio.config import LOGS_DIR

WHATSAPP_LOG = LOGS_DIR / "whatsapp_mensagens.md"


def _ensure_log_file() -> None:
    if WHATSAPP_LOG.is_file():
        return
    WHATSAPP_LOG.parent.mkdir(parents=True, exist_ok=True)
    WHATSAPP_LOG.write_text(
        "# WhatsApp — log de mensagens\n\n"
        "Registro inbound/outbound do Caio via webhook (TASK-007).\n\n"
        "---\n\n"
        "<!-- Novas entradas acima desta linha -->\n",
        encoding="utf-8",
    )


def log_exchange(
    *,
    from_wa_id: str,
    inbound: str,
    outbound: str,
    message_id: str,
    status: str = "ok",
) -> None:
    _ensure_log_file()
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    entry = f"""### {stamp} — {from_wa_id}
- **message_id:** `{message_id}`
- **inbound:** {inbound}
- **outbound:** {outbound}
- **status:** {status}

"""
    text = WHATSAPP_LOG.read_text(encoding="utf-8")
    marker = "<!-- Novas entradas acima desta linha -->"
    if marker in text:
        text = text.replace(marker, entry + marker)
    else:
        text = entry + text
    WHATSAPP_LOG.write_text(text, encoding="utf-8")
