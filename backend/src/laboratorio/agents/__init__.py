"""Agentes do Laboratório (CrewAI).

Reexports *lazy* (PEP 562): importar utilitários que apenas referenciam
`agents` por caminho não força o carregamento do CrewAI.
"""

from typing import Any

__all__ = ["build_agent", "resolve_agent_llm_config"]


def __getattr__(name: str) -> Any:
    if name == "build_agent":
        from laboratorio.agents.builder import build_agent

        return build_agent
    if name == "resolve_agent_llm_config":
        from laboratorio.agents.llm_config import resolve_agent_llm_config

        return resolve_agent_llm_config
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
