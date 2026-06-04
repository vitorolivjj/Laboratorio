"""Coleta do markdown e escrita no Postgres — núcleo da migração (Fase 6).

Fonte única usada pelos scripts:
- scripts/backfill_markdown_to_db.py  (grava)
- scripts/verify_markdown_vs_db.py     (confere)

`collect_markdown()` lê os mesmos arquivos do painel (via ops.parsers) e devolve
linhas prontas. `apply_to_db()` faz upsert idempotente.
"""

from __future__ import annotations

import hashlib

from laboratorio.config import LOGS_DIR, MEMORIA_DIR, REPO_ROOT, TASKS_DIR
from laboratorio.ops import parsers
from laboratorio.ops.tasks_store import STATE_FILES

CRM_DIR = REPO_ROOT / "crm"
CRM_SEGMENT_FILES = ["crm_laboratorio.md", "crm_landing_pintor.md", "crm_appvs.md"]
PROJETOS_REGISTRY = REPO_ROOT / "projetos" / "projetos.md"


def _hash(*parts: str | None) -> str:
    return hashlib.sha256("".join(p or "" for p in parts).encode("utf-8")).hexdigest()


def collect_markdown() -> dict:
    """Parseia projetos/tasks/leads/eventos/decisões do markdown (sem tocar no banco)."""
    registry = parsers.parse_projects_registry(parsers.read_text(PROJETOS_REGISTRY))
    index = parsers._build_project_index(registry)
    by_id = {p["id"]: p for p in registry}

    tasks: list[dict] = []
    for state, (fname, _heading) in STATE_FILES.items():
        for t in parsers.parse_executando_tasks(parsers.read_text(TASKS_DIR / fname)):
            proj = parsers.project_for_task(t, registry, index=index, by_id=by_id)
            tasks.append({**t, "state": state, "project_id": proj["id"] if proj else None})

    leads: list[dict] = []
    for fname in CRM_SEGMENT_FILES:
        content = parsers.read_text(CRM_DIR / fname)
        if not content:
            continue
        seg = parsers.parse_crm_segment(content)
        for lead in seg["leads"]:
            leads.append({**lead, "segment": seg["segment"]})

    events = parsers.parse_event_blocks(parsers.read_text(LOGS_DIR / "eventos.md"), limit=10_000)
    decisions = parsers.parse_decisions(parsers.read_text(MEMORIA_DIR / "decisoes.md"), limit=10_000)
    return {
        "projects": registry,
        "tasks": tasks,
        "leads": leads,
        "events": events,
        "decisions": decisions,
    }


def apply_to_db(data: dict) -> None:
    """Upsert idempotente no Postgres (requer migration aplicada)."""
    from laboratorio.db.core import connection, missing_core_tables

    missing = missing_core_tables()
    if missing:
        raise SystemExit(
            f"Tabelas ausentes: {missing}. Aplique a migration "
            "supabase/migrations/20260604120000_lab_core_tables.sql primeiro."
        )

    with connection() as conn, conn.cursor() as cur:
        for p in data["projects"]:
            cur.execute(
                """
                insert into lab_projects
                  (id,name,prefix,nature,status,crm,repo,description,legacy,updated_at)
                values (%s,%s,%s,%s,%s,%s,%s,%s,%s, now())
                on conflict (id) do update set
                  name=excluded.name, prefix=excluded.prefix, nature=excluded.nature,
                  status=excluded.status, crm=excluded.crm, repo=excluded.repo,
                  description=excluded.description, legacy=excluded.legacy, updated_at=now()
                """,
                (p["id"], p["name"], p.get("prefix"), p.get("nature"), p.get("status"),
                 p.get("crm"), p.get("repo"), p.get("description"), p.get("legacy")),
            )
        for t in data["tasks"]:
            cur.execute(
                """
                insert into lab_tasks
                  (id,title,state,project_id,agents,status,proxima_acao,bloqueio,entregaveis,updated_at)
                values (%s,%s,%s,%s,%s,%s,%s,%s,%s, now())
                on conflict (id) do update set
                  title=excluded.title, state=excluded.state, project_id=excluded.project_id,
                  agents=excluded.agents, status=excluded.status, proxima_acao=excluded.proxima_acao,
                  bloqueio=excluded.bloqueio, entregaveis=excluded.entregaveis, updated_at=now()
                """,
                (t["id"], t["title"], t["state"], t.get("project_id"), t.get("agents"),
                 t.get("status"), t.get("proxima_acao"), t.get("bloqueio"), t.get("entregaveis")),
            )
        for lead in data["leads"]:
            cur.execute(
                """
                insert into lab_leads
                  (id,segment,nome,cidade,servico,contato,origem,status,etapa,responsavel,
                   projeto,score,temperatura,prioridade,tags,observacoes,proxima_acao,captura,updated_at)
                values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s, now())
                on conflict (id) do update set
                  segment=excluded.segment, nome=excluded.nome, cidade=excluded.cidade,
                  servico=excluded.servico, contato=excluded.contato, origem=excluded.origem,
                  status=excluded.status, etapa=excluded.etapa, responsavel=excluded.responsavel,
                  projeto=excluded.projeto, score=excluded.score, temperatura=excluded.temperatura,
                  prioridade=excluded.prioridade, tags=excluded.tags, observacoes=excluded.observacoes,
                  proxima_acao=excluded.proxima_acao, captura=excluded.captura, updated_at=now()
                """,
                (lead["id"], lead["segment"], lead.get("nome"), lead.get("cidade"),
                 lead.get("servico"), lead.get("contato"), lead.get("origem"), lead.get("status"),
                 lead.get("etapa"), lead.get("responsavel"), lead.get("projeto"), lead.get("score"),
                 lead.get("temperatura"), lead.get("prioridade"), lead.get("tags"),
                 lead.get("observacoes"), lead.get("proxima_acao"), lead.get("captura")),
            )
        for e in data["events"]:
            cur.execute(
                """
                insert into lab_events (at,type,title,agents,detail,ref,status,source_hash)
                values (%s,%s,%s,%s,%s,%s,%s,%s) on conflict (source_hash) do nothing
                """,
                (e.get("datetime"), e.get("type"), e.get("title"), e.get("agents"),
                 e.get("detail"), e.get("ref"), e.get("status"),
                 _hash(e.get("datetime"), e.get("type"), e.get("title"), e.get("detail"))),
            )
        for d in data["decisions"]:
            cur.execute(
                """
                insert into lab_decisions (title,date,body,source_hash)
                values (%s,%s,%s,%s) on conflict (source_hash) do nothing
                """,
                (d.get("title"), d.get("date"), d.get("body"),
                 _hash(d.get("title"), d.get("date"), d.get("body"))),
            )


def db_counts() -> dict[str, int]:
    """Contagem por tabela no banco (para conferência)."""
    from laboratorio.db.core import connection

    tables = {
        "projects": "lab_projects",
        "tasks": "lab_tasks",
        "leads": "lab_leads",
        "events": "lab_events",
        "decisions": "lab_decisions",
    }
    out: dict[str, int] = {}
    with connection() as conn, conn.cursor() as cur:
        for key, table in tables.items():
            cur.execute(f"select count(*) from {table}")
            out[key] = cur.fetchone()[0]
    return out
