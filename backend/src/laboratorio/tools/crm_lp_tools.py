"""Ferramentas CRM Landing Pintor (PROJ-LP)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from laboratorio.ops import crm_lp_store, tool_bridge
from laboratorio.tools.base import BaseTool, safe


class LerCRMLPTool(BaseTool):
    name: str = "ler_crm_lp"
    description: str = (
        "Lista leads do CRM Landing Pintor (funil PROJ-LP: prospectado, pronto_pra_pagina, …)."
    )

    @safe
    def _run(self) -> str:
        return tool_bridge.ler_crm_lp()


class _AdicionarLeadLPArgs(BaseModel):
    nome: str = Field(..., description="Nome ou @perfil do pintor")
    cidade: str = Field("", description="Cidade capturada no stalk")
    servico: str = Field("Pintura", description="Serviço")
    contato: str = Field("", description="WhatsApp/telefone se público")
    grupo_origem: str = Field("", description="Nome do grupo Facebook")
    origem: str = Field("", description="Canal: post-isca, garimpo, stalk…")
    tags: str = Field("", description="indicacao | autopromocao")
    status: str = Field(
        "prospectado",
        description="prospectado | pronto_pra_pagina | previa_no_ar | abordado | ativo | recusou",
    )
    link_origem: str = Field("", description="URL do perfil ou post")
    observacoes: str = Field("", description="Contexto do garimpo/stalk")


class AdicionarLeadLPTool(BaseTool):
    name: str = "adicionar_lead_lp"
    description: str = (
        "Registra lead no CRM Landing Pintor (crm_landing_pintor.md). "
        "Use só com dados reais vistos no Facebook via ferramentas fb_*."
    )
    args_schema: type[BaseModel] = _AdicionarLeadLPArgs

    @safe
    def _run(self, **kwargs) -> str:
        lead = crm_lp_store.add_lead_lp(**kwargs)
        crm_lp_store.ensure_lead_capture_dir(
            lead["slug"],
            lead_id=lead["id"],
            perfil_url=kwargs.get("link_origem") or "",
            bio_raw=kwargs.get("observacoes") or "",
        )
        return lead["message"] + f" Pasta: frontend/lp-pintor/leads/{lead['slug']}/captura/"


class _AtualizarLeadLPArgs(BaseModel):
    lead_id: str = Field(..., description="Ex.: LEAD-002")
    status: str = Field(..., description="Etapa do funil LP")
    nota: str = Field("", description="Observação opcional")


class AtualizarStatusLeadLPTool(BaseTool):
    name: str = "atualizar_status_lead_lp"
    description: str = "Atualiza status de lead no CRM Landing Pintor."
    args_schema: type[BaseModel] = _AtualizarLeadLPArgs

    @safe
    def _run(self, lead_id: str, status: str, nota: str = "") -> str:
        return crm_lp_store.update_lead_lp(lead_id, status, nota)
