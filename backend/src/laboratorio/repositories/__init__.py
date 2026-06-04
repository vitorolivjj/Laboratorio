"""Repositórios — a "porta única" para os dados operacionais (Fase 5).

Em vez de cada módulo abrir o markdown direto (parsers/stores), passa-se por um
repositório. Hoje a implementação é markdown (delega ao código atual, sem mudar
comportamento); amanhã, Postgres (lab_*), trocando só a fábrica — o resto do
código não muda.

Seleção por env `DATA_BACKEND`: "markdown" (default) | "postgres".
"""

from __future__ import annotations

import os

_POSTGRES_ALIASES = ("postgres", "pg", "db")


def use_postgres() -> bool:
    """True se o backend de leitura é Postgres (env DATA_BACKEND). Lido por chamada.

    Fonte única usada por todas as fábricas get_*_repository() — antes o mesmo
    check estava duplicado em cada módulo.
    """
    return os.getenv("DATA_BACKEND", "markdown").strip().lower() in _POSTGRES_ALIASES
