"""API REST — fila da Esteira de Conteúdo (fonte: logs/content_queue.json).

Permite ver e CANCELAR itens pendentes pelo painel (item cancelado não publica
no slot). A geração/aprovação seguem o fluxo normal da esteira.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from laboratorio.api.auth import require_panel_token

router = APIRouter(
    prefix="/api/content",
    tags=["content"],
    dependencies=[Depends(require_panel_token)],
)


@router.get("/queue")
def get_queue() -> dict:
    from laboratorio.ops.content_schedule import list_queue

    items = list_queue()
    return {"queue": items, "total": len(items),
            "pending": sum(1 for i in items if i.get("status") == "pending")}


@router.post("/queue/{item_id}/cancel")
def cancel_item(item_id: str) -> dict:
    from laboratorio.ops.content_schedule import cancel

    item = cancel(item_id)
    if not item:
        raise HTTPException(status_code=404,
                            detail=f"Item {item_id} não encontrado ou não está pendente")
    return {"ok": True, "item": item}
