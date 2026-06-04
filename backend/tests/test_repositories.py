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
    # Postgres: embrulhado com fallback markdown (não conecta — conexão é lazy).
    monkeypatch.setenv("DATA_BACKEND", "postgres")
    repo = get_task_repository()
    assert isinstance(repo.primary, PostgresTaskRepository)
    assert isinstance(repo.fallback, MarkdownTaskRepository)


def test_project_repository(monkeypatch):
    from laboratorio.repositories.projects import (
        MarkdownProjectRepository,
        PostgresProjectRepository,
        get_project_repository,
    )

    monkeypatch.delenv("DATA_BACKEND", raising=False)
    repo = get_project_repository()
    assert isinstance(repo, MarkdownProjectRepository)
    projs = repo.all()
    assert projs and all("id" in p and "name" in p for p in projs)
    monkeypatch.setenv("DATA_BACKEND", "postgres")
    assert isinstance(get_project_repository().primary, PostgresProjectRepository)


def test_fallback_repository_degrades_to_markdown():
    """Se o repo do banco falhar, FallbackRepository cai no markdown."""
    from laboratorio.repositories import FallbackRepository

    class _Boom:
        def list_by_state(self, state):
            raise RuntimeError("banco fora do ar")

    class _Ok:
        def list_by_state(self, state):
            return [{"id": "X", "state": state}]

    repo = FallbackRepository(_Boom(), _Ok())
    assert repo.list_by_state("executando") == [{"id": "X", "state": "executando"}]


def test_lead_repository(monkeypatch):
    from laboratorio.repositories.leads import MarkdownLeadRepository, get_lead_repository

    monkeypatch.delenv("DATA_BACKEND", raising=False)
    repo = get_lead_repository()
    assert isinstance(repo, MarkdownLeadRepository)
    leads = repo.all()
    assert all("id" in lead and "segment" in lead for lead in leads)


def test_event_repository(monkeypatch):
    from laboratorio.repositories.events import MarkdownEventRepository, get_event_repository

    monkeypatch.delenv("DATA_BACKEND", raising=False)
    repo = get_event_repository()
    assert isinstance(repo, MarkdownEventRepository)
    evs = repo.recent(limit=5)
    assert isinstance(evs, list) and len(evs) <= 5
