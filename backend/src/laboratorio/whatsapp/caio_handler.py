"""Gera respostas do Caio para mensagens WhatsApp inbound."""

from __future__ import annotations

import logging
import os
import re

from crewai import Crew, Process, Task

from laboratorio.agents.builder import build_agent
from laboratorio.agents.llm_config import resolve_agent_llm_config
from laboratorio.ops import usage
from laboratorio.ops.review import review_text

logger = logging.getLogger("laboratorio.whatsapp.caio")

_REVIEW_CRITERIA = (
    "Máximo 4 linhas. Português natural e humano, sem tom robótico/corporativo. "
    "Sem markdown, sem aspas, sem links na 1ª mensagem. Não inventar fatos."
)


def _review_enabled() -> bool:
    return os.getenv("CAIO_REVIEW", "1").strip().lower() not in ("0", "false", "no")

CAIO_WHATSAPP_INSTRUCTIONS = """
Você é Caio Manteiga respondendo uma mensagem REAL no WhatsApp do Laboratório de Agentes IA.

Regras obrigatórias:
- Responda APENAS com o texto da mensagem WhatsApp (sem markdown, sem aspas, sem prefixos).
- Máximo 4 linhas · tom humano, natural, brasileiro · sem tom robótico ou corporativo.
- Se for saudação (olá, oi, bom dia): apresente-se como assistente do Laboratório de Agentes IA.
- Não faça pitch agressivo · não envie links na primeira mensagem.
- Não peça dados pessoais desnecessários.
"""


def _clean_reply(raw: str) -> str:
    text = raw.strip()
    text = re.sub(r"^```(?:\w*\n)?", "", text)
    text = re.sub(r"\n?```$", "", text)
    text = text.strip().strip('"').strip("'")
    return text


def generate_caio_reply(from_wa_id: str, user_message: str) -> str:
    """Envia contexto ao Caio (CrewAI) e retorna texto da resposta."""
    logger.info("Caio processando mensagem de %s", from_wa_id)

    caio = build_agent("caio_manteiga", verbose=False, log_llm=False)

    task = Task(
        description=(
            f"{CAIO_WHATSAPP_INSTRUCTIONS}\n\n"
            f"Remetente (WhatsApp ID): {from_wa_id}\n"
            f"Mensagem recebida:\n{user_message}\n\n"
            "Gere a resposta WhatsApp agora."
        ),
        expected_output=(
            "Uma única mensagem WhatsApp curta e natural, pronta para enviar ao usuário."
        ),
        agent=caio,
    )

    crew = Crew(
        agents=[caio],
        tasks=[task],
        process=Process.sequential,
        verbose=False,
    )

    result = crew.kickoff()
    reply = _clean_reply(str(result))

    # Registra tokens/custo reais desta resposta (degrada se métricas ausentes).
    try:
        usage.record_usage(
            source="whatsapp_caio",
            model=resolve_agent_llm_config("caio_manteiga").model,
            metrics=getattr(crew, "usage_metrics", None),
            extra={"from_wa_id": from_wa_id},
        )
    except Exception as exc:  # noqa: BLE001
        logger.debug("Sem métricas de uso: %s", exc)

    if not reply:
        reply = (
            "Olá! Sou o Caio, assistente do Laboratório de Agentes IA. "
            "Como posso ajudar?"
        )

    # Camada de revisão: melhora a mensagem antes de enviar ao cliente.
    if _review_enabled():
        reply = review_text(reply, role="atendimento comercial WhatsApp", criteria=_REVIEW_CRITERIA)

    logger.info("Caio respondeu (%d chars)", len(reply))
    return reply
