#!/usr/bin/env python3
"""
Atualiza snapshot automático em dashboard/metricas_operacionais.md.

Fontes: tasks/TASK-*.md, tasks/*.md (kanban), crm/leads.md, memoria/hipoteses_testadas.md
Sem dependências externas. Markdown-first.
"""
from __future__ import annotations

import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DASHBOARD = ROOT / "dashboard" / "metricas_operacionais.md"
MARKER_START = "<!-- AUTO-SNAPSHOT:START -->"
MARKER_END = "<!-- AUTO-SNAPSHOT:END -->"


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def count_kanban_tasks(path: Path, section: str) -> list[str]:
    """Conta ### TASK-XXX dentro de uma seção markdown."""
    content = read_text(path)
    if not content:
        return []
    match = re.search(
        rf"{re.escape(section)}\s*\n(.*?)(?:\n## |\n---|\Z)",
        content,
        re.DOTALL,
    )
    block = match.group(1) if match else content
    return re.findall(r"^### (TASK-\d+)", block, re.MULTILINE)


def parse_task_file(path: Path) -> dict:
    content = read_text(path)
    task_id = path.stem
    status_match = re.search(r"\*\*Status:\*\*\s*`(\w+)`", content)
    status = status_match.group(1) if status_match else "desconhecido"

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


def parse_leads(crm_path: Path) -> dict:
    content = read_text(crm_path)
    leads: list[dict] = []

    # Índice de leads (tabela)
    in_index = False
    for line in content.splitlines():
        if line.startswith("| ID |"):
            in_index = True
            continue
        if in_index:
            if not line.startswith("|"):
                in_index = False
                continue
            if re.match(r"\|\s*[_—\-]", line) or "nenhum lead" in line.lower():
                continue
            cols = [c.strip() for c in line.strip("|").split("|")]
            if len(cols) >= 6 and re.match(r"LEAD-", cols[0]):
                leads.append(
                    {
                        "id": cols[0],
                        "nome": cols[1],
                        "score": cols[2],
                        "status": cols[5],
                    }
                )

    # Fallback: seções ## LEAD-XXX
    if not leads:
        for m in re.finditer(
            r"^## (LEAD-\d+).*?\n\| \*\*Status\*\* \| (\w+)",
            content,
            re.MULTILINE | re.DOTALL,
        ):
            leads.append({"id": m.group(1), "nome": "—", "score": "—", "status": m.group(2)})

    status_counts: dict[str, int] = {}
    for lead in leads:
        st = lead["status"].lower().replace("`", "")
        status_counts[st] = status_counts.get(st, 0) + 1

    total = len(leads)
    return {"total": total, "leads": leads, "by_status": status_counts}


def count_hypotheses_testing(path: Path) -> int:
    content = read_text(path)
    return len(re.findall(r"\*\*Status:\*\*\s*`?a_testar`?", content))


