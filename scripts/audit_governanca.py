#!/usr/bin/env python3
"""Auditoria de governança (stdlib) — kanban, protocolo, hierarquia."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TASKS = ROOT / "tasks"
LOGS = ROOT / "logs"
CONTEXT = ROOT / "contexto" / "contexto_global.md"
AUDIT_STATE = LOGS / "ronaldo_audit_state.json"
GOV_LOG = LOGS / "governanca_auditoria.md"

KANBAN = {
    "executando": ("executando.md", "## Em andamento"),
    "planejando": ("planejando.md", "## Em planejamento"),
    "aguardando": ("aguardando.md", "## Bloqueadas"),
    "backlog": ("backlog.md", "## Fila"),
    "concluidas": ("concluidas.md", "## Concluídas"),
}
STATUS_MAP = {
    "executando": "executando",
    "planejando": "planejando",
    "aguardando": "aguardando",
    "backlog": "backlog",
    "concluido": "concluidas",
    "concluído": "concluidas",
}
SKIP = {"backlog", "executando", "planejando", "concluidas", "aguardando", "arquivado"}
TID = re.compile(r"^[A-Z][A-Z0-9\-]*-\d+$")


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8") if p.is_file() else ""


def kanban_ids(path: Path, section: str) -> list[str]:
    content = read(path)
    blocks = re.findall(rf"{re.escape(section)}\s*\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
    block = "\n".join(blocks) if blocks else content
    seen: set[str] = set()
    out: list[str] = []
    for tid in re.findall(r"^### ([A-Z][A-Z0-9\-]*-\d+)", block, re.MULTILINE):
        if tid not in seen:
            seen.add(tid)
            out.append(tid)
    return out


def build_kanban_map() -> dict[str, str]:
    loc: dict[str, str] = {}
    for col, (fname, sec) in KANBAN.items():
        for tid in kanban_ids(TASKS / fname, sec):
            if tid in loc:
                loc[tid] = f"{loc[tid]}+{col}"
            else:
                loc[tid] = col
    return loc


def task_status(path: Path) -> str | None:
    m = re.search(r"\|\s*\*\*Status\*\*\s*\|\s*([^\|]+)", read(path))
    return m.group(1).strip().split()[0] if m else None


def audited_ids() -> set[str]:
    if not AUDIT_STATE.is_file():
        return set()
    return set(json.loads(read(AUDIT_STATE)).get("audited") or [])


def main() -> int:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    kanban = build_kanban_map()
    findings: list[tuple[str, str, str]] = []

    for tid, col in kanban.items():
        if "+" in col:
            findings.append(("critical", "kanban_duplicado", f"{tid} → {col}"))

    for p in sorted(TASKS.glob("*.md")):
        if p.stem in SKIP or not TID.match(p.stem):
            continue
        st = task_status(p)
        if not st:
            continue
        exp = STATUS_MAP.get(st)
        loc = kanban.get(p.stem)
        if exp and loc != exp:
            findings.append(("warn", "kanban_drift", f"{p.stem} file={st} kanban={loc or 'fora'}"))

    exec_ids = kanban_ids(TASKS / "executando.md", "## Em andamento")
    for tid in exec_ids:
        tp = TASKS / f"{tid}.md"
        if tp.is_file() and "Briefing" not in read(tp):
            findings.append(("warn", "sem_briefing", tid))

    conc = kanban_ids(TASKS / "concluidas.md", "## Concluídas")
    missing = [t for t in conc if t not in audited_ids()]
    if missing:
        findings.append(("warn", "audit_pendente", ", ".join(missing)))

    seen: set[str] = set()
    dups = [t for t in conc if t in seen or seen.add(t)]  # type: ignore
    if dups:
        findings.append(("warn", "id_duplicado", ", ".join(sorted(set(dups)))))

    p0 = re.search(r"\*\*LP-PINTOR-(\d+)\*\*", read(CONTEXT))
    if p0 and exec_ids and f"LP-PINTOR-{p0.group(1)}" not in exec_ids:
        findings.append(("warn", "contexto_p0", f"P0 LP-PINTOR-{p0.group(1)} vs exec {exec_ids}"))

    ok = not any(s in ("warn", "critical") for s, _, _ in findings)
    summary = f"{'OK' if ok else 'GAPS'} · exec={exec_ids} · findings={len(findings)}"
    print(f"Governança {now}\n{summary}\n")
    for sev, code, detail in findings:
        print(f"  {'🔴' if sev == 'critical' else '🟡'} [{code}] {detail}")
    if ok:
        print("  ✅ Kanban · briefings · contexto alinhados")

    if "--log" in sys.argv:
        GOV_LOG.parent.mkdir(parents=True, exist_ok=True)
        if not GOV_LOG.is_file():
            GOV_LOG.write_text("# Governança\n\n---\n\n", encoding="utf-8")
        block = f"### {now}\n- **Resumo:** {summary}\n"
        for sev, code, detail in findings:
            block += f"- 🟡 [{code}] {detail}\n"
        if ok:
            block += "- ✅ Sem gaps\n"
        block += "\n"
        t = read(GOV_LOG)
        marker = "---\n\n"
        if marker in t:
            h, tail = t.split(marker, 1)
            GOV_LOG.write_text(h + marker + block + tail, encoding="utf-8")
        else:
            GOV_LOG.write_text(t + block, encoding="utf-8")
        print(f"\nLog: {GOV_LOG}")

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
