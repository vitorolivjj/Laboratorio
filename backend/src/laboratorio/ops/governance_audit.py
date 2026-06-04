"""Auditoria de governança — kanban, hierarquia, protocolo Ronaldo.

Valida alinhamento entre arquivos Kanban, task files, contexto global e
estado de auditoria pós-conclusão. Usado pela patrulha e CLI `governanca-audit`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from laboratorio.config import CONTEXTO_GLOBAL, MEMORIA_DIR, TASKS_DIR
from laboratorio.ops import parsers
from laboratorio.ops.donizete_capture_task import load_capture_config

LOGS_DIR = TASKS_DIR.parent / "logs"
AUDIT_STATE = LOGS_DIR / "ronaldo_audit_state.json"
GOVERNANCE_LOG = LOGS_DIR / "governanca_auditoria.md"

KANBAN_FILES: dict[str, tuple[str, str]] = {
    "executando": ("executando.md", "## Em andamento"),
    "planejando": ("planejando.md", "## Em planejamento"),
    "aguardando": ("aguardando.md", "## Bloqueadas"),
    "backlog": ("backlog.md", "## Fila"),
    "concluidas": ("concluidas.md", "## Concluídas"),
}

STATUS_TO_COLUMN = {
    "executando": "executando",
    "planejando": "planejando",
    "aguardando": "aguardando",
    "backlog": "backlog",
    "concluido": "concluidas",
    "concluído": "concluidas",
}

TASK_ID_RE = re.compile(r"^[A-Z][A-Z0-9\-]*-\d+$")
SKIP_FILES = frozenset(
    {"backlog", "executando", "planejando", "concluidas", "aguardando", "arquivado"}
)


@dataclass
class GovernanceFinding:
    code: str
    severity: str  # ok | info | warn | critical
    title: str
    detail: str
    ref: str = ""
    action: str = ""


@dataclass
class GovernanceReport:
    generated_at: str
    findings: list[GovernanceFinding] = field(default_factory=list)
    summary: str = ""
    ok: bool = True

    def add(self, finding: GovernanceFinding) -> None:
        self.findings.append(finding)
        if finding.severity in ("warn", "critical"):
            self.ok = False


def _kanban_map(tasks_dir: Path) -> dict[str, str]:
    """task_id → coluna kanban."""
    loc: dict[str, str] = {}
    for col, (fname, section) in KANBAN_FILES.items():
        ids = parsers.parsers_count(tasks_dir / fname, section)
        for tid in ids:
            if tid in loc:
                loc[tid] = f"{loc[tid]}+{col}"
            else:
                loc[tid] = col
    return loc


def _task_file_status(path: Path) -> str | None:
    content = parsers.read_text(path)
    m = re.search(r"\|\s*\*\*Status\*\*\s*\|\s*([^\|]+)", content)
    if m:
        return m.group(1).strip().split()[0]
    m2 = re.search(r"\*\*Status:\*\*\s*`([^`]+)`", content)
    if m2:
        return m2.group(1).strip().split()[0]
    return None


def _load_audited_ids() -> set[str]:
    import json

    if not AUDIT_STATE.is_file():
        return set()
    try:
        data = json.loads(AUDIT_STATE.read_text(encoding="utf-8"))
        return set(data.get("audited") or [])
    except (OSError, json.JSONDecodeError):
        return set()


def _contexto_p0(context_path: Path) -> str | None:
    content = parsers.read_text(context_path)
    m = re.search(r"\*\*LP-PINTOR-(\d+)\*\*", content)
    if m:
        return f"LP-PINTOR-{m.group(1)}"
    return None


def run_governance_audit(*, tasks_dir: Path | None = None) -> GovernanceReport:
    tasks_dir = tasks_dir or TASKS_DIR
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    report = GovernanceReport(generated_at=now)
    kanban = _kanban_map(tasks_dir)
    audited = _load_audited_ids()

    # Duplicatas no kanban
    for tid, col in kanban.items():
        if "+" in col:
            report.add(
                GovernanceFinding(
                    code="kanban_duplicado",
                    severity="critical",
                    title=f"{tid} em múltiplas colunas",
                    detail=f"Colunas: {col}",
                    ref=f"tasks/{tid}.md",
                    action="Manter task em uma única coluna kanban",
                )
            )

    # Drift task file ↔ kanban
    for path in sorted(tasks_dir.glob("*.md")):
        if path.stem in SKIP_FILES or not TASK_ID_RE.match(path.stem):
            continue
        st = _task_file_status(path)
        if not st:
            continue
        kid = path.stem
        loc = kanban.get(kid)
        expected = STATUS_TO_COLUMN.get(st)
        if expected and loc != expected:
            report.add(
                GovernanceFinding(
                    code="kanban_drift",
                    severity="warn",
                    title=f"{kid} desalinhado",
                    detail=f"Arquivo status={st} · kanban={loc or 'fora'}",
                    ref=str(path.relative_to(tasks_dir.parent)),
                    action=f"Mover para tasks/{expected}.md ou corrigir status no arquivo",
                )
            )

    # Briefing em executando
    exec_ids = parsers.parsers_count(tasks_dir / "executando.md", "## Em andamento")
    for tid in exec_ids:
        task_path = tasks_dir / f"{tid}.md"
        if not task_path.is_file():
            report.add(
                GovernanceFinding(
                    code="sem_task_file",
                    severity="warn",
                    title=f"{tid} sem arquivo dedicado",
                    detail="Kanban referencia task sem tasks/<ID>.md",
                    ref=f"tasks/executando.md",
                    action="Criar tasks/<ID>.md",
                )
            )
            continue
        content = parsers.read_text(task_path)
        if "Briefing" not in content:
            report.add(
                GovernanceFinding(
                    code="sem_briefing",
                    severity="warn",
                    title=f"{tid} em executando sem briefing",
                    detail="Protocolo Ronaldo — gate antes de executar",
                    ref=f"tasks/{tid}.md",
                    action="Emitir ### Briefing por agente",
                )
            )

    # Concluídas sem auditoria registrada
    conc_ids = parsers.parsers_count(tasks_dir / "concluidas.md", "## Concluídas")
    missing_audit = [tid for tid in conc_ids if tid not in audited]
    if missing_audit:
        report.add(
            GovernanceFinding(
                code="audit_pendente",
                severity="warn",
                title=f"{len(missing_audit)} concluída(s) sem auditoria Ronaldo",
                detail=", ".join(missing_audit[:12]) + ("…" if len(missing_audit) > 12 else ""),
                ref="logs/ronaldo_audit_state.json",
                action="Rodar `./run.sh ronaldo-audit` ou backfill manual",
            )
        )

    # IDs duplicados em concluidas
    seen: set[str] = set()
    dups: list[str] = []
    for tid in conc_ids:
        if tid in seen:
            dups.append(tid)
        seen.add(tid)
    if dups:
        report.add(
            GovernanceFinding(
                code="id_duplicado_concluidas",
                severity="warn",
                title="IDs repetidos em concluidas.md",
                detail=", ".join(sorted(set(dups))),
                ref="tasks/concluidas.md",
                action="Renumerar ou arquivar entrada duplicada",
            )
        )

    # Contexto P0 vs executando
    p0 = _contexto_p0(CONTEXTO_GLOBAL)
    if p0 and exec_ids and p0 not in exec_ids:
        report.add(
            GovernanceFinding(
                code="contexto_desalinhado",
                severity="warn",
                title="P0 do contexto_global ≠ executando",
                detail=f"contexto P0={p0} · executando={', '.join(exec_ids)}",
                ref="contexto/contexto_global.md",
                action="Alinhar foco ou kanban",
            )
        )
    elif p0 and exec_ids and p0 in exec_ids:
        report.add(
            GovernanceFinding(
                code="contexto_ok",
                severity="ok",
                title="P0 alinhado com executando",
                detail=p0,
                ref="contexto/contexto_global.md",
            )
        )

    # TASK-001 histórica usada como captura (pós-reset: só LP-PINTOR-*)
    for path in sorted(tasks_dir.glob("TASK-*.md")):
        doc = parsers.read_text(path)
        if re.search(r"## Captura intermitente|grupo_fixo|Grupo Facebook", doc, re.I):
            report.add(
                GovernanceFinding(
                    code="captura_task_prefixo_antigo",
                    severity="warn",
                    title=f"{path.stem} usa prefixo TASK para captura",
                    detail="Capturas novas devem ser LP-PINTOR-XXX com grupo fixo",
                    ref=str(path.relative_to(tasks_dir.parent)),
                    action="Migrar para LP-PINTOR ou remover seção captura de TASK-*",
                )
            )

    # LP-PINTOR sem grupo fixo na seção captura
    for path in sorted(tasks_dir.glob("LP-PINTOR-*.md")):
        cfg = load_capture_config(path.stem, tasks_dir=tasks_dir)
        kid = path.stem
        in_kanban = kid in kanban
        if in_kanban and cfg and not cfg.get("group_url"):
            report.add(
                GovernanceFinding(
                    code="captura_sem_grupo",
                    severity="warn",
                    title=f"{kid} no kanban sem URL de grupo",
                    detail="PlayDonizete exige grupo fixo em ## Captura intermitente",
                    ref=f"tasks/{kid}.md",
                    action="Preencher | **Grupo Facebook** | ou Criar captura <url>",
                )
            )

    # memoria/donizete_social — referências a tasks fora do kanban
    mem_refs: set[str] = set(kanban.keys())
    donizete_mem = MEMORIA_DIR / "donizete_social"
    orphan_count = 0
    if donizete_mem.is_dir():
        for mp in donizete_mem.glob("*.md"):
            text = parsers.read_text(mp)
            for tid in re.findall(r"\bLP-PINTOR-\d{3}[A-Z]?\b", text):
                if tid in mem_refs or orphan_count >= 5:
                    continue
                orphan_count += 1
                report.add(
                    GovernanceFinding(
                        code="memoria_task_orfa",
                        severity="info",
                        title=f"{tid} em doc Donizete sem kanban ativo",
                        detail=str(mp.relative_to(MEMORIA_DIR.parent)),
                        ref=str(mp.relative_to(MEMORIA_DIR.parent)),
                        action="Alinhar doc ao fluxo grupo fixo ou recriar task",
                    )
                )

    # decisoes.md — entradas sem data no título
    decisoes_path = MEMORIA_DIR / "decisoes.md"
    dec_text = parsers.read_text(decisoes_path)
    dec_section = dec_text.split("## Decisões", 1)[-1] if "## Decisões" in dec_text else dec_text
    for m in re.finditer(r"^### (.+)$", dec_section, re.MULTILINE):
        title = m.group(1).strip()
        if title.startswith("[") or not re.search(r"\d{4}-\d{2}-\d{2}", title):
            report.add(
                GovernanceFinding(
                    code="decisao_sem_data",
                    severity="info",
                    title="Decisão sem data no título",
                    detail=title[:80],
                    ref="memoria/decisoes.md",
                    action="Padronizar: ### Título — YYYY-MM-DD",
                )
            )

    # Seções duplicadas em backlog (bug histórico)
    backlog_text = parsers.read_text(tasks_dir / "backlog.md")
    fila_count = len(re.findall(r"^## Fila\s*$", backlog_text, re.MULTILINE))
    if fila_count > 1:
        report.add(
            GovernanceFinding(
                code="backlog_secoes_duplicadas",
                severity="warn",
                title="backlog.md com múltiplas seções ## Fila",
                detail=f"{fila_count} ocorrências — parser pode ignorar tasks",
                ref="tasks/backlog.md",
                action="Unificar em uma única seção ## Fila",
            )
        )

    warns = sum(1 for f in report.findings if f.severity == "warn")
    crits = sum(1 for f in report.findings if f.severity == "critical")
    oks = sum(1 for f in report.findings if f.severity == "ok")
    report.summary = (
        f"Governança {'OK' if report.ok else 'com gaps'} · "
        f"{oks} ok · {warns} warn · {crits} critical · "
        f"executando={len(exec_ids)} · kanban={len(kanban)}"
    )
    return report


def append_governance_log(report: GovernanceReport) -> None:
    GOVERNANCE_LOG.parent.mkdir(parents=True, exist_ok=True)
    if not GOVERNANCE_LOG.is_file():
        GOVERNANCE_LOG.write_text(
            "# Governança — auditorias periódicas\n\n"
            "Kanban · hierarquia · protocolo Ronaldo.\n\n---\n\n",
            encoding="utf-8",
        )
    lines = [f"### {report.generated_at}", f"- **Resumo:** {report.summary}"]
    for f in report.findings:
        if f.severity == "ok":
            continue
        icon = "🔴" if f.severity == "critical" else "🟡"
        lines.append(f"- {icon} [{f.code}] {f.title} — {f.detail[:120]}")
    if report.ok:
        lines.append("- ✅ Nenhum gap crítico ou warn")
    lines.append("")
    text = GOVERNANCE_LOG.read_text(encoding="utf-8")
    marker = "---\n\n"
    if marker in text:
        head, tail = text.split(marker, 1)
        GOVERNANCE_LOG.write_text(head + marker + "\n".join(lines) + tail, encoding="utf-8")
    else:
        GOVERNANCE_LOG.write_text(text + "\n".join(lines), encoding="utf-8")
