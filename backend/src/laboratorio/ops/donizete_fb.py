"""CLI e ciclo Donizete — Facebook local + CRM LP."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from laboratorio.config import DATA_DIR, LOGS_DIR, REPO_ROOT, TASKS_DIR, load_env
from laboratorio.social import cycle, facebook_cdp, groups, session
from laboratorio.social.capture import run_garimpo, stalk_profile

logger = logging.getLogger("laboratorio.donizete_fb")

AUTOPILOT_STATE = DATA_DIR / "autopilot_state.json"
CADENCE_STATE = LOGS_DIR / "task_cadence_state.json"
EVENTOS_PATH = REPO_ROOT / "logs" / "eventos.md"


def cmd_status() -> int:
    load_env()
    print(f"CDP: {facebook_cdp.CDP_URL}")
    print(f"FB enabled: {facebook_cdp.facebook_enabled()}")
    print(f"CDP reachable: {facebook_cdp.cdp_reachable()}")
    if facebook_cdp.facebook_available():
        from laboratorio.tools.facebook_tools import FacebookStatusTool

        print(FacebookStatusTool()._run())
        return 0
    print(
        "\nInicie o Chrome:\n  ./scripts/facebook-cdp-mac.sh\n"
        "Depois abra https://www.facebook.com e faça login."
    )
    return 1


def cmd_garimpo() -> int:
    load_env()
    print(run_garimpo())
    return 0


def cmd_stalk(
    url: str,
    nome: str,
    cidade: str = "",
    grupo: str = "",
    tags: str = "autopromocao",
) -> int:
    load_env()
    print(
        stalk_profile(
            url,
            nome=nome,
            cidade=cidade,
            grupo_origem=grupo,
            tags=tags,
        )
    )
    return 0


def restart_capture_task(task_id: str = "LP-PINTOR-001") -> str:
    """Reinicia relógio de captação, cooldown autopilot e briefing operacional."""
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()
    today = now.strftime("%Y-%m-%d")

    # Cadência / patrulha — novo start
    cadence: dict = {"starts": {}}
    if CADENCE_STATE.is_file():
        try:
            cadence = json.loads(CADENCE_STATE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    cadence.setdefault("starts", {})[task_id] = now_iso
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    CADENCE_STATE.write_text(json.dumps(cadence, indent=2), encoding="utf-8")

    # Autopilot — remove cooldown desta task
    if AUTOPILOT_STATE.is_file():
        try:
            ap = json.loads(AUTOPILOT_STATE.read_text(encoding="utf-8"))
            ap.pop(task_id, None)
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            AUTOPILOT_STATE.write_text(json.dumps(ap, indent=2), encoding="utf-8")
        except (json.JSONDecodeError, OSError):
            pass

    # Estado monitor captação
    cap_state = LOGS_DIR / "donizete_captura_state.json"
    session.reset_session(task_id=task_id, rodada=3)
    groups.list_my_groups()

    # Evento
    line = (
        f"\n### {today} — [captacao] Reinício Donizete LP — {task_id}\n"
        f"- **Agente(s):** donizete_social\n"
        f"- **Detalhe:** Rodada 2 · grupos via perfil (fb_meus_grupos/busca) · sem URL chutada\n"
        f"- **Ref:** LP-PINTOR-001 · social_executor/README.md\n"
    )
    if EVENTOS_PATH.is_file():
        EVENTOS_PATH.write_text(EVENTOS_PATH.read_text(encoding="utf-8") + line, encoding="utf-8")

    return (
        f"Captação reiniciada (rodada 3): {task_id} às {now.strftime('%H:%M UTC')}.\n"
        f"Donizete escolhe grupos sozinho.\n"
        f"  Navegação: ./run.sh donizete-fb navegar\n"
        f"  Post:       ./run.sh donizete-fb post"
    )


def cmd_grupos() -> int:
    load_env()
    print(groups.format_groups_list(groups.list_my_groups(), title="Meus grupos"))
    return 0


def cmd_buscar(termo: str) -> int:
    load_env()
    print(groups.format_groups_list(groups.search_groups(termo), title=f"Busca: {termo}"))
    return 0


def cmd_abrir(indice: int = 0, nome: str = "") -> int:
    load_env()
    g = groups.open_group(indice=indice if indice > 0 else None, nome=nome)
    print(groups.scroll_group_feed())
    print(f"\nGrupo: {g.name}\n{g.url}")
    print(run_garimpo())
    return 0


def cmd_iniciar(task_id: str = "LP-PINTOR-001") -> int:
    load_env()
    print(restart_capture_task(task_id))
    if not facebook_cdp.facebook_available():
        print("\nChrome CDP offline — rode ./scripts/facebook-cdp-mac.sh")
        return 1
    ranked = cycle.rank_groups(groups.load_cached_groups())
    print(f"\nDonizete priorizou {len(ranked)} grupo(s) relevantes (ele escolhe sozinho).")
    if ranked:
        print(f"Próximo na fila: {ranked[0].name}")
    return 0


def cmd_navegar(max_leads: int = 1) -> int:
    load_env()
    captured, report = cycle.run_navigation_cycle(max_leads=max_leads)
    print(report)
    print(f"\n(capturados neste ciclo: {captured})")
    return 0


def cmd_post(variacao: int | None = None) -> int:
    load_env()
    print(cycle.run_post_cycle(variacao=variacao))
    return 0


def cmd_run(task_id: str = "LP-PINTOR-001") -> int:
    """Um ciclo CrewAI Donizete com tools Facebook + CRM LP."""
    load_env()
    if not facebook_cdp.facebook_available():
        print("Facebook CDP offline. Rode: ./scripts/facebook-cdp-mac.sh")
        return 1

    from laboratorio.ops import parsers
    from laboratorio.ops.autopilot import _advance_task
    from laboratorio.config import TASKS_DIR

    tasks = parsers.parse_executando_tasks(
        parsers.read_text(TASKS_DIR / "executando.md")
    )
    task = next((t for t in tasks if t["id"] == task_id), None)
    if not task:
        print(f"Task {task_id} não está em executando.md")
        return 1

    print(_advance_task(task))
    return 0
