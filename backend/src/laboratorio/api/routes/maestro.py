"""Rotas API — Painel Maestro."""

from pydantic import BaseModel, Field

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from laboratorio.ops.maestro import build_maestro_snapshot, get_cached_snapshot
from laboratorio.ops.ronaldo_tts import synthesize_speech
from laboratorio.ops.ronaldo_voice import generate_ronaldo_voice_reply
from laboratorio.ops.ronaldo_voice_history import list_voice_history

router = APIRouter(prefix="/api/maestro", tags=["maestro"])


class RonaldoCommandBody(BaseModel):
    command: str = Field(..., min_length=2, max_length=2000)


class RonaldoSpeakBody(BaseModel):
    text: str = Field(..., min_length=1, max_length=4096)


@router.get("/snapshot")
def get_snapshot(fresh: bool = False) -> dict:
    """Snapshot operacional completo para o dashboard (cacheado por padrão)."""
    return build_maestro_snapshot() if fresh else get_cached_snapshot()


@router.post("/ronaldo/command")
def ronaldo_voice_command(body: RonaldoCommandBody) -> dict:
    """Comando de voz transcrito → Ronaldo Maestro → resposta para o painel."""
    try:
        return generate_ronaldo_voice_reply(body.command)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/ronaldo/speak")
def ronaldo_speak(body: RonaldoSpeakBody) -> Response:
    """Texto → áudio MP3 (OpenAI TTS, voz natural)."""
    try:
        audio = synthesize_speech(body.text)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return Response(content=audio, media_type="audio/mpeg")


@router.get("/ronaldo/history")
def ronaldo_voice_history(limit: int = 30) -> dict:
    """Histórico persistente de comandos de voz."""
    capped = max(1, min(limit, 100))
    return {"entries": list_voice_history(capped)}


@router.get("/health")
def maestro_health() -> dict[str, str]:
    return {"status": "ok", "service": "painel-maestro"}
