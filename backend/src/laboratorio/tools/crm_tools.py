"""Ferramentas de CRM para Caio e Donizete."""

from __future__ import annotations

from pydantic import BaseModel, Field

from laboratorio.ops import crm_store
from laboratorio.tools.base import BaseTool, safe


class LerCRMTool(BaseTool):
    name: str = "ler_crm"
    description: str = "Lista os leads atuais do CRM (ID e nome). Use para saber quem já está cadastrado."

    @safe
    def _run(self) -> str:
        return crm_store.render_leads()


class _AdicionarLeadArgs(BaseModel):
    nome: str = Field(..., description="Nome ou @perfil do lead")
    contato: str = Field("", description="Telefone/WhatsApp/e-mail, se houver")
    cidade: str = Field("", description="Cidade do lead")
    servico: str = Field("", description="Serviço/segmento de interesse")
    origem: str = Field("", description="De onde veio o lead (canal/campanha)")
    observacoes: str = Field("", description="Contexto da captação")
    score: str = Field("0", description="Score de 0 a 5")
    temperatura: str = Field("frio", description="frio | morno | quente")
    prioridade: str = Field("P2", description="P1 | P2 | P3")
    status: str = Field("novo", description="novo | qualificado | entregue_caio | abordado | convertido | sem_resposta | descartado")


class AdicionarLeadTool(BaseTool):
    name: str = "adicionar_lead"
    description: str = "Cria um novo lead no CRM. O ID (LEAD-XXX) é gerado automaticamente."
    args_schema: type[BaseModel] = _AdicionarLeadArgs

    @safe
    def _run(self, **kwargs) -> str:
        return crm_store.add_lead(**kwargs)


class _AtualizarLeadArgs(BaseModel):
    lead_id: str = Field(..., description="ID do lead, ex.: LEAD-001")
    status: str = Field(..., description="Novo status (ver lista de status válidos)")
    nota: str = Field("", description="Observação opcional a anexar")


class AtualizarStatusLeadTool(BaseTool):
    name: str = "atualizar_status_lead"
    description: str = "Atualiza o status de um lead existente (e anexa observação opcional)."
    args_schema: type[BaseModel] = _AtualizarLeadArgs

    @safe
    def _run(self, lead_id: str, status: str, nota: str = "") -> str:
        return crm_store.update_lead_status(lead_id, status, nota)
