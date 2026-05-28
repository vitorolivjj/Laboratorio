"""CLI do backend multiagente."""

import argparse
import sys

from laboratorio import __version__
from laboratorio.config import AGENT_FILES, BACKEND_ROOT, REPO_ROOT, ensure_paths, load_env


def cmd_check() -> int:
    """Valida ambiente sem chamar LLM."""
    print(f"Laboratório backend v{__version__}")
    print(f"Repo root:     {REPO_ROOT}")
    print(f"Backend root:  {BACKEND_ROOT}")

    try:
        import crewai  # noqa: F401

        import crewai as crewai_mod

        print(f"CrewAI:        OK ({getattr(crewai_mod, '__version__', 'installed')})")
    except ImportError:
        print("CrewAI:        ERRO — pacote ausente. Rode: .venv/bin/pip install -r requirements.txt")
        return 1
    except Exception as e:
        print(f"CrewAI:        ERRO no import — {type(e).__name__}: {e}")
        print("              Dica: setuptools<81 (ver requirements.txt)")
        return 1

    issues = ensure_paths()
    if issues:
        print("\nPaths com problema:")
        for i in issues:
            print(f"  - {i}")
        return 1

    print("\nAgentes encontrados:")
    for name, path in AGENT_FILES.items():
        print(f"  - {name}: {path.name}")

    return 0


def cmd_run_sample() -> int:
    """Executa crew de exemplo (requer API key no .env)."""
    load_env()
    from laboratorio.crews.sample import build_sample_crew

    crew = build_sample_crew()
    result = crew.kickoff()
    print("\n--- Resultado ---\n")
    print(result)
    return 0


def cmd_orchestrate(objective: str) -> int:
    """Executa crew do Ronaldo Maestro com objetivo em texto."""
    load_env()
    from laboratorio.crews.orchestrator import build_orchestrator_crew

    crew = build_orchestrator_crew(objective)
    result = crew.kickoff()
    print("\n--- Resultado ---\n")
    print(result)
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Laboratório — backend CrewAI")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("check", help="Verifica instalação e paths dos agentes")

    sub.add_parser("run-sample", help="Roda crew de exemplo com o agente Dev")

    p_orch = sub.add_parser("orchestrate", help="Roda orquestrador (Ronaldo Maestro)")
    p_orch.add_argument(
        "objective",
        nargs="+",
        help="Objetivo ou pedido do Vitor (texto livre)",
    )

    args = parser.parse_args()

    if args.command == "check":
        sys.exit(cmd_check())
    if args.command == "run-sample":
        sys.exit(cmd_run_sample())
    if args.command == "orchestrate":
        objective = " ".join(args.objective)
        sys.exit(cmd_orchestrate(objective))

    parser.print_help()
    sys.exit(1)
