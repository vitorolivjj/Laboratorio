"""API REST — Kanban tasks (fonte: tasks/*.md)."""

from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from laboratorio.ops import task_kanban_api
from laboratorio.ops.maestro import build_maestro_snapshot
from laboratorio.ops.snapshot_cache import invalidate_maestro_snapshot

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


class CreateTaskBody(BaseModel):
    titulo: str = Field(..., min_length=2, max_length=200)
    objetivo: str = ""
    agente: str = ""
    prioridade: str = "media"
    contexto: str = ""
    resultado: str = ""
    to_state: str = "backlog"


class CreateCaptureBody(BaseModel):
    group_url: str = Field(..., min_length=20)
    titulo: str = ""
    to_state: str = "executando"


class MoveTaskBody(BaseModel):
    to_state: str
    nota: str = ""
    force: bool = False


class PatchTaskBody(BaseModel):
    titulo: str | None = None
    objetivo: str | None = None
    prioridade: str | None = None
    grupo_fb: str | None = None


class BulkArchiveBody(BaseModel):
    nota: str = "cancelada e arquivada pelo painel"
    stop_capture: bool = True
    clear_agenda: bool = True


def _check_token(request: Request) -> None:
    token = os.getenv("MAESTRO_API_TOKEN", "").strip()
    if not token:
        return
    auth = request.headers.get("authorization") or ""
    if auth != f"Bearer {token}":
        raise HTTPException(status_code=403, detail="Token inválido")


@router.get("")
def list_tasks() -> dict:
    """Kanban completo (colunas + cards parseados)."""
    return task_kanban_api.build_kanban_board()


@router.post("")
def post_task(body: CreateTaskBody, request: Request) -> dict:
    _check_token(request)
    try:
        return task_kanban_api.create_task_api(
            titulo=body.titulo,
            objetivo=body.objetivo,
            agente=body.agente,
            prioridade=body.prioridade,
            contexto=body.contexto,
            resultado=body.resultado,
            to_state=body.to_state,
        )
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/bulk-archive")
def post_bulk_archive(body: BulkArchiveBody, request: Request) -> dict:
    """Cancela/arquiva tasks em executando, planejando, standby e aguardando."""
    _check_token(request)
    return task_kanban_api.bulk_archive_active(
        nota=body.nota,
        stop_capture=body.stop_capture,
        clear_agenda=body.clear_agenda,
    )


@router.post("/capture")
def post_capture(body: CreateCaptureBody, request: Request) -> dict:
    _check_token(request)
    try:
        return task_kanban_api.create_capture_api(
            group_url=body.group_url,
            titulo=body.titulo,
            to_state=body.to_state,
        )
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/invalidate-snapshot")
def post_invalidate_snapshot(request: Request) -> dict:
    _check_token(request)
    invalidate_maestro_snapshot()
    snap = build_maestro_snapshot()
    return {"ok": True, "generated_at": snap.get("generated_at")}


@router.get("/{task_id}")
def get_task(task_id: str) -> dict:
    try:
        return task_kanban_api.get_task_detail(task_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{task_id}/move")
def post_move(task_id: str, body: MoveTaskBody, request: Request) -> dict:
    _check_token(request)
    try:
        return task_kanban_api.move_task_api(
            task_id, body.to_state, body.nota, force=body.force
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("/{task_id}")
def patch_task(task_id: str, body: PatchTaskBody, request: Request) -> dict:
    _check_token(request)
    try:
        return task_kanban_api.patch_task_api(
            task_id,
            titulo=body.titulo,
            objetivo=body.objetivo,
            prioridade=body.prioridade,
            grupo_fb=body.grupo_fb,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
