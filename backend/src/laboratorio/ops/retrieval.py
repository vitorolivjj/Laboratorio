"""Recuperação de trechos relevantes (RAG leve, sem dependências externas).

Substitui o truncamento cego `texto[:N]` por seleção dos parágrafos mais
relevantes ao objetivo, via sobreposição de palavras (TF simples). Mantém o
contexto coerente mesmo quando a memória cresce — sem embeddings nem libs.
"""

from __future__ import annotations

import re
import unicodedata

_STOPWORDS = {
    "a", "o", "e", "de", "da", "do", "que", "para", "com", "em", "um", "uma",
    "os", "as", "no", "na", "por", "se", "ao", "dos", "das", "como", "mais",
    "the", "to", "of", "and", "in", "is", "for",
}


def _fold(text: str) -> str:
    nfkd = unicodedata.normalize("NFD", text.lower())
    return "".join(c for c in nfkd if unicodedata.category(c) != "Mn")


def _tokens(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]{3,}", _fold(text)) if t not in _STOPWORDS]


def _split_paragraphs(text: str) -> list[str]:
    parts = re.split(r"\n\s*\n", text.strip())
    return [p.strip() for p in parts if p.strip()]


def relevant_excerpt(text: str, query: str, max_chars: int = 2000) -> str:
    """Devolve os parágrafos de `text` mais relevantes a `query`, até max_chars.

    Sem query útil, cai no comportamento antigo (prefixo do texto) — seguro.
    """
    text = text or ""
    if len(text) <= max_chars:
        return text

    query_terms = set(_tokens(query))
    if not query_terms:
        return text[:max_chars]

    paragraphs = _split_paragraphs(text)
    scored: list[tuple[float, int, str]] = []
    for idx, para in enumerate(paragraphs):
        ptoks = _tokens(para)
        if not ptoks:
            continue
        hits = sum(1 for t in ptoks if t in query_terms)
        if hits:
            score = hits / (len(ptoks) ** 0.5)  # normaliza tamanho do parágrafo
            scored.append((score, idx, para))

    if not scored:
        return text[:max_chars]

    # Ordena por relevância, depois remonta na ordem original do documento.
    scored.sort(key=lambda x: x[0], reverse=True)
    chosen: list[tuple[int, str]] = []
    total = 0
    for score, idx, para in scored:
        if total + len(para) > max_chars and chosen:
            break
        chosen.append((idx, para))
        total += len(para) + 2
    chosen.sort(key=lambda x: x[0])
    return "\n\n".join(p for _, p in chosen)[:max_chars]
