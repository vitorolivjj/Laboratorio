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
import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(_BACKEND / "src"))

from laboratorio.config import load_env  # noqa: E402
from laboratorio.db.markdown_sync import apply_to_db, collect_markdown  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description="Backfill markdown -> Postgres (lab_*)")
    ap.add_argument("--apply", action="store_true", help="Grava no banco (default: dry-run)")
    ap.add_argument(
        "--mirror",
        action="store_true",
        help="Espelho exato: remove do banco projetos/tasks/leads ausentes no markdown",
    )
    args = ap.parse_args()

    load_env()
    data = collect_markdown()
    print("Backfill markdown -> Postgres (Fase 6)\n")
    for key in ("projects", "tasks", "leads", "events", "decisions"):
        print(f"  {key:9}: {len(data[key])}")

    if not args.apply:
        print("\n(dry-run — nada gravado. Use --apply para gravar no banco.)")
        return

    apply_to_db(data, mirror=args.mirror)
    extra = " (espelho — removeu o que sumiu do markdown)" if args.mirror else ""
    print(f"\n✓ Gravado no banco{extra}.")


if __name__ == "__main__":
    main()
