"""Base comum das ferramentas CrewAI.

`safe` envolve a execução: qualquer exceção vira uma string de erro legível
para o agente (que pode tentar de novo), em vez de derrubar a crew inteira.
"""

from __future__ import annotations

import functools
import logging
from collections.abc import Callable

logger = logging.getLogger("laboratorio.tools")

# Reexporta BaseTool do CrewAI (necessário em runtime; CrewAI é dependência do backend).
from crewai.tools import BaseTool

__all__ = ["BaseTool", "safe"]


def safe(fn: Callable[..., str]) -> Callable[..., str]:
    @functools.wraps(fn)
    def wrapper(*args, **kwargs) -> str:
        try:
            return fn(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001 — devolve erro ao agente
            logger.warning("Tool %s falhou: %s", fn.__qualname__, exc)
            return f"ERRO ao executar ferramenta: {type(exc).__name__}: {exc}"

    return wrapper
