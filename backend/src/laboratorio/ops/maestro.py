"""Snapshot JSON completo do Painel Maestro."""

from __future__ import annotations

import os
import subprocess
from datetime import datetime, timezone
from typing import Any

from laboratorio.agents.llm_config import resolve_agent_llm_config
from laboratorio.config import LOGS_DIR, MEMORIA_DIR, REPO_ROOT, TASKS_DIR
from laboratorio.ops import parsers

CRM_LEADS = REPO_ROOT / "crm" / "leads.md"

AGENT_CATALOG: list[dict[str, str]] = [
    {
        "id": "ronaldo_maestro",
        "name": "Ronaldo",
        "role": "Orquestrador estratégico",
        "function": "Coordena agentes, prioriza e consolida entregas",
        "has_backend": "true",
    },
    {
        "id": "caio_manteiga",
        "name": "Caio",
        "role": "Comercial",
        "function": "Conversão WhatsApp e funis de venda",
        "has_backend": "true",
    },
    {
        "id": "donizete_social",
        "name": "Donizete",
        "role": "Captação",
        "function": "Captura e qualifica leads orgânicos",
        "has_backend": "true",
    },
    {
        "id": "dev",
        "name": "Dev",
        "role": "Desenvolvimento",
        "function": "Sistemas, backend e automações",
        "has_backend": "true",
    },
    {
        "id": "juarez",
        "name": "Juarez",
        "role": "Operações",
        "function": "KPIs, processos e produtividade",
        "has_backend": "true",
    },
    {
        "id": "loide",
        "name": "Loide",
        "role": "UX / Operações",
        "function": "Experiência, fluxos e governança de interface",
        "has_backend": "false",
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
    active_ids = [t["id"] for t in executando]
    delegations = parsers.parse_delegations_from_tasks(TASKS_DIR, active_ids)
    decisions = parsers.parse_decisions(parsers.read_text(MEMORIA_DIR / "decisoes.md"))

    messages_today = parsers.count_today(wa_log)
    leads_today = sum(1 for l in leads if l.get("captura", "").startswith(datetime.now(timezone.utc).strftime("%Y-%m-%d")))

    last_error = _last_error(events, wa_log)
    wa_online = _whatsapp_online(wa_log)
    vps_online = check_vps_service()

    agents = _build_agents(executando, events, wa_log, active_ids)
    estimated_cost = round(messages_today * 0.012 + len(executando) * 0.05, 3)

    errors = [e for e in events if e["type"] == "erro"]
    alerts = [e for e in events if e["type"] in ("erro", "marco")][:5]

    return {
        "generated_at": now,
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
            "active_tasks": active_ids,
        },
        "agents": agents,
        "delegations": delegations,
        "conversations": wa_log,
        "leads": leads,
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
            }
            for t in executando
        ],
    }


def _build_agents(
    executando: list[dict],
    events: list[dict],
    wa_log: list[dict],
    active_ids: list[str],
) -> list[dict]:
    agent_tasks: dict[str, list[str]] = {}
    for task in executando:
        for part in re_split_agents(task["agents"]):
            agent_tasks.setdefault(part, []).append(f"{task['id']}: {task['title']}")

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
        elif aid == "ronaldo_maestro" and executando:
            status = "executando"
            current_task = f"Coordena {len(executando)} TASK(s)"

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
            }
        )
    return result


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
