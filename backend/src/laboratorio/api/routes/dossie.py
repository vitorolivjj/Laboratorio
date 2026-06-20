"""API REST — geração do Dossiê de Vazamentos (sem SSH).

POST /api/dossie/{lead_id} gera a página do Dossiê (Ronaldo analisa). dry=true
(default) só gera a página em /d/; dry=false dispara também a aprovação do Vitor
e, ao APROVAR, a abordagem do Caio. Síncrono (a análise leva ~30-60s).
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from laboratorio.api.auth import require_panel_token

logger = logging.getLogger("laboratorio.api.dossie")

router = APIRouter(
    prefix="/api/dossie",
    tags=["dossie"],
    dependencies=[Depends(require_panel_token)],
)


class DossieBody(BaseModel):
    dry: bool = True  # default seguro: só gera a página, não aborda a clínica real


@router.post("/{lead_id}")
def gerar(lead_id: str, body: DossieBody) -> dict:
    from laboratorio.ops import dossie as dossie_mod

    try:
        res = dossie_mod.gerar(lead_id, dry=body.dry)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("Dossiê falhou p/ %s", lead_id)
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    diag = res.pop("diag", {})
    return {"ok": True, "url": res.get("url"), "score": res.get("score"),
            "approval_id": res.get("approval_id"), "vazamentos": diag.get("vazamentos", []),
            "angulo": diag.get("angulo_abordagem")}
