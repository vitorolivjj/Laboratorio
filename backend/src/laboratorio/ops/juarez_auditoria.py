"""Juarez — auditoria PASSIVA de atendimento (evidência pública, zero contato).

Lê o que o Donizete coletou (reviews do Google, sinais do perfil) e produz o
diagnóstico de atendimento que alimenta o Dossiê: reclamações de demora/falta
de resposta, qualidade percebida, canal. Sem custo de risco — roda sempre.

A sondagem ATIVA (mystery shopping) é outra peça: whatsapp/juarez_sondagem.py.
"""

from __future__ import annotations

import json
import logging
import re

from laboratorio.config import load_env

logger = logging.getLogger("laboratorio.ops.juarez_auditoria")

_SYSTEM = """Você é JUAREZ, auditor de atendimento do Laboratório de Agentes.
Recebe os sinais públicos de um negócio local (perfil Google + até 5 avaliações
com texto) e avalia APENAS o ATENDIMENTO — não a qualidade técnica do serviço.

Procure: reclamações de demora, falta de resposta, dificuldade de contato,
atendimento ruim; elogios de atendimento; presença de canal claro.
Só afirme o que tem evidência nos dados.

Devolva APENAS JSON:
{"nota_atendimento": 0-10, "reclamacoes_atendimento": ["trechos/observações"],
"elogios_atendimento": ["..."], "canal_claro": true/false,
"resumo": "2 frases objetivas para o Dossiê"}"""


def auditar(lead_id: str, *, analise: dict | None = None) -> dict | None:
    """Auditoria passiva do lead. Devolve o bloco (e grava na análise) ou None."""
    load_env()
    lead_id = lead_id.strip().upper()
    if analise is None:
        try:
            from laboratorio.db import lead_assets

            analise = (lead_assets.get_analysis(lead_id) or {}).get("analise") or {}
        except Exception as exc:  # noqa: BLE001
            logger.warning("Sem análise no DB p/ %s: %s", lead_id, exc)
            analise = {}

    captacao = analise.get("captacao") or {}
    if not captacao:
        logger.info("Auditoria passiva sem dados de captação p/ %s", lead_id)
        return None

    contexto = {
        "nota_google": captacao.get("nota"),
        "n_avaliacoes": captacao.get("n_avaliacoes"),
        "tem_site": bool(captacao.get("site")),
        "horario_preenchido": captacao.get("horario_preenchido"),
        "reviews": captacao.get("reviews") or [],
        "sinais_donizete": captacao.get("sinais") or [],
    }

    from laboratorio.graph.llm import chat

    raw, _cost = chat(_SYSTEM, json.dumps(contexto, ensure_ascii=False),
                      max_tokens=600)
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip())
    m = re.search(r"\{[\s\S]*\}", t)
    if not m:
        logger.warning("Auditoria passiva sem JSON p/ %s", lead_id)
        return None
    bloco = json.loads(m.group(0))

    try:
        from laboratorio.ops.captacao import _merge_analysis

        _merge_analysis(lead_id, "auditoria_atendimento", bloco)
    except Exception:  # noqa: BLE001
        pass
    logger.info("Auditoria passiva de %s: nota %s", lead_id,
                bloco.get("nota_atendimento"))
    return bloco
