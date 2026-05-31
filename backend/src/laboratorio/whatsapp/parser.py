"""Parse payloads do webhook Meta WhatsApp."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class InboundMessage:
    message_id: str
    from_wa_id: str
    text: str
    timestamp: str


def extract_text_messages(payload: dict[str, Any]) -> list[InboundMessage]:
    """Extrai mensagens de texto inbound do payload do webhook."""
    if payload.get("object") != "whatsapp_business_account":
        return []

    messages: list[InboundMessage] = []

    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for msg in value.get("messages", []):
                if msg.get("type") != "text":
                    continue
                text_body = (msg.get("text") or {}).get("body", "").strip()
                if not text_body:
                    continue
                messages.append(
                    InboundMessage(
                        message_id=msg["id"],
                        from_wa_id=msg["from"],
                        text=text_body,
                        timestamp=str(msg.get("timestamp", "")),
                    )
                )

    return messages
