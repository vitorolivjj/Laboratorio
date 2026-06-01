"""Ferramentas de memória compartilhada e logs para todos os agentes."""

from __future__ import annotations

from pydantic import BaseModel, Field

from laboratorio.ops import memory_store
from laboratorio.tools.base import BaseTool, safe


class _LerMemoriaArgs(BaseModel):
    name: str = Field(
        ...,
        description="Qual memória ler: contexto_global | decisoes | aprendizados | agentes | projetos",
    )


class LerMemoriaTool(BaseTool):
    name: str = "ler_memoria"
    description: str = "Lê um arquivo de memória/contexto compartilhado antes de decidir."
    args_schema: type[BaseModel] = _LerMemoriaArgs

    @safe
    def _run(self, name: str) -> str:
        return memory_store.read_memory(name)


class _DecisaoArgs(BaseModel):
    titulo: str = Field(..., description="Título da decisão")
    contexto: str = Field(..., description="Por que a decisão foi necessária")
    decisao: str = Field(..., description="O que foi decidido")
    responsavel: str = Field("agente", description="Quem decidiu")
    impactados: str = Field("—", description="Agentes impactados")


class RegistrarDecisaoTool(BaseTool):
    name: str = "registrar_decisao"
    description: str = "Registra uma decisão operacional em memoria/decisoes.md (visível a todos)."
    args_schema: type[BaseModel] = _DecisaoArgs

    @safe
    def _run(self, **kwargs) -> str:
        return memory_store.registrar_decisao(**kwargs)


class _AprendizadoArgs(BaseModel):
    titulo: str = Field(..., description="Título curto do aprendizado")
    situacao: str = Field(..., description="Situação observada")
    aprendizado: str = Field(..., description="O que se aprendeu")
    acao: str = Field("", description="O que muda daqui pra frente")
    tags: str = Field("", description="Tags, ex.: #dev #comercial")


class RegistrarAprendizadoTool(BaseTool):
    name: str = "registrar_aprendizado"
    description: str = "Registra um aprendizado em memoria/aprendizados.md."
    args_schema: type[BaseModel] = _AprendizadoArgs

    @safe
    def _run(self, **kwargs) -> str:
        return memory_store.registrar_aprendizado(**kwargs)


class _EventoArgs(BaseModel):
    titulo: str = Field(..., description="Título do evento")
    tipo: str = Field("tarefa", description="orquestracao | deploy | decisao | erro | marco | tarefa")
    agentes: str = Field("—", description="Agente(s) envolvido(s)")
    detalhe: str = Field("", description="Detalhe curto")
    ref: str = Field("", description="TASK-XXX | PROJ-XXX")


class RegistrarEventoTool(BaseTool):
    name: str = "registrar_evento"
    description: str = "Registra um evento na linha do tempo (logs/eventos.md)."
    args_schema: type[BaseModel] = _EventoArgs

    @safe
    def _run(self, **kwargs) -> str:
        return memory_store.registrar_evento(**kwargs)
