"""FastAPI — webhook WhatsApp Business."""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
from typing import Any

from fastapi import BackgroundTasks, FastAPI, HTTPException, Query, Request, Response
from fastapi.staticfiles import StaticFiles

from laboratorio.api.routes.donizete import router as donizete_router
from laboratorio.api.routes.maestro import router as maestro_router
from laboratorio.api.routes.tasks import router as tasks_router
from laboratorio.config import REPO_ROOT, load_env
from laboratorio.whatsapp.handler import process_inbound_message
from laboratorio.whatsapp.parser import InboundMessage, extract_text_messages

load_env()

logger = logging.getLogger("laboratorio.api")

app = FastAPI(
    title="Laboratório — API",
    description="WhatsApp Caio + Painel Maestro (TASK-007/008)",
    version="0.2.0",
)

app.include_router(maestro_router)
app.include_router(donizete_router)
app.include_router(tasks_router)

PAINEL_DIR = REPO_ROOT / "frontend" / "painel-maestro"
if PAINEL_DIR.is_dir():
    app.mount("/painel", StaticFiles(directory=str(PAINEL_DIR), html=True), name="painel")

DASHBOARD_DIR = REPO_ROOT / "dashboard"
if DASHBOARD_DIR.is_dir():
    app.mount("/dashboard", StaticFiles(directory=str(DASHBOARD_DIR)), name="dashboard")

LP_PREVIAS_DIR = REPO_ROOT / "frontend" / "lp-pintor" / "dist"
if LP_PREVIAS_DIR.is_dir():
    app.mount("/previas", StaticFiles(directory=str(LP_PREVIAS_DIR), html=True), name="lp-previas")


@app.on_event("startup")
def _maybe_start_autopilot() -> None:
    """Liga o piloto automático em background se AUTOPILOT_ENABLED=1."""
    try:
        from laboratorio.ops.autopilot import start_background

        if start_background():
            logger.info("Autopilot ativado no startup da API.")
    except Exception as exc:  # noqa: BLE001 — nunca derruba a API por causa disso
        logger.warning("Não foi possível iniciar o autopilot: %s", exc)


@app.on_event("startup")
def _security_advisory() -> None:
    """Alerta (não bloqueia) quando defesas estão desligadas — visível no log."""
    if not os.getenv("MAESTRO_API_TOKEN", "").strip():
        logger.warning(
            "MAESTRO_API_TOKEN ausente — /api/maestro e /api/tasks estão ABERTAS. "
            "Defina MAESTRO_API_TOKEN em produção (painel envia ?token=... uma vez)."
        )
    if not os.getenv("META_APP_SECRET", "").strip():
        logger.warning(
            "META_APP_SECRET ausente — assinatura do webhook WhatsApp NÃO é verificada."
        )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "whatsapp-caio"}


@app.get("/webhook/whatsapp")
def verify_webhook(
    hub_mode: str = Query(alias="hub.mode", default=""),
    hub_verify_token: str = Query(alias="hub.verify_token", default=""),
    hub_challenge: str = Query(alias="hub.challenge", default=""),
) -> Response:
    """Verificação do webhook Meta (GET)."""
    verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN", "").strip()
    if not verify_token:
        raise HTTPException(status_code=500, detail="WHATSAPP_VERIFY_TOKEN não configurado")

    if hub_mode == "subscribe" and hub_verify_token == verify_token:
        logger.info("Webhook WhatsApp verificado com sucesso")
        return Response(content=hub_challenge, media_type="text/plain")

    logger.warning("Falha na verificação do webhook WhatsApp")
    raise HTTPException(status_code=403, detail="Token de verificação inválido")


def _verify_signature(body: bytes, signature_header: str | None) -> bool:
    secret = os.getenv("META_APP_SECRET", "").strip()
    if not secret:
        return True  # opcional em dev local

    if not signature_header or not signature_header.startswith("sha256="):
        return False

    expected = hmac.new(
        secret.encode("utf-8"),
        body,
        hashlib.sha256,
    ).hexdigest()
    received = signature_header.removeprefix("sha256=")
    return hmac.compare_digest(expected, received)


@app.post("/webhook/whatsapp")
async def receive_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
) -> dict[str, str]:
    """Recebe mensagens inbound (POST)."""
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")

    if not _verify_signature(body, signature):
        raise HTTPException(status_code=403, detail="Assinatura inválida")

    payload: dict[str, Any] = await request.json()
    messages = extract_text_messages(payload)

    if not messages:
        return {"status": "ignored"}

    for msg in messages:
        logger.info("Inbound de %s: %s", msg.from_wa_id, msg.text[:80])
        background_tasks.add_task(_process_message, msg)

    return {"status": "ok"}


def _process_message(msg: InboundMessage) -> None:
    try:
        process_inbound_message(msg)
    except Exception:
        logger.exception("Erro no processamento assíncrono message_id=%s", msg.message_id)
