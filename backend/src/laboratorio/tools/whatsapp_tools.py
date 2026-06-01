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
        from laboratorio.whatsapp.owner import is_owner

        # Mensagem a CLIENTE (não-dono) iniciada por agente exige aprovação do Vitor.
        # Respostas diretas a inbound não passam por aqui (vão pelo handler), então
        # o atendimento automático do Caio continua instantâneo.
        if not is_owner(to_wa_id):
            from laboratorio.ops.approvals import request_approval

            rec = request_approval(
                kind="whatsapp_message",
                summary=f'Enviar ao cliente +{to_wa_id}:\n"{body[:300]}"',
                payload={"to": to_wa_id, "body": body},
            )
            return (
                f"Mensagem para {to_wa_id} aguardando aprovação do Vitor no WhatsApp "
                f"(código {rec['id']}). NÃO foi enviada ainda."
            )

        resp = send_text_message(to_wa_id, body)
        msgs = resp.get("messages") if isinstance(resp, dict) else None
        mid = msgs[0].get("id") if msgs else "?"
        return f"WhatsApp enviado para {to_wa_id} (id={mid})."
