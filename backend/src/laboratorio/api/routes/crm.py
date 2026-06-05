"""Rotas API — CRM (comercial + produção): leads, análise e arquivos.

Lista e detalhe de leads para o painel: o comercial vê básico + perfil + como
abordar; a produção vê os arquivos (fotos de trabalho / materiais) com URL
pública pra montar a página. Protegido pelo mesmo token do painel.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from laboratorio.api.auth import require_panel_token
from laboratorio.db import lead_assets
from laboratorio.repositories.leads import get_lead_repository

router = APIRouter(
    prefix="/api/crm",
    tags=["crm"],
    dependencies=[Depends(require_panel_token)],
)

_LIST_FIELDS = ("id", "nome", "cidade", "contato", "segment", "status", "etapa", "projeto", "perfil")


@router.get("/leads")
def list_leads(response: Response, segment: str = "", limit: int = 300) -> dict:
    """Lista enxuta de leads (+ contagem de arquivos), opcionalmente por segmento."""
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    repo = get_lead_repository()
    leads = repo.by_segment(segment) if segment.strip() else repo.all()
    leads = leads[: max(1, min(limit, 1000))]
    counts = lead_assets.file_counts()
    perfis = lead_assets.perfis()
    out = []
    for ld in leads:
        lid = ld.get("id")
        row = {k: ld.get(k, "") for k in _LIST_FIELDS}
        row["perfil"] = perfis.get(lid) or row.get("perfil") or ""
        row["arquivos"] = counts.get(lid, 0)
        out.append(row)
    return {"leads": out, "total": len(out)}


@router.get("/leads/{lead_id}")
def lead_detail(response: Response, lead_id: str) -> dict:
    """Detalhe completo do lead: básico + análise + arquivos (com URL)."""
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    repo = get_lead_repository()
    lead = repo.get(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail=f"Lead {lead_id} não encontrado")
    return {
        "lead": lead,
        "analise": lead_assets.get_analysis(lead_id),
        "arquivos": lead_assets.list_files(lead_id),
    }


@router.post("/leads/{lead_id}/files/{file_id}/aprovar")
def approve_file(lead_id: str, file_id: int, aprovado: bool = True) -> dict:
    """Curadoria (Loide/produção): aprova/rejeita um arquivo para a página."""
    if not lead_assets.set_approved(file_id, aprovado):
        raise HTTPException(status_code=404, detail=f"Arquivo {file_id} não encontrado")
    return {"ok": True, "file_id": file_id, "aprovado": aprovado}
