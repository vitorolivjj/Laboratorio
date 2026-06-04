"""Repositório de projetos — porta única para o registry de projetos.

MarkdownProjectRepository delega ao parser atual; PostgresProjectRepository lê
lab_projects. Seleção por DATA_BACKEND (default markdown).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from laboratorio.config import REPO_ROOT
from laboratorio.ops import parsers
from laboratorio.repositories import use_postgres

PROJETOS_REGISTRY = REPO_ROOT / "projetos" / "projetos.md"

_COLS = "id,name,prefix,nature,status,crm,repo,description,legacy"


@runtime_checkable
class ProjectRepository(Protocol):
    def all(self) -> list[dict]: ...
    def get(self, project_id: str) -> dict | None: ...


class MarkdownProjectRepository:
    def all(self) -> list[dict]:
        return parsers.parse_projects_registry(parsers.read_text(PROJETOS_REGISTRY))

    def get(self, project_id: str) -> dict | None:
        pid = project_id.strip().upper()
        return next((p for p in self.all() if p["id"].upper() == pid), None)


class PostgresProjectRepository:
    def _row(self, r: tuple) -> dict:
        return {
            "id": r[0], "name": r[1], "prefix": r[2] or "", "nature": r[3] or "—",
            "status": r[4] or "ativo", "crm": r[5] or "", "repo": r[6] or "",
            "description": r[7] or "", "legacy": r[8] or "",
        }

    def all(self) -> list[dict]:
        from laboratorio.db.core import connection

        with connection() as conn, conn.cursor() as cur:
            cur.execute(f"select {_COLS} from lab_projects order by id")
            return [self._row(r) for r in cur.fetchall()]

    def get(self, project_id: str) -> dict | None:
        from laboratorio.db.core import connection

        with connection() as conn, conn.cursor() as cur:
            cur.execute(f"select {_COLS} from lab_projects where upper(id)=upper(%s)", (project_id.strip(),))
            row = cur.fetchone()
            return self._row(row) if row else None


def get_project_repository() -> ProjectRepository:
    if use_postgres():
        return PostgresProjectRepository()
    return MarkdownProjectRepository()
