"""Camada de revisão/auto-crítica de respostas antes do envio.

Usa um LLM rápido e barato (HTTP direto, mesmo padrão da voz do Ronaldo) para
revisar um rascunho contra critérios. Em qualquer falha, devolve o rascunho
original — nunca bloqueia o fluxo principal.
"""

from __future__ import annotations

import logging
import os
import re

import httpx

from laboratorio.config import load_env

logger = logging.getLogger("laboratorio.ops.review")

OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"


def _clean(raw: str) -> str:
    text = raw.strip()
    text = re.sub(r"^```(?:\w*\n)?", "", text)
    text = re.sub(r"\n?```$", "", text)
    return text.strip().strip('"').strip("'")


def review_text(draft: str, *, role: str, criteria: str, timeout: float = 15.0) -> str:
    """Revisa `draft` segundo `criteria`. Devolve o texto final (revisado ou original)."""
    draft = (draft or "").strip()
    if not draft:
        return draft

    load_env()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.info("Revisão pulada — OPENAI_API_KEY ausente")
        return draft

    model = os.getenv("REVIEW_LLM_MODEL", "gpt-4o-mini")
    system = (
        f"Você é um revisor de qualidade para mensagens de {role}. "
        "Receba um rascunho e devolva APENAS a versão final melhorada — "
        "sem comentários, sem markdown, sem aspas. Se já estiver bom, "
        "devolva igual. Nunca invente fatos novos."
    )
    user = f"Critérios:\n{criteria}\n\nRascunho:\n{draft}\n\nVersão final:"

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.2,
        "max_tokens": 400,
    }

    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(
                OPENAI_CHAT_URL,
                headers={"Authorization": f"Bearer {api_key}"},
                json=payload,
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
    except Exception as exc:  # rede, timeout, parsing — degrada para o rascunho
        logger.warning("Revisão falhou (%s) — usando rascunho original", exc)
        return draft

    revised = _clean(content)
    return revised or draft
