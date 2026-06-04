"""Parsers markdown → estruturas para o Painel Maestro."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

# Fonte única de leitura e extração de campos (antes duplicado aqui).
from laboratorio.ops.markdown_io import extract_cell, extract_field, read_text

__all__ = ["read_text"]  # mantém parsers.read_text como API pública

# Padrão canônico de ID de task: PREFIXO-NÚMERO (TASK-007, LP-PINTOR-002, LAB-3).
# Fonte única — componha com rf"...({TASK_ID_RE})..." para capturar um ID inteiro.
TASK_ID_RE = r"[A-Z][A-Z0-9\-]*-\d+"


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
        # Ignora linha de template em eventos.md
        if titulo in ("Título", "Titulo") or "YYYY-MM-DD" in header_date:
            continue
        if tipo in ("tipo",):
            continue
        body = m.group(4)
        agentes = _field(body, "Agente(s)")
        detalhe = _field(body, "Detalhe")
        ref = _field(body, "Ref")
        status = _field(body, "Status").lower()
        if tipo == "erro" and status == "resolvido":
            tipo = "resolvido"
        blocks.append(
            {
                "datetime": header_date,
                "type": tipo,
                "title": titulo,
                "agents": agentes,
                "detail": detalhe,
                "ref": ref,
                "status": status,
            }
        )
        if len(blocks) >= limit:
            break
    return blocks


def _field(body: str, key: str) -> str:
    return extract_field(body, key)


def event_is_open_error(ev: dict) -> bool:
    """Erro ainda ativo no painel/patrulha (não resolvido)."""
    return ev.get("type") == "erro" and ev.get("status", "").lower() != "resolvido"


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
    return extract_field(body, key)


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
            return extract_cell(block, key) or "—"

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
        rf"^### ({TASK_ID_RE}) — (.+?)\n(.*?)(?=^### |\n---|\Z)",
        content,
        re.MULTILINE | re.DOTALL,
    ):
        block = m.group(3)
        agents = _field(block, "Agente") or _field(block, "Responsável")
        aux = _field(block, "Auxiliares")
        if aux and aux not in ("—", "-", ""):
            agents = f"{agents} · {aux}" if agents else aux
        tasks.append(
            {
                "id": m.group(1),
                "title": m.group(2).strip(),
                "agents": agents,
                "status": _field(block, "Status") or "em_progresso",
                "projeto": _field(block, "Projeto"),
                "proxima_acao": _field(block, "Próxima ação"),
                "bloqueio": _field(block, "Bloqueio"),
                "entregaveis": _field(block, "Entregáveis"),
            }
        )
    return tasks


def parse_briefings_from_task(content: str, task_id: str) -> list[dict]:
    """Extrai briefings Ronaldo → agente de TASK-XXX.md."""
    delegations: list[dict] = []
    title_m = re.search(rf"^# {TASK_ID_RE} — (.+?)$", content, re.MULTILINE)
    task_title = title_m.group(1).strip() if title_m else task_id
    for m in re.finditer(
        r"^### Briefing — (.+?) — (" + TASK_ID_RE + r")(?: — (\d{4}-\d{2}-\d{2}))?\n(.*?)(?=^### |\Z)",
        content,
        re.MULTILINE | re.DOTALL,
    ):
        agent_label = m.group(1).strip()
        obj = _field(m.group(4), "Objetivo desta rodada") or task_title
        task_ref = m.group(2)
        delegations.append(
            {
                "from": "ronaldo_maestro",
                "from_label": "Ronaldo",
                "to": _normalize_agent_id(agent_label),
                "to_label": agent_label,
                "task_id": task_ref,
                "task": f"{obj} ({task_ref})",
                "status": "delegado",
                "priority": "P1",
                "datetime": m.group(3) or "—",
                "next_step": _field(m.group(4), "Critério de pronto") or obj,
            }
        )
    return delegations


def parse_delegations_from_tasks(tasks_dir: Path, active_ids: list[str]) -> list[dict]:
    delegations: list[dict] = []
    for task_id in active_ids:
        path = tasks_dir / f"{task_id}.md"
        if not path.is_file():
            continue
        content = read_text(path)
        briefings = parse_briefings_from_task(content, task_id)
        if briefings:
            delegations.extend(briefings)
            continue
        title_m = re.search(rf"^# {TASK_ID_RE} — (.+?)$", content, re.MULTILINE)
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
                            "task_id": task_id,
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
        # título numa única linha ([^\n]) — evita engolir blocos vizinhos via DOTALL
        r"^### ([^\n]+?) — (\d{4}-\d{2}-\d{2})\n(.*?)(?=^### |\Z)",
        content,
        re.MULTILINE | re.DOTALL,
    ):
        title = m.group(1).strip()
        if title.startswith("[") or "Título" in title:
            continue
        decisions.append(
            {
                "title": title,
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
        "standby": parsers_count(tasks_dir / "standby.md", "## Em standby"),
        "planejando": parsers_count(tasks_dir / "planejando.md", "## Em planejamento"),
        "aguardando": parsers_count(tasks_dir / "aguardando.md", "## Bloqueadas"),
        "backlog": parsers_count(tasks_dir / "backlog.md", "## Fila"),
        "concluidas": parsers_count(tasks_dir / "concluidas.md", "## Concluídas"),
        "arquivado": parsers_count(tasks_dir / "arquivado.md", "## Arquivo"),
    }


def parsers_count(path: Path, section: str) -> list[str]:
    content = read_text(path)
    if not content:
        return []
    pattern = rf"{re.escape(section)}\s*\n(.*?)(?=\n## |\Z)"
    blocks = re.findall(pattern, content, re.DOTALL)
    block = "\n".join(blocks) if blocks else content
    # dedupe preserving order
    seen: set[str] = set()
    ids: list[str] = []
    # Título deve ser "### ID — nome" (evita LP-PINTOR-001B ser lido como LP-PINTOR-001)
    for tid in re.findall(r"^### ([A-Z][A-Z0-9\-]+)(?:\s|—)", block, re.MULTILINE):
        if tid not in seen:
            seen.add(tid)
            ids.append(tid)
    return ids


# ---------------------------------------------------------------------------
# Projetos (registry) + classificação de tasks por projeto
# ---------------------------------------------------------------------------
def parse_projects_registry(content: str) -> list[dict]:
    """Lê projetos/projetos.md → lista de projetos estruturados."""
    projects: list[dict] = []
    # Pula blocos antes de "## Projetos" e ignora o template
    anchor = content.find("## Projetos")
    body = content[anchor:] if anchor != -1 else content
    for m in re.finditer(r"^### (.+?)\n(.*?)(?=^### |\Z)", body, re.MULTILINE | re.DOTALL):
        name = m.group(1).strip()
        block = m.group(2)
        if name.lower().startswith("[") or "Nome do projeto" in name:
            continue
        pid = _field(block, "ID")
        if not pid:
            continue
        legado = _field(block, "Legado")
        projects.append(
            {
                "id": pid,
                "name": name,
                "prefix": _field(block, "Prefixo"),
                "nature": _field(block, "Natureza") or "—",
                "status": _field(block, "Status") or "ativo",
                "crm": _field(block, "CRM"),
                "legacy": legado,
                "repo": _field(block, "Repo / deploy") or _field(block, "Repo"),
                "description": _field(block, "Descrição"),
            }
        )
    return projects


def _build_project_index(projects: list[dict]) -> dict[str, str]:
    """Mapa de chaves (PROJ-XXX, prefixo, TASK-id legado) → id do projeto."""
    index: dict[str, str] = {}
    for p in projects:
        pid = p["id"]
        index[pid.upper()] = pid
        if p.get("prefix"):
            index[p["prefix"].upper()] = pid
        legacy = p.get("legacy") or ""
        for token in re.split(r"[·,;]", legacy):
            token = token.strip().upper()
            if not token or token in ("—", "-"):
                continue
            # Faixas "TASK-010 a TASK-021"
            rng = re.match(r"TASK-(\d+)\s+A\s+TASK-(\d+)", token)
            if rng:
                lo, hi = int(rng.group(1)), int(rng.group(2))
                for n in range(lo, hi + 1):
                    index[f"TASK-{n:03d}"] = pid
                continue
            index[token] = pid
    return index


def project_for_task(task: dict, projects: list[dict]) -> dict | None:
    """Resolve o projeto de uma task (campo Projeto, prefixo do ID, ou legado)."""
    index = _build_project_index(projects)
    by_id = {p["id"]: p for p in projects}

    # 1) Campo Projeto explícito
    explicit = (task.get("projeto") or "").strip().upper()
    if explicit:
        # pode citar "PROJ-001 (transversal PROJ-002)" — pega primeiro token
        first = re.split(r"[\s(]", explicit)[0].strip()
        if first in index:
            return by_id.get(index[first])

    # 2) Prefixo do próprio ID da task (ex.: VITOROS-003)
    tid = (task.get("id") or "").upper()
    prefix_m = re.match(r"([A-Z\-]+)-\d+", tid)
    if prefix_m:
        pref = prefix_m.group(1)
        if pref in index:
            return by_id.get(index[pref])

    # 3) ID legado TASK-XXX
    if tid in index:
        return by_id.get(index[tid])

    return None


# ---------------------------------------------------------------------------
# CRM segmentado
# ---------------------------------------------------------------------------
def parse_crm_meta(content: str) -> dict:
    """Lê o bloco <!-- crm-meta ... --> de um arquivo de CRM."""
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


def parse_crm_leads(content: str) -> list[dict]:
    """Leads de um CRM — seções ## LEAD-XXX (id alfanumérico) + fallback índice."""
    leads: list[dict] = []
    for m in re.finditer(r"^## (LEAD-[\w-]+) — (.+?)$", content, re.MULTILINE):
        lead_id = m.group(1)
        nome = m.group(2).strip()
        start = m.end()
        next_h = re.search(r"^## ", content[start:], re.MULTILINE)
        block = content[start : start + next_h.start()] if next_h else content[start:]

        def fld(key: str) -> str:
            return extract_cell(block, key)

        leads.append(
            {
                "id": lead_id,
                "nome": fld("Nome") or nome,
                "cidade": fld("Cidade"),
                "servico": fld("Serviço"),
                "contato": fld("Contato"),
                "origem": fld("Origem") or "—",
                "status": (fld("Status") or "novo").strip("`"),
                "etapa": (fld("Status") or "novo").strip("`"),
                "responsavel": fld("Responsável") or "—",
                "projeto": fld("Projeto"),
                "score": fld("Score") or "—",
                "temperatura": fld("Temperatura"),
                "prioridade": fld("Prioridade"),
                "tags": fld("Tags"),
                "observacoes": fld("Observações"),
                "proxima_acao": fld("Próxima ação") or fld("Observações") or "—",
                "captura": fld("Data captura"),
            }
        )
    if leads:
        return leads
    # Fallback: índice tabular (ID, Nome, Score, Temp, Prioridade, Status, TASK, Captura)
    return parse_leads_index(content)


def normalize_crm_status(raw: str) -> str:
    """Extrai etapa canônica — ex.: `**ativo** — PIX` → `ativo`."""
    s = raw.lower().strip().strip("`")
    s = re.sub(r"\*+", "", s)
    m = re.match(r"([a-z_]+)", s)
    return m.group(1) if m else (s.split()[0] if s else "")


def parse_crm_segment(content: str) -> dict:
    """Arquivo de CRM completo → meta + leads + contagem por etapa do funil."""
    meta = parse_crm_meta(content)
    leads = parse_crm_leads(content)
    funnel = meta.get("funil") or []
    counts = {stage: 0 for stage in funnel}
    for lead in leads:
        st = normalize_crm_status(lead.get("etapa") or lead.get("status") or "")
        lead["etapa"] = st or lead.get("etapa", "")
        if st in counts:
            counts[st] += 1
    return {
        "segment": meta.get("segmento", "crm"),
        "name": meta.get("nome", "CRM"),
        "description": meta.get("descricao", ""),
        "funnel": funnel,
        "funnel_counts": counts,
        "leads": leads,
        "total": len(leads),
    }


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
