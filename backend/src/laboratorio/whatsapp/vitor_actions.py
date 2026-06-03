"""Ações executáveis no canal WhatsApp Vitor → Ronaldo."""

from __future__ import annotations

import re
from datetime import datetime, timezone

from laboratorio.config import LOGS_DIR
from laboratorio.ops.maestro import build_maestro_snapshot
from laboratorio.ops.ronaldo_patrol import run_patrol
from laboratorio.whatsapp.notify import notify_vitor
from laboratorio.whatsapp.vitor_schedule import add_schedule, cancel_item, list_pending, parse_schedule_request


def run_patrol_now(*, notify_on_issues: bool = True) -> str:
    report = run_patrol(dry_run=False, notify=notify_on_issues)
    lines = [f"Patrulha {report.generated_at}", report.summary]
    for issue in report.issues[:6]:
        icon = "🔴" if issue.notify else "🟡"
        lines.append(f"{icon} {issue.title}")
    if report.notified:
        lines.append(f"Alertas enviados: {', '.join(report.notified)}")
    elif not report.issues:
        lines.append("✓ Nenhum problema detectado.")
    return "\n".join(lines)


def append_operational_event(title: str, detail: str = "", ref: str = "WhatsApp Vitor") -> str:
    path = LOGS_DIR / "eventos.md"
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    block = f"""### {stamp} — [orquestracao] {title}
- **Agente(s):** Vitor · ronaldo_maestro (WhatsApp)
- **Detalhe:** {detail or title}
- **Ref:** {ref}

"""
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    marker = "## Log\n"
    if marker in text:
        text = text.replace(marker, marker + "\n" + block)
    else:
        text = block + text
    path.write_text(text, encoding="utf-8")
    return f"Evento registrado: {title}"


def format_help() -> str:
    return """🎛 Ronaldo — comandos WhatsApp (Laboratório)

CONSULTAR
• status / resumo / briefing
• agentes / time
• tasks / tarefas / wip
• delegações / delegacoes
• erros / logs
• patrulha (último check)
• captura / donizete — monitor LP-PINTOR-001 (CRM + pastas)

EXECUTAR
• patrulha agora — roda check completo
• registrar: [texto] — evento em logs/eventos.md
• teste alerta — valida notificação

AGENDAR
• agendar em 30 min: status
• agendar amanhã 9h: patrulha
• agendar 01/06 14h: resumo tasks
• agenda — lista lembretes pendentes

APROVAÇÃO (Fase 0–4)
• Agente / gasto / ação: APROVAR XXXX ou RECUSAR XXXX
• Resumo diário autoevolução: mesmo formato (aplica propostas do dia)

LIVRE
Qualquer pedido operacional (delegar, priorizar, explicar TASK, VitorOS, Lab). Respondo com contexto real do painel.

Canal autorizado — equivalente ao Cursor/Painel Maestro."""


def format_agenda() -> str:
    pending = list_pending()
    if not pending:
        return "Agenda vazia — nenhum lembrete pendente."
    lines = ["📅 Lembretes pendentes:"]
    for item in pending[:10]:
        lines.append(f"• {item['due_local']} — {item.get('label', item.get('command'))} (id:{item['id']})")
    lines.append("\nPara cancelar: cancelar lembrete ID")
    return "\n".join(lines)


def try_schedule(text: str) -> str | None:
    parsed = parse_schedule_request(text)
    if not parsed:
        if text.lower().strip() in ("agenda", "agendamentos", "lembretes"):
            return format_agenda()
        m = re.match(r"cancelar\s+(?:lembrete\s+)?([a-f0-9]{6,12})", text.lower())
        if m:
            ok = cancel_item(m.group(1))
            return "Lembrete cancelado." if ok else "ID não encontrado."
        return None
    due, cmd, label = parsed
    item = add_schedule(due_at=due, command=cmd, label=label)
    due_str = due.strftime("%d/%m/%Y %H:%M")
    return f"✓ Agendado {due_str} (id:{item['id']})\nComando: {cmd}"


def format_delegations(snapshot: dict) -> str:
    rows = snapshot.get("delegations") or []
    if not rows:
        return "Sem delegações ativas."
    by_task: dict[str, list] = {}
    for d in rows:
        tid = d.get("task_id") or "?"
        by_task.setdefault(tid, []).append(d)
    lines = ["Delegações Ronaldo → especialistas:"]
    for tid in sorted(by_task.keys(), reverse=True):
        lines.append(f"\n{tid}:")
        for d in by_task[tid][:4]:
            lines.append(f"  • {d['to_label']}: {d['task'][:70]}")
    return "\n".join(lines)


def format_tasks_detail(snapshot: dict) -> str:
    o = snapshot.get("overview", {})
    kb = snapshot.get("kanban", {})
    exec_tasks = kb.get("executando", {}).get("tasks", [])
    plan = o.get("planning_task_ids") or []
    lines = [
        f"Em execução: {o.get('wip_tasks', 0)} · cadência {o.get('cadence_min', '—')}min",
        f"Executando: {', '.join(exec_tasks) or '—'}",
        f"Planejando: {', '.join(plan) or '—'}",
    ]
    for t in snapshot.get("pending_tasks", []):
        lines.append(
            f"\n{t['id']} ({t.get('phase', 'exec')})\n"
            f"  {t.get('title', '')[:60]}\n"
            f"  Próxima: {t.get('proxima_acao', '—')[:80]}"
        )
    concl = kb.get("concluidas", {}).get("tasks", [])[:3]
    if concl:
        lines.append(f"\nRecentes concluídas: {', '.join(concl)}")
    return "\n".join(lines)


def format_logs_summary(snapshot: dict) -> str:
    logs = snapshot.get("logs", {})
    lines = ["📋 Logs recentes:"]
    for e in (logs.get("events") or [])[:4]:
        lines.append(f"• [{e.get('type')}] {e.get('title', '')[:70]}")
    dec = logs.get("decisions") or []
    if dec:
        lines.append("\nDecisões:")
        for d in dec[:3]:
            lines.append(f"• {d.get('title', '')[:60]} ({d.get('date', '')})")
    errs = logs.get("errors") or logs.get("alerts") or []
    if errs:
        lines.append("\nAlertas:")
        for e in errs[:3]:
            lines.append(f"• {e.get('title', '')[:70]}")
    return "\n".join(lines)


def test_alert() -> str:
    ok = notify_vitor(
        "Teste de alerta — canal Vitor OK",
        "Ronaldo via Caio. Se recebeu, notificações proativas funcionam.",
        action="Nenhuma — só teste",
        ref="autorizacao_vitor_whatsapp.md",
    )
    return "Alerta de teste enviado ✓" if ok else "Falha ao enviar alerta — verificar token WhatsApp."
