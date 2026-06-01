"""Operações de negócio (snapshot, parsers) do Painel Maestro.

Reexports são *lazy* (PEP 562): importar um submódulo leve (ex.: crm_store,
retrieval) não puxa o maestro/agents/crewai por tabela.
"""

from typing import Any

__all__ = ["build_maestro_snapshot", "read_text"]


def __getattr__(name: str) -> Any:
    if name == "build_maestro_snapshot":
        from laboratorio.ops.maestro import build_maestro_snapshot

        return build_maestro_snapshot
    if name == "read_text":
        from laboratorio.ops.parsers import read_text

        return read_text
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
