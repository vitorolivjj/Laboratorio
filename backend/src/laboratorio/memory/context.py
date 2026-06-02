"""Injeção de memória semântica no contexto dos agentes."""

from __future__ import annotations

import logging

from laboratorio.memory.semantic import is_memory_enabled, recall

logger = logging.getLogger("laboratorio.memory.context")


def format_hits_block(query: str, *, top_k: int = 5) -> str:
    if not is_memory_enabled():
        return ""

    try:
        hits = recall(query, top_k=top_k)
    except Exception as exc:
        logger.warning("Memória semântica indisponível: %s", exc)
        return ""

    if not hits:
        return ""

    lines = ["\n\n## Memória semântica (trechos relevantes)", f"_Consulta: {query[:120]}_\n"]
    for h in hits:
        ref = f" ({h.source_ref})" if h.source_ref else ""
        lines.append(
            f"- **[{h.namespace}]** sim={h.similarity:.2f}{ref}\n  {h.content[:500]}"
        )
    return "\n".join(lines) + "\n"


def augment_with_semantic_memory(query: str, *, top_k: int = 5) -> str:
    """Retorna bloco markdown para anexar ao briefing (vazio se desligado)."""
    return format_hits_block(query, top_k=top_k)
