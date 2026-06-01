"""Ferramentas de Kanban (tasks) para Ronaldo e especialistas."""

from __future__ import annotations

from pydantic import BaseModel, Field

from laboratorio.ops import tasks_store
from laboratorio.tools.base import BaseTool, safe


class ListarTasksTool(BaseTool):
    name: str = "listar_tasks"
    description: str = "Lista as TASKs por estado do kanban (backlog, executando, etc.)."

    @safe
    def _run(self) -> str:
        return tasks_store.list_tasks()


class _CriarTaskArgs(BaseModel):
    titulo: str = Field(..., description="Título curto da TASK")
    objetivo: str = Field("", description="Objetivo/descrição")
    agente: str = Field("", description="Agente(s) responsável(is)")
    prioridade: str = Field("media", description="alta | media | baixa")
    contexto: str = Field("", description="Projeto/contexto, ex.: PROJ-002")
    resultado: str = Field("", description="Resultado esperado / critério de pronto")


class CriarTaskTool(BaseTool):
    name: str = "criar_task"
    description: str = "Cria uma nova TASK no backlog. O ID (TASK-XXX) é gerado automaticamente."
    args_schema: type[BaseModel] = _CriarTaskArgs

    @safe
    def _run(self, **kwargs) -> str:
        return tasks_store.create_task(**kwargs)


class _MoverTaskArgs(BaseModel):
    task_id: str = Field(..., description="ID da TASK, ex.: TASK-012")
    to_state: str = Field(
        ...,
        description="Destino: backlog | planejando | executando | aguardando | concluidas | arquivado",
    )
    nota: str = Field("", description="Nota opcional sobre a movimentação")


class MoverTaskTool(BaseTool):
    name: str = "mover_task"
    description: str = "Move uma TASK entre estados do kanban (ex.: backlog → executando)."
    args_schema: type[BaseModel] = _MoverTaskArgs

    @safe
    def _run(self, task_id: str, to_state: str, nota: str = "") -> str:
        return tasks_store.move_task(task_id, to_state, nota)
