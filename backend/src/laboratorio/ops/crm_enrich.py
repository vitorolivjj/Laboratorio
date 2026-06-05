"""Enriquecimento da análise do lead via LLM (perfil + como abordar).

Lê o que a captura já tem (nome, observações, bio dos posts) e pede ao LLM uma
análise objetiva pro comercial: perfil, resumo de abordagem, dor, gancho,
objeções, canal e tom. Salva em lab_leads (set_analysis). On-demand (botão no
painel) pra o custo ficar sob controle.
"""

from __future__ import annotations

import json
import logging
import re

from laboratorio.db import lead_assets
from laboratorio.graph.llm import chat

logger = logging.getLogger("laboratorio.ops.crm_enrich")

_SYSTEM = (
    "Você é analista comercial de uma agência que cria landing pages para "
    "prestadores de serviço (pintores etc.) captados em grupos de Facebook. "
    "Dado os dados de um lead, devolva uma análise curta e prática para o vendedor "
    "abordar. Responda APENAS um objeto JSON válido (sem markdown, sem comentários) "
    "com as chaves: perfil (string curta, ex.: 'pintor residencial'), "
    "resumo_abordagem (1-2 frases de como abordar), dor (string), gancho (string), "
    "objecoes (lista de strings), melhor_canal (string), tom (string). "
    "Use português do Brasil. Se faltar dado, infira com bom senso."
)


def _build_user(lead: dict, analysis: dict) -> str:
    bio = str((analysis.get("analise") or {}).get("bio", ""))
    return (
        f"Nome: {lead.get('nome', '')}\n"
        f"Cidade: {lead.get('cidade', '')}\n"
        f"Serviço: {lead.get('servico', '')}\n"
        f"Tags: {lead.get('tags', '')}\n"
        f"Observações: {lead.get('observacoes', '')}\n"
        f"Bio/posts capturados: {bio[:1500]}"
    )


def _parse_json(text: str) -> dict:
    t = text.strip()
    if t.startswith("```"):
        t = re.sub(r"^```[a-zA-Z]*\n?", "", t).rstrip("`").strip()
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", t, re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                pass
    return {}


def enrich(lead_id: str, lead: dict) -> dict:
    """Gera a análise via LLM e persiste. Retorna a análise salva.

    Levanta em caso de falha do LLM (sem OPENAI_API_KEY, rede, etc.) — o caller
    (API) traduz pra um erro amigável.
    """
    current = lead_assets.get_analysis(lead_id)
    text, cost = chat(_SYSTEM, _build_user(lead, current), max_tokens=600)
    data = _parse_json(text)
    if not data:
        raise ValueError(f"LLM não devolveu JSON válido: {text[:200]}")

    perfil = str(data.get("perfil", "")).strip()
    resumo = str(data.get("resumo_abordagem", "")).strip()
    objecoes = data.get("objecoes") or []
    if isinstance(objecoes, str):
        objecoes = [objecoes]
    analise = {
        "dor": str(data.get("dor", "")).strip(),
        "gancho": str(data.get("gancho", "")).strip(),
        "objecoes": [str(o).strip() for o in objecoes if str(o).strip()],
        "melhor_canal": str(data.get("melhor_canal", "")).strip(),
        "tom": str(data.get("tom", "")).strip(),
        "_fonte": "llm",
        "_custo_usd": round(cost, 4),
    }
    # preserva a bio original (contexto da captura)
    bio = str((current.get("analise") or {}).get("bio", ""))
    if bio:
        analise["bio"] = bio[:1500]

    lead_assets.ensure_lead(
        lead_id, segment=lead.get("segment", ""), nome=lead.get("nome", ""),
        projeto=lead.get("projeto", ""), cidade=lead.get("cidade", ""),
        contato=lead.get("contato", ""),
    )
    lead_assets.set_analysis(
        lead_id, perfil=perfil or None, resumo_abordagem=resumo or None, analise=analise
    )
    logger.info("Lead %s enriquecido (perfil=%s, custo=$%.4f)", lead_id, perfil, cost)
    return lead_assets.get_analysis(lead_id)
