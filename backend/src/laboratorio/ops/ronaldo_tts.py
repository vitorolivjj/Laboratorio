"""Síntese de voz do Ronaldo — agora via ElevenLabs (vozes congeladas).

Mantém a assinatura pública histórica (`synthesize_speech(text)`) usada por
`/api/maestro/speak`. O provider real migrou de OpenAI tts-1 para ElevenLabs
(ver `ops/elevenlabs_tts.py`). OpenAI segue só no caminho de LLM, não de voz.
"""

from __future__ import annotations

import logging

from laboratorio.ops.elevenlabs_tts import synthesize_speech as _eleven_speech

logger = logging.getLogger("laboratorio.ops.ronaldo_tts")


def synthesize_speech(text: str, *, agent: str = "ronaldo") -> bytes:
    """Gera áudio MP3 da fala. Alias estável → ElevenLabs (agent ronaldo|caio)."""
    return _eleven_speech(text, agent=agent)
