"""Snapshot JSON completo do Painel Maestro."""

from __future__ import annotations

import logging
import os
import re
import subprocess
import time
from datetime import datetime, timezone
from typing import Any

import json

from laboratorio.agents.llm_config import resolve_agent_llm_config
from laboratorio.config import (
    CRM_LEADS,
    LOGS_DIR,
    MEMORIA_DIR,
    REPO_ROOT,
    TASK_CADENCE_MIN,
    TASK_STALE_CRITICAL_HOURS,
    TASK_STALE_HOURS,
    TASKS_DIR,
    WIP_SOFT_MAX,
)
from laboratorio.ops import parsers, usage
from laboratorio.ops.interactions import recent_interactions
from laboratorio.ops.maestro_metrics import append_metric_from_overview
from laboratorio.repositories.crm import get_crm_repository
from laboratorio.repositories.events import get_event_repository
from laboratorio.repositories.projects import get_project_repository
from laboratorio.repositories.tasks import get_task_repository

CADENCE_STATE = LOGS_DIR / "task_cadence_state.json"

logger = logging.getLogger("laboratorio.ops.maestro")


def _task_cadence(executando_ids: list[str]) -> dict[str, Any]:
    """Cadência de tasks: registra quando cada task entra em execução e
    calcula o intervalo desde o último start. Substitui o teto rígido de WIP."""
    interval = TASK_CADENCE_MIN
    now_dt = datetime.now(timezone.utc)
    try:
        state = json.loads(CADENCE_STATE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        state = {}
    starts: dict[str, str] = state.get("starts", {})

    changed = False
    # Carimba novas tasks; remove as que saíram de execução.
    for tid in executando_ids:
        if tid not in starts:
            starts[tid] = now_dt.isoformat()
            changed = True
    for tid in list(starts.keys()):
        if tid not in executando_ids:
            del starts[tid]
            changed = True
    if changed:
        try:
            CADENCE_STATE.write_text(json.dumps({"starts": starts}, indent=2), encoding="utf-8")
        except OSError:
            pass

    parsed: list[tuple[str, datetime]] = []
    for tid, iso in starts.items():
        try:
            parsed.append((tid, datetime.fromisoformat(iso)))
        except ValueError:
            continue
    parsed.sort(key=lambda x: x[1], reverse=True)

    if not parsed:
        return {
            "interval_min": interval, "minutes_since_last": None, "can_start_next": True,
            "next_start_in_min": 0, "last_task": None, "violation": False,
        }

    last_tid, last_dt = parsed[0]
    secs_since = (now_dt - last_dt).total_seconds()
    minutes_since = round(secs_since / 60, 1)
    can_start = secs_since >= interval * 60
    next_in = max(0, round(interval - secs_since / 60))

    violation = False
    if len(parsed) >= 2:
        gap = (parsed[0][1] - parsed[1][1]).total_seconds()
        violation = gap < interval * 60 and secs_since < interval * 60

    return {
        "interval_min": interval,
        "minutes_since_last": minutes_since,
        "can_start_next": can_start,
        "next_start_in_min": next_in,
        "last_task": last_tid,
        "violation": violation,
    }


def executando_stale_report(executando_ids: list[str]) -> list[dict[str, Any]]:
    """Tasks em executando há mais que TASK_STALE_HOURS (start em task_cadence_state)."""
    if not executando_ids:
        return []
    now_dt = datetime.now(timezone.utc)
    try:
        state = json.loads(CADENCE_STATE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        state = {}
    starts: dict[str, str] = state.get("starts", {})
    out: list[dict[str, Any]] = []
    for tid in executando_ids:
        iso = starts.get(tid)
        if not iso:
            continue
        try:
            started = datetime.fromisoformat(iso)
        except ValueError:
            continue
        hours = (now_dt - started).total_seconds() / 3600
        if hours < TASK_STALE_HOURS:
            continue
        severity = "critical" if hours >= TASK_STALE_CRITICAL_HOURS else "warn"
        out.append(
            {
                "id": tid,
                "hours": round(hours, 1),
                "started_at": iso,
                "severity": severity,
            }
        )
    out.sort(key=lambda x: x["hours"], reverse=True)
    return out


CRM_DIR = REPO_ROOT / "crm"
PROJETOS_REGISTRY = REPO_ROOT / "projetos" / "projetos.md"
CRM_SEGMENT_FILES = ["crm_laboratorio.md", "crm_landing_pintor.md", "crm_appvs.md"]

from laboratorio.ops.snapshot_cache import (
    get_snapshot_cache,
    invalidate_maestro_snapshot,
    set_snapshot_cache,
)

_SNAPSHOT_TTL = float(os.getenv("MAESTRO_SNAPSHOT_TTL", "8"))


def get_cached_snapshot(max_age: float | None = None) -> dict[str, Any]:
    """Snapshot com cache curto — ideal para respostas de voz de baixa latência."""
    ttl = _SNAPSHOT_TTL if max_age is None else max_age
    now = time.monotonic()
    cached, ts = get_snapshot_cache()
    if cached is not None and (now - ts) < ttl:
        return cached
    data = build_maestro_snapshot()
    set_snapshot_cache(data)
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

    events = get_event_repository().recent()
    wa_log = parsers.parse_whatsapp_log(
        parsers.read_text(LOGS_DIR / "whatsapp_mensagens.md")
    )
    project_registry = get_project_repository().all()
    # Índice de projetos construído UMA vez e reaproveitado (antes refeito por task).
    proj_index = parsers._build_project_index(project_registry)
    proj_by_id = {p["id"]: p for p in project_registry}
    crms = _build_crms()
    leads = [
        {**lead, "crm": seg["segment"], "crm_name": seg["name"]}
        for seg in crms
        for lead in seg["leads"]
    ]
    if not leads:
        crm_raw = parsers.read_text(CRM_LEADS)
        leads = parsers.parse_leads_index(crm_raw) or parsers.parse_lead_sections(crm_raw)
    task_repo = get_task_repository()
    executando = task_repo.list_by_state("executando")
    planejando = task_repo.list_by_state("planejando")
    for t in executando:
        t["phase"] = "executando"
    for t in planejando:
        t["phase"] = "planejando"
    standby_tasks = task_repo.list_by_state("standby")
    for t in standby_tasks:
        t["phase"] = "standby"
    active_work = executando + planejando
    active_ids = [t["id"] for t in active_work]

    donizete_busca: dict[str, Any] = {}
    try:
        from laboratorio.ops.donizete_runner import busca_snapshot_for_panel

        donizete_busca = busca_snapshot_for_panel()
    except Exception as exc:  # noqa: BLE001 — snapshot nunca quebra por um sub-bloco
        logger.warning("Snapshot Donizete indisponível: %s", exc)
        donizete_busca = {}
    delegations = parsers.parse_delegations_from_tasks(TASKS_DIR, active_ids)
    decisions = parsers.parse_decisions(parsers.read_text(MEMORIA_DIR / "decisoes.md"))
    kanban = task_repo.counts()
    projects = _build_projects(
        project_registry, kanban, active_work, crms, index=proj_index, by_id=proj_by_id
    )
    wa_threads = parsers.group_whatsapp_threads(wa_log)

    messages_today = parsers.count_today(wa_log)
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    leads_today = sum(1 for l in leads if l.get("captura", "").startswith(today_str))

    last_error = _last_error(events, wa_log)
    wa_online = _whatsapp_online(wa_log)
    vps_online = check_vps_service()

    agents = _build_agents(
        active_work, events, wa_log, active_ids, donizete_busca=donizete_busca
    )
    estimated_cost, cost_is_real = _resolve_cost(messages_today, len(active_work))
    briefing = _build_briefing(
        agents,
        active_work,
        wa_log,
        leads,
        last_error,
        vps_online,
        wa_online,
        standby_tasks=standby_tasks,
        donizete_busca=donizete_busca,
    )

    exec_ids = [t["id"] for t in executando]
    cadence = _task_cadence(exec_ids)
    stale_tasks = executando_stale_report(exec_ids)
    lp_capture: dict[str, Any] = {}
    try:
        from laboratorio.ops.donizete_capture import build_capture_report

        cr = build_capture_report()
        lp_capture = {
            "pronto": cr.pronto_count,
            "meta": cr.meta_goal,
            "progress_pct": cr.progress_pct,
            "prospectado": cr.prospectado_count,
            "folders": len(cr.folders),
            "summary": cr.summary_line(),
        }
    except Exception as exc:  # noqa: BLE001 — bloco LP é opcional no painel
        logger.warning("Captura LP indisponível no snapshot: %s", exc)
        lp_capture = {}

    errors = [e for e in events if parsers.event_is_open_error(e)]
    # Alertas = só erros reais (marcos ficam em Eventos)
    alerts = errors[:8]
    # Teto opcional (WIP_SOFT_MAX); 0 = sem teto. Regra principal é a cadência.
    if WIP_SOFT_MAX and len(executando) > WIP_SOFT_MAX:
        alerts = [
            {
                "datetime": now,
                "type": "alerta",
                "title": f"Tasks simultâneas acima do teto — {len(executando)}/{WIP_SOFT_MAX}",
                "detail": ", ".join(t["id"] for t in executando),
                "agents": "ronaldo_maestro",
                "ref": "tasks/executando.md",
            },
            *alerts,
        ]
    if cadence["violation"]:
        alerts = [
            {
                "datetime": now,
                "type": "alerta",
                "title": f"Cadência rápida — 2 tasks iniciadas em < {cadence['interval_min']} min",
                "detail": f"Espaçar starts em ~{cadence['interval_min']} min entre tasks",
                "agents": "ronaldo_maestro",
                "ref": "tasks/executando.md",
            },
            *alerts,
        ]
    for st in stale_tasks:
        h = st["hours"]
        alerts = [
            {
                "datetime": now,
                "type": "alerta",
                "title": f"{st['id']} parada em executando — {h}h",
                "detail": (
                    f"Concluir, fatiar em sub-task ou mover para backlog "
                    f"(limite {TASK_STALE_HOURS}h warn / {TASK_STALE_CRITICAL_HOURS}h crítico)"
                ),
                "agents": "ronaldo_maestro",
                "ref": st["id"],
            },
            *alerts,
        ]
    # Decisões formais vão ao painel Decisões; timeline Eventos = operacional
    events_timeline = [e for e in events if e["type"] != "decisao"]
    decision_titles = {d["title"].lower() for d in decisions}
    events_timeline = [
        e
        for e in events_timeline
        if e["title"].lower() not in decision_titles
    ]

    overview = {
        "system_online": True,
        "vps_online": vps_online,
        "whatsapp_online": wa_online,
        "messages_today": messages_today,
        "leads_today": leads_today,
        "estimated_cost_usd": estimated_cost,
        "cost_is_real": cost_is_real,
        "last_error": last_error,
        "wip_tasks": len(executando),
        "wip_max": WIP_SOFT_MAX,
        "cadence_min": cadence["interval_min"],
        "minutes_since_last_start": cadence["minutes_since_last"],
        "can_start_next": cadence["can_start_next"],
        "next_start_in_min": cadence["next_start_in_min"],
        "last_task_started": cadence["last_task"],
        "stale_tasks": stale_tasks,
        "stale_hours_warn": TASK_STALE_HOURS,
        "stale_hours_critical": TASK_STALE_CRITICAL_HOURS,
        "planning_tasks": len(planejando),
        "active_tasks": exec_ids,
        "planning_task_ids": [t["id"] for t in planejando],
        "lp_capture": lp_capture,
        "donizete_busca": donizete_busca,
        "standby_task_ids": [t["id"] for t in standby_tasks],
    }
    append_metric_from_overview(overview)

    return {
        "generated_at": now,
        "sync_meta": _sync_meta(),
        "briefing": briefing,
        "overview": overview,
        "agents": agents,
        "projects": projects,
        "crms": crms,
        "delegations": delegations,
        "conversations": wa_log,
        "whatsapp_threads": wa_threads,
        "leads": leads,
        "kanban": {k: {"count": len(v), "tasks": v} for k, v in kanban.items()},
        "logs": {
            "events": events_timeline,
            "errors": errors[:10],
            "alerts": alerts[:8],
            "decisions": decisions,
        },
        "interactions": recent_interactions(40),
        "usage": usage.summarize(),
        "pending_tasks": [
            _pending_task_entry(t, project_registry, index=proj_index, by_id=proj_by_id)
            for t in active_work
        ],
        "standby_tasks": [
            _pending_task_entry(t, project_registry, index=proj_index, by_id=proj_by_id)
            for t in standby_tasks
        ],
        "donizete_busca": donizete_busca,
    }


def _pending_task_entry(
    task: dict,
    registry: list[dict],
    *,
    index: dict | None = None,
    by_id: dict | None = None,
) -> dict:
    proj = parsers.project_for_task(task, registry, index=index, by_id=by_id)
    return {
        "id": task["id"],
        "title": task["title"],
        "agents": task["agents"],
        "proxima_acao": task["proxima_acao"],
        "bloqueio": task["bloqueio"],
        "phase": task.get("phase", "executando"),
        "project_id": proj["id"] if proj else None,
        "project_name": proj["name"] if proj else "Sem projeto",
        "project_prefix": proj["prefix"] if proj else None,
    }


def _build_crms() -> list[dict]:
    """CRM segmentado por finalidade (Laboratório, Landing Page Pintor, AppVS…)."""
    return get_crm_repository().segments()


def _build_projects(
    registry: list[dict],
    kanban: dict[str, list[str]],
    active_work: list[dict],
    crms: list[dict],
    *,
    index: dict | None = None,
    by_id: dict | None = None,
) -> list[dict]:
    """Projetos com contagem de tasks por status e tasks ativas (regra: toda task tem projeto)."""
    import re as _re

    if index is None:
        index = parsers._build_project_index(registry)
    crm_names = {seg["segment"]: seg["name"] for seg in crms}

    def resolve(tid: str) -> str | None:
        up = tid.upper()
        m = _re.match(r"([A-Z][A-Z0-9\-]*)-\d+", up)
        if m and m.group(1) in index:
            return index[m.group(1)]
        return index.get(up)

    status_keys = ["executando", "planejando", "aguardando", "backlog", "concluidas", "arquivado"]
    counts: dict[str, dict[str, int]] = {
        p["id"]: {k: 0 for k in status_keys} | {"total": 0} for p in registry
    }
    orphans: list[str] = []
    for status, ids in kanban.items():
        for tid in ids:
            pid = resolve(tid)
            if pid and pid in counts:
                counts[pid][status] = counts[pid].get(status, 0) + 1
                counts[pid]["total"] += 1
            elif status not in ("arquivado",):
                orphans.append(tid)

    active_by_proj: dict[str, list[dict]] = {}
    for t in active_work:
        proj = parsers.project_for_task(t, registry, index=index, by_id=by_id)
        if proj:
            active_by_proj.setdefault(proj["id"], []).append(
                {"id": t["id"], "title": t["title"], "phase": t.get("phase", "")}
            )

    result: list[dict] = []
    for p in registry:
        result.append(
            {
                "id": p["id"],
                "name": p["name"],
                "prefix": p["prefix"],
                "nature": p["nature"],
                "status": p["status"],
                "crm": p.get("crm"),
                "crm_name": crm_names.get(p.get("crm") or "", None),
                "repo": p.get("repo"),
                "description": p.get("description"),
                "counts": counts.get(p["id"], {}),
                "active_tasks": active_by_proj.get(p["id"], []),
            }
        )
    # Projeto fantasma para tasks órfãs (critério: nenhuma task solta — deve ficar vazio)
    if orphans:
        result.append(
            {
                "id": "SEM-PROJETO",
                "name": "Sem projeto",
                "prefix": None,
                "nature": "indefinido",
                "status": "alerta",
                "crm": None,
                "crm_name": None,
                "repo": None,
                "description": "Tasks sem projeto associado — corrigir no registry projetos/projetos.md.",
                "counts": {"total": len(orphans)},
                "active_tasks": [],
                "orphan_ids": sorted(set(orphans)),
            }
        )
    return result


def _build_agents(
    active_work: list[dict],
    events: list[dict],
    wa_log: list[dict],
    active_ids: list[str],
    *,
    donizete_busca: dict[str, Any] | None = None,
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
        elif aid == "donizete_social" and (donizete_busca or {}).get("active"):
            status = "executando"
            db = donizete_busca or {}
            tid = db.get("active_task_id") or ""
            standby = db.get("standby_tasks") or []
            task_ref = tid or (standby[0] if standby else "busca intermitente")
            grupo = db.get("last_group") or db.get("lock_group_url") or "—"
            current_task = f"{task_ref}: captura · {db.get('cycles', 0)} ciclos · {grupo[:50]}"
            last_action = db.get("summary", "Busca Donizete ativa")[:100]
            last_update = (db.get("last_cycle_at") or "—")[:16]
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
    *,
    standby_tasks: list[dict] | None = None,
    donizete_busca: dict[str, Any] | None = None,
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
        ]
        + [
            {
                "id": t["id"],
                "title": t["title"],
                "next": t.get("proxima_acao", "—"),
                "phase": "standby",
            }
            for t in (standby_tasks or [])
        ],
        "donizete_busca": donizete_busca or {},
        "leads_total": len(leads),
        "caio_last_reply": wa_log[0]["outbound"][:160] if wa_log else "Nenhuma conversa ainda",
        "caio_last_phone": wa_log[0]["phone"] if wa_log else "—",
        "had_error": last_error != "Nenhum erro recente",
        "last_error": last_error,
    }


# IDs canônicos dos agentes com backend (mesma lista do AGENT_CATALOG).
_KNOWN_AGENT_IDS = {
    "ronaldo_maestro", "caio_manteiga", "donizete_social", "dev", "juarez", "loide",
}


def re_split_agents(text: str) -> list[str]:
    """Divide um campo multi-agente (separadores · , ;) em IDs conhecidos.

    Usa o normalizador único `parsers._normalize_agent_id` (fonte única do
    mapeamento nome→id); ignora tokens sem agente conhecido e preserva
    duplicatas (comportamento legado).
    """
    ids: list[str] = []
    for token in re.split(r"[·,;]", text):
        if not token.strip():
            continue
        aid = parsers._normalize_agent_id(token)
        if aid in _KNOWN_AGENT_IDS:
            ids.append(aid)
    return ids


def _last_error(events: list[dict], wa_log: list[dict]) -> str:
    for entry in wa_log:
        if "erro" in entry.get("status", "").lower():
            return entry["status"][:200]
    for ev in events:
        if parsers.event_is_open_error(ev):
            return ev["title"]
    return "Nenhum erro recente"


def _whatsapp_online(wa_log: list[dict]) -> bool:
    if not wa_log:
        return bool(os.getenv("WHATSAPP_ACCESS_TOKEN"))
    return wa_log[0].get("status") == "ok" or "erro" not in wa_log[0].get("status", "")


def _resolve_cost(messages_today: int, active_work: int) -> tuple[float, bool]:
    """Custo real (usage.jsonl) quando disponível; senão, estimativa heurística."""
    try:
        summary = usage.summarize()
        if summary.get("total_cost_usd"):
            return round(float(summary["total_cost_usd"]), 3), True
    except Exception as exc:  # noqa: BLE001 — cai para estimativa heurística
        logger.warning("Custo real indisponível, usando estimativa: %s", exc)
    return round(messages_today * 0.012 + active_work * 0.05, 3), False


def _sync_meta() -> dict[str, str | None]:
    """Timestamps dos arquivos-fonte — detecta dados desatualizados na VPS."""
    paths = {
        "executando": TASKS_DIR / "executando.md",
        "eventos": LOGS_DIR / "eventos.md",
        "decisoes": MEMORIA_DIR / "decisoes.md",
    }
    meta: dict[str, str | None] = {}
    for key, path in paths.items():
        try:
            if path.is_file():
                ts = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
                meta[key] = ts.strftime("%Y-%m-%d %H:%M UTC")
            else:
                meta[key] = None
        except OSError:
            meta[key] = None
    return meta


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
