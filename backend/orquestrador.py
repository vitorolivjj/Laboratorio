#!/usr/bin/env python3
"""
Orquestrador multiagente — Ronaldo Maestro coordena Juarez, Dev, Loide (UX),
Caio Manteiga e Donizete (captação).

Fonte única do fluxo: `laboratorio.crews.orchestrator.build_orchestrator_crew`
(processo hierárquico — Ronaldo decide quem acionar). Este script é só o wrapper
de linha de comando que executa a crew, registra o ciclo e o custo.

Uso:
  .venv/bin/python orquestrador.py "seu objetivo"
  ./run.sh orquestrar
"""

from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent
sys.path.insert(0, str(_BACKEND / "src"))

from laboratorio.config import LOGS_DIR, MEMORIA_RONALDO_DIR, REPO_ROOT, load_env
from laboratorio.crews.orchestrator import build_orchestrator_crew
from laboratorio.ops.markdown_io import insert_after_heading, read_text, write_text_atomic

OBJETIVO_EXEMPLO = (
    "Criar uma oferta low ticket de página simples para pintores autônomos."
)

EVENTOS_FILE = LOGS_DIR / "eventos.md"
HISTORICO_FILE = MEMORIA_RONALDO_DIR / "historico_de_orquestracao.md"


def _require_llm_key() -> None:
    load_env()
    if os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY"):
        return
    print(
        "Erro: nenhuma API key de LLM encontrada.\n"
        "  1. cp .env.example .env\n"
        "  2. Defina OPENAI_API_KEY=sk-... (ou ANTHROPIC_API_KEY)\n"
        "  3. Rode novamente: ./run.sh orquestrar"
    )
    sys.exit(1)


def registrar_ciclo(objective: str, resultado: str) -> None:
    now = datetime.now()
    stamp = now.strftime("%Y-%m-%d %H:%M")
    date = now.strftime("%Y-%m-%d")
    resumo = resultado.strip()
    resumo_evento = resumo[:400] + "…" if len(resumo) > 400 else resumo

    evento = f"""### {stamp} — [orquestracao] Ciclo multiagente
- **Agente(s):** Ronaldo Maestro, Juarez, Dev, Loide (UX), Caio Manteiga, Donizete
- **Detalhe:** Objetivo: {objective} | Resumo: {resumo_evento}
- **Ref:** PROJ-001
"""

    historico = f"""### {date} — Orquestração multiagente
- **Objetivo:** {objective}
- **Agentes disponíveis:** Juarez, Dev, Loide (UX), Caio Manteiga, Donizete — coordenados por Ronaldo (manager hierárquico)
- **Resultado consolidado:**

{resultado.strip()}

- **Próximo passo:** Executar DECISÃO DE HOJE e registrar TASK em `tasks/`.
"""

    for path, heading, block in (
        (EVENTOS_FILE, "## Log", evento),
        (HISTORICO_FILE, "## Registros", historico),
    ):
        write_text_atomic(path, insert_after_heading(read_text(path), heading, block))
    print(f"\nRegistrado em:\n  - {EVENTOS_FILE.relative_to(REPO_ROOT)}\n  - {HISTORICO_FILE.relative_to(REPO_ROOT)}")


def run(objective: str) -> str:
    _require_llm_key()

    from laboratorio.agents.llm_config import log_all_agent_llm_configs

    log_all_agent_llm_configs()

    print(f"Objetivo:\n{objective}\n")
    print("Iniciando orquestração hierárquica (Ronaldo Maestro coordena os especialistas)\n")

    crew = build_orchestrator_crew(objective)
    result = crew.kickoff()
    output = str(result)

    try:
        from laboratorio.ops import usage

        usage.record_usage(
            source="orquestrador",
            model="multi",
            metrics=getattr(crew, "usage_metrics", None),
            extra={"objective": objective[:120]},
        )
    except Exception as exc:  # noqa: BLE001
        print(f"(aviso: não foi possível registrar uso: {exc})")

    registrar_ciclo(objective, output)
    return output


def main() -> None:
    if len(sys.argv) > 1:
        objective = " ".join(sys.argv[1:])
    else:
        objective = OBJETIVO_EXEMPLO
        print("(objetivo padrão de exemplo)\n")

    try:
        output = run(objective)
    except (FileNotFoundError, ValueError) as e:
        print(f"Erro ao registrar ciclo: {e}")
        sys.exit(1)

    print("\n" + "=" * 60 + "\nRESULTADO FINAL\n" + "=" * 60 + "\n")
    print(output)


if __name__ == "__main__":
    main()
