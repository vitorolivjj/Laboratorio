"""Parsers markdown → estruturas para o Painel Maestro."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path


def read_text(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def parse_event_blocks(content: str, limit: int = 30) -> list[dict]:
    blocks: list[dict] = []
    pattern = re.compile(
        r"^### (.+?) — \[(.+?)\] (.+?)\n(.*?)(?=^### |\Z)",
        re.MULTILINE | re.DOTALL,
    )
    for m in pattern.finditer(content):
        header_date = m.group(1).strip()
        tipo = m.group(2).strip().lower()
        titulo = m.group(3).strip()
        body = m.group(4)
        agentes = _field(body, "Agente(s)")
        detalhe = _field(body, "Detalhe")
        ref = _field(body, "Ref")
        blocks.append(
            {
                "datetime": header_date,
                "type": tipo,
                "title": titulo,
                "agents": agentes,
                "detail": detalhe,
                "ref": ref,
            }
        )
        if len(blocks) >= limit:
            break
    return blocks


def _field(body: str, key: str) -> str:
    m = re.search(rf"- \*\*{re.escape(key)}:\*\*\s*(.+)", body)
    return m.group(1).strip() if m else ""


def parse_whatsapp_log(content: str, limit: int = 50) -> list[dict]:
    entries: list[dict] = []
    pattern = re.compile(
        r"^### (\d{4}-\d{2}-\d{2} \d{2}:\d{2} UTC) — (\d+)\n"
        r"(.*?)(?=^### |\n<!--|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    for m in pattern.finditer(content):
        ts = m.group(1)
        phone = m.group(2)
        body = m.group(3)
        inbound = _bullet(body, "inbound")
        outbound = _bullet(body, "outbound")
        status = _bullet(body, "status")
        msg_id = _bullet(body, "message_id").strip("`")
        entries.append(
            {
                "datetime": ts,
                "phone": phone,
                "inbound": inbound,
                "outbound": outbound,
                "status": status,
                "message_id": msg_id,
            }
        )
    return entries[:limit]


def _bullet(body: str, key: str) -> str:
    m = re.search(rf"- \*\*{key}:\*\*\s*(.+)", body)
    return m.group(1).strip() if m else ""


def parse_leads_index(content: str) -> list[dict]:
    leads: list[dict] = []
    in_index = False
    for line in content.splitlines():
        if line.startswith("| ID |"):
            in_index = True
            continue
        if in_index:
            if not line.startswith("|"):
                break
            if re.match(r"\|\s*[_—\-]", line) or "nenhum lead" in line.lower():
                continue
            cols = [c.strip() for c in line.strip("|").split("|")]
            if len(cols) >= 8 and re.match(r"LEAD-", cols[0]):
                leads.append(
                    {
                        "id": cols[0],
                        "nome": cols[1],
                        "score": cols[2],
                        "temperatura": cols[3],
                        "prioridade": cols[4],
                        "status": cols[5].strip("`"),
                        "task": cols[6],
                        "captura": cols[7],
                        "origem": "—",
                        "responsavel": "caio_manteiga",
                        "proxima_acao": "—",
                        "etapa": cols[5].strip("`"),
                    }
                )
    return leads


def parse_lead_sections(content: str) -> list[dict]:
    leads: list[dict] = []
    for m in re.finditer(r"^## (LEAD-\d+) — (.+?)$", content, re.MULTILINE):
        lead_id = m.group(1)
        nome = m.group(2).strip()
        start = m.end()
        next_h = re.search(r"^## ", content[start:], re.MULTILINE)
        block = content[start : start + next_h.start()] if next_h else content[start:]

        def fld(key: str) -> str:
            fm = re.search(rf"\| \*\*{re.escape(key)}\*\* \| (.+?) \|", block)
            return fm.group(1).strip() if fm else "—"

        leads.append(
            {
                "id": lead_id,
                "nome": fld("Nome") if fld("Nome") != "—" else nome,
                "score": fld("Score"),
                "temperatura": fld("Temperatura"),
                "prioridade": fld("Prioridade"),
                "status": fld("Status").strip("`"),
                "task": fld("TASK"),
                "captura": fld("Data captura"),
                "origem": fld("Origem"),
                "responsavel": fld("Responsável"),
                "proxima_acao": fld("Observações"),
                "etapa": fld("Status").strip("`"),
            }
        )
    return leads


def parse_executando_tasks(content: str) -> list[dict]:
    tasks: list[dict] = []
    for m in re.finditer(
        r"^### (TASK-\d+) — (.+?)\n(.*?)(?=^### |\n---|\Z)",
        content,
        re.MULTILINE | re.DOTALL,
    ):
        block = m.group(3)
        tasks.append(
            {
                "id": m.group(1),
                "title": m.group(2).strip(),
                "agents": _field(block, "Agente"),
                "status": _field(block, "Status") or "em_progresso",
                "proxima_acao": _field(block, "Próxima ação"),
                "bloqueio": _field(block, "Bloqueio"),
                "entregaveis": _field(block, "Entregáveis"),
            }
        )
    return tasks


def parse_delegations_from_tasks(tasks_dir: Path, active_ids: list[str]) -> list[dict]:
    delegations: list[dict] = []
    for task_id in active_ids:
        path = tasks_dir / f"{task_id}.md"
        if not path.is_file():
            continue
        content = read_text(path)
        title_m = re.search(r"^# TASK-\d+ — (.+?)$", content, re.MULTILINE)
        task_title = title_m.group(1).strip() if title_m else task_id

        in_table = False
        for line in content.splitlines():
            if re.match(r"\| Ordem \|.*Agente", line):
                in_table = True
                continue
            if in_table:
                if not line.startswith("|") or line.startswith("| ---"):
                    if line.startswith("|") and "---" not in line:
                        continue
                    if not line.startswith("|"):
                        in_table = False
                    continue
                cols = [c.strip() for c in line.strip("|").split("|")]
                if len(cols) >= 3 and cols[0].isdigit():
                    agente = cols[2]
                    acao = cols[1] if len(cols) > 1 else task_title
                    status = cols[3] if len(cols) > 3 else "executando"
                    status = status.replace("✅", "concluído").replace("🔄", "executando").replace("⬜", "pendente")
                    delegations.append(
                        {
                            "from": "ronaldo_maestro",
                            "from_label": "Ronaldo",
                            "to": _normalize_agent_id(agente),
                            "to_label": agente,
                            "task": f"{acao} ({task_id})",
                            "status": status,
                            "priority": "P1",
                            "datetime": "—",
                            "next_step": acao,
                        }
                    )
    return delegations


def parse_decisions(content: str, limit: int = 10) -> list[dict]:
    decisions: list[dict] = []
    for m in re.finditer(
        r"^### (.+?) — (\d{4}-\d{2}-\d{2})\n(.*?)(?=^### |\Z)",
        content,
        re.MULTILINE | re.DOTALL,
    ):
        decisions.append(
            {
                "title": m.group(1).strip(),
                "date": m.group(2),
                "body": m.group(3).strip()[:300],
            }
        )
        if len(decisions) >= limit:
            break
    return decisions


def _normalize_agent_id(label: str) -> str:
    label_l = label.lower()
    mapping = {
        "ronaldo": "ronaldo_maestro",
        "caio": "caio_manteiga",
        "donizete": "donizete_social",
        "dev": "dev",
        "juarez": "juarez",
        "loide": "loide",
    }
    for key, val in mapping.items():
        if key in label_l:
            return val
    return label_l.replace(" ", "_")


def count_kanban(tasks_dir: Path) -> dict[str, list[str]]:
    return {
        "executando": parsers_count(tasks_dir / "executando.md", "## Em andamento"),
        "planejando": parsers_count(tasks_dir / "planejando.md", "## Em planejamento"),
        "aguardando": parsers_count(tasks_dir / "aguardando.md", "## Bloqueadas"),
        "backlog": parsers_count(tasks_dir / "backlog.md", "## Fila"),
        "concluidas": parsers_count(tasks_dir / "concluidas.md", "## Concluídas"),
    }


def parsers_count(path: Path, section: str) -> list[str]:
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


def group_whatsapp_threads(entries: list[dict]) -> list[dict]:
    """Agrupa mensagens por telefone — thread mais recente primeiro."""
    threads: dict[str, dict] = {}
    for entry in entries:
        phone = entry["phone"]
        if phone not in threads:
            threads[phone] = {
                "phone": phone,
                "last_inbound": entry["inbound"],
                "last_outbound": entry["outbound"],
                "datetime": entry["datetime"],
                "status": entry["status"],
                "message_count": 1,
                "messages": [entry],
            }
        else:
            threads[phone]["message_count"] += 1
            threads[phone]["messages"].append(entry)
    return sorted(threads.values(), key=lambda t: t["datetime"], reverse=True)


def count_today(items: list[dict], date_key: str = "datetime") -> int:
    today = date.today().isoformat()
    count = 0
    for item in items:
        val = item.get(date_key, "")
        if val.startswith(today):
            count += 1
    return count
