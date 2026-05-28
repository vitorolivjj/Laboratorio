"""Crew mínima para validar o setup — um agente, uma tarefa."""

from crewai import Crew, Process, Task

from laboratorio.agents.builder import build_agent


def build_sample_crew() -> Crew:
    """Crew de smoke test com o Dev."""
    dev = build_agent("dev", verbose=True)

    task = Task(
        description=(
            "Em até 5 linhas, descreva como você organizaria um backend Python "
            "multiagente com CrewAI para um laboratório de experimentos."
        ),
        expected_output="Resposta curta em português, formato de lista ou parágrafos breves.",
        agent=dev,
    )

    return Crew(
        agents=[dev],
        tasks=[task],
        process=Process.sequential,
        verbose=True,
    )
