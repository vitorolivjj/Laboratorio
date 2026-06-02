"""Aplica propostas aprovadas (append-only)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from laboratorio.config import MEMORIA_DIR

ALLOWED_TARGETS = {"aprendizados", "decisoes"}


def apply_proposals(proposals: list[dict[str, Any]]) -> list[str]:
    """Retorna lista de mensagens de resultado por proposta."""
    results: list[str] = []
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    for p in proposals:
        target = (p.get("target") or "").strip().lower()
        if target not in ALLOWED_TARGETS:
            results.append(f"Ignorada #{p.get('id')}: target inválido")
            continue

        path = MEMORIA_DIR / ("aprendizados.md" if target == "aprendizados" else "decisoes.md")
        title = (p.get("title") or "Proposta").strip()[:80]
        body = (p.get("body") or "").strip()
        if not body:
            results.append(f"Ignorada #{p.get('id')}: body vazio")
            continue

        block = f"""
### {stamp} — [autoevolução] {title}
- **Aprovado em:** {stamp} (resumo diário)
- **Proposta:**

{body}

"""
        text = path.read_text(encoding="utf-8")
        marker = "## Aprendizados\n" if target == "aprendizados" else "## Decisões\n"
        if marker in text:
            text = text.replace(marker, marker + block)
        else:
            text = text.rstrip() + "\n" + block
        path.write_text(text, encoding="utf-8")
        results.append(f"✓ #{p.get('id')} → {target}")

    return results
