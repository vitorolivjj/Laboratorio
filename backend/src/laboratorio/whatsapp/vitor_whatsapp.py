"""Canal WhatsApp Vitor — Ronaldo operador completo (via Caio)."""

from __future__ import annotations

import json
import logging
import os
import re
import unicodedata
from datetime import datetime, timezone

import httpx

from laboratorio.config import (
    CONTEXTO_GLOBAL,
    LOGS_DIR,
    load_env,
)
from laboratorio.ops.maestro import build_maestro_snapshot, get_cached_snapshot
from laboratorio.ops.ronaldo_voice import (
    _answer_agents,
    _answer_errors,
    _answer_pending,
    _answer_status,
    _answer_whatsapp,
    _fast_answer,
    _fold,
    _normalize_command,
)
from laboratorio.whatsapp.approvals import try_handle_approval_message
from laboratorio.whatsapp.vitor_actions import (
    append_operational_event,
    format_delegations,
    format_help,
    format_logs_summary,
    format_tasks_detail,
    run_patrol_now,
    test_alert,
    try_schedule,
)
from laboratorio.whatsapp.vitor_schedule import run_due_schedules

logger = logging.getLogger("laboratorio.whatsapp.vitor_brain")

SESSION_FILE = LOGS_DIR / "vitor_whatsapp_session.json"
OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"
MAX_HISTORY = 8

VITOR_SYSTEM = """Você é Ronaldo Maestro no canal WhatsApp autorizado do Vitor (dono do Laboratório de Agentes IA).

CANAL = mesmo poder do Cursor e Painel Maestro. NÃO é vendedor.

REGRA CRÍTICA — NUNCA:
- Dizer "vou consultar", "aguarde", "já volto", "deixa eu ver", "em instantes"
- Prometer retorno depois — os dados JÁ ESTÃO no CONTEXTO abaixo
- Responder vazio ou só cumprimento se houver pergunta operacional

Você DEVE responder AGORA com os dados do CONTEXTO:
- Status, TASK-XXX, WIP, agentes, delegações, erros, próximos passos
- Se faltar dado no contexto, diga explicitamente o que falta — não finja que vai buscar

Formato WhatsApp: PT-BR, direto, • bullets ok, TASK-XXX permitido, ~15 linhas max."""

DEFERRAL_PATTERNS = (
    r"vou consultar",
    r"vou verificar",
    r"vou checar",
    r"deixa eu ver",
    r"deixe-me ver",
    r"aguarde",
    r"aguarda",
    r"j[aá] volto",
    r"em instantes",
    r"um momento",
    r"retorno em breve",
    r"assim que tiver",
)


def _load_session(wa_id: str) -> list[dict]:
    if not SESSION_FILE.is_file():
        return []
    try:
        data = json.loads(SESSION_FILE.read_text(encoding="utf-8"))
        return data.get(wa_id, [])[-MAX_HISTORY:]
    except (json.JSONDecodeError, OSError):
        return []


