"""Conexão e checagem de schema das tabelas operacionais (lab_*).

Reutiliza SUPABASE_DB_URL (mesmo banco da memória semântica). Mantido separado
de memory/semantic.py para não acoplar dados operacionais a pgvector.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from laboratorio.memory.semantic import supabase_db_url

CORE_TABLES = (
    "lab_projects",
    "lab_tasks",
    "lab_leads",
    "lab_events",
    "lab_decisions",
    "lab_runtime_state",
)


def db_enabled() -> bool:
    """True se há SUPABASE_DB_URL configurado (banco disponível)."""
    return bool(supabase_db_url())


@contextmanager
def connection() -> Iterator["object"]:
    """Conexão psycopg autocommit. Levanta se SUPABASE_DB_URL ausente."""
    import os

    import psycopg

    url = supabase_db_url()
    if not url:
        raise RuntimeError("SUPABASE_DB_URL não configurado no backend/.env")
    # connect_timeout curto: se o host resolver para IPv6 inacessível, falha
    # rápido e tenta o próximo endereço (IPv4) em vez de pendurar no SO.
    timeout = int(os.getenv("DB_CONNECT_TIMEOUT", "10"))
    with psycopg.connect(url, autocommit=True, connect_timeout=timeout) as conn:
        yield conn


def missing_core_tables() -> list[str]:
    """Lista as tabelas lab_* que ainda não existem (vazio = migration aplicada)."""
    missing: list[str] = []
    with connection() as conn, conn.cursor() as cur:
        for table in CORE_TABLES:
            cur.execute(
                "select 1 from information_schema.tables "
                "where table_schema = 'public' and table_name = %s",
                (table,),
            )
            if cur.fetchone() is None:
                missing.append(table)
    return missing
