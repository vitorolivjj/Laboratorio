"""Constrói Agent do CrewAI a partir das definições em markdown."""

from crewai import Agent

from laboratorio.agents.loader import load_agent_prompt

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
}


def build_agent(
    agent_id: str,
    *,
    verbose: bool = True,
    allow_delegation: bool | None = None,
) -> Agent:
    """Instancia um Agent CrewAI usando o markdown em agentes/{agent_id}.md."""
    meta = _AGENT_META.get(agent_id)
    if meta is None:
        raise KeyError(f"Metadados não definidos para agente: {agent_id}")

    backstory = load_agent_prompt(agent_id)

    if allow_delegation is None:
        allow_delegation = agent_id == "ronaldo_maestro"

    return Agent(
        role=meta["role"],
        goal=meta["goal"],
        backstory=backstory,
        verbose=verbose,
        allow_delegation=allow_delegation,
    )
