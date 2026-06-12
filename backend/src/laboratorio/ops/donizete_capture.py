"""Monitoramento da captação Donizete — PROJ-LP / LP-PINTOR-001."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from laboratorio.config import (
    CAPTURE_BEHIND_CRITICAL_HOURS,
    CAPTURE_ZERO_CRITICAL_MINUTES,
    CAPTURE_ZERO_WARN_MINUTES,
    LOGS_DIR,
    REPO_ROOT,
    TASKS_DIR,
)
from laboratorio.ops import parsers

CAPTURE_LOG = LOGS_DIR / "donizete_captura.md"
CAPTURE_STATE = LOGS_DIR / "donizete_captura_state.json"
CRM_LP = REPO_ROOT / "crm" / "crm_landing_pintor.md"
LEADS_ROOT = REPO_ROOT / "frontend" / "lp-pintor" / "leads"
TASK_IDS_CAPTURE = ("LP-PINTOR-001", "LP-PINTOR-001B")
META_DEFAULT = 10

EXCLUDE_SLUGS = frozenset({"exemplo", "_template", "stephanie-turnley"})
FUNIL_CAPTURE = ("prospectado", "pronto_pra_pagina", "previa_no_ar", "abordado")


@dataclass
class CaptureLeadFolder:
    slug: str
    raw_images: int = 0
    has_manifest: bool = False
    has_config: bool = False


@dataclass
class DonizeteCaptureReport:
    generated_at: str
    meta_goal: int
    crm_counts: dict[str, int] = field(default_factory=dict)
    pronto_count: int = 0
    prospectado_count: int = 0
    folders: list[CaptureLeadFolder] = field(default_factory=list)
    crm_leads_capture: list[dict[str, Any]] = field(default_factory=list)
    task_in_executando: bool = False
    minutes_since_task_start: float | None = None
    hours_since_task_start: float | None = None
    issues: list[dict[str, str]] = field(default_factory=list)

    @property
    def progress_pct(self) -> int:
        if self.meta_goal <= 0:
            return 0
        return min(100, round(100 * self.pronto_count / self.meta_goal))

    def has_any_progress(self) -> bool:
        return self.pronto_count > 0 or self.prospectado_count > 0 or len(self.folders) > 0

    def summary_line(self) -> str:
        return (
            f"Captação LP: {self.pronto_count}/{self.meta_goal} pronto_pra_pagina "
            f"({self.progress_pct}%) · prospectados {self.prospectado_count} · "
            f"pastas captura {len(self.folders)}"
        )


def _meta_goal() -> int:
    try:
        return max(1, int(os.getenv("DONIZETE_CAPTURE_META", str(META_DEFAULT))))
    except ValueError:
        return META_DEFAULT


def _scan_lead_folders() -> list[CaptureLeadFolder]:
    if not LEADS_ROOT.is_dir():
        return []
    out: list[CaptureLeadFolder] = []
    for path in sorted(LEADS_ROOT.iterdir()):
        if not path.is_dir() or path.name in EXCLUDE_SLUGS or path.name.startswith("."):
            continue
        raw_dir = path / "captura" / "raw"
        raw_n = 0
        if raw_dir.is_dir():
            raw_n = sum(
                1
                for f in raw_dir.iterdir()
                if f.is_file() and f.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp", ".gif")
            )
        out.append(
            CaptureLeadFolder(
                slug=path.name,
                raw_images=raw_n,
                has_manifest=(path / "captura" / "manifest.json").is_file(),
                has_config=(path / "config.json").is_file(),
            )
        )
    return out


def _load_crm_lp() -> dict[str, Any]:
    if not CRM_LP.is_file():
        return {"leads": [], "funnel_counts": {}}
    return parsers.parse_crm_segment(parsers.read_text(CRM_LP))


def _is_donizete_capture_lead(lead: dict) -> bool:
    if lead.get("id") == "LEAD-001":
        return False
    orig = (lead.get("origem") or "").lower()
    resp = (lead.get("responsavel") or "").lower()
    if "manual_vitrine" in orig or "vitrine" in orig:
        return False
    if "donizete" in resp:
        return True
    if any(t in orig for t in ("indicacao", "autopromocao", "autopromoção")):
        return True
    etapa = parsers.normalize_crm_status(lead.get("etapa") or lead.get("status") or "")
    return etapa in FUNIL_CAPTURE


def _task_start_elapsed() -> tuple[float | None, float | None]:
    """Retorna (minutos, horas) desde o start da captação em task_cadence_state."""
    state_path = LOGS_DIR / "task_cadence_state.json"
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None, None
    starts = state.get("starts", {})
    earliest: datetime | None = None
    for tid in TASK_IDS_CAPTURE:
        iso = starts.get(tid)
        if not iso:
            continue
        try:
            dt = datetime.fromisoformat(iso)
        except ValueError:
            continue
        if earliest is None or dt < earliest:
            earliest = dt
    if earliest is None:
        return None, None
    secs = (datetime.now(timezone.utc) - earliest).total_seconds()
    return round(secs / 60, 1), round(secs / 3600, 1)


def _capture_task_active() -> bool:
    exec_ids = parsers.parsers_count(TASKS_DIR / "executando.md", "## Em andamento")
    return any(tid in exec_ids for tid in TASK_IDS_CAPTURE)


def build_capture_report() -> DonizeteCaptureReport:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    meta = _meta_goal()
    crm = _load_crm_lp()
    capture_leads = [l for l in crm.get("leads") or [] if _is_donizete_capture_lead(l)]

    pronto_capture = sum(
        1
        for l in capture_leads
        if parsers.normalize_crm_status(l.get("etapa") or "") == "pronto_pra_pagina"
    )
    prospectado = sum(
        1
        for l in capture_leads
        if parsers.normalize_crm_status(l.get("etapa") or "") == "prospectado"
    )

    folders = _scan_lead_folders()
    minutes, hours = _task_start_elapsed()
    in_exec = _capture_task_active()
    issues: list[dict[str, str]] = []

    report_stub = DonizeteCaptureReport(
        generated_at=now,
        meta_goal=meta,
        pronto_count=pronto_capture,
        prospectado_count=prospectado,
        folders=folders,
    )

    if in_exec and not report_stub.has_any_progress():
        if minutes is not None and minutes >= CAPTURE_ZERO_CRITICAL_MINUTES:
            issues.append(
                {
                    "severity": "critical",
                    "code": "capture_zero_30m",
                    "title": (
                        f"Captação LP — zero progresso em {CAPTURE_ZERO_CRITICAL_MINUTES}+ min"
                    ),
                    "detail": (
                        f"Sem pronto/prospectado/pasta captura · {minutes:.0f} min · "
                        f"meta {meta} · Donizete: 1º post + grupos"
                    ),
                }
            )
        elif minutes is not None and minutes >= CAPTURE_ZERO_WARN_MINUTES:
            issues.append(
                {
                    "severity": "warn",
                    "code": "capture_zero_15m",
                    "title": f"Captação LP — sem sinal de trabalho ({CAPTURE_ZERO_WARN_MINUTES}+ min)",
                    "detail": (
                        f"{minutes:.0f} min desde start · publicar post-isca e mapear grupos"
                    ),
                }
            )

    if (
        in_exec
        and pronto_capture < meta
        and hours is not None
        and hours >= CAPTURE_BEHIND_CRITICAL_HOURS
    ):
        issues.append(
            {
                "severity": "critical",
                "code": "capture_behind_sprint",
                "title": f"Captação LP atrasada — {pronto_capture}/{meta} após {hours}h",
                "detail": f"Sprint meta {meta} · checkpoint Ronaldo + Donizete",
            }
        )

    incomplete = [f.slug for f in folders if f.raw_images > 0 and not f.has_manifest]
    if incomplete:
        issues.append(
            {
                "severity": "warn",
                "code": "capture_manifest_missing",
                "title": "Captura com mídia sem manifest.json",
                "detail": ", ".join(incomplete[:5]),
            }
        )

    return DonizeteCaptureReport(
        generated_at=now,
        meta_goal=meta,
        crm_counts=dict(crm.get("funnel_counts") or {}),
        pronto_count=pronto_capture,
        prospectado_count=prospectado,
        folders=folders,
        crm_leads_capture=capture_leads,
        task_in_executando=in_exec,
        minutes_since_task_start=minutes,
        hours_since_task_start=hours,
        issues=issues,
    )


def format_capture_whatsapp(report: DonizeteCaptureReport | None = None) -> str:
    r = report or build_capture_report()
    lines = [
        f"Captação Donizete · {r.generated_at}",
        f"Meta: {r.pronto_count}/{r.meta_goal} pronto_pra_pagina ({r.progress_pct}%)",
        f"CRM: prospectado {r.prospectado_count} · pastas {len(r.folders)} com captura/",
    ]
    if r.task_in_executando:
        if r.minutes_since_task_start is not None:
            lines.append(f"Task captação: executando há {r.minutes_since_task_start:.0f} min")
        else:
            lines.append("Task captação: executando")
    else:
        lines.append("Task captação: nenhuma LP-PINTOR-001/001B em executando")

    if r.crm_leads_capture:
        lines.append("\nLeads captação:")
        for lead in r.crm_leads_capture[:8]:
            st = parsers.normalize_crm_status(lead.get("etapa") or lead.get("status") or "?")
            lines.append(f"• {lead.get('id')} {lead.get('nome', '?')[:28]} — {st}")
    elif r.folders:
        lines.append("\nPastas (sem CRM ainda):")
        for f in r.folders[:8]:
            flag = "ok" if f.has_manifest and f.raw_images else "…"
            lines.append(f"• {f.slug} — {f.raw_images} imgs {flag}")
    else:
        lines.append("\nNenhum lead/pasta de captação ainda.")

    if r.issues:
        lines.append("\nAlertas:")
        for i in r.issues[:4]:
            icon = "CRIT" if i["severity"] == "critical" else "warn"
            lines.append(f"[{icon}] {i['title']}")
    return "\n".join(lines)


def format_capture_cli(report: DonizeteCaptureReport | None = None) -> str:
    r = report or build_capture_report()
    lines = [r.summary_line(), f"Gerado: {r.generated_at}", ""]
    if r.minutes_since_task_start is not None:
        lines.append(f"Tempo desde start captação: {r.minutes_since_task_start:.0f} min")
    if r.crm_leads_capture:
        lines.append("CRM (captação):")
        for lead in r.crm_leads_capture:
            st = lead.get("etapa") or lead.get("status")
            lines.append(
                f"  {lead.get('id')} | {lead.get('nome', '?')[:30]} | {st} | {lead.get('cidade', '—')}"
            )
    if r.folders:
        lines.append("\nPastas frontend/lp-pintor/leads/:")
        for f in r.folders:
            parts = []
            if f.raw_images:
                parts.append(f"{f.raw_images} raw")
            if f.has_manifest:
                parts.append("manifest")
            if f.has_config:
                parts.append("config")
            lines.append(f"  {f.slug}: {', '.join(parts) or 'vazia'}")
    if r.issues:
        lines.append("\nIssues:")
        for i in r.issues:
            lines.append(f"  [{i['severity']}] {i['title']} — {i['detail']}")
    return "\n".join(lines)


def capture_patrol_issues() -> list[dict[str, str]]:
    return build_capture_report().issues


def append_capture_log(report: DonizeteCaptureReport) -> None:
    CAPTURE_LOG.parent.mkdir(parents=True, exist_ok=True)
    if not CAPTURE_LOG.is_file():
        CAPTURE_LOG.write_text(
            "# Monitor captura Donizete — PROJ-LP\n\n"
            "Atualizado pela patrulha e pelo CLI `donizete-captura`.\n\n---\n\n",
            encoding="utf-8",
        )
    block = (
        f"### {report.generated_at}\n"
        f"- **Resumo:** {report.summary_line()}\n"
        f"- **Task:** executando={report.task_in_executando}"
    )
    if report.minutes_since_task_start is not None:
        block += f" · {report.minutes_since_task_start:.0f} min"
    block += "\n"
    if report.issues:
        block += "- **Alertas:** " + "; ".join(i["title"] for i in report.issues) + "\n"
    block += "\n"
    text = CAPTURE_LOG.read_text(encoding="utf-8")
    marker = "---\n\n"
    if marker in text:
        head, rest = text.split(marker, 1)
        CAPTURE_LOG.write_text(head + marker + block + rest, encoding="utf-8")
    else:
        CAPTURE_LOG.write_text(text + block, encoding="utf-8")


def record_lead_pronto_event(lead_id: str, slug: str) -> None:
    """Registra marco operacional quando um lead atinge pronto_pra_pagina."""
    from laboratorio.whatsapp.vitor_actions import append_operational_event

    append_operational_event(
        f"Lead {lead_id} pronto_pra_pagina",
        f"slug={slug} · handoff Loide+Dev · task LP-PINTOR-009",
        ref="LP-PINTOR-001",
    )


def maybe_notify_milestones(report: DonizeteCaptureReport, *, dry_run: bool = False) -> list[str]:
    from laboratorio.whatsapp.notify import notify_vitor

    state: dict[str, Any] = {}
    if CAPTURE_STATE.is_file():
        try:
            state = json.loads(CAPTURE_STATE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            state = {}

    notified: list[str] = []
    n = report.pronto_count
    milestones = {1, 3, 5, report.meta_goal}
    last = int(state.get("last_pronto_notified", -1))

    for m in sorted(milestones):
        if n >= m > last:
            ok = notify_vitor(
                f"Captação LP — marco {m}/{report.meta_goal}",
                report.summary_line(),
                action="Conferir CRM e abrir LP-PINTOR-009 produção",
                ref="LP-PINTOR-001",
                dry_run=dry_run,
            )
            if ok:
                notified.append(f"milestone_{m}")
                state["last_pronto_notified"] = m

    if any(i["code"] == "capture_zero_30m" for i in report.issues):
        dedup_key = state.get("zero_30m_notified_at", "")
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
        if dedup_key != stamp[:13]:  # dedup ~1h bucket
            crit = next(i for i in report.issues if i["code"] == "capture_zero_30m")
            ok = notify_vitor(
                crit["title"],
                crit["detail"],
                action="Donizete: 1º post-isca + grupos · Ronaldo checkpoint",
                ref="LP-PINTOR-001",
                dry_run=dry_run,
            )
            if ok:
                notified.append("zero_30m")
                state["zero_30m_notified_at"] = stamp[:13]

    state["last_pronto"] = n
    state["last_check"] = report.generated_at
    if not dry_run:
        CAPTURE_STATE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    return notified
