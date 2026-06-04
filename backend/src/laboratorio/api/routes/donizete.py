"""API — estado da busca Donizete (Mac consulta / envia após PlayDonizete)."""

from __future__ import annotations

import json
import os

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from laboratorio.config import LOGS_DIR
from laboratorio.ops.donizete_runner import (
    BUSCA_STATE,
    busca_snapshot_for_panel,
    capture_active,
    is_running,
    mac_hint_from_snapshot,
    start_busca,
    status_line,
    stop_busca,
)

router = APIRouter(prefix="/api/donizete", tags=["donizete"])


def _check_token(request: Request) -> None:
    token = os.getenv("MAESTRO_API_TOKEN", "").strip()
    if not token:
        return
    auth = request.headers.get("authorization") or ""
    if auth != f"Bearer {token}":
        raise HTTPException(status_code=403, detail="Token inválido")


class BuscaStateBody(BaseModel):
    """Corpo opcional — Mac envia o JSON completo de donizete_busca_state."""

    cycles: int | None = None
    leads_captured: int | None = None
    running: bool | None = None
    modo: str | None = None
    active_task_id: str | None = None
    lock_group_url: str | None = None
    last_group: str | None = None
    last_cycle_at: str | None = None
    last_error: str | None = None
    standby_tasks: list[str] | None = None
    armed_vps: bool | None = None


def _check_push_token(request: Request) -> None:
    token = os.getenv("DONIZETE_STATE_PUSH_TOKEN", "").strip()
    if not token:
        return
    auth = request.headers.get("authorization") or ""
    if auth != f"Bearer {token}":
        raise HTTPException(status_code=403, detail="Token inválido")


@router.get("/busca-status")
def get_busca_status() -> dict:
    """Estado da busca para painel e Mac --watch."""
    snap = busca_snapshot_for_panel()
    return {
        **snap,
        "running_vps_thread": is_running(),
        "capture_active": capture_active(),
        "status_text": status_line(),
    }


@router.post("/busca-state")
def post_busca_state(body: BuscaStateBody, request: Request) -> dict:
    """Mac publica estado após cada ciclo (painel na VPS fica alinhado)."""
    _check_push_token(request)

    current: dict = {}
    if BUSCA_STATE.is_file():
        try:
            current = json.loads(BUSCA_STATE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            current = {}

    payload = body.model_dump(exclude_none=True)
    if payload.get("running"):
        payload["armed_vps"] = False
    incoming_cycles = payload.get("cycles")
    if incoming_cycles is not None:
        try:
            payload["cycles"] = max(int(incoming_cycles), int(current.get("cycles") or 0))
        except (TypeError, ValueError):
            pass
    current.update(payload)
    from datetime import datetime, timezone

    current["updated_at"] = datetime.now(timezone.utc).isoformat()
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    BUSCA_STATE.write_text(
        json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return {"ok": True, "capture_active": capture_active(), **busca_snapshot_for_panel()}


class PlayBody(BaseModel):
    task_id: str | None = None
    group_url: str | None = None


class StopBody(BaseModel):
    task_id: str | None = None


@router.post("/play")
def post_play(body: PlayBody, request: Request) -> dict:
    """Inicia busca Donizete (arm na VPS se CDP offline no servidor)."""
    _check_token(request)
    msg = start_busca(
        task_id=(body.task_id or "").strip().upper() or None,
        group_url=(body.group_url or "").strip() or None,
        allow_arm_without_cdp=True,
    )
    snap = busca_snapshot_for_panel()
    hint = mac_hint_from_snapshot(snap)
    return {
        "ok": not msg.startswith("ERRO"),
        "message": msg,
        "mac_hint": hint,
        "status_text": status_line(),
        "capture_active": capture_active(),
        **snap,
    }


@router.post("/stop")
def post_stop(body: StopBody, request: Request) -> dict:
    """Para busca Donizete e restaura kanban standby → executando."""
    _check_token(request)
    tid = (body.task_id or "").strip().upper() or None
    msg = stop_busca(task_id=tid)
    snap = busca_snapshot_for_panel()
    return {
        "ok": True,
        "message": msg,
        "status_text": status_line(),
        "capture_active": capture_active(),
        **snap,
    }
