#!/usr/bin/env python3
"""
Atualiza snapshot automático em dashboard/metricas_operacionais.md.

Fontes: tasks/*.md (kanban), crm/crm_*.md (segmentado), memoria/hipoteses_testadas.md
Sem dependências externas. Markdown-first.
"""
from __future__ import annotations

import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CRM_DIR = ROOT / "crm"
DASHBOARD = ROOT / "dashboard" / "metricas_operacionais.md"
MARKER_START = "<!-- AUTO-SNAPSHOT:START -->"
MARKER_END = "<!-- AUTO-SNAPSHOT:END -->"

CRM_SEGMENT_FILES = [
    "crm_laboratorio.md",
    "crm_landing_pintor.md",
    "crm_appvs.md",
]


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def normalize_crm_status(raw: str) -> str:
    s = raw.lower().strip().strip("`")
    s = re.sub(r"\*+", "", s)
    m = re.match(r"([a-z_]+)", s)
    return m.group(1) if m else (s.split()[0] if s else "")


def count_kanban_tasks(path: Path, section: str) -> list[str]:
    content = read_text(path)
    if not content:
        return []
    pattern = rf"{re.escape(section)}\s*\n(.*?)(?=\n## |\Z)"
    blocks = re.findall(pattern, content, re.DOTALL)
    block = "\n".join(blocks) if blocks else content
    seen: set[str] = set()
    ids: list[str] = []
    for tid in re.findall(r"^### ([A-Z][A-Z0-9\-]*-\d+)", block, re.MULTILINE):
        if tid not in seen:
            seen.add(tid)
            ids.append(tid)
    return ids


def parse_task_file(path: Path) -> dict:
    content = read_text(path)
    task_id = path.stem
    status_match = re.search(r"\*\*Status:\*\*\s*`([^`]+)`", content)
    if not status_match:
        status_match = re.search(r"\|\s*\*\*Status\*\*\s*\|\s*([^\|]+)", content)
    status = status_match.group(1).strip().split()[0] if status_match else "desconhecido"

    entregaveis_done = 0
    entregaveis_total = 0
    for line in content.splitlines():
        if re.match(r"\| E\d+ \|", line):
            entregaveis_total += 1
            if "✅" in line:
                entregaveis_done += 1

    progress = (
        f"{round(100 * entregaveis_done / entregaveis_total)}%"
        if entregaveis_total
        else "—"
    )
    return {
        "id": task_id,
        "status": status,
        "entregaveis_done": entregaveis_done,
        "entregaveis_total": entregaveis_total,
        "progress": progress,
    }


def parse_crm_meta(content: str) -> dict:
    m = re.search(r"<!--\s*crm-meta\s*(.*?)-->", content, re.DOTALL)
    meta: dict = {"funil": []}
    if not m:
        return meta
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip()
        if key == "funil":
            meta["funil"] = [s.strip() for s in val.split(",") if s.strip()]
        elif key:
            meta[key] = val
    return meta


def parse_leads_index(content: str) -> list[dict]:
    leads: list[dict] = []
    headers: list[str] = []
    in_index = False
    for line in content.splitlines():
        if line.startswith("| ID |"):
            headers = [h.strip().lower() for h in line.strip("|").split("|")]
            in_index = True
            continue
        if in_index:
            if not line.startswith("|"):
                break
            if re.match(r"\|\s*[_—\-]", line) or "nenhum lead" in line.lower():
                continue
            cols = [c.strip() for c in line.strip("|").split("|")]
            if not cols or not re.match(r"LEAD-", cols[0]):
                continue
            status_idx = headers.index("status") if "status" in headers else min(5, len(cols) - 1)
            status = normalize_crm_status(cols[status_idx] if status_idx < len(cols) else "")
            leads.append(
                {
                    "id": cols[0],
                    "nome": cols[1] if len(cols) > 1 else "—",
                    "score": cols[2] if len(cols) > 2 else "—",
                    "status": status,
                    "captura": cols[-1] if len(cols) > 1 else "—",
                }
            )
    return leads


