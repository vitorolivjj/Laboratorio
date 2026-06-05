"""Rotas API — CRM (comercial + produção): leads, análise e arquivos.

Lista e detalhe de leads para o painel: o comercial vê básico + perfil + como
abordar; a produção vê os arquivos (fotos de trabalho / materiais) com URL
pública pra montar a página. Protegido pelo mesmo token do painel.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel

from laboratorio.api.auth import require_panel_token
from laboratorio.db import lead_assets, storage
from laboratorio.ops import crm_enrich
from laboratorio.repositories.leads import get_lead_repository

router = APIRouter(
    prefix="/api/crm",
    tags=["crm"],
    dependencies=[Depends(require_panel_token)],
)

_LIST_FIELDS = ("id", "nome", "cidade", "contato", "segment", "status", "etapa", "projeto", "perfil")
_MAX_UPLOAD = 15 * 1024 * 1024  # 15 MB por arquivo


def _require_lead(lead_id: str) -> dict:
    lead = get_lead_repository().get(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail=f"Lead {lead_id} não encontrado")
    return lead


class AnaliseBody(BaseModel):
    perfil: str | None = None
    resumo_abordagem: str | None = None
    analise: dict | None = None


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


@router.post("/leads/{lead_id}/analisar")
def analisar_lead(lead_id: str) -> dict:
    """Enriquece a análise do lead via LLM (perfil + como abordar). On-demand."""
    lead = _require_lead(lead_id)
    try:
        analise = crm_enrich.enrich(lead_id, lead)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Falha ao analisar: {exc}") from exc
    return {"ok": True, "analise": analise}


@router.patch("/leads/{lead_id}")
def edit_lead(lead_id: str, body: AnaliseBody) -> dict:
    """Edita a análise do lead (perfil, resumo, análise estruturada).

    Só toca colunas DB-nativas (perfil/resumo/analise) — o sync markdown→DB não
    mexe nelas, então a edição do painel é estável. Garante o lead pro update.
    """
    if body.perfil is None and body.resumo_abordagem is None and body.analise is None:
        raise HTTPException(status_code=400, detail="Nada para editar")
    lead = _require_lead(lead_id)
    lead_assets.ensure_lead(
        lead_id, segment=lead.get("segment", ""), nome=lead.get("nome", ""),
        projeto=lead.get("projeto", ""), cidade=lead.get("cidade", ""),
        contato=lead.get("contato", ""),
    )
    lead_assets.set_analysis(
        lead_id, perfil=body.perfil, resumo_abordagem=body.resumo_abordagem, analise=body.analise
    )
    return {"ok": True, "analise": lead_assets.get_analysis(lead_id)}


@router.post("/leads/{lead_id}/arquivos")
async def upload_arquivo(lead_id: str, request: Request, nome: str = "arquivo", tipo: str = "material") -> dict:
    """Upload manual de arquivo (raw body) → Supabase Storage + lab_lead_files.

    Sem multipart: o corpo é o byte do arquivo; nome/tipo vêm na query.
    Requer Storage configurado (service_role no .env do servidor).
    """
    if not storage.enabled():
        raise HTTPException(status_code=503, detail="Supabase Storage não configurado no servidor")
    lead = _require_lead(lead_id)
    data = await request.body()
    if not data:
        raise HTTPException(status_code=400, detail="Corpo vazio (nenhum arquivo)")
    if len(data) > _MAX_UPLOAD:
        raise HTTPException(status_code=413, detail=f"Arquivo > {_MAX_UPLOAD // (1024 * 1024)} MB")
    projeto = lead.get("projeto") or "PROJ-LP"
    mime = request.headers.get("content-type", "") or ""
    lead_assets.ensure_lead(
        lead_id, segment=lead.get("segment", ""), nome=lead.get("nome", ""),
        projeto=projeto, cidade=lead.get("cidade", ""), contato=lead.get("contato", ""),
    )
    try:
        keypath = storage.lead_object_path(projeto, lead_id, nome)
        storage.upload(keypath, data, mime=mime)
        fid = lead_assets.add_file(
            lead_id, keypath, projeto=projeto, tipo=tipo, url=storage.public_url(keypath),
            mime=mime, bytes_=len(data), origem="upload_manual",
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Falha no upload: {exc}") from exc
    return {"ok": True, "id": fid, "url": storage.public_url(keypath), "tipo": tipo}


@router.delete("/leads/{lead_id}/files/{file_id}")
def delete_file(lead_id: str, file_id: int) -> dict:
    """Remove um arquivo (linha + objeto no Storage)."""
    removed = lead_assets.remove_file(file_id)
    if not removed:
        raise HTTPException(status_code=404, detail=f"Arquivo {file_id} não encontrado")
    try:
        storage.remove(removed["storage_path"])
    except Exception:  # noqa: BLE001 — best-effort; a linha já saiu
        pass
    return {"ok": True, "file_id": file_id}
