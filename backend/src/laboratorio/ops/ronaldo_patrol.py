"""Patrulha operacional periódica — Ronaldo Maestro."""

from __future__ import annotations

import hashlib
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from laboratorio.config import LOGS_DIR, TASKS_DIR, TASK_STALE_CRITICAL_HOURS, TASK_STALE_HOURS, WIP_SOFT_MAX
from laboratorio.ops import parsers
from laboratorio.ops.maestro import build_maestro_snapshot, executando_stale_report
from laboratorio.whatsapp.notify import notify_vitor

logger = logging.getLogger("laboratorio.ops.ronaldo_patrol")

PATROL_LOG = LOGS_DIR / "ronaldo_patrol.md"
PATROL_STATE = LOGS_DIR / "ronaldo_patrol_state.json"
DEDUP_HOURS = 4

ESCALATION_KEYWORDS = (
    "vitor",
    "credencial",
    "senha",
    "token",
    "autoriz",
    "aprova",
    "pagamento",
    "custo",
    "conta nova",
    "api key",
)


@dataclass
class PatrolIssue:
    code: str
    severity: str  # info | warn | critical
    title: str
    detail: str
    action: str = ""
    ref: str = ""
    notify: bool = False


@dataclass
class PatrolReport:
    generated_at: str
    issues: list[PatrolIssue] = field(default_factory=list)
    notified: list[str] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> dict:
        return {
            "generated_at": self.generated_at,
            "issues": [i.__dict__ for i in self.issues],
            "notified": self.notified,
            "summary": self.summary,
        }


def _issue_hash(issue: PatrolIssue) -> str:
    raw = f"{issue.code}|{issue.title}|{issue.ref}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _load_state() -> dict:
    if not PATROL_STATE.is_file():
        return {"notified": {}}
    try:
        return json.loads(PATROL_STATE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"notified": {}}


def _save_state(state: dict) -> None:
    PATROL_STATE.parent.mkdir(parents=True, exist_ok=True)
    PATROL_STATE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _should_notify(state: dict, issue: PatrolIssue) -> bool:
    if not issue.notify:
        return False
    h = _issue_hash(issue)
    last = state.get("notified", {}).get(h)
    if not last:
        return True
    try:
        last_dt = datetime.fromisoformat(last.replace("Z", "+00:00"))
        elapsed = datetime.now(timezone.utc) - last_dt
        return elapsed.total_seconds() > DEDUP_HOURS * 3600
    except ValueError:
        return True


def _mark_notified(state: dict, issue: PatrolIssue) -> None:
    h = _issue_hash(issue)
    state.setdefault("notified", {})[h] = datetime.now(timezone.utc).isoformat()


def _scan_governance() -> list[PatrolIssue]:
    from laboratorio.ops.governance_audit import run_governance_audit

    report = run_governance_audit()
    issues: list[PatrolIssue] = []
    for f in report.findings:
        if f.severity in ("ok", "info"):
            continue
        issues.append(
            PatrolIssue(
                code=f.code,
                severity="critical" if f.severity == "critical" else "warn",
                title=f.title,
                detail=f.detail[:240],
                action=f.action or "Ver logs/governanca_auditoria.md",
                ref=f.ref,
                notify=f.severity == "critical",
            )
        )
    return issues


def _scan_tasks() -> list[PatrolIssue]:
    issues: list[PatrolIssue] = []
    exec_content = parsers.read_text(TASKS_DIR / "executando.md")
    tasks = parsers.parse_executando_tasks(exec_content)
    wip = len(tasks)

    # Sem teto rígido — regra principal é cadência (intervalo entre starts).
    # Só alerta se WIP_SOFT_MAX estiver configurado e for excedido.
    if WIP_SOFT_MAX and wip > WIP_SOFT_MAX:
        issues.append(
            PatrolIssue(
                code="wip_overflow",
                severity="warn",
                title=f"Tasks simultâneas acima do teto — {wip}/{WIP_SOFT_MAX}",
                detail=", ".join(t["id"] for t in tasks),
                action="Concluir uma TASK ou ajustar WIP_SOFT_MAX",
                ref="tasks/executando.md",
                notify=True,
            )
        )

    for st in executando_stale_report([t["id"] for t in tasks]):
        sev = "critical" if st["severity"] == "critical" else "warn"
        issues.append(
            PatrolIssue(
                code="task_stale",
                severity=sev,
                title=f"{st['id']} em executando há {st['hours']}h",
                detail=(
                    f"Start {st['started_at'][:10]} · fatiar, concluir parcial ou mover para backlog "
                    f"(>{TASK_STALE_HOURS}h / crítico >{TASK_STALE_CRITICAL_HOURS}h)"
                ),
                action="Ronaldo: checkpoint — entregável do dia ou nova task menor",
                ref=st["id"],
                notify=st["severity"] == "critical",
            )
        )

    for task in tasks:
        bloqueio = (task.get("bloqueio") or "").lower()
        if bloqueio and bloqueio not in ("—", "-", "nenhum", "nenhum —"):
            needs_vitor = any(k in bloqueio for k in ESCALATION_KEYWORDS)
            if needs_vitor:
                issues.append(
                    PatrolIssue(
                        code="bloqueio_vitor",
                        severity="critical",
                        title=f"{task['id']} bloqueada — precisa de você",
                        detail=task.get("bloqueio", "")[:200],
                        action="Responder ou desbloquear via WhatsApp ou Cursor",
                        ref=task["id"],
                        notify=True,
                    )
                )

        task_path = TASKS_DIR / f"{task['id']}.md"
        if task_path.is_file():
            content = parsers.read_text(task_path)
            if "Briefing" not in content and "briefing" not in content.lower():
                issues.append(
                    PatrolIssue(
                        code="sem_briefing",
                        severity="warn",
                        title=f"{task['id']} em executando sem briefing",
                        detail="Protocolo Ronaldo exige briefing antes de executar",
                        action="Ronaldo emitir briefing ou mover para planejando",
                        ref=task["id"],
                        notify=False,
                    )
                )

    return issues


