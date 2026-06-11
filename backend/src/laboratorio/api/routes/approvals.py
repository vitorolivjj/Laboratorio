"""API REST — aprovações pendentes do Vitor (fonte: logs/approvals_pending.json).

Expõe no painel a mesma fila que o WhatsApp resolve com APROVAR/RECUSAR <id>.
Decidir pelo painel tem o MESMO efeito (executa via resolve_decision) — o canal
que decidir primeiro vale; o segundo recebe 409.
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from laboratorio.api.auth import api_token, require_panel_token

router = APIRouter(
    prefix="/api/approvals",
    tags=["approvals"],
    dependencies=[Depends(require_panel_token)],
)


class DecideBody(BaseModel):
    action: Literal["approve", "reject"]


@router.get("")
def list_approvals() -> dict:
    """Aprovações pendentes (mais recentes primeiro)."""
    from laboratorio.whatsapp.approvals import list_pending

    pending = list_pending()
    return {"pending": pending, "total": len(pending)}


@router.post("/{approval_id}/decide")
def decide(approval_id: str, body: DecideBody) -> dict:
    """Aprova/recusa — dispara a execução real (publicação, envio, etc.).

    Hardening: leitura pode ficar aberta em dev, mas DECIDIR exige
    MAESTRO_API_TOKEN configurado no servidor."""
    if not api_token():
        raise HTTPException(
            status_code=503,
            detail="MAESTRO_API_TOKEN não configurado — decisão via painel desabilitada",
        )

    from laboratorio.whatsapp.approvals import resolve_decision

    result = resolve_decision(body.action, approval_id)
    if result["code"] == "not_found":
        raise HTTPException(status_code=404, detail=result["message"])
    if result["code"] == "already_resolved":
        raise HTTPException(status_code=409, detail=result["message"])
    if result["code"] == "error":
        raise HTTPException(status_code=502, detail=result["message"])
    return {"ok": True, "message": result["message"]}
