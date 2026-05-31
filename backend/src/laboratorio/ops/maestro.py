"""Snapshot JSON completo do Painel Maestro."""

from __future__ import annotations

import os
import subprocess
import threading
import time
from datetime import datetime, timezone
from typing import Any

from laboratorio.agents.llm_config import resolve_agent_llm_config
from laboratorio.config import LOGS_DIR, MEMORIA_DIR, REPO_ROOT, TASKS_DIR
from laboratorio.ops import parsers

CRM_LEADS = REPO_ROOT / "crm" / "leads.md"

# Cache em memória: evita reler arquivos + rodar systemctl a cada chamada de voz.
_SNAPSHOT_CACHE: dict[str, Any] = {"data": None, "ts": 0.0}
_SNAPSHOT_TTL = float(os.getenv("MAESTRO_SNAPSHOT_TTL", "8"))
_SNAPSHOT_LOCK = threading.Lock()


def get_cached_snapshot(max_age: float | None = None) -> dict[str, Any]:
    """Snapshot com cache curto — ideal para respostas de voz de baixa latência."""
    ttl = _SNAPSHOT_TTL if max_age is None else max_age
    now = time.monotonic()
    cached = _SNAPSHOT_CACHE["data"]
    if cached is not None and (now - _SNAPSHOT_CACHE["ts"]) < ttl:
        return cached
    with _SNAPSHOT_LOCK:
        cached = _SNAPSHOT_CACHE["data"]
        if cached is not None and (time.monotonic() - _SNAPSHOT_CACHE["ts"]) < ttl:
            return cached
        data = build_maestro_snapshot()
        _SNAPSHOT_CACHE["data"] = data
        _SNAPSHOT_CACHE["ts"] = time.monotonic()
        return data

AGENT_AVATARS: dict[str, str] = {
    "ronaldo_maestro": "ronaldo-maestro.png",
    "caio_manteiga": "caio-manteiga.png",
    "donizete_social": "donizete.png",
    "dev": "dev.png",
    "juarez": "juarez.png",
    "loide": "loide.png",
}

AGENT_CATALOG: list[dict[str, str]] = [
    {
        "id": "ronaldo_maestro",
        "name": "Ronaldo",
        "role": "Maestro",
        "function": "Estratégia, visão e arquitetura do laboratório",
        "has_backend": "true",
    },
    {
        "id": "caio_manteiga",
        "name": "Caio",
        "role": "Comercial",
        "function": "Abordagem inteligente, relacionamento e conversão",
        "has_backend": "true",
    },
    {
        "id": "donizete_social",
        "name": "Donizete",
        "role": "Captura",
        "function": "Executor social, captação e qualificação de leads",
        "has_backend": "true",
    },
    {
        "id": "dev",
        "name": "Dev",
        "role": "Desenvolvimento",
        "function": "Código, integrações e IA aplicada ao negócio",
        "has_backend": "true",
    },
    {
        "id": "juarez",
        "name": "Juarez",
        "role": "Backoffice",
        "function": "Suporte, dados e execução operacional",
        "has_backend": "true",
    },
    {
        "id": "loide",
        "name": "Loide",
        "role": "UX Designer",
        "function": "Experiência de uso, usabilidade e interface — trabalha junto com o Dev",
        "has_backend": "true",
    },
]


def build_maestro_snapshot() -> dict[str, Any]:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    events = parsers.parse_event_blocks(parsers.read_text(LOGS_DIR / "eventos.md"))
    wa_log = parsers.parse_whatsapp_log(
        parsers.read_text(LOGS_DIR / "whatsapp_mensagens.md")
    )
    crm_raw = parsers.read_text(CRM_LEADS)
    leads = parsers.parse_leads_index(crm_raw) or parsers.parse_lead_sections(crm_raw)
    executando = parsers.parse_executando_tasks(
        parsers.read_text(TASKS_DIR / "executando.md")
    )
    planejando = parsers.parse_executando_tasks(
        parsers.read_text(TASKS_DIR / "planejando.md")
    )
    for t in executando:
        t["phase"] = "executando"
    for t in planejando:
        t["phase"] = "planejando"
    active_work = executando + planejando
    active_ids = [t["id"] for t in active_work]
    delegations = parsers.parse_delegations_from_tasks(TASKS_DIR, active_ids)
    decisions = parsers.parse_decisions(parsers.read_text(MEMORIA_DIR / "decisoes.md"))
    kanban = parsers.count_kanban(TASKS_DIR)
    wa_threads = parsers.group_whatsapp_threads(wa_log)

    messages_today = parsers.count_today(wa_log)
    leads_today = sum(1 for l in leads if l.get("captura", "").startswith(datetime.now(timezone.utc).strftime("%Y-%m-%d")))

    last_error = _last_error(events, wa_log)
    wa_online = _whatsapp_online(wa_log)
    vps_online = check_vps_service()

    agents = _build_agents(active_work, events, wa_log, active_ids)
    estimated_cost = round(messages_today * 0.012 + len(active_work) * 0.05, 3)
    briefing = _build_briefing(agents, active_work, wa_log, leads, last_error, vps_online, wa_online)

    errors = [e for e in events if e["type"] == "erro"]
    alerts = [e for e in events if e["type"] in ("erro", "marco")][:5]

    return {
        "generated_at": now,
        "briefing": briefing,
        "overview": {
            "system_online": True,
            "vps_online": vps_online,
            "whatsapp_online": wa_online,
            "messages_today": messages_today,
            "leads_today": leads_today,
            "estimated_cost_usd": estimated_cost,
            "last_error": last_error,
            "wip_tasks": len(executando),
            "wip_max": 3,
            "planning_tasks": len(planejando),
            "active_tasks": [t["id"] for t in executando],
            "planning_task_ids": [t["id"] for t in planejando],
        },
        "agents": agents,
        "delegations": delegations,
        "conversations": wa_log,
        "whatsapp_threads": wa_threads,
        "leads": leads,
        "kanban": {k: {"count": len(v), "tasks": v} for k, v in kanban.items()},
        "logs": {
            "events": events,
            "errors": errors[:10],
            "alerts": alerts,
            "decisions": decisions,
        },
        "pending_tasks": [
            {
                "id": t["id"],
                "title": t["title"],
                "agents": t["agents"],
                "proxima_acao": t["proxima_acao"],
                "bloqueio": t["bloqueio"],
                "phase": t.get("phase", "executando"),
            }
            for t in active_work
        ],
    }


