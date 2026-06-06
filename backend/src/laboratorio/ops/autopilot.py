"""Piloto automático — dá sequência às TASKs sem intervenção manual.

A cada ciclo lê `tasks/executando.md`, escolhe o agente responsável de cada
TASK e o aciona para produzir/executar a próxima ação concreta. Tudo é gravado
no trace de interações (visível no painel).

Ligado por padrão (`AUTOPILOT_ENABLED=1`), mas limitado por controles de custo —
para pausar, defina `AUTOPILOT_ENABLED=0`:
- `AUTOPILOT_ENABLED=1` — ligado; sobe junto com a API (ver `api/app.py::startup`).
- `AUTOPILOT_INTERVAL_S=600` — período entre ciclos (default do código).
- `AUTOPILOT_MAX_TASKS=1` — teto de TASKs trabalhadas por ciclo (controle de custo).
- `AUTOPILOT_COOLDOWN_S=1800` — não reprocessa a mesma TASK antes disso.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from datetime import datetime, timezone

from laboratorio.config import DATA_DIR, TASKS_DIR, load_env
from laboratorio.ops import interactions, parsers

logger = logging.getLogger("laboratorio.autopilot")

_STATE_FILE = DATA_DIR / "autopilot_state.json"
_VALID_AGENTS = {
    "ronaldo_maestro", "juarez", "dev", "caio_manteiga", "donizete_social", "loide",
}
_started = False
_started_lock = threading.Lock()


def enabled() -> bool:
    return os.getenv("AUTOPILOT_ENABLED", "1").strip().lower() in ("1", "true", "yes", "on")


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def _load_state() -> dict[str, float]:
    if not _STATE_FILE.is_file():
        return {}
    try:
        return json.loads(_STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _save_state(state: dict[str, float]) -> None:
    try:
        _STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        _STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError as exc:
        logger.warning("Falha ao salvar estado do autopilot: %s", exc)


def _resolve_agent_id(task: dict) -> str:
    label = task.get("agents") or task.get("responsavel") or ""
    aid = parsers._normalize_agent_id(label) if label else "ronaldo_maestro"
    return aid if aid in _VALID_AGENTS else "ronaldo_maestro"


def _is_lp_capture_task(task: dict) -> bool:
    tid = (task.get("id") or "").upper()
    return tid.startswith("LP-PINTOR-001") or tid == "LP-PINTOR-003"


def _advance_task(task: dict) -> str:
    """Aciona o agente responsável para dar sequência a UMA task. Retorna o output."""
    from crewai import Crew, Process, Task

    from laboratorio.agents.builder import build_agent

    agent_id = _resolve_agent_id(task)
    if agent_id == "donizete_social" and _is_lp_capture_task(task):
        from laboratorio.ops.donizete_runner import busca_ativa
        from laboratorio.social.facebook_cdp import facebook_available

        if busca_ativa():
            raise RuntimeError(
                "Donizete em busca WhatsApp (PlayDonizete). "
                "Use StopDonizete antes do autopilot nesta task."
            )
        if not facebook_available():
            raise RuntimeError(
                "Donizete LP exige Facebook no Mac (CDP). "
                "Rode ./scripts/facebook-cdp-mac.sh — autopilot na VPS não captura FB."
            )
    context = f"autopilot:{task['id']}"
    interactions.record_interaction(
        kind="autopilot",
        context=context,
        agent=agent_id,
        detail=f"Acionando {agent_id} para avançar {task['id']} — {task.get('title', '')}",
    )

    fb_block = ""
    if agent_id == "donizete_social" and _is_lp_capture_task(task):
        fb_block = (
            "\n\nMODO FACEBOOK — Donizete escolhe grupos SOZINHO (2 atuações):\n"
            "A) NAVEGAÇÃO: fb_ciclo_navegacao OU fb_escolher_grupo → scroll lento → "
            "fb_analisar_posts → fb_qualificar_perfil → fb_stalk se lead → CRM LP\n"
            "B) POST: fb_ciclo_post — publicação autorizada (post-isca)\n"
            "Leads vêm de POSTS JÁ EXISTENTES no grupo — assimilar post → visitar perfil → qualificar.\n"
            "PROIBIDO chutar URL de grupo. PROIBIDO inventar leads.\n"
        )
    objetivo = (
        f"TASK {task['id']} — {task.get('title', '')}.\n"
        f"Próxima ação atual: {task.get('proxima_acao') or '—'}.\n"
        f"Bloqueio: {task.get('bloqueio') or 'nenhum'}.\n\n"
        "Dê sequência a ESTA tarefa AGORA: execute a próxima ação concreta dentro "
        "da sua função usando suas ferramentas (registrar evento/aprendizado, "
        "atualizar CRM etc.) e descreva o que foi feito e qual a próxima ação. "
        "NÃO crie novas tarefas nem subtarefas — apenas avance e relate a TASK "
        "atual. Se estiver bloqueada, registre o bloqueio e o que precisa para "
        "destravar. Seja objetivo (máx. 8 linhas)."
        f"{fb_block}"
    )

    # Remove a ferramenta de criar TASK para o autopilot não multiplicar tarefas.
    from laboratorio.agents.llm_config import AGENT_DISPLAY_NAME
    from laboratorio.tools.registry import tools_for

    tools = [t for t in tools_for(agent_id) if "criar" not in type(t).__name__.lower()]
    agent = build_agent(agent_id, verbose=False, log_llm=False, allow_delegation=False, tools=tools)
    crew = Crew(
        agents=[agent],
        tasks=[Task(
            description=objetivo,
            expected_output="O que foi feito + próxima ação concreta, em português.",
            agent=agent,
        )],
        process=Process.sequential,
        verbose=False,
        **interactions.crew_callbacks(context, default_agent=AGENT_DISPLAY_NAME.get(agent_id, agent_id)),
    )
    output = str(crew.kickoff()).strip()

    # Registra custo/tokens reais deste avanço (fonte=autopilot) para o painel.
    try:
        from laboratorio.agents.llm_config import resolve_agent_llm_config
        from laboratorio.ops import usage

        usage.record_usage(
            source="autopilot",
            model=resolve_agent_llm_config(agent_id).model,
            metrics=getattr(crew, "usage_metrics", None),
            extra={"task": task["id"], "agent": agent_id},
        )
    except Exception as exc:  # noqa: BLE001 — custo é observabilidade, não bloqueia
        logger.warning("Não foi possível registrar uso do autopilot: %s", exc)

    return output


def _budget_gate(state: dict) -> bool:
    """Cost gate diário (convergência com o cost_gate do LangGraph).

    True = pode trabalhar. Se o custo de HOJE passou de AUTOPILOT_DAILY_BUDGET_USD
    (>0), pausa o ciclo e notifica o Vitor 1x/dia (mesma notify_vitor do piloto).
    Default 0 = sem teto (não muda o comportamento atual; é opt-in).
    """
    from laboratorio.settings import get_settings

    budget = get_settings().autopilot_daily_budget_usd
    if budget <= 0:
        return True

    from laboratorio.ops import usage

    try:
        today_cost = float(usage.summarize().get("today_cost_usd") or 0)
    except Exception:  # noqa: BLE001 — observabilidade não bloqueia o piloto
        return True
    if today_cost < budget:
        return True

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if state.get("__budget_notified__") != today:
        try:
            from laboratorio.whatsapp.notify import notify_vitor

            notify_vitor(
                "Autopilot pausado — orçamento do dia",
                f"Custo de hoje US$ {today_cost:.2f} ≥ orçamento US$ {budget:.2f}. "
                "Pausa até o custo cair (ou aumente AUTOPILOT_DAILY_BUDGET_USD).",
                ref="autopilot",
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Falha ao notificar orçamento do autopilot: %s", exc)
        state["__budget_notified__"] = today
    logger.info("Autopilot pausado por orçamento: hoje US$ %.2f ≥ US$ %.2f", today_cost, budget)
    return False


def run_cycle() -> dict:
    """Executa um ciclo: trabalha até AUTOPILOT_MAX_TASKS TASKs em execução."""
    load_env()
    # Ritmo equilibrado: 1 tarefa por ciclo e não repete a mesma antes de 30 min
    # (ela alterna entre as TASKs). Ajustável por estas variáveis de ambiente.
    max_tasks = max(1, _int_env("AUTOPILOT_MAX_TASKS", 1))
    cooldown = _int_env("AUTOPILOT_COOLDOWN_S", 1800)
    now = time.time()

    tasks = parsers.parse_executando_tasks(
        parsers.read_text(TASKS_DIR / "executando.md")
    )
    state = _load_state()
    if not _budget_gate(state):
        _save_state(state)
        return {
            "at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "in_progress": len(tasks),
            "worked": [],
            "skipped_cooldown": [],
            "paused_budget": True,
        }
    worked: list[str] = []
    skipped: list[str] = []

    for task in tasks:
        if len(worked) >= max_tasks:
            break
        tid = task["id"]
        agent_id = _resolve_agent_id(task)
        try:
            from laboratorio.ops.donizete_runner import blocks_autopilot_for_task

            if blocks_autopilot_for_task(tid, agent_id):
                skipped.append(f"{tid}(busca_whatsapp)")
                logger.info(
                    "Autopilot ignorou %s — busca Donizete ativa (PlayDonizete)", tid
                )
                continue
        except ImportError:
            pass
        last = float(state.get(tid, 0))
        if now - last < cooldown:
            skipped.append(tid)
            continue
        try:
            _advance_task(task)
            worked.append(tid)
            state[tid] = now
        except Exception as exc:  # noqa: BLE001 — um erro não derruba o ciclo
            logger.warning("Autopilot falhou em %s: %s", tid, exc)
            interactions.record_interaction(
                kind="error", context=f"autopilot:{tid}", agent="autopilot",
                detail=f"Erro ao avançar {tid}: {exc}",
            )
            _notify_task_error(tid, exc, state, now)

    _save_state(state)
    summary = {
        "at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "in_progress": len(tasks),
        "worked": worked,
        "skipped_cooldown": skipped,
    }
    logger.info("Autopilot ciclo: %s", summary)
    return summary


def _notify_task_error(tid: str, exc: Exception, state: dict, now: float) -> None:
    """Notifica o Vitor (WhatsApp) quando uma TASK falha na execução do autopilot.

    Throttle por task (AUTOPILOT_ERROR_NOTIFY_COOLDOWN, default 6h) para não
    repetir o aviso a cada ciclo. Best-effort; nunca derruba o piloto.
    """
    if os.getenv("TASK_NOTIFY", "1").strip().lower() in ("0", "false", "no"):
        return
    cooldown = _int_env("AUTOPILOT_ERROR_NOTIFY_COOLDOWN", 21600)
    key = f"__errnotify__{tid}"
    if now - float(state.get(key, 0)) < cooldown:
        return
    state[key] = now
    try:
        from laboratorio.whatsapp.notify import notify_vitor

        notify_vitor(
            f"❌ TASK {tid} falhou na execução",
            str(exc)[:300],
            action="Verificar / decidir",
            ref=f"autopilot:{tid}",
        )
    except Exception:  # noqa: BLE001 — notificação nunca quebra o ciclo
        logger.warning("Falha ao notificar erro de %s", tid)


def run_forever() -> None:
    interval = max(30, _int_env("AUTOPILOT_INTERVAL_S", 600))
    logger.info("Autopilot iniciado (intervalo=%ss).", interval)
    interactions.record_interaction(
        kind="autopilot", context="autopilot", agent="autopilot",
        detail=f"Piloto automático iniciado (intervalo {interval}s).",
    )
    while True:
        try:
            run_cycle()
        except Exception as exc:  # noqa: BLE001
            logger.exception("Erro no ciclo do autopilot: %s", exc)
        time.sleep(interval)


def start_background() -> bool:
    """Inicia o autopilot em thread daemon, se AUTOPILOT_ENABLED. Idempotente."""
    global _started
    load_env()
    if not enabled():
        return False
    with _started_lock:
        if _started:
            return True
        thread = threading.Thread(target=run_forever, name="autopilot", daemon=True)
        thread.start()
        _started = True
    logger.info("Autopilot em background ativado.")
    return True
