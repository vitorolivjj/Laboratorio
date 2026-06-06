"""Síntese de voz do Ronaldo — ElevenLabs (com fallback OpenAI no /speak).

`/api/maestro/ronaldo/speak` (voz conversacional) usa ElevenLabs quando a chave
está presente; se faltar `ELEVENLABS_API_KEY`, cai graciosamente no OpenAI tts-1
(evita quebrar o endpoint). A voz da ESTEIRA (conteúdo publicado) usa
`ops/elevenlabs_tts` direto e é ESTRITA — sem fallback, voz congelada.
"""

from __future__ import annotations

import logging
import os

import httpx

from laboratorio.ops.elevenlabs_tts import synthesize_speech as _eleven_speech

logger = logging.getLogger("laboratorio.ops.ronaldo_tts")

OPENAI_SPEECH_URL = "https://api.openai.com/v1/audio/speech"


def _openai_tts(text: str) -> bytes:
    """Fallback conversacional (voz OpenAI onyx) quando ElevenLabs indisponível."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Sem ELEVENLABS_API_KEY nem OPENAI_API_KEY para TTS")
    payload = {
        "model": os.getenv("TTS_MODEL", "tts-1"),
        "voice": os.getenv("TTS_VOICE", "onyx"),
        "input": text.strip()[:4096],
        "speed": float(os.getenv("TTS_SPEED", "1.05")),
        "response_format": "mp3",
    }
    with httpx.Client(timeout=45.0) as client:
        r = client.post(
            OPENAI_SPEECH_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
        )
        r.raise_for_status()
        return r.content


def synthesize_speech(text: str, *, agent: str = "ronaldo") -> bytes:
    """Voz MP3. ElevenLabs (vozes congeladas); fallback OpenAI só se faltar a chave."""
    if not os.getenv("ELEVENLABS_API_KEY", "").strip():
        logger.warning("ELEVENLABS_API_KEY ausente — /speak usando fallback OpenAI")
        return _openai_tts(text)
    try:
        return _eleven_speech(text, agent=agent)
    except Exception as exc:  # noqa: BLE001 — não derruba o /speak conversacional
        logger.warning("ElevenLabs falhou (%s) — fallback OpenAI no /speak", exc)
        return _openai_tts(text)
