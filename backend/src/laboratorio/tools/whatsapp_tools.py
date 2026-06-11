"""Ferramenta de envio de WhatsApp para o Caio."""

from __future__ import annotations

from pydantic import BaseModel, Field

from laboratorio.tools.base import BaseTool, safe
from laboratorio.whatsapp.client import send_text_message


class _EnviarWhatsAppArgs(BaseModel):
    to_wa_id: str = Field(..., description="ID/telefone WhatsApp do destinatário")
    body: str = Field(..., description="Texto da mensagem a enviar")


class _AbordarLeadArgs(BaseModel):
    to_wa_id: str = Field(..., description="WhatsApp do lead (com DDI, ex.: 5533...)")
    template: str = Field(
        ...,
        description=(
            "Template aprovado por segmento: abordagem_clinica | abordagem_veterinaria | "
            "abordagem_servicos_profissionais | abordagem_reforma_obra | "
            "abordagem_oficina_tecnico"
        ),
    )
    nome_negocio: str = Field(..., description="Nome do negócio do lead (personaliza a mensagem)")


class AbordarLeadTool(BaseTool):
    name: str = "abordar_lead"
    description: str = (
        "Abordagem comercial proativa do Caio com TEMPLATE APROVADO pelo Vitor "
        "(sem aprovação individual; limite diário). Use só para primeiro contato "
        "com lead qualificado do CRM. Mensagem fora de template → enviar_whatsapp."
    )
    args_schema: type[BaseModel] = _AbordarLeadArgs

    @safe
    def _run(self, to_wa_id: str, template: str, nome_negocio: str) -> str:
        from laboratorio.whatsapp.abordagem import abordar

        return abordar(to_wa_id, template, nome_negocio)


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
