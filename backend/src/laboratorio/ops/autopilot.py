"""Piloto automático — dá sequência às TASKs sem intervenção manual.

A cada ciclo lê `tasks/executando.md`, escolhe o agente responsável de cada
TASK e o aciona para produzir/executar a próxima ação concreta. Tudo é gravado
no trace de interações (visível no painel).

Seguro por padrão:
- `AUTOPILOT_ENABLED=0` (desligado) — precisa ser ligado explicitamente.
- `AUTOPILOT_INTERVAL_S=300` — período entre ciclos.
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
    return os.getenv("AUTOPILOT_ENABLED", "0").strip().lower() in ("1", "true", "yes", "on")


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


def _advance_task(task: dict) -> str:
    """Aciona o agente responsável para dar sequência a UMA task. Retorna o output."""
    from crewai import Crew, Process, Task

    from laboratorio.agents.builder import build_agent

    agent_id = _resolve_agent_id(task)
    context = f"autopilot:{task['id']}"
    interactions.record_interaction(
        kind="autopilot",
        context=context,
        agent=agent_id,
        detail=f"Acionando {agent_id} para avançar {task['id']} — {task.get('title', '')}",
    )

    objetivo = (
        f"TASK {task['id']} — {task.get('title', '')}.\n"
        f"Próxima ação atual: {task.get('proxima_acao') or '—'}.\n"
        f"Bloqueio: {task.get('bloqueio') or 'nenhum'}.\n\n"
        "Dê sequência a esta tarefa AGORA: execute a próxima ação concreta dentro "
        "da sua função usando suas ferramentas (registrar evento/aprendizado, atualizar "
        "CRM, criar subtarefa etc.) e descreva o que foi feito e qual a próxima ação. "
        "Se estiver bloqueada, registre o bloqueio e o que precisa para destravar. "
        "Seja objetivo (máx. 8 linhas)."
    )

    agent = build_agent(agent_id, verbose=False, log_llm=False, allow_delegation=False)
    crew = Crew(
        agents=[agent],
        tasks=[Task(
            description=objetivo,
            expected_output="O que foi feito + próxima ação concreta, em português.",
            agent=agent,
        )],
        process=Process.sequential,
        verbose=False,
        **interactions.crew_callbacks(context),
    )
    return str(crew.kickoff()).strip()


def run_cycle() -> dict:
    """Executa um ciclo: trabalha até AUTOPILOT_MAX_TASKS TASKs em execução."""
    load_env()
    max_tasks = max(1, _int_env("AUTOPILOT_MAX_TASKS", 1))
    cooldown = _int_env("AUTOPILOT_COOLDOWN_S", 1800)
    now = time.time()

    tasks = parsers.parse_executando_tasks(
        parsers.read_text(TASKS_DIR / "executando.md")
    )
    state = _load_state()
    worked: list[str] = []
    skipped: list[str] = []

    for task in tasks:
        if len(worked) >= max_tasks:
            break
        tid = task["id"]
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

    _save_state(state)
    summary = {
        "at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "in_progress": len(tasks),
        "worked": worked,
        "skipped_cooldown": skipped,
    }
    logger.info("Autopilot ciclo: %s", summary)
    return summary


def run_forever() -> None:
    interval = max(30, _int_env("AUTOPILOT_INTERVAL_S", 300))
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
