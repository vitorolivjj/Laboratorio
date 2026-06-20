"""API REST — captação por célula (Donizete/Places).

Permite disparar uma varredura de célula (segmento × área) pelo painel/curl, sem
SSH. A varredura roda em thread (leva minutos) e notifica o Vitor no fim; o
endpoint retorna na hora. Mesmo efeito de aprovar a célula na Fila Quente.
"""

from __future__ import annotations

import logging
import threading

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from laboratorio.api.auth import require_panel_token

logger = logging.getLogger("laboratorio.api.captacao")

router = APIRouter(
    prefix="/api/captacao",
    tags=["captacao"],
    dependencies=[Depends(require_panel_token)],
)


class CelulaBody(BaseModel):
    segmento: str = Field(..., min_length=2)
    area: str = Field(..., min_length=2)
    dry: bool = False


@router.get("/celulas")
def listar_celulas() -> dict:
    from laboratorio.ops.captacao import celulas_varridas

    cel = celulas_varridas()
    return {"celulas": cel, "total": len(cel)}


@router.post("/celula")
def varrer(body: CelulaBody) -> dict:
    """Dispara a varredura da célula. Valida a Places key na hora; varre em thread."""
    from laboratorio.ops import places
    from laboratorio.ops.captacao import varrer_celula

    try:
        places.api_key()  # falha já aqui se GOOGLE_PLACES_API_KEY ausente
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    seg, area, dry = body.segmento.strip(), body.area.strip(), body.dry

    if dry:  # dry é rápido o suficiente p/ responder síncrono e devolver o resumo
        try:
            return {"ok": True, **varrer_celula(seg, area, dry=True)}
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    def _run() -> None:
        try:
            varrer_celula(seg, area)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Varredura via API falhou (%s/%s)", seg, area)
            try:
                from laboratorio.whatsapp.notify import notify_vitor

                notify_vitor(f"⚠️ Varredura falhou — {seg} em {area}",
                             f"Erro: {exc}"[:280], ref="captacao")
            except Exception:  # noqa: BLE001
                pass

    threading.Thread(target=_run, daemon=True).start()
    return {"ok": True, "started": True, "segmento": seg, "area": area,
            "message": "Varredura iniciada — leads aparecem no painel em minutos."}
