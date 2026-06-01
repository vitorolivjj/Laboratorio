"""Modo dono — pelo número do Vitor, quem responde no WhatsApp é o Ronaldo.

Regra (definida pelo Vitor):
- Caio só atende comercial (outros números).
- Quando a mensagem vem do número do dono, quem responde é o **Ronaldo**, que
  além de relatar status PODE AGIR — gerar tarefa, mover/interromper tarefa —
  usando suas ferramentas.

Roteamento interno do modo dono:
- Pergunta de status/consulta  → resposta instantânea do snapshot (sem LLM).
- Comando de ação (criar/interromper/mover/delegar) → Ronaldo com ferramentas
  executa de verdade e confirma o que fez.

Segurança: se OWNER_WA_IDS não tiver número, cai no default do Vitor. Para
desativar o modo dono explicitamente, basta OWNER_WA_IDS=none (ou vazio com
OWNER_MODE=off). Assim nunca vaza operação interna para cliente por engano.
"""

from __future__ import annotations

import logging
import os
import re

logger = logging.getLogger("laboratorio.whatsapp.owner")

# Número do dono (Vitor). Pode ser sobrescrito por OWNER_WA_IDS no .env.
_DEFAULT_OWNER = "5533999353242"

# Verbos que indicam AÇÃO (Ronaldo deve executar, não só consultar).
_ACTION_WORDS = (
    "cria", "crie", "criar", "nova task", "nova tarefa", "novo card",
    "adiciona", "adicionar", "delega", "delegar", "move", "mover",
    "interrompe", "interromper", "pausa", "pausar", "para a task",
    "conclui", "concluir", "finaliza", "finalizar", "registra", "registrar",
)


def _only_digits(value: str) -> str:
    """Normaliza um número de WhatsApp para só dígitos (ignora +, espaços, traços)."""
    return re.sub(r"\D", "", value or "")


def owner_ids() -> set[str]:
    """Números de dono. Lê OWNER_WA_IDS (vírgula-separado) ou usa o default do Vitor."""
    raw = os.getenv("OWNER_WA_IDS")
    if raw is None:
        return {_DEFAULT_OWNER}
    if raw.strip().lower() in ("none", "off", ""):
        return set()
    ids = {_only_digits(part) for part in raw.split(",") if _only_digits(part)}
    return ids or {_DEFAULT_OWNER}


def is_owner(wa_id: str) -> bool:
    """True se o número for de um dono configurado."""
    ids = owner_ids()
    return bool(ids) and _only_digits(wa_id) in ids


def _is_action(text: str) -> bool:
    folded = text.lower()
    return any(word in folded for word in _ACTION_WORDS)


_RONALDO_WHATSAPP_INSTRUCTIONS = """
Você é Ronaldo Maestro respondendo ao Vitor (dono) pelo WhatsApp.
Você tem ferramentas para AGIR: listar/criar/mover tarefas, ler CRM e memória,
registrar decisões/eventos. Quando o Vitor pedir para criar, mover, interromper
ou pausar uma tarefa, USE a ferramenta correspondente e só então confirme.

Para interromper/pausar uma tarefa: mova-a para o estado 'aguardando'.
Responda curto e direto (WhatsApp), em português, dizendo o que você fez.
"""


def _act_as_ronaldo(text: str) -> str:
    """Roda o Ronaldo (CrewAI) com ferramentas para executar o comando do dono."""
    from crewai import Crew, Process, Task

    from laboratorio.agents.builder import build_agent
    from laboratorio.ops import interactions

    ronaldo = build_agent("ronaldo_maestro", verbose=False, log_llm=False, allow_delegation=False)
    task = Task(
        description=f"{_RONALDO_WHATSAPP_INSTRUCTIONS}\n\nPedido do Vitor:\n{text}\n\nExecute agora.",
        expected_output="Confirmação curta em português do que foi feito (1-3 linhas).",
        agent=ronaldo,
    )
    crew = Crew(
        agents=[ronaldo],
        tasks=[task],
        process=Process.sequential,
        verbose=False,
        **interactions.crew_callbacks("modo-dono"),
    )
    reply = str(crew.kickoff()).strip()
    return reply or "Feito."


def generate_owner_reply(text: str) -> str:
    """Resposta do Ronaldo ao dono: consulta status OU executa ação com ferramentas."""
    if _is_action(text):
        try:
            reply = _act_as_ronaldo(text)
            logger.info("Modo dono [ação]: '%s' -> %d chars", text[:50], len(reply))
            return reply
        except Exception as exc:  # noqa: BLE001 — degrada para consulta de status
            logger.warning("Ação do Ronaldo falhou (%s) — caindo para status", exc)

    # Consulta de status (instantâneo, sem LLM) via cérebro operacional do Maestro.
    from laboratorio.ops.ronaldo_voice import generate_ronaldo_voice_reply

    result = generate_ronaldo_voice_reply(text)
    reply = (result.get("reply") or result.get("reply_speech") or "").strip()
    if not reply:
        reply = "Sem dados operacionais no momento — verifique o Painel Maestro."
    logger.info("Modo dono [status]: '%s' -> %d chars (fonte=%s)", text[:50], len(reply), result.get("source"))
    return reply
