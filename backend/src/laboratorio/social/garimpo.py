"""Garimpo passivo — sinais de pintor na página Facebook atual."""

from __future__ import annotations

import re
from dataclasses import dataclass

from laboratorio.social.facebook_cdp import PageSnapshot

_PAINT_SIGNALS = re.compile(
    r"\b(pintor|pintura|pintar|pinturas|tinta|massa\s+corrida|"
    r"acabamento|fachada|residencial|comercial|orçamento|orcamento|"
    r"antes\s+e\s+depois|reforma|impermeabiliza)\b",
    re.IGNORECASE,
)
_REQUEST_SIGNALS = re.compile(
    r"\b(indic|recomend|procuro|preciso|quem\s+faz)\b",
    re.IGNORECASE,
)
_SERVICE_OFFER = re.compile(
    r"\b(faço|fazemos|realizo|atendo|orçamento|orcamento|serviço|servico|"
    r"trabalho|antes\s+e\s+depois|chama\s+no\s+zap|whatsapp|wpp|"
    r"pintamos|pintamos|especialista|profissional)\b",
    re.IGNORECASE,
)
_PROFILE_HINT = re.compile(
    r"facebook\.com/(?:profile\.php\?id=|people/|[\w.-]+/?$)",
    re.IGNORECASE,
)


@dataclass
class GarimpoCandidate:
    nome: str
    url: str
    score: int
    motivo: str
    snippet: str


def score_text(text: str) -> tuple[int, str]:
    if not text.strip():
        return 0, ""
    score = 0
    reasons: list[str] = []
    if _PAINT_SIGNALS.search(text):
        score += 3
        reasons.append("sinal_pintor")
    if _SERVICE_OFFER.search(text) and _PAINT_SIGNALS.search(text):
        score += 3
        reasons.append("oferece_servico")
    elif _REQUEST_SIGNALS.search(text):
        score += 2
        reasons.append("pedido_indicacao")
    if re.search(r"\b\d{2}\s?\d{4,5}[-\s]?\d{4}\b", text):
        score += 1
        reasons.append("telefone")
    snippet = text.strip().replace("\n", " ")[:220]
    return score, ", ".join(reasons) or "contexto"


def candidates_from_snapshot(
    snap: PageSnapshot, *, min_score: int = 3, filter_leads: bool = True
) -> list[GarimpoCandidate]:
    from laboratorio.social.lead_classifier import should_register_lead

    out: list[GarimpoCandidate] = []
    seen: set[str] = set()

    chunks = re.split(r"(?<=[.!?])\s+|\n{2,}", snap.text_excerpt)
    for chunk in chunks:
        sc, motivo = score_text(chunk)
        if sc < min_score:
            continue
        if filter_leads and not should_register_lead(chunk):
            continue
        nome = chunk[:60].strip() or "perfil"
        key = nome[:40].lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(
            GarimpoCandidate(
                nome=nome,
                url=snap.url,
                score=sc,
                motivo=motivo,
                snippet=chunk[:220],
            )
        )

    for link in snap.links:
        href = (link.get("href") or "").split("?")[0]
        text = link.get("text") or ""
        if not _PROFILE_HINT.search(href):
            continue
        sc, motivo = score_text(text)
        if sc < min_score - 1:
            continue
        nome = text.strip() or href.rstrip("/").split("/")[-1][:40]
        if filter_leads and not should_register_lead(text, nome=nome):
            continue
        key = href.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(
            GarimpoCandidate(
                nome=nome,
                url=href,
                score=sc + 1,
                motivo=motivo or "perfil_link",
                snippet=text[:220] or href,
            )
        )

    out.sort(key=lambda c: c.score, reverse=True)
    return out[:15]


def format_garimpo_report(snap: PageSnapshot, candidates: list[GarimpoCandidate]) -> str:
    lines = [
        f"Página: {snap.title[:70]}",
        f"URL: {snap.url}",
        f"Candidatos: {len(candidates)}",
        "",
    ]
    if not candidates:
        lines.append(
            "Nenhum sinal forte nesta tela. Role o feed/grupo ou abra um post com comentários."
        )
        return "\n".join(lines)
    for i, c in enumerate(candidates, 1):
        lines.append(f"{i}. [{c.score}] {c.nome}")
        lines.append(f"   {c.motivo} — {c.snippet[:100]}")
        if c.url != snap.url:
            lines.append(f"   {c.url}")
    return "\n".join(lines)
