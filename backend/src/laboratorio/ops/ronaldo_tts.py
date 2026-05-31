"""Síntese de voz do Ronaldo via OpenAI TTS (TASK-009 v3)."""

from __future__ import annotations

import logging
import os

import httpx

logger = logging.getLogger("laboratorio.ops.ronaldo_tts")

OPENAI_SPEECH_URL = "https://api.openai.com/v1/audio/speech"


def synthesize_speech(text: str) -> bytes:
    """Gera áudio MP3 natural a partir do texto de fala."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY não configurada para TTS")

    cleaned = text.strip()
    if not cleaned:
        raise ValueError("Texto vazio para síntese de voz")

    # tts-1 tem menor latência que tts-1-hd (melhor para conversa fluida).
    payload = {
        "model": os.getenv("TTS_MODEL", "tts-1"),
        "voice": os.getenv("TTS_VOICE", "onyx"),
        "input": cleaned[:4096],
        "speed": float(os.getenv("TTS_SPEED", "1.05")),
        "response_format": "mp3",
    }

    with httpx.Client(timeout=45.0) as client:
        response = client.post(
            OPENAI_SPEECH_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        response.raise_for_status()
        audio = response.content

    logger.info("TTS gerado (%d bytes, %d chars)", len(audio), len(cleaned))
    return audio
