#!/usr/bin/env python3
"""Conferência markdown x Postgres — Fase 6, degrau 4.

Compara as contagens do markdown (fonte da verdade hoje) com o que está no banco.
Use durante a escrita dupla para ganhar confiança antes de virar a leitura
(DATA_BACKEND=postgres). Sem banco configurado, mostra só o lado markdown.

Uso:
  python scripts/verify_markdown_vs_db.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(_BACKEND / "src"))

from laboratorio.config import load_env  # noqa: E402
from laboratorio.db.markdown_sync import collect_markdown  # noqa: E402

KEYS = ("projects", "tasks", "leads", "events", "decisions")


def main() -> int:
    load_env()
    md = {k: len(v) for k, v in collect_markdown().items()}

    print("Conferência markdown x banco (Fase 6)\n")

    try:
        from laboratorio.db.core import db_enabled, missing_core_tables
        from laboratorio.db.markdown_sync import db_counts

        if not db_enabled():
            print("  (SUPABASE_DB_URL ausente — mostrando só o markdown)\n")
            for k in KEYS:
                print(f"  {k:9}: markdown={md[k]}")
            return 0

        missing = missing_core_tables()
        if missing:
            print(f"  ⚠️ Tabelas ausentes no banco: {missing}")
            print("     Aplique a migration antes de comparar.\n")
            for k in KEYS:
                print(f"  {k:9}: markdown={md[k]}  banco=—")
            return 1

        db = db_counts()
        all_ok = True
        for k in KEYS:
            m, d = md[k], db.get(k, 0)
            # eventos/decisões usam dedup por hash → banco pode ter <= markdown.
            flag = "ok" if (m == d or (k in ("events", "decisions") and d <= m)) else "DIVERGE"
            if flag != "ok":
                all_ok = False
            print(f"  {k:9}: markdown={m:<5} banco={d:<5} {flag}")
        print("\n" + ("✓ Consistente." if all_ok else "⚠️ Há divergências — rode o backfill --apply."))
        return 0 if all_ok else 1

    except ImportError as exc:
        print(f"  (driver de banco indisponível: {exc} — mostrando só o markdown)\n")
        for k in KEYS:
            print(f"  {k:9}: markdown={md[k]}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
