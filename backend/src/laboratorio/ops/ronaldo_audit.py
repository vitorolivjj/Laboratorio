"""Rotina de auditoria pós-conclusão — Ronaldo Maestro.

Ciclo: quando uma task entra em `concluidas.md`, Ronaldo audita.
Se houver necessidade, delega e cria tasks de follow-up no backlog.

Fluxo por task recém-concluída (ainda não auditada):
1. Audita (LLM persona Ronaldo) → veredito, gaps, aprendizados, follow-ups.
2. Registra em `logs/auditorias.md`.
3. Cria tasks de follow-up no backlog (máx. 2) com briefing/delegação.
4. Notifica Vitor só se precisar de decisão dele.
5. Marca como auditada (state) — idempotente.

CLI: `python -m laboratorio.main ronaldo-audit [--dry-run] [--no-create] [--no-notify]`
"""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import httpx

from laboratorio.config import MEMORIA_DIR, TASK_CADENCE_MIN, TASKS_DIR, load_env
from laboratorio.ops import parsers
from laboratorio.whatsapp.notify import notify_vitor

logger = logging.getLogger("laboratorio.ops.ronaldo_audit")

LOGS_DIR = TASKS_DIR.parent / "logs"
AUDIT_LOG = LOGS_DIR / "auditorias.md"
AUDIT_STATE = LOGS_DIR / "ronaldo_audit_state.json"
PROJETOS_REGISTRY = TASKS_DIR.parent / "projetos" / "projetos.md"
BACKLOG = TASKS_DIR / "backlog.md"
OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"
MAX_FOLLOWUPS = 2

RONALDO_AUDIT_SYSTEM = (
    "Você é o Ronaldo Maestro, orquestrador do Laboratório de Agentes IA. "
    "Acabou de receber uma TASK CONCLUÍDA por um especialista. Faça a conferência (auditoria) "
    "com rigor de maestro: verifique se o resultado cumpre o objetivo, aponte gaps, extraia "
    "aprendizados e decida se há follow-ups necessários. Seja conciso e prático.\n\n"
    "Responda SOMENTE com JSON válido neste formato:\n"
    "{\n"
    '  "veredito": "aprovado" | "aprovado_com_ressalvas" | "ajustes_necessarios",\n'
    '  "resumo": "1-2 frases sobre a entrega",\n'
    '  "gaps": ["pontos faltantes ou riscos"],\n'
    '  "aprendizados": ["lições para o ecossistema"],\n'
    '  "followups": [\n'
    '    {"titulo": "...", "agente": "dev|loide|caio_manteiga|donizete_social|juarez|ronaldo_maestro", '
    '"objetivo": "...", "prioridade": "alta|media|baixa"}\n'
    "  ],\n"
    '  "escalar_vitor": true | false,\n'
    '  "motivo_escalacao": "vazio se não escalar"\n'
    "}\n"
    "Crie follow-ups SÓ se forem realmente necessários (no máximo 2). Se a entrega fecha o escopo, deixe followups vazio."
)


@dataclass
class AuditResult:
    task_id: str
    title: str
    veredito: str
    resumo: str
    gaps: list[str] = field(default_factory=list)
    aprendizados: list[str] = field(default_factory=list)
    followups: list[dict] = field(default_factory=list)
    escalar_vitor: bool = False
    motivo_escalacao: str = ""
    created_tasks: list[str] = field(default_factory=list)
    notified: bool = False
    via: str = "llm"


# --------------------------------------------------------------------------- #
# Estado / parsing
# --------------------------------------------------------------------------- #
def _load_state() -> dict:
    try:
        return json.loads(AUDIT_STATE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"audited": []}


def _save_state(state: dict) -> None:
    try:
        AUDIT_STATE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    except OSError:
        logger.exception("Falha ao gravar estado de auditoria")


def parse_completed_tasks(content: str) -> list[dict]:
    """Lê concluidas.md → tasks finalizadas (id, title, agent, projeto, resultado, aprendizado)."""
    tasks: list[dict] = []
    anchor = content.find("## Concluídas")
    body = content[anchor:] if anchor != -1 else content
    for m in re.finditer(
        r"^### ([A-Z][A-Z0-9\-]*-\d+) — (.+?)\n(.*?)(?=^### |\Z)",
        body,
        re.MULTILINE | re.DOTALL,
    ):
        block = m.group(3)
        tasks.append(
            {
                "id": m.group(1),
                "title": m.group(2).strip(),
                "agents": parsers._field(block, "Agente"),
                "projeto": parsers._field(block, "Projeto"),
                "concluida_em": parsers._field(block, "Concluída em"),
                "resultado": parsers._field(block, "Resultado"),
                "aprendizado": parsers._field(block, "Aprendizado"),
            }
        )
    return tasks


