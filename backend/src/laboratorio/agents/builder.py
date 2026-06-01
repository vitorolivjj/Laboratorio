"""Constrói Agent do CrewAI a partir das definições em markdown."""

import os

from crewai import Agent

from laboratorio.agents.llm_config import build_llm_for_agent
from laboratorio.agents.loader import load_agent_prompt
from laboratorio.tools.registry import tools_for


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


# Limites de segurança: evitam loop de raciocínio/delegação e travamento eterno.
# Ajustáveis por env; valores default conservadores.
def _agent_max_iter() -> int:
    return _int_env("AGENT_MAX_ITER", 12)


def _agent_max_exec_seconds() -> int:
    return _int_env("AGENT_MAX_EXECUTION_TIME", 240)


def _agent_max_rpm() -> int | None:
    if not os.getenv("AGENT_MAX_RPM"):
        return None
    return _int_env("AGENT_MAX_RPM", 0) or None

# Metadados mínimos por agente (role/goal); backstory vem do .md
_AGENT_META: dict[str, dict[str, str]] = {
    "ronaldo_maestro": {
        "role": "Ronaldo Maestro — Orquestrador",
        "goal": "Coordenar agentes, distribuir tarefas e consolidar entregas com simplicidade.",
    },
    "juarez": {
        "role": "Juarez — Gestor operacional",
        "goal": "Melhorar operações, KPIs, processos e produtividade com ações objetivas.",
    },
    "dev": {
        "role": "Dev — Desenvolvedor",
        "goal": "Construir e manter sistemas simples, seguros e escaláveis.",
    },
    "caio_manteiga": {
        "role": "Caio Manteiga — Comercial",
        "goal": "Converter interesse em venda com baixa fricção no WhatsApp e funis simples.",
    },
    "donizete_social": {
        "role": "Donizete Social — Captação",
        "goal": "Captar e classificar leads com qualidade, sem spam e com contexto para o comercial.",
    },
    "loide": {
        "role": "Loide — UX Designer",
        "goal": "Garantir experiência de uso simples, clara e acessível, trabalhando junto com o Dev.",
    },
}


def build_agent(
    agent_id: str,
    *,
    verbose: bool = True,
    allow_delegation: bool | None = None,
    log_llm: bool = True,
    tier: str | None = None,
    tools: list | None = None,
) -> Agent:
    """Instancia um Agent CrewAI usando o markdown em agentes/{agent_id}.md.

    tier: nível de modelo por custo ("simple" | "standard" | "strong").
    tools: ferramentas; None usa o conjunto padrão do agente (registry).
    """
    meta = _AGENT_META.get(agent_id)
    if meta is None:
        raise KeyError(f"Metadados não definidos para agente: {agent_id}")

    backstory = load_agent_prompt(agent_id)
    llm = build_llm_for_agent(agent_id, log=log_llm, tier=tier)

    if allow_delegation is None:
        allow_delegation = agent_id == "ronaldo_maestro"

    if tools is None:
        tools = tools_for(agent_id)

    return Agent(
        role=meta["role"],
        goal=meta["goal"],
        backstory=backstory,
        llm=llm,
        verbose=verbose,
        allow_delegation=allow_delegation,
        tools=tools,
        max_iter=_agent_max_iter(),
        max_execution_time=_agent_max_exec_seconds(),
        max_rpm=_agent_max_rpm(),
    )
