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
    """Conexão psycopg autocommit, com timeout curto e retry.

    Supabase resolve para IPv6 e IPv4; em redes onde o IPv6 é instável a 1ª
    tentativa pode estourar. `connect_timeout` falha rápido e o retry tenta de
    novo (em geral cai no IPv4). Levanta se SUPABASE_DB_URL ausente.
    """
    import time

    import psycopg

    from laboratorio.settings import get_settings

    url = supabase_db_url()
    if not url:
        raise RuntimeError("SUPABASE_DB_URL não configurado no backend/.env")
    s = get_settings()
    timeout = s.db_connect_timeout
    attempts = max(1, s.db_connect_retries)

    conn = None
    last_exc: Exception | None = None
    for i in range(attempts):
        try:
            conn = psycopg.connect(url, autocommit=True, connect_timeout=timeout)
            break
        except psycopg.OperationalError as exc:
            last_exc = exc
            if i < attempts - 1:
                time.sleep(1)
    if conn is None:
        raise last_exc if last_exc else RuntimeError("falha ao conectar no banco")

    try:
        yield conn
    finally:
        conn.close()


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
