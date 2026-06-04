"""Repositório de tasks (kanban) — a porta única para ler/escrever TASKs.

- MarkdownTaskRepository: delega ao código atual (parsers + tasks_store). Fonte da
  verdade hoje. **Zero mudança de comportamento.**
- PostgresTaskRepository: lê/escreve `lab_tasks` (Fase 6). EXPERIMENTAL — requer
  SUPABASE_DB_URL e a migration aplicada; escrita ainda não suportada (use markdown).

`get_task_repository()` decide qual usar por `DATA_BACKEND` (default: markdown).
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from laboratorio.config import TASKS_DIR
from laboratorio.ops import parsers, tasks_store
from laboratorio.ops.tasks_store import STATE_FILES
from laboratorio.repositories import use_postgres


@runtime_checkable
class TaskRepository(Protocol):
    """Contrato do repositório de tasks (independe de markdown/banco)."""

    def list_by_state(self, state: str) -> list[dict]:
        """TASKs de um estado do kanban (dicts com id, title, agents, …)."""
        ...

    def counts(self) -> dict[str, list[str]]:
        """IDs por estado (mesmo formato de parsers.count_kanban)."""
        ...

    def get(self, task_id: str) -> dict | None:
        """Uma TASK por id (com a chave 'state'), ou None."""
        ...

    def create(self, **kwargs) -> str:
        """Cria TASK no backlog; retorna mensagem com o ID."""
        ...

    def move(self, task_id: str, to_state: str, nota: str = "", *, force: bool = False) -> str:
        """Move TASK entre estados."""
        ...


class MarkdownTaskRepository:
    """Implementação sobre tasks/*.md — delega ao código existente."""

    def __init__(self, tasks_dir: Path = TASKS_DIR) -> None:
        self.tasks_dir = tasks_dir

    def list_by_state(self, state: str) -> list[dict]:
        fname, _heading = STATE_FILES[state]
        return parsers.parse_executando_tasks(parsers.read_text(self.tasks_dir / fname))

    def counts(self) -> dict[str, list[str]]:
        return parsers.count_kanban(self.tasks_dir)

    def get(self, task_id: str) -> dict | None:
        task_id = task_id.strip().upper()
        for state in STATE_FILES:
            for t in self.list_by_state(state):
                if t["id"].upper() == task_id:
                    return {**t, "state": state}
        return None

    def create(self, **kwargs) -> str:
        return tasks_store.create_task(tasks_dir=self.tasks_dir, **kwargs)

    def move(self, task_id: str, to_state: str, nota: str = "", *, force: bool = False) -> str:
        return tasks_store.move_task(
            task_id, to_state, nota, tasks_dir=self.tasks_dir, force=force
        )


class PostgresTaskRepository:
    """Implementação sobre lab_tasks (Fase 6). EXPERIMENTAL — leitura apenas.

    A escrita (create/move) exige a estratégia de escrita dupla / cutover e fica
    para o degrau 3-5 da migração; por ora delega ao markdown para não perder
    funcionalidade caso alguém ligue DATA_BACKEND=postgres cedo demais.
    """

    _COLS = "id,title,agents,status,proxima_acao,bloqueio,entregaveis,project_id"

    def _row_to_task(self, r: tuple) -> dict:
        return {
            "id": r[0], "title": r[1], "agents": r[2] or "", "status": r[3] or "",
            "proxima_acao": r[4] or "", "bloqueio": r[5] or "", "entregaveis": r[6] or "",
            "projeto": r[7] or "",
        }

    def list_by_state(self, state: str) -> list[dict]:
        from laboratorio.db.core import connection

        with connection() as conn, conn.cursor() as cur:
            cur.execute(
                f"select {self._COLS} from lab_tasks where state = %s order by id",
                (state,),
            )
            return [self._row_to_task(r) for r in cur.fetchall()]

    def counts(self) -> dict[str, list[str]]:
        from laboratorio.db.core import connection

        out: dict[str, list[str]] = {s: [] for s in STATE_FILES}
        with connection() as conn, conn.cursor() as cur:
            cur.execute("select state, id from lab_tasks order by id")
            for state, tid in cur.fetchall():
                out.setdefault(state, []).append(tid)
        return out

    def get(self, task_id: str) -> dict | None:
        from laboratorio.db.core import connection

        with connection() as conn, conn.cursor() as cur:
            cur.execute(
                f"select {self._COLS}, state from lab_tasks where upper(id) = upper(%s)",
                (task_id.strip(),),
            )
            row = cur.fetchone()
            if not row:
                return None
            task = self._row_to_task(row)
            task["state"] = row[8]
            return task

    # Escrita ainda não migrada — delega ao markdown (fonte da verdade na escrita).
    def create(self, **kwargs) -> str:
        return MarkdownTaskRepository().create(**kwargs)

    def move(self, task_id: str, to_state: str, nota: str = "", *, force: bool = False) -> str:
        return MarkdownTaskRepository().move(task_id, to_state, nota, force=force)


def get_task_repository() -> TaskRepository:
    """Fábrica: escolhe a implementação por DATA_BACKEND (default markdown)."""
    if use_postgres():
        return PostgresTaskRepository()
    return MarkdownTaskRepository()
