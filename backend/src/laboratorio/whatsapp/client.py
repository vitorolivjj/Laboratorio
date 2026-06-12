"""WhatsApp Business Cloud API — envio de mensagens."""

from __future__ import annotations

import logging
import os

import httpx

logger = logging.getLogger("laboratorio.whatsapp.client")

GRAPH_API_BASE = "https://graph.facebook.com"


class WhatsAppApiError(Exception):
    """Erro da Graph API com código Meta quando disponível."""

    def __init__(self, status_code: int, message: str, *, meta_code: int | None = None):
        self.status_code = status_code
        self.meta_code = meta_code
        super().__init__(message)


def _parse_api_error(response: httpx.Response) -> WhatsAppApiError:
    try:
        err = response.json().get("error") or {}
        msg = err.get("message") or response.text[:300]
        meta_code = err.get("code")
    except Exception:
        msg = response.text[:300]
        meta_code = None
    return WhatsAppApiError(response.status_code, msg, meta_code=meta_code)


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


def _post_message(payload: dict, *, phone_number_id: str | None = None) -> dict:
    # phone_number_id opcional: permite enviar por outro número da mesma WABA
    # (ex.: número de sondagem do Juarez) sem mexer no canal padrão (Caio).
    sender = (phone_number_id or "").strip() or _phone_number_id()
    url = f"{GRAPH_API_BASE}/{_api_version()}/{sender}/messages"
    with httpx.Client(timeout=30.0) as client:
        response = client.post(
            url,
            headers={
                "Authorization": f"Bearer {_access_token()}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        if not response.is_success:
            api_err = _parse_api_error(response)
            logger.error("WhatsApp API falhou: %s (meta=%s)", api_err, api_err.meta_code)
            raise api_err
        return response.json()


def send_text_message(to_wa_id: str, body: str, *, phone_number_id: str | None = None) -> dict:
    """Envia mensagem de texto via WhatsApp Cloud API."""
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_wa_id,
        "type": "text",
        "text": {"preview_url": True, "body": body},
    }
    logger.info("WhatsApp send → %s (%d chars)", to_wa_id, len(body))
    return _post_message(payload, phone_number_id=phone_number_id)


def send_template_message(
    to_wa_id: str,
    template_name: str,
    *,
    language_code: str = "pt_BR",
    body_params: list[str] | None = None,
    phone_number_id: str | None = None,
) -> dict:
    """Envia template Meta aprovado — obrigatório para iniciar conversa proativa."""
    template: dict = {
        "name": template_name,
        "language": {"code": language_code},
    }
    if body_params:
        template["components"] = [
            {
                "type": "body",
                "parameters": [{"type": "text", "text": p} for p in body_params],
            }
        ]

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_wa_id,
        "type": "template",
        "template": template,
    }

    logger.info(
        "WhatsApp template → %s name=%s params=%s",
        to_wa_id,
        template_name,
        body_params,
    )
    return _post_message(payload, phone_number_id=phone_number_id)


def render_template_body(template_name: str, body_params: list[str]) -> str:
    """Monta texto legível a partir do catálogo local (fallback texto livre)."""
    from laboratorio.whatsapp.templates import get_template

    spec = get_template(template_name)
    text = spec.meta_body
    for i, val in enumerate(body_params, start=1):
        text = text.replace(f"{{{{{i}}}}}", val)
    return text