def parse_crm_leads(content: str) -> list[dict]:
    leads: list[dict] = []
    for m in re.finditer(r"^## (LEAD-[\w-]+) — (.+?)$", content, re.MULTILINE):
        lead_id = m.group(1)
        nome = m.group(2).strip()
        start = m.end()
        next_h = re.search(r"^## ", content[start:], re.MULTILINE)
        block = content[start : start + next_h.start()] if next_h else content[start:]

        def fld(key: str) -> str:
            fm = re.search(rf"\|\s*\*\*{re.escape(key)}\*\*\s*\|\s*(.+?)\s*\|", block)
            return fm.group(1).strip() if fm else ""

        raw_status = fld("Status") or "novo"
        status = normalize_crm_status(raw_status)
        leads.append(
            {
                "id": lead_id,
                "nome": fld("Nome") or nome,
                "score": fld("Score") or "—",
                "status": status,
                "captura": fld("Data captura") or "—",
                "cidade": fld("Cidade") or "—",
            }
        )
    if leads:
        return leads
    return parse_leads_index(content)


def parse_crm_segment(path: Path) -> dict | None:
    content = read_text(path)
    if not content:
        return None
    meta = parse_crm_meta(content)
    leads = parse_crm_leads(content)
    funnel = meta.get("funil") or []
    counts = {stage: 0 for stage in funnel}
    for lead in leads:
        st = lead.get("status") or ""
        if st in counts:
            counts[st] += 1
    return {
        "file": path.name,
        "segment": meta.get("segmento", path.stem),
        "name": meta.get("nome", path.stem),
        "funnel": funnel,
        "funnel_counts": counts,
        "leads": leads,
        "total": len(leads),
    }


def load_crm_segments() -> list[dict]:
    segments: list[dict] = []
    for fname in CRM_SEGMENT_FILES:
        seg = parse_crm_segment(CRM_DIR / fname)
        if seg:
            segments.append(seg)
    return segments


def count_hypotheses_testing(path: Path) -> int:
    content = read_text(path)
    return len(re.findall(r"\*\*Status:\*\*\s*`?a_testar`?", content))


def _crm_funnel_table(seg: dict) -> str:
    rows = []
    for stage in seg["funnel"]:
        rows.append(f"| `{stage}` | {seg['funnel_counts'].get(stage, 0)} |")
    rows.append(f"| **Total** | **{seg['total']}** |")
    return "\n".join(rows)


