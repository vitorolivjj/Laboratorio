"""LLM leve para nós do grafo (OpenAI via httpx)."""

from __future__ import annotations

import os

import httpx

from laboratorio.config import load_env

OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"


def chat(
    system: str,
    user: str,
    *,
    model: str | None = None,
    max_tokens: int = 1200,
) -> tuple[str, float]:
    """Retorna (texto, custo_estimado_usd)."""
    load_env()
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY ausente")

    model = model or os.getenv("GRAPH_PILOT_MODEL", os.getenv("VOICE_LLM_MODEL", "gpt-4o-mini"))
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.3,
        "max_tokens": max_tokens,
    }
    with httpx.Client(timeout=90.0) as client:
        resp = client.post(
            OPENAI_CHAT_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()

    text = data["choices"][0]["message"]["content"].strip()
    usage = data.get("usage") or {}
    total = int(usage.get("total_tokens", 0))
    # gpt-4o-mini ~ $0.15/1M in + $0.60/1M out — aproximação conservadora
    cost = (total / 1000) * 0.0003
    return text, max(cost, 0.0001)
