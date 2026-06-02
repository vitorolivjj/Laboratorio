"""Gera resumo + propostas via LLM."""

from __future__ import annotations

import json
import re
from typing import Any

from laboratorio.graph.llm import chat

SYSTEM = """Você é Ronaldo Maestro — autoevolução SUPERVISIONADA do Laboratório.

REGRAS:
- NUNCA altere nada sozinho; só PROPOSTAS que o Vitor aprovará no WhatsApp.
- Resumo diário: 4-6 linhas, direto, PT-BR.
- Propostas: 1 a 4 itens, cada um append-only em memoria/aprendizados.md ou memoria/decisoes.md.
- target só pode ser: "aprendizados" ou "decisoes"
- Propostas devem ser conservadoras (melhoria de processo, aprendizado, não mudança radical).

Responda APENAS JSON válido:
{
  "summary": "texto do resumo",
  "proposals": [
    {"id": 1, "target": "aprendizados", "title": "título curto", "body": "markdown do bloco a acrescentar"}
  ]
}
"""


def _parse_json(raw: str) -> dict[str, Any]:
    text = raw.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence:
        text = fence.group(1)
    else:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            text = m.group(0)
    data = json.loads(text)
    if not isinstance(data.get("proposals"), list):
        data["proposals"] = []
    return data


def generate_digest_package(context: str) -> dict[str, Any]:
    user = f"Contexto operacional (últimas 24h):\n\n{context[:12000]}\n\nGere o JSON."
    raw, _ = chat(SYSTEM, user, max_tokens=1400)
    try:
        return _parse_json(raw)
    except (json.JSONDecodeError, TypeError) as exc:
        return {
            "summary": raw[:500] if raw else "Resumo indisponível (parse falhou).",
            "proposals": [],
            "parse_error": str(exc),
        }
