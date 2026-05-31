"""WhatsApp Business Cloud API — envio de mensagens."""

from __future__ import annotations

import logging
import os

import httpx

logger = logging.getLogger("laboratorio.whatsapp.client")

GRAPH_API_BASE = "https://graph.facebook.com"


def _api_version() -> str:
    return os.getenv("WHATSAPP_API_VERSION", "v21.0").strip()


def _phone_number_id() -> str:
    phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "").strip()
    if not phone_id:
        raise RuntimeError("WHATSAPP_PHONE_NUMBER_ID não configurado no .env")
    return phone_id


def _access_token() -> str:
    token = os.getenv("WHATSAPP_ACCESS_TOKEN", "").strip()
    if not token:
        raise RuntimeError("WHATSAPP_ACCESS_TOKEN não configurado no .env")
    return token


def send_text_message(to_wa_id: str, body: str) -> dict:
    """Envia mensagem de texto via WhatsApp Cloud API."""
    url = f"{GRAPH_API_BASE}/{_api_version()}/{_phone_number_id()}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_wa_id,
        "type": "text",
        "text": {"preview_url": False, "body": body},
    }

    logger.info("WhatsApp send → %s (%d chars)", to_wa_id, len(body))

    with httpx.Client(timeout=30.0) as client:
        response = client.post(
            url,
            headers={
                "Authorization": f"Bearer {_access_token()}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        response.raise_for_status()
        return response.json()
