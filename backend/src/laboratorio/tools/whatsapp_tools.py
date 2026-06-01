"""Ferramenta de envio de WhatsApp para o Caio."""

from __future__ import annotations

from pydantic import BaseModel, Field

from laboratorio.tools.base import BaseTool, safe
from laboratorio.whatsapp.client import send_text_message


class _EnviarWhatsAppArgs(BaseModel):
    to_wa_id: str = Field(..., description="ID/telefone WhatsApp do destinatário")
    body: str = Field(..., description="Texto da mensagem a enviar")


class EnviarWhatsAppTool(BaseTool):
    name: str = "enviar_whatsapp"
    description: str = (
        "Envia uma mensagem de texto via WhatsApp Business. "
        "Use só quando decidir ativamente responder/contatar um número."
    )
    args_schema: type[BaseModel] = _EnviarWhatsAppArgs

    @safe
    def _run(self, to_wa_id: str, body: str) -> str:
        resp = send_text_message(to_wa_id, body)
        msgs = resp.get("messages") if isinstance(resp, dict) else None
        mid = msgs[0].get("id") if msgs else "?"
        return f"WhatsApp enviado para {to_wa_id} (id={mid})."
