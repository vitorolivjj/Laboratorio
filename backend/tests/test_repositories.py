"""Testes do repositório de tasks (Fase 5).

MarkdownTaskRepository deve delegar ao código atual sem mudar comportamento.
Opera sobre cópia temporária de tasks/ — não toca no repo real.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

_REPO = Path(__file__).resolve().parents[2]

from laboratorio.repositories.tasks import (  # noqa: E402
    MarkdownTaskRepository,
    PostgresTaskRepository,
    get_task_repository,
)


def test_markdown_task_repository_crud(tmp_path):
    tasks_dir = tmp_path / "tasks"
    shutil.copytree(_REPO / "tasks", tasks_dir)
    repo = MarkdownTaskRepository(tasks_dir=tasks_dir)

    # create -> backlog
    tid = repo.create(titulo="Repo test", objetivo="x", agente="dev").split()[0]
    assert tid.startswith("TASK-")
    got = repo.get(tid)
    assert got and got["state"] == "backlog"
    assert tid in repo.counts()["backlog"]

    # move (force pula o gate de briefing) -> executando
    repo.move(tid, "executando", force=True)
    assert repo.get(tid)["state"] == "executando"
    ids = [t["id"] for t in repo.list_by_state("executando")]
    assert tid in ids

    # inexistente
    assert repo.get("TASK-999999") is None


def test_factory_selects_by_env(monkeypatch):
    monkeypatch.delenv("DATA_BACKEND", raising=False)
    assert isinstance(get_task_repository(), MarkdownTaskRepository)
    monkeypatch.setenv("DATA_BACKEND", "markdown")
    assert isinstance(get_task_repository(), MarkdownTaskRepository)
    # Postgres só é instanciado (não conecta — conexão é lazy).
    monkeypatch.setenv("DATA_BACKEND", "postgres")
    assert isinstance(get_task_repository(), PostgresTaskRepository)