# --------------------------------------------------------------------------- #
# Auditoria (LLM + fallback)
# --------------------------------------------------------------------------- #
def _audit_via_llm(task: dict) -> dict | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    model = os.getenv("AUDIT_LLM_MODEL", os.getenv("VITOR_WHATSAPP_MODEL", "gpt-4o-mini"))
    user = (
        f"TASK {task['id']} — {task['title']}\n"
        f"Projeto: {task.get('projeto') or '—'}\n"
        f"Agente(s): {task.get('agents') or '—'}\n"
        f"Concluída em: {task.get('concluida_em') or '—'}\n"
        f"Resultado declarado: {task.get('resultado') or '—'}\n"
        f"Aprendizado declarado: {task.get('aprendizado') or '—'}"
    )
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": RONALDO_AUDIT_SYSTEM},
            {"role": "user", "content": user},
        ],
        "temperature": 0.3,
        "max_tokens": 700,
        "response_format": {"type": "json_object"},
    }
    try:
        with httpx.Client(timeout=45.0) as client:
            resp = client.post(
                OPENAI_CHAT_URL,
                headers={"Authorization": f"Bearer {api_key}"},
                json=payload,
            )
            resp.raise_for_status()
            raw = resp.json()["choices"][0]["message"]["content"]
        return json.loads(raw)
    except Exception:
        logger.exception("Auditoria LLM falhou para %s", task["id"])
        return None


def _audit_fallback(task: dict) -> dict:
    """Sem API key: registra auditoria mínima sem inventar follow-ups."""
    has_result = bool((task.get("resultado") or "").strip())
    return {
        "veredito": "aprovado_com_ressalvas" if has_result else "ajustes_necessarios",
        "resumo": task.get("resultado") or "Sem resultado declarado — revisar manualmente.",
        "gaps": [] if has_result else ["Resultado não declarado em concluidas.md"],
        "aprendizados": [task["aprendizado"]] if task.get("aprendizado") else [],
        "followups": [],
        "escalar_vitor": not has_result,
        "motivo_escalacao": "" if has_result else f"{task['id']} concluída sem resultado declarado",
    }


def audit_task(task: dict) -> AuditResult:
    data = _audit_via_llm(task)
    via = "llm"
    if data is None:
        data = _audit_fallback(task)
        via = "fallback"
    followups = data.get("followups") or []
    if isinstance(followups, dict):
        followups = [followups]
    return AuditResult(
        task_id=task["id"],
        title=task["title"],
        veredito=str(data.get("veredito") or "aprovado"),
        resumo=str(data.get("resumo") or "").strip(),
        gaps=[str(g) for g in (data.get("gaps") or [])],
        aprendizados=[str(a) for a in (data.get("aprendizados") or [])],
        followups=followups[:MAX_FOLLOWUPS],
        escalar_vitor=bool(data.get("escalar_vitor")),
        motivo_escalacao=str(data.get("motivo_escalacao") or "").strip(),
        via=via,
    )


# --------------------------------------------------------------------------- #
# Criação de follow-ups (delegação)
# --------------------------------------------------------------------------- #
def _registry() -> list[dict]:
    return parsers.parse_projects_registry(parsers.read_text(PROJETOS_REGISTRY))


def _next_task_id(prefix: str) -> str:
    nums = []
    for p in TASKS_DIR.glob(f"{prefix}-*.md"):
        m = re.match(rf"{re.escape(prefix)}-(\d+)", p.stem)
        if m:
            nums.append(int(m.group(1)))
    nxt = (max(nums) + 1) if nums else 1
    return f"{prefix}-{nxt:03d}"


def _agent_label(agent_id: str) -> str:
    labels = {
        "ronaldo_maestro": "Ronaldo", "caio_manteiga": "Caio", "donizete_social": "Donizete",
        "dev": "Dev", "juarez": "Juarez", "loide": "Loide",
    }
    return labels.get(agent_id, agent_id.replace("_", " ").title())


