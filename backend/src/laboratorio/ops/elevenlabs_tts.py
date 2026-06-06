"""Provider de voz — ElevenLabs (substitui o OpenAI tts-1 no caminho de TTS).

Vozes congeladas (cofre): Ronaldo (narração/v3) e Caio (mensagens/Flash).
Mesma assinatura pública de `ronaldo_tts.synthesize_speech` para não quebrar
`/api/maestro/speak` — agora com `agent` ∈ {'ronaldo','caio'}.

Config (env, com defaults):
- ELEVENLABS_API_KEY        (obrigatória)
- RONALDO_VOICE_ID / CAIO_VOICE_ID  (IDs congelados)
- ELEVENLABS_MODEL_RONALDO  (default eleven_v3)
- ELEVENLABS_MODEL_CAIO     (default eleven_flash_v2_5)
- RONALDO_VOICE_SPEED       (default 1.08; Caio usa 1.05)
- ELEVENLABS_OUTPUT_FORMAT  (default mp3_44100_128)
"""

from __future__ import annotations

import logging
import os

import httpx

from laboratorio.config import load_env

logger = logging.getLogger("laboratorio.ops.elevenlabs_tts")

_BASE_URL = "https://api.elevenlabs.io/v1/text-to-speech"
_DEFAULT_MODEL = {"ronaldo": "eleven_v3", "caio": "eleven_flash_v2_5"}
_DEFAULT_SPEED = {"ronaldo": "1.08", "caio": "1.05"}


def _voice_id(agent: str) -> str:
    key = "RONALDO_VOICE_ID" if agent == "ronaldo" else "CAIO_VOICE_ID"
    vid = os.getenv(key, "").strip()
    if not vid:
        raise RuntimeError(f"{key} não configurada (voz {agent} congelada ausente)")
    return vid


def _model(agent: str) -> str:
    env = "ELEVENLABS_MODEL_RONALDO" if agent == "ronaldo" else "ELEVENLABS_MODEL_CAIO"
    return os.getenv(env, _DEFAULT_MODEL[agent]).strip()


def _speed(agent: str) -> float:
    if agent == "ronaldo":
        raw = os.getenv("RONALDO_VOICE_SPEED", _DEFAULT_SPEED["ronaldo"])
    else:
        raw = os.getenv("CAIO_VOICE_SPEED", _DEFAULT_SPEED["caio"])
    try:
        return float(raw)
    except (TypeError, ValueError):
        return float(_DEFAULT_SPEED[agent])


def synthesize_speech(text: str, *, agent: str = "ronaldo") -> bytes:
    """Gera MP3 via ElevenLabs. agent ∈ {'ronaldo','caio'}. Retorna bytes do áudio.

    Tags de emoção do v3 (ex.: ``[seco]``, ``[irônico]``) vão no próprio `text`.
    """
    load_env()
    agent = (agent or "ronaldo").strip().lower()
    if agent not in ("ronaldo", "caio"):
        agent = "ronaldo"

    text = (text or "").strip()
    if not text:
        raise ValueError("synthesize_speech: texto vazio")

    api_key = os.getenv("ELEVENLABS_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("ELEVENLABS_API_KEY não configurada para TTS")

    voice_id = _voice_id(agent)
    output_format = os.getenv("ELEVENLABS_OUTPUT_FORMAT", "mp3_44100_128").strip()
    payload = {
        "text": text,
        "model_id": _model(agent),
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
            "speed": _speed(agent),
        },
    }

    try:
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(
                f"{_BASE_URL}/{voice_id}",
                params={"output_format": output_format},
                headers={"xi-api-key": api_key, "accept": "audio/mpeg"},
                json=payload,
            )
            resp.raise_for_status()
            audio = resp.content
    except httpx.HTTPStatusError as exc:
        body = exc.response.text[:300] if exc.response is not None else ""
        logger.warning("ElevenLabs TTS HTTP %s: %s", exc.response.status_code, body)
        raise RuntimeError(f"ElevenLabs TTS falhou ({exc.response.status_code}): {body}") from exc
    except Exception as exc:  # noqa: BLE001
        logger.warning("ElevenLabs TTS erro: %s", exc)
        raise RuntimeError(f"ElevenLabs TTS erro: {exc}") from exc

    if not audio:
        raise RuntimeError("ElevenLabs TTS: resposta de áudio vazia")
    logger.info("TTS %s ok (%d bytes, %s)", agent, len(audio), _model(agent))
    return audio