def _build_agents(
    active_work: list[dict],
    events: list[dict],
    wa_log: list[dict],
    active_ids: list[str],
) -> list[dict]:
    agent_tasks: dict[str, list[str]] = {}
    for task in active_work:
        phase = task.get("phase", "")
        prefix = "[planejando] " if phase == "planejando" else ""
        for part in re_split_agents(task.get("agents") or task.get("responsavel", "")):
            agent_tasks.setdefault(part, []).append(f"{prefix}{task['id']}: {task['title']}")

    result: list[dict] = []
    for meta in AGENT_CATALOG:
        aid = meta["id"]
        status = "aguardando"
        current_task = "—"
        last_action = "—"
        last_update = "—"

        if aid in agent_tasks:
            status = "executando"
            current_task = agent_tasks[aid][0]
        elif aid == "ronaldo_maestro" and active_work:
            status = "executando"
            current_task = f"Coordena {len(active_work)} TASK(s)"

        if aid == "caio_manteiga" and wa_log:
            last = wa_log[0]
            if last.get("status") == "ok":
                status = "ativo" if status == "aguardando" else status
                last_action = f"Respondeu: {last['outbound'][:80]}"
                last_update = last["datetime"]
            elif "erro" in last.get("status", ""):
                status = "erro"
                last_action = last["status"][:120]
                last_update = last["datetime"]

        for ev in events[:15]:
            if aid.replace("_maestro", "").replace("_social", "").replace("_manteiga", "") in ev.get("agents", "").lower() or aid in ev.get("agents", ""):
                if not last_action or last_action == "—":
                    last_action = ev["title"][:100]
                    last_update = ev["datetime"]

        model = "—"
        provider = "—"
        if meta["has_backend"] == "true":
            try:
                cfg = resolve_agent_llm_config(aid)
                model = cfg.model
                provider = cfg.provider
            except KeyError:
                pass

        result.append(
            {
                "id": aid,
                "name": meta["name"],
                "role": meta["role"],
                "function": meta["function"],
                "status": status,
                "model": model,
                "provider": provider,
                "current_task": current_task,
                "last_action": last_action,
                "last_update": last_update,
                "avatar": AGENT_AVATARS.get(aid, ""),
            }
        )
    return result


def _build_briefing(
    agents: list[dict],
    active_work: list[dict],
    wa_log: list[dict],
    leads: list[dict],
    last_error: str,
    vps_online: bool,
    wa_online: bool,
) -> dict[str, Any]:
    working = [a["name"] for a in agents if a["status"] in ("executando", "ativo")]
    idle = [a["name"] for a in agents if a["status"] == "aguardando"]
    errored = [a["name"] for a in agents if a["status"] == "erro"]

    all_online = vps_online and wa_online
    return {
        "headline": "Operação normal" if all_online and not errored else "Atenção necessária",
        "system_online": all_online,
        "who_working": working,
        "who_idle": idle,
        "who_error": errored,
        "agent_tasks": {
            a["name"]: a["current_task"]
            for a in agents
            if a["status"] in ("executando", "ativo")
        },
        "pending_count": len(active_work),
        "pending_tasks": [
            {
                "id": t["id"],
                "title": t["title"],
                "next": t.get("proxima_acao", "—"),
                "phase": t.get("phase", "executando"),
            }
            for t in active_work
        ],
        "leads_total": len(leads),
        "caio_last_reply": wa_log[0]["outbound"][:160] if wa_log else "Nenhuma conversa ainda",
        "caio_last_phone": wa_log[0]["phone"] if wa_log else "—",
        "had_error": last_error != "Nenhum erro recente",
        "last_error": last_error,
    }


def re_split_agents(text: str) -> list[str]:
    import re

    ids: list[str] = []
    for token in re.split(r"[·,;]", text):
        t = token.strip().lower()
        if not t:
            continue
        for key in ("ronaldo_maestro", "caio_manteiga", "donizete_social", "dev", "juarez", "loide"):
            if key.split("_")[0] in t or key in t:
                ids.append(key)
                break
    return ids


def _last_error(events: list[dict], wa_log: list[dict]) -> str:
    for entry in wa_log:
        if "erro" in entry.get("status", "").lower():
            return entry["status"][:200]
    for ev in events:
        if ev["type"] == "erro":
            return ev["title"]
    return "Nenhum erro recente"


def _whatsapp_online(wa_log: list[dict]) -> bool:
    if not wa_log:
        return bool(os.getenv("WHATSAPP_ACCESS_TOKEN"))
    return wa_log[0].get("status") == "ok" or "erro" not in wa_log[0].get("status", "")


def check_vps_service() -> bool:
    try:
        proc = subprocess.run(
            ["systemctl", "is-active", "laboratorio-api"],
            capture_output=True,
            text=True,
            timeout=3,
        )
        return proc.stdout.strip() == "active"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return True