def create_followup_task(parent: dict, fu: dict, registry: list[dict], dry_run: bool) -> str | None:
    """Cria task de follow-up no backlog com briefing (delegação)."""
    proj = parsers.project_for_task(parent, registry)
    prefix = (proj["prefix"] if proj else None) or "TASK"
    proj_id = proj["id"] if proj else (parent.get("projeto") or "—")
    new_id = _next_task_id(prefix)
    title = (fu.get("titulo") or "Follow-up").strip()
    agent_id = parsers._normalize_agent_id(str(fu.get("agente") or "ronaldo_maestro"))
    objetivo = (fu.get("objetivo") or title).strip()
    prioridade = (fu.get("prioridade") or "media").strip()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    if dry_run:
        return f"{new_id} → {_agent_label(agent_id)} ({title})"

    doc = f"""# {new_id} — {title}

## Metadados

| Campo | Valor |
|-------|-------|
| **ID** | {new_id} |
| **Projeto** | {proj_id} |
| **Status** | backlog |
| **Kanban** | tasks/backlog.md |
| **Prioridade** | {prioridade} |
| **Agente responsável** | {agent_id} |
| **Origem** | auditoria {parent['id']} (Ronaldo) |
| **Criada em** | {today} |

## Objetivo

{objetivo}

## Critérios de aceite

- [ ] Cumpre o objetivo derivado da auditoria de {parent['id']}

### Briefing — {_agent_label(agent_id)} — {new_id} — {today}
- **Objetivo desta rodada:** {objetivo}
- **Origem:** follow-up da auditoria de {parent['id']} — {parent['title']}
- **Critério de pronto:** entrega que fecha o gap apontado na auditoria
"""
    (TASKS_DIR / f"{new_id}.md").write_text(doc, encoding="utf-8")
    _append_backlog(new_id, title, proj_id, agent_id, parent["id"])
    return f"{new_id} → {_agent_label(agent_id)} ({title})"


def _append_backlog(new_id: str, title: str, proj_id: str, agent_id: str, parent_id: str) -> None:
    content = parsers.read_text(BACKLOG)
    entry = (
        f"### {new_id} — {title}\n"
        f"- **Contexto:** {proj_id} · follow-up auditoria {parent_id}\n"
        f"- **Prioridade:** media\n"
        f"- **Agente responsável:** {agent_id}\n"
        f"- **Status:** backlog · [{new_id}.md]({new_id}.md)\n\n"
    )
    marker = "<!-- Novas tarefas acima desta linha -->"
    if marker in content:
        content = content.replace(marker, entry + marker)
    else:
        content = content.rstrip() + "\n\n" + entry
    BACKLOG.write_text(content, encoding="utf-8")


# --------------------------------------------------------------------------- #
# Log de auditoria
# --------------------------------------------------------------------------- #
def _append_audit_log(result: AuditResult) -> None:
    if not AUDIT_LOG.exists():
        AUDIT_LOG.write_text(
            "# Auditorias (Ronaldo Maestro)\n\n"
            "Conferência pós-conclusão de tasks. Mais recente no topo.\n\n---\n\n",
            encoding="utf-8",
        )
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"## {result.task_id} — {result.title}",
        f"- **Auditada em:** {ts} · via {result.via}",
        f"- **Veredito:** {result.veredito}",
        f"- **Resumo:** {result.resumo or '—'}",
    ]
    if result.gaps:
        lines.append("- **Gaps:** " + " · ".join(result.gaps))
    if result.aprendizados:
        lines.append("- **Aprendizados:** " + " · ".join(result.aprendizados))
    if result.created_tasks:
        lines.append("- **Follow-ups criados:** " + " · ".join(result.created_tasks))
    elif result.followups:
        lines.append("- **Follow-ups sugeridos:** " + " · ".join(f.get("titulo", "?") for f in result.followups))
    if result.escalar_vitor:
        lines.append(f"- **Escalado ao Vitor:** {result.motivo_escalacao or 'sim'}")
    block = "\n".join(lines) + "\n\n"
    content = AUDIT_LOG.read_text(encoding="utf-8")
    content = content.replace("---\n\n", "---\n\n" + block, 1)
    AUDIT_LOG.write_text(content, encoding="utf-8")


# --------------------------------------------------------------------------- #
# Runner
# --------------------------------------------------------------------------- #
def run_audit(*, dry_run: bool = False, create: bool = True, notify: bool = True) -> list[AuditResult]:
    load_env()
    completed = parse_completed_tasks(parsers.read_text(TASKS_DIR / "concluidas.md"))
    state = _load_state()
    audited: set[str] = set(state.get("audited", []))
    registry = _registry()
    results: list[AuditResult] = []

    for task in completed:
        if task["id"] in audited:
            continue
        result = audit_task(task)

        if create and result.followups:
            for fu in result.followups:
                try:
                    created = create_followup_task(task, fu, registry, dry_run)
                    if created:
                        result.created_tasks.append(created)
                except Exception:
                    logger.exception("Falha ao criar follow-up de %s", task["id"])

        if notify and result.escalar_vitor:
            ok = notify_vitor(
                f"Auditoria {task['id']} — {result.veredito}",
                result.motivo_escalacao or result.resumo,
                action="Revisar / decidir",
                ref=f"logs/auditorias.md · {task['id']}",
                dry_run=dry_run,
            )
            result.notified = ok

        if not dry_run:
            _append_audit_log(result)
            audited.add(task["id"])

        results.append(result)

    if not dry_run and results:
        state["audited"] = sorted(audited)
        _save_state(state)

    return results
