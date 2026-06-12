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
    "Você é Caio Manteiga — assistente comercial do Laboratório de Agentes. O Laboratório "
    "ajuda NEGÓCIOS LOCAIS (clínicas, advocacia, imobiliárias, oficinas, reforma, estética) "
    "a parar de perder clientes por bagunça em captação, atendimento e comercial. A escada: "
    "Dossiê de Vazamentos (grátis) → Plano de Ataque (R$450) → Sprint → Acompanhamento. "
    "Você NÃO vende IA nem ferramenta: você mostra onde o negócio perde oportunidade por "
    "falta de processo, e conduz pro Plano de Ataque. "
    "Recebe os dados de um lead (captado pelo Donizete no Google: sinais públicos, reviews, "
    "auditoria de atendimento do Juarez) e faz uma ANÁLISE COMERCIAL pra você mesmo abordar. "
    "Responda APENAS um objeto JSON válido (sem markdown, sem comentários) com as chaves: "
    "perfil (classificação curta, ex.: 'clínica odontológica estabelecida'), "
    "servico (o que o negócio vende, concreto), "
    "maturidade (porte/organização aparente: ex.: 'consolidada, muita demanda, presença "
    "mal cuidada'), "
    "resumo_abordagem (2-3 frases: o VAZAMENTO principal a nomear na conversa + como "
    "abordar — tom de quem viu o caminho do cliente vazando, nunca de agência/guru), "
    "ganchos (lista de 2-4 ganchos CONCRETOS dos dados: review reclamando de demora, "
    "perfil sem site, comentário sem resposta, contradição demanda × processo), "
    "objecoes (lista de objeções prováveis, cada uma com o contorno entre parênteses — "
    "ex.: 'já tenho site (página sem processo é vitrine sem vendedor)'), "
    "dor (a dor operacional provável do dono: controle, retorno perdido, improviso), "
    "melhor_canal (ex.: whatsapp), tom (ex.: 'direto e respeitoso'). "
    "Só afirme o que tem evidência nos dados. Português do Brasil, específico ao lead."
)


def _build_user(lead: dict, analysis: dict) -> str:
    bio = str(lead.get("bio") or (analysis.get("analise") or {}).get("bio", ""))
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

    def _list(v):
        if isinstance(v, str):
            v = [v]
        return [str(x).strip() for x in (v or []) if str(x).strip()]

    perfil = str(data.get("perfil", "")).strip()
    resumo = str(data.get("resumo_abordagem", "")).strip()
    analise = {
        "servico": str(data.get("servico", "")).strip(),
        "maturidade": str(data.get("maturidade", "")).strip(),
        "ganchos": _list(data.get("ganchos") or data.get("gancho")),
        "objecoes": _list(data.get("objecoes")),
        "dor": str(data.get("dor", "")).strip(),
        "melhor_canal": str(data.get("melhor_canal", "")).strip(),
        "tom": str(data.get("tom", "")).strip(),
        "_fonte": "caio_llm",
        "_custo_usd": round(cost, 4),
    }
    # link do perfil — pro Caio consultar depois / virar gancho
    link = str(lead.get("link_perfil") or (current.get("analise") or {}).get("link_perfil", "")).strip()
    if link:
        analise["link_perfil"] = link
    # preserva a bio original (contexto da captura)
    bio = str(lead.get("bio") or (current.get("analise") or {}).get("bio", ""))
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


def auto_enrich_on() -> bool:
    """CRM_AUTO_ENRICH != 0 (default ligado)."""
    import os

    return os.getenv("CRM_AUTO_ENRICH", "1").strip().lower() not in ("0", "false", "no", "off")


def auto_enrich(lead_id: str, lead: dict, *, bio: str = "") -> bool:
    """Enriquece um lead recém-capturado se o auto-enrich estiver ligado.

    Best-effort: qualquer falha (LLM/rede/DB) é engolida e logada — nunca derruba
    a captura. Usado tanto no caminho com-stalk quanto no sem-URL.
    """
    if not auto_enrich_on():
        return False
    try:
        enrich(lead_id, {**lead, "bio": bio} if bio else lead)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("auto_enrich %s falhou: %s", lead_id, exc)
        return False