def build_snapshot() -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    tasks_dir = ROOT / "tasks"
    task_files = sorted(tasks_dir.glob("TASK-*.md"))
    tasks = [parse_task_file(p) for p in task_files]

    executando = count_kanban_tasks(tasks_dir / "executando.md", "## Em andamento")
    planejando = count_kanban_tasks(tasks_dir / "planejando.md", "## Em planejamento")
    aguardando = count_kanban_tasks(tasks_dir / "aguardando.md", "## Bloqueadas")
    backlog = count_kanban_tasks(tasks_dir / "backlog.md", "## Fila")
    concluidas = count_kanban_tasks(tasks_dir / "concluidas.md", "## Concluídas")

    wip = len(executando)
    wip_max = 3

    active_tasks = [t for t in tasks if t["status"] == "executando"]
    ent_done = sum(t["entregaveis_done"] for t in active_tasks)
    ent_total = sum(t["entregaveis_total"] for t in active_tasks)

    leads_data = parse_leads(ROOT / "crm" / "leads.md")
    by_st = leads_data["by_status"]
    total_leads = leads_data["total"]

    hyp_testing = count_hypotheses_testing(ROOT / "memoria" / "hipoteses_testadas.md")

    abordados = by_st.get("abordado", 0)
    convertidos = by_st.get("convertido", 0)
    entregues_caio = by_st.get("entregue_caio", 0) + by_st.get("qualificado", 0)
    captados = total_leads

    conv_lead_abordado = (
        f"{round(100 * abordados / entregues_caio)}%"
        if entregues_caio
        else "—"
    )
    conv_end_to_end = (
        f"{round(100 * convertidos / captados)}%" if captados else "—"
    )

    task_rows = "\n".join(
        f"| [{t['id']}](../tasks/{t['id']}.md) | `{t['status']}` | "
        f"{t['entregaveis_done']}/{t['entregaveis_total']} | {t['progress']} |"
        for t in tasks
    )

    lead_rows = "\n".join(
        f"| {l['id']} | {l['nome']} | {l['score']} | `{l['status']}` |"
        for l in leads_data["leads"][:10]
    ) or "| _—_ | _nenhum lead_ | — | — |"

    return f"""{MARKER_START}
> **Snapshot automático** · gerado em **{now}** · script `scripts/update_dashboard_snapshot.py`

### Resumo

| Indicador | Valor |
|-----------|-------|
| TASKs em execução (WIP) | {wip} / {wip_max} |
| Entregáveis (TASKs `executando`) | {ent_done} / {ent_total} |
| Total leads CRM | {total_leads} |
| Hipóteses `a_testar` | {hyp_testing} |
| Taxa lead → convertido | {conv_end_to_end} |
| Taxa entregue → abordado | {conv_lead_abordado} |

### Pipeline Kanban

| Status | Qtd | TASKs |
|--------|-----|-------|
| `executando` | {len(executando)} | {", ".join(executando) or "—"} |
| `planejando` | {len(planejando)} | {", ".join(planejando) or "—"} |
| `aguardando` | {len(aguardando)} | {", ".join(aguardando) or "—"} |
| `backlog` | {len(backlog)} | {", ".join(backlog) or "—"} |
| `concluído` (kanban) | {len(concluidas)} | {", ".join(concluidas) or "—"} |

### TASKs (arquivos persistentes)

| TASK | Status | Entregáveis | Progresso |
|------|--------|-------------|-----------|
{task_rows}

### Funil CRM

| Status | Qtd |
|--------|-----|
| `novo` | {by_st.get("novo", 0)} |
| `qualificado` | {by_st.get("qualificado", 0)} |
| `entregue_caio` | {by_st.get("entregue_caio", 0)} |
| `abordado` | {by_st.get("abordado", 0)} |
| `convertido` | {by_st.get("convertido", 0)} |
| `sem_resposta` | {by_st.get("sem_resposta", 0)} |
| `descartado` | {by_st.get("descartado", 0)} |
| **Total** | **{total_leads}** |

### Leads (índice)

| ID | Nome | Score | Status |
|----|------|-------|--------|
{lead_rows}

{MARKER_END}"""


def update_dashboard(content: str, snapshot: str) -> str:
    pattern = re.compile(
        re.escape(MARKER_START) + r".*?" + re.escape(MARKER_END),
        re.DOTALL,
    )
    if pattern.search(content):
        return pattern.sub(snapshot, content)

    # Inserir após cabeçalho inicial se markers ainda não existirem
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

    # Atualizar timestamp manual no topo
    auto_ts = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    updated = re.sub(
        r"\*\*Última atualização automática:\*\*.*",
        f"**Última atualização automática:** {auto_ts} (GitHub Actions)",
        updated,
    )
    if "**Última atualização automática:**" not in updated:
        updated = updated.replace(
            f"**Última atualização:** {auto_ts}",
            f"**Última atualização:** {auto_ts}\n**Última atualização automática:** {auto_ts} (GitHub Actions)",
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