def build_snapshot() -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    tasks_dir = ROOT / "tasks"
    task_files = sorted(tasks_dir.glob("*.md"))
    task_files = [
        p
        for p in task_files
        if p.stem not in ("backlog", "executando", "planejando", "concluidas", "aguardando", "arquivado")
        and re.match(r"^[A-Z][A-Z0-9\-]*-\d+$", p.stem)
    ]
    tasks = [parse_task_file(p) for p in task_files]

    executando = count_kanban_tasks(tasks_dir / "executando.md", "## Em andamento")
    planejando = count_kanban_tasks(tasks_dir / "planejando.md", "## Em planejamento")
    aguardando = count_kanban_tasks(tasks_dir / "aguardando.md", "## Bloqueadas")
    backlog = count_kanban_tasks(tasks_dir / "backlog.md", "## Fila")
    concluidas = count_kanban_tasks(tasks_dir / "concluidas.md", "## Concluídas")
    arquivado = count_kanban_tasks(tasks_dir / "arquivado.md", "## Arquivo")

    wip = len(executando)
    cadence_min = int(os.getenv("TASK_CADENCE_MIN", "10"))
    planning = len(planejando)

    active_tasks = [t for t in tasks if t["status"] == "executando"]
    ent_done = sum(t["entregaveis_done"] for t in active_tasks)
    ent_total = sum(t["entregaveis_total"] for t in active_tasks)

    crm_segments = load_crm_segments()
    total_leads = sum(s["total"] for s in crm_segments)

    lp_seg = next((s for s in crm_segments if s["segment"] == "crm_landing_pintor"), None)
    lp_ativos = lp_seg["funnel_counts"].get("ativo", 0) if lp_seg else 0
    lp_abordados = lp_seg["funnel_counts"].get("abordado", 0) if lp_seg else 0
    lp_previas = lp_seg["funnel_counts"].get("previa_no_ar", 0) if lp_seg else 0
    lp_taxa_ativacao = (
        f"{round(100 * lp_ativos / max(lp_previas + lp_abordados + lp_ativos, 1))}%"
        if lp_seg and lp_seg["total"]
        else "—"
    )

    hyp_testing = count_hypotheses_testing(ROOT / "memoria" / "hipoteses_testadas.md")

    task_rows = "\n".join(
        f"| [{t['id']}](../tasks/{t['id']}.md) | `{t['status']}` | "
        f"{t['entregaveis_done']}/{t['entregaveis_total']} | {t['progress']} |"
        for t in tasks
    )

    all_leads: list[dict] = []
    for seg in crm_segments:
        for lead in seg["leads"]:
            all_leads.append({**lead, "crm": seg["name"]})
    lead_rows = "\n".join(
        f"| {l['id']} | {l.get('crm', '—')} | {l['nome']} | `{l['status']}` | {l.get('captura', '—')} |"
        for l in all_leads[:15]
    ) or "| _—_ | _—_ | _nenhum lead_ | — | — |"

    crm_sections = []
    for seg in crm_segments:
        crm_sections.append(
            f"#### {seg['name']} (`{seg['file']}`)\n\n"
            f"| Etapa | Qtd |\n|-------|-----|\n{_crm_funnel_table(seg)}"
        )
    crm_block = "\n\n".join(crm_sections) if crm_sections else "_Nenhum CRM segmentado encontrado._"

    return f"""{MARKER_START}
> **Snapshot automático** · gerado em **{now}** · script `scripts/update_dashboard_snapshot.py`  
> **CRM:** segmentado (`crm/crm_*.md`) — alinhado ao Painel Maestro

### Resumo

| Indicador | Valor |
|-----------|-------|
| TASKs em execução | {wip} (cadência {cadence_min}min entre starts) |
| TASKs em planejamento | {planning} |
| Entregáveis (tasks `executando`) | {ent_done} / {ent_total} |
| **Total leads (todos CRMs)** | **{total_leads}** |
| KPI LP — ativos | {lp_ativos} |
| KPI LP — taxa ativação | {lp_taxa_ativacao} |
| Hipóteses `a_testar` | {hyp_testing} |

### Pipeline Kanban

| Status | Qtd | Tasks |
|--------|-----|-------|
| `executando` | {len(executando)} | {", ".join(executando) or "—"} |
| `planejando` | {len(planejando)} | {", ".join(planejando) or "—"} |
| `aguardando` | {len(aguardando)} | {", ".join(aguardando) or "—"} |
| `backlog` | {len(backlog)} | {", ".join(backlog) or "—"} |
| `concluído` (kanban) | {len(concluidas)} | {", ".join(concluidas) or "—"} |
| `arquivado` (canceladas) | {len(arquivado)} | {", ".join(arquivado) or "—"} |

### Tasks (arquivos persistentes)

| Task | Status | Entregáveis | Progresso |
|------|--------|-------------|-----------|
{task_rows}

### CRM segmentado

{crm_block}

### Leads (todos os CRMs)

| ID | CRM | Nome | Status | Captura |
|----|-----|------|--------|---------|
{lead_rows}

{MARKER_END}"""


def update_dashboard(content: str, snapshot: str) -> str:
    pattern = re.compile(
        re.escape(MARKER_START) + r".*?" + re.escape(MARKER_END),
        re.DOTALL,
    )
    if pattern.search(content):
        return pattern.sub(snapshot, content)

    insert_after = "**Última atualização:**"
    lines = content.splitlines()
    for i, line in enumerate(lines):
        if line.startswith(insert_after):
            return "\n".join(lines[: i + 1]) + "\n\n---\n\n## 0. Snapshot automático\n\n" + snapshot + "\n" + "\n".join(lines[i + 1 :])
    return content + "\n\n## 0. Snapshot automático\n\n" + snapshot + "\n"


def main() -> int:
    if not DASHBOARD.exists():
        print(f"Dashboard não encontrado: {DASHBOARD}", file=sys.stderr)
        return 1

    snapshot = build_snapshot()
    content = read_text(DASHBOARD)
    updated = update_dashboard(content, snapshot)

    auto_ts = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    updated = re.sub(
        r"\*\*Última atualização automática:\*\*.*",
        f"**Última atualização automática:** {auto_ts} (script local / GitHub Actions)",
        updated,
    )
    if "**Última atualização automática:**" not in updated:
        updated = updated.replace(
            f"**Última atualização:** {auto_ts}",
            f"**Última atualização:** {auto_ts}\n**Última atualização automática:** {auto_ts} (script local / GitHub Actions)",
            1,
        )

    if updated == content:
        print("Snapshot já está atualizado.")
        return 0

    DASHBOARD.write_text(updated, encoding="utf-8")
    print(f"Snapshot atualizado em {DASHBOARD}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
