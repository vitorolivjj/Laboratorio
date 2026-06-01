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
        import crewai

        print(f"CrewAI:        OK ({getattr(crewai, '__version__', 'installed')})")
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


def cmd_llm_config() -> int:
    """Exibe provider/model carregado por agente (sem chamar LLM)."""
    from laboratorio.agents.llm_config import log_all_agent_llm_configs

    log_all_agent_llm_configs(
        [
            "ronaldo_maestro",
            "caio_manteiga",
            "donizete_social",
            "dev",
            "juarez",
            "loide",
        ]
    )
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


def cmd_autopilot(once: bool, interval: int | None) -> int:
    """Piloto automático: dá sequência às TASKs em execução."""
    import os

    load_env()
    if interval is not None:
        os.environ["AUTOPILOT_INTERVAL_S"] = str(interval)
    # Via CLI o autopilot roda mesmo sem a flag de ambiente.
    os.environ.setdefault("AUTOPILOT_ENABLED", "1")

    from laboratorio.ops import autopilot

    if once:
        summary = autopilot.run_cycle()
        print(f"Ciclo concluído: {summary}")
        return 0
    try:
        autopilot.run_forever()
    except KeyboardInterrupt:
        print("\nAutopilot interrompido.")
    return 0


def cmd_whatsapp_check() -> int:
    """Valida variáveis WhatsApp sem iniciar servidor."""
    import os

    load_env()
    required = [
        "WHATSAPP_VERIFY_TOKEN",
        "WHATSAPP_ACCESS_TOKEN",
        "WHATSAPP_PHONE_NUMBER_ID",
    ]
    optional = ["META_APP_SECRET", "WHATSAPP_API_VERSION", "ANTHROPIC_API_KEY"]

    ok = True
    print("WhatsApp — config (TASK-007)\n")
    for key in required:
        val = os.getenv(key, "").strip()
        if val:
            masked = val[:4] + "…" if len(val) > 4 else "(ok)"
            print(f"  {key}: {masked}")
        else:
            print(f"  {key}: AUSENTE")
            ok = False

    for key in optional:
        val = os.getenv(key, "").strip()
        print(f"  {key}: {'ok' if val else '(opcional)'}")

    print(f"\nWebhook URL (local): http://localhost:{os.getenv('WHATSAPP_PORT', '8000')}/webhook/whatsapp")
    return 0 if ok else 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Laboratório — backend CrewAI")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("check", help="Verifica instalação e paths dos agentes")

    sub.add_parser(
        "llm-config",
        help="Exibe provider/model por agente (TASK-005)",
    )

    sub.add_parser("run-sample", help="Roda crew de exemplo com o agente Dev")

    p_orch = sub.add_parser("orchestrate", help="Roda orquestrador (Ronaldo Maestro)")
    p_orch.add_argument(
        "objective",
        nargs="+",
        help="Objetivo ou pedido do Vitor (texto livre)",
    )

    sub.add_parser(
        "whatsapp-check",
        help="Valida variáveis WhatsApp (TASK-007)",
    )

    p_auto = sub.add_parser("autopilot", help="Dá sequência automática às TASKs em execução")
    p_auto.add_argument("--once", action="store_true", help="Roda um único ciclo e sai")
    p_auto.add_argument("--interval", type=int, default=None, help="Segundos entre ciclos")

    args = parser.parse_args()

    if args.command == "check":
        sys.exit(cmd_check())
    if args.command == "llm-config":
        sys.exit(cmd_llm_config())
    if args.command == "run-sample":
        sys.exit(cmd_run_sample())
    if args.command == "orchestrate":
        objective = " ".join(args.objective)
        sys.exit(cmd_orchestrate(objective))
    if args.command == "whatsapp-check":
        sys.exit(cmd_whatsapp_check())
    if args.command == "autopilot":
        sys.exit(cmd_autopilot(args.once, args.interval))

    parser.print_help()
    sys.exit(1)