def _scan_infra(snapshot: dict) -> list[PatrolIssue]:
    issues: list[PatrolIssue] = []
    o = snapshot.get("overview", {})
    b = snapshot.get("briefing", {})

    if not o.get("vps_online"):
        issues.append(
            PatrolIssue(
                code="vps_off",
                severity="critical",
                title="VPS Laboratório offline",
                detail="systemctl laboratorio-api não está active",
                action="Verificar VPS ou autorizar Dev a reiniciar",
                ref="PROJ-001",
                notify=True,
            )
        )

    if not o.get("whatsapp_online"):
        issues.append(
            PatrolIssue(
                code="wa_off",
                severity="critical",
                title="WhatsApp API indisponível",
                detail="Caio não consegue enviar/receber mensagens",
                action="Verificar token Meta / WHATSAPP_ACCESS_TOKEN",
                ref="TASK-007",
                notify=True,
            )
        )

    if b.get("had_error") and str(b.get("last_error", "")).strip() not in (
        "",
        "Nenhum erro recente",
    ):
        issues.append(
            PatrolIssue(
                code="last_error",
                severity="warn",
                title="Erro operacional recente",
                detail=str(b.get("last_error", ""))[:200],
                action="Ver painel Logs ou responder aqui no WhatsApp",
                ref="logs/eventos.md",
                notify=True,
            )
        )

    errors = snapshot.get("logs", {}).get("errors") or []
    for err in errors[:2]:
        issues.append(
            PatrolIssue(
                code=f"evento_erro_{err.get('title', '')[:20]}",
                severity="warn",
                title=f"Erro: {err.get('title', 'evento')[:60]}",
                detail=str(err.get("detail", ""))[:160],
                ref=err.get("ref", "logs/eventos.md"),
                notify=True,
            )
        )

    return issues


def run_patrol(*, dry_run: bool = False, notify: bool = True) -> PatrolReport:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    snapshot = build_maestro_snapshot()
    issues = _scan_tasks() + _scan_governance() + _scan_infra(snapshot)

    o = snapshot.get("overview", {})
    active = o.get("active_tasks") or []
    cad = o.get("cadence_min", "—")
    summary = (
        f"Em execução {o.get('wip_tasks', 0)} · cadência {cad}min · "
        f"Tasks: {', '.join(active) or 'nenhuma'} · "
        f"Issues: {len(issues)} ({sum(1 for i in issues if i.notify)} escaláveis)"
    )

    report = PatrolReport(generated_at=now, issues=issues, summary=summary)
    state = _load_state()
    notified_codes: list[str] = []

    if notify:
        for issue in issues:
            if _should_notify(state, issue):
                ok = notify_vitor(
                    issue.title,
                    issue.detail,
                    action=issue.action,
                    ref=issue.ref,
                    dry_run=dry_run,
                )
                if ok:
                    _mark_notified(state, issue)
                    notified_codes.append(issue.code)

    if not dry_run:
        _append_patrol_log(report)
        _save_state(state)
        from laboratorio.ops.governance_audit import append_governance_log, run_governance_audit

        append_governance_log(run_governance_audit())

    report.notified = notified_codes
    logger.info("Patrulha: %s | notificados: %s", summary, notified_codes)
    return report


def _append_patrol_log(report: PatrolReport) -> None:
    PATROL_LOG.parent.mkdir(parents=True, exist_ok=True)
    if not PATROL_LOG.is_file():
        PATROL_LOG.write_text(
            "# Patrulha operacional — Ronaldo\n\n"
            "Checks periódicos automáticos.\n\n---\n\n",
            encoding="utf-8",
        )
    lines = [
        f"### {report.generated_at}",
        f"- **Resumo:** {report.summary}",
    ]
    if report.notified:
        lines.append(f"- **WhatsApp Vitor:** {', '.join(report.notified)}")
    for issue in report.issues[:8]:
        flag = "🔴" if issue.notify else "🟡"
        lines.append(f"- {flag} [{issue.severity}] {issue.title} ({issue.ref})")
    lines.append("")
    text = PATROL_LOG.read_text(encoding="utf-8")
    marker = "---\n\n"
    if marker in text:
        head, tail = text.split(marker, 1)
        PATROL_LOG.write_text(head + marker + "\n".join(lines) + tail, encoding="utf-8")
    else:
        PATROL_LOG.write_text(text + "\n".join(lines), encoding="utf-8")