def _save_session(wa_id: str, history: list[dict]) -> None:
    SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {}
    if SESSION_FILE.is_file():
        try:
            data = json.loads(SESSION_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            data = {}
    data[wa_id] = history[-MAX_HISTORY:]
    SESSION_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _rich_context(snapshot: dict, *, query: str = "") -> str:
    o = snapshot.get("overview", {})
    b = snapshot.get("briefing", {})
    sync = snapshot.get("sync_meta") or {}
    agents = "; ".join(
        f"{a['name']}={a['status']}:{str(a.get('current_task',''))[:40]}"
        for a in snapshot.get("agents", [])
    )
    tasks = "\n".join(
        f"  {t['id']} [{t.get('phase','')}] {t.get('title','')[:50]} → {t.get('proxima_acao','')[:40]}"
        for t in snapshot.get("pending_tasks", [])
    )
    events = "\n".join(
        f"  [{e.get('type')}] {e.get('title','')[:60]}"
        for e in (snapshot.get("logs", {}).get("events") or [])[:5]
    )
    ctx_snip = ""
    if CONTEXTO_GLOBAL.is_file():
        ctx_snip = CONTEXTO_GLOBAL.read_text(encoding="utf-8")[:800]

    base = f"""CONTEXTO GLOBAL (trecho):
{ctx_snip}

SNAPSHOT {snapshot.get('generated_at')} · sync kanban {sync.get('executando', '?')}
Headline: {b.get('headline')}
Online sys/vps/wa: {o.get('system_online')}/{o.get('vps_online')}/{o.get('whatsapp_online')}
Em execução: {o.get('wip_tasks')} · cadência {o.get('cadence_min')}min · Ativas: {', '.join(o.get('active_tasks') or [])}
Planejando: {', '.join(o.get('planning_task_ids') or []) or '—'}
Trabalhando: {', '.join(b.get('who_working') or []) or 'ninguém'}
Erro recente: {b.get('last_error', '—')}

TASKS:
{tasks or '  —'}

AGENTES:
{agents}

EVENTOS RECENTES:
{events or '  —'}

DELEGAÇÕES: {len(snapshot.get('delegations') or [])} ativas
LEADS: {b.get('leads_total', 0)} · Msgs WA hoje: {o.get('messages_today', 0)}"""

    if query.strip():
        semantic = augment_with_semantic_memory(query, top_k=4)
        if semantic:
            base += semantic[:2000]
    return base


def _llm_reply(message: str, snapshot: dict, history: list[dict]) -> str:
    load_env()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "OPENAI_API_KEY ausente — consultas livres indisponíveis. Use: status, tasks, patrulha agora, ajuda."

    model = os.getenv("VITOR_WHATSAPP_MODEL", os.getenv("VOICE_LLM_MODEL", "gpt-4o-mini"))
    messages = [{"role": "system", "content": VITOR_SYSTEM + "\n\n" + _rich_context(snapshot, query=message)}]
    for turn in history[-4:]:
        messages.append({"role": turn["role"], "content": turn["content"]})
    messages.append({"role": "user", "content": message})

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.35,
        "max_tokens": int(os.getenv("VITOR_WHATSAPP_MAX_TOKENS", "900")),
    }
    with httpx.Client(timeout=45.0) as client:
        resp = client.post(
            OPENAI_CHAT_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()


def _is_deferral(text: str) -> bool:
    low = text.lower()
    return any(re.search(p, low) for p in DEFERRAL_PATTERNS)


def _fallback_from_snapshot(snapshot: dict, prefix: str = "") -> str:
    parts = []
    if prefix:
        parts.append(prefix)
    panel, _ = _answer_status(snapshot)
    parts.append(panel)
    tasks = format_tasks_detail(snapshot)
    if tasks:
        parts.append("\n" + tasks)
    return _trim("\n".join(parts))


def _vitor_fast_answer(text: str, snapshot: dict) -> str | None:
    """Fast-path ampliado — Vitor não cai em LLM por verbos de ação se for consulta."""
    normalized = _normalize_command(text)
    folded = _fold(normalized)

    query_hints = (
        "status", "resumo", "briefing", "panorama", "situacao", "como esta", "como ta",
        "operacao", "visao geral", "consulta", "consultar", "me fala", "me diz",
        "qual", "quais", "mostra", "mostrar", "ver ", "wip", "andamento",
    )
    is_query = any(h in folded for h in query_hints)

    if is_query:
        if any(k in folded for k in ("erro", "problema", "falha", "bug")):
            panel, _ = _answer_errors(snapshot)
            return panel
        if any(k in folded for k in ("agente", "time", "equipe", "quem")):
            panel, _ = _answer_agents(snapshot)
            return panel
        if any(k in folded for k in ("task", "tarefa", "wip", "andamento", "kanban", "pendente")):
            return format_tasks_detail(snapshot)
        if any(k in folded for k in ("deleg", "delegação", "delegacao")):
            return format_delegations(snapshot)
        if any(k in folded for k in ("log", "evento", "decis")):
            return format_logs_summary(snapshot)
        panel, _ = _answer_status(snapshot)
        return panel

    fast = _fast_answer(normalized, snapshot)
    if fast is not None:
        return fast[0]
    return None


def _needs_ack(text: str) -> bool:
    """Operações que podem demorar — manda ack antes."""
    f = _fold(text)
    if any(k in f for k in ("patrulha", "patrol", "orquestr", "delega", "criar task")):
        return True
    quick = (
        "status", "tasks", "tarefas", "ajuda", "help", "agentes", "deleg",
        "logs", "agenda", "wip", "resumo", "briefing", "oi", "ola", "olá",
    )
    return not any(q in f for q in quick)


def _match_exec(text: str) -> str | None:
    f = _fold(text)

    if f in ("ajuda", "help", "comandos", "menu", "?"):
        return format_help()

    if any(k in f for k in ("patrulha agora", "rodar patrulha", "executar patrulha", "check agora")):
        return run_patrol_now(notify_on_issues=False)

    if f.strip() in ("patrulha", "patrol"):
        return run_patrol_now(notify_on_issues=False)

    if any(k in f for k in ("teste alerta", "testar alerta", "testar notificacao", "ping alerta")):
        return test_alert()

    if f.startswith("registrar:") or f.startswith("registrar "):
        body = re.sub(r"^registrar\s*:?\s*", "", text, flags=re.I).strip()
        if body:
            return append_operational_event(body[:120], body)

    scheduled = try_schedule(text)
    if scheduled:
        return scheduled

    return None


def process_vitor_message(from_wa_id: str, user_message: str, *, fresh_snapshot: bool = False) -> str:
    """Processa mensagem do Vitor — executa, agenda ou responde com contexto completo."""
    text = user_message.strip()
    if not text:
        return "Manda o comando — status, tasks, patrulha agora, agendar, ou pergunta livre."

    logger.info("Vitor WA: %s", text[:100])

    approval_reply = try_handle_approval_message(text)
    if approval_reply is not None:
        return _trim(approval_reply)

    # Snapshot: cache primeiro (rápido); refresh só se pedido ou LLM
    snapshot = get_cached_snapshot(max_age=20)

    # 1) Ações executáveis
    exec_result = _match_exec(text)
    if exec_result:
        _append_history(from_wa_id, text, exec_result, source="exec")
        return _trim(exec_result)

    # 2) Fast-path ampliado (consultas reais — nunca "vou consultar")
    fast_reply = _vitor_fast_answer(text, snapshot)
    if fast_reply:
        _append_history(from_wa_id, text, fast_reply, source="fast")
        return _trim(fast_reply)

    # 3) LLM — contexto fresco
    if fresh_snapshot:
        snapshot = build_maestro_snapshot()

    history = _load_session(from_wa_id)
    try:
        reply = _llm_reply(text, snapshot, history)
        source = "llm"
        if _is_deferral(reply) or len(reply.strip()) < 40:
            logger.warning("LLM deferiu ou resposta curta — fallback snapshot")
            reply = _fallback_from_snapshot(
                snapshot,
                "Segue situação atual do Laboratório:",
            )
            source = "fallback_deferral"
    except Exception as exc:
        logger.warning("LLM Vitor falhou: %s", exc)
        reply = _fallback_from_snapshot(snapshot, f"(LLM indisponível: {exc})\n")
        source = "fallback"

    _append_history(from_wa_id, text, reply, source=source)
    return _trim(reply)


def _append_history(wa_id: str, user: str, assistant: str, source: str) -> None:
    hist = _load_session(wa_id)
    hist.append({"role": "user", "content": user, "ts": datetime.now(timezone.utc).isoformat()})
    hist.append({"role": "assistant", "content": assistant[:2000], "source": source})
    _save_session(wa_id, hist)


def _trim(text: str, limit: int = 3800) -> str:
    t = re.sub(r"\n{3,}", "\n\n", text.strip())
    if len(t) <= limit:
        return t
    return t[: limit - 1].rsplit("\n", 1)[0] + "\n…"


def process_due_reminders() -> list[tuple[str, str]]:
    """Chamado pelo timer — envia lembretes vencidos."""

    def _run_cmd(command: str) -> str:
        fake_id = "schedule"
        return process_vitor_message(fake_id, command, fresh_snapshot=True)

    results = run_due_schedules(_run_cmd)
    out: list[tuple[str, str]] = []
    for row in results:
        item = row["item"]
        body = f"⏰ Lembrete ({item.get('label', item.get('command'))})\n\n{row['body']}"
        out.append((item.get("id", ""), body))
    return out


def vitor_needs_ack(text: str) -> bool:
    return _needs_ack(text)
