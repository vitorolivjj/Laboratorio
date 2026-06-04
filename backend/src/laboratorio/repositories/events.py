"""Repositório de eventos (linha do tempo) — porta única para o log de eventos.

MarkdownEventRepository lê logs/eventos.md; PostgresEventRepository lê lab_events.
Seleção por DATA_BACKEND (default markdown).
"""

from __future__ import annotations

import os
from typing import Protocol, runtime_checkable

from laboratorio.config import LOGS_DIR
from laboratorio.ops import parsers

EVENTOS_FILE = LOGS_DIR / "eventos.md"


@runtime_checkable
class EventRepository(Protocol):
    def recent(self, limit: int = 30) -> list[dict]: ...


class MarkdownEventRepository:
    def recent(self, limit: int = 30) -> list[dict]:
        return parsers.parse_event_blocks(parsers.read_text(EVENTOS_FILE), limit=limit)


class PostgresEventRepository:
    def recent(self, limit: int = 30) -> list[dict]:
        from laboratorio.db.core import connection

        with connection() as conn, conn.cursor() as cur:
            cur.execute(
                "select at,type,title,agents,detail,ref,status "
                "from lab_events order by id desc limit %s",
                (max(1, limit),),
            )
            return [
                {
                    "datetime": r[0] or "", "type": r[1] or "", "title": r[2] or "",
                    "agents": r[3] or "", "detail": r[4] or "", "ref": r[5] or "",
                    "status": (r[6] or "").lower(),
                }
                for r in cur.fetchall()
            ]


def get_event_repository() -> EventRepository:
    if os.getenv("DATA_BACKEND", "markdown").strip().lower() in ("postgres", "pg", "db"):
        return PostgresEventRepository()
    return MarkdownEventRepository()
