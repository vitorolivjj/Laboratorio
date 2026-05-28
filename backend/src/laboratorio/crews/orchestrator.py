"""
Crew do orquestrador (Ronaldo Maestro) — esqueleto para evolução.

Próximos passos:
- Carregar contexto_estrategico.md e decisoes_criticas.md como input
- Definir tasks de delegação para Juarez, Dev e Caio
- Process.hierarchical com manager_agent=ronaldo (quando habilitado no plano)
"""

from crewai import Crew, Process, Task

from laboratorio.agents.builder import build_agent
from laboratorio.agents.loader import load_memory_file


def build_orchestrator_crew(user_objective: str) -> Crew:
    """
    Monta crew com Ronaldo Maestro + contexto de memória estratégica.

    Ainda não delega automaticamente aos outros agentes — estrutura pronta para isso.
    """
    ronaldo = build_agent("ronaldo_maestro", verbose=True)

    try:
        contexto = load_memory_file("contexto_estrategico.md")
        regras = load_memory_file("regras_do_ecossistema.md")
        memory_block = f"\n\n## Memória estratégica\n\n### Contexto\n{contexto[:2000]}\n\n### Regras\n{regras[:1500]}"
    except FileNotFoundError:
        memory_block = ""

    task = Task(
        description=(
            f"Objetivo do Vitor:\n{user_objective}\n"
            f"{memory_block}\n\n"
            "Produza: (1) objetivo identificado, (2) agentes envolvidos, "
            "(3) plano de execução, (4) distribuição de tarefas, "
            "(5) consolidação, (6) próximo passo — conforme seu formato padrão."
        ),
        expected_output=(
            "Resposta em português seguindo as 6 seções do Ronaldo Maestro, "
            "com tabela de delegação quando aplicável."
        ),
        agent=ronaldo,
    )

    return Crew(
        agents=[ronaldo],
        tasks=[task],
        process=Process.sequential,
        verbose=True,
    )
