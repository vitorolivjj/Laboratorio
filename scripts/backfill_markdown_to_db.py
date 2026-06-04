#!/usr/bin/env python3
"""Backfill markdown -> Postgres (tabelas lab_*) — Fase 6, degrau 2.

Lê os MESMOS arquivos do painel (via laboratorio.ops.parsers) e grava no banco
de forma idempotente: upsert por id (projetos/tasks/leads), por hash de conteúdo
(eventos/decisões). Pode rodar quantas vezes quiser.

Uso:
  python scripts/backfill_markdown_to_db.py            # dry-run (só conta; sem banco)
  python scripts/backfill_markdown_to_db.py --apply    # grava no banco

Pré-requisito do --apply: SUPABASE_DB_URL no backend/.env e a migration
supabase/migrations/20260604120000_lab_core_tables.sql aplicada.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(_BACKEND / "src"))

from laboratorio.config import LOGS_DIR, MEMORIA_DIR, REPO_ROOT, TASKS_DIR, load_env  # noqa: E402
from laboratorio.ops import parsers  # noqa: E402
from laboratorio.ops.tasks_store import STATE_FILES  # noqa: E402

CRM_DIR = REPO_ROOT / "crm"
CRM_SEGMENT_FILES = ["crm_laboratorio.md", "crm_landing_pintor.md", "crm_appvs.md"]
PROJETOS_REGISTRY = REPO_ROOT / "projetos" / "projetos.md"


def _hash(*parts: str | None) -> str:
    return hashlib.sha256("".join(p or "" for p in parts).encode("utf-8")).hexdigest()


def collect() -> dict:
    """Parseia tudo do markdown (sem tocar no banco)."""
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


def apply(data: dict) -> None:
    """Upsert idempotente no Postgres."""
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


def main() -> None:
    ap = argparse.ArgumentParser(description="Backfill markdown -> Postgres (lab_*)")
    ap.add_argument("--apply", action="store_true", help="Grava no banco (default: dry-run)")
    args = ap.parse_args()

    load_env()
    data = collect()
    print("Backfill markdown -> Postgres (Fase 6)\n")
    for key in ("projects", "tasks", "leads", "events", "decisions"):
        print(f"  {key:9}: {len(data[key])}")

    if not args.apply:
        print("\n(dry-run — nada gravado. Use --apply para gravar no banco.)")
        return

    apply(data)
    print("\n✓ Gravado no banco (idempotente — pode rodar de novo).")


if __name__ == "__main__":
    main()
