"""Crew do orquestrador (Ronaldo Maestro) — processo hierárquico.

Ronaldo atua como manager: decide quais especialistas acionar para cada
objetivo (em vez de rodar todos numa sequência fixa). Especialistas têm
ferramentas (CRM, tasks, memória) e podem agir, não só sugerir.

Flags por env:
- CREW_MEMORY=1  → memória nativa do CrewAI (requer embedder/API key)
"""

from __future__ import annotations

import os

from crewai import Crew, Process, Task

from laboratorio.agents.builder import build_agent
from laboratorio.agents.loader import load_memory_file
from laboratorio.ops.retrieval import relevant_excerpt


def _memory_block(objective: str) -> str:
    """Memória estratégica relevante ao objetivo (sem truncar cego)."""
    try:
        contexto = load_memory_file("contexto_estrategico.md")
        regras = load_memory_file("regras_do_ecossistema.md")
    except FileNotFoundError:
        return ""
    contexto = relevant_excerpt(contexto, objective, max_chars=2000)
    regras = relevant_excerpt(regras, objective, max_chars=1500)
    return (
        "\n\n## Memória estratégica (trechos relevantes)\n\n"
        f"### Contexto\n{contexto}\n\n### Regras\n{regras}"
    )


def _memory_enabled() -> bool:
    return os.getenv("CREW_MEMORY", "0").strip().lower() in ("1", "true", "yes")


def build_orchestrator_crew(user_objective: str) -> Crew:
    """Monta crew hierárquica: Ronaldo (manager) + especialistas com ferramentas."""
    # No modo hierárquico o manager NÃO entra na lista de agents.
    ronaldo = build_agent("ronaldo_maestro", verbose=True, allow_delegation=True)
    juarez = build_agent("juarez", verbose=True)
    dev = build_agent("dev", verbose=True)
    loide = build_agent("loide", verbose=True)
    caio = build_agent("caio_manteiga", verbose=True)

    task = Task(
        description=(
            f"Objetivo do Vitor:\n{user_objective}\n"
            f"{_memory_block(user_objective)}\n\n"
            "Como Ronaldo Maestro, coordene os especialistas (Juarez=operação, "
            "Dev=software, Loide=UX, Caio=comercial). Acione SOMENTE quem o "
            "objetivo exige. Use suas ferramentas para consultar memória/CRM e, "
            "quando fizer sentido, registrar decisões/eventos ou criar TASKs.\n"
            "Entregue: (1) objetivo identificado, (2) agentes acionados e por quê, "
            "(3) plano único, (4) decisão de hoje, (5) próximo passo, (6) KPI."
        ),
        expected_output=(
            "Plano consolidado em português, com decisão clara e próximo passo "
            "acionável. Inclua TASK sugerida e KPI de sucesso."
        ),
    )

    return Crew(
        agents=[juarez, dev, loide, caio],
        tasks=[task],
        process=Process.hierarchical,
        manager_agent=ronaldo,
        memory=_memory_enabled(),
        verbose=True,
    )
