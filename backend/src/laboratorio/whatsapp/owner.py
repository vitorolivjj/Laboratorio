"""Modo dono ("coringa") do Caio no WhatsApp.

Quando quem manda mensagem é um número de dono (configurado em OWNER_WA_IDS),
o Caio responde de forma ampla sobre o laboratório — status, andamento, tarefas
em execução, erros — usando o mesmo cérebro operacional do Painel Maestro.

Para os demais números, o fluxo segue comercial (caio_handler), inalterado.

Segurança: se OWNER_WA_IDS estiver vazio, NINGUÉM é dono — todos caem no
comercial. Assim nunca vaza informação interna por engano.
"""

from __future__ import annotations

import logging
import os
import re

logger = logging.getLogger("laboratorio.whatsapp.owner")


def _only_digits(value: str) -> str:
    """Normaliza um número de WhatsApp para só dígitos (ignora +, espaços, traços)."""
    return re.sub(r"\D", "", value or "")


def owner_ids() -> set[str]:
    """Conjunto de números de dono, lidos de OWNER_WA_IDS (separados por vírgula)."""
    raw = os.getenv("OWNER_WA_IDS", "")
    return {_only_digits(part) for part in raw.split(",") if _only_digits(part)}


def is_owner(wa_id: str) -> bool:
    """True se o número for de um dono configurado."""
    ids = owner_ids()
    return bool(ids) and _only_digits(wa_id) in ids


def generate_owner_reply(text: str) -> str:
    """Resposta ampla sobre o laboratório para o dono (reusa o cérebro do Maestro).

    Usa o caminho de baixa latência da voz do Ronaldo: perguntas de status,
    tarefas, erros e WhatsApp são respondidas direto do snapshot (sem LLM);
    perguntas livres usam o LLM rápido quando há chave configurada.
    """
    from laboratorio.ops.ronaldo_voice import generate_ronaldo_voice_reply

    result = generate_ronaldo_voice_reply(text)
    reply = (result.get("reply") or result.get("reply_speech") or "").strip()
    if not reply:
        reply = "Sem dados operacionais no momento — verifique o Painel Maestro."
    logger.info("Resposta modo-dono gerada (%d chars, fonte=%s)", len(reply), result.get("source"))
    return reply
