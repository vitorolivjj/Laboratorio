"""Rotas API — Painel Maestro."""

from fastapi import APIRouter

from laboratorio.ops.maestro import build_maestro_snapshot

router = APIRouter(prefix="/api/maestro", tags=["maestro"])


@router.get("/snapshot")
def get_snapshot() -> dict:
    """Snapshot operacional completo para o dashboard."""
    return build_maestro_snapshot()


@router.get("/health")
def maestro_health() -> dict[str, str]:
    return {"status": "ok", "service": "painel-maestro"}
