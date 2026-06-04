"""Repositórios — a "porta única" para os dados operacionais (Fase 5).

Em vez de cada módulo abrir o markdown direto (parsers/stores), passa-se por um
repositório. Hoje a implementação é markdown (delega ao código atual, sem mudar
comportamento); amanhã, Postgres (lab_*), trocando só a fábrica — o resto do
código não muda.

Seleção por env `DATA_BACKEND`: "markdown" (default) | "postgres".
"""

from __future__ import annotations

import logging

from laboratorio.settings import get_settings

logger = logging.getLogger("laboratorio.repositories")


def use_postgres() -> bool:
    """True se o backend de leitura é Postgres (Settings.data_backend). Lido por chamada.

    Fonte única usada por todas as fábricas get_*_repository().
    """
    return get_settings().use_postgres()


class FallbackRepository:
    """Tenta o repo primário (banco); se falhar, cai no fallback (markdown).

    Markdown é sempre a fonte da verdade da escrita, então cair nele é seguro.
    Torna `DATA_BACKEND=postgres` resiliente a soluços de rede (IPv6 instável):
    o painel nunca quebra por causa do banco — só degrada para o markdown.
    """

    def __init__(self, primary: object, fallback: object) -> None:
        self.primary = primary
        self.fallback = fallback

    def __getattr__(self, name: str):
        prim = getattr(self.primary, name)
        fb = getattr(self.fallback, name)

        def call(*args, **kwargs):
            try:
                return prim(*args, **kwargs)
            except Exception as exc:  # noqa: BLE001 — banco indisponível -> markdown
                logger.warning(
                    "Repositório do banco falhou em %s() — fallback markdown: %s", name, exc
                )
                return fb(*args, **kwargs)

        return call


def pick(markdown_factory, postgres_factory):
    """Escolhe o repositório por DATA_BACKEND. No modo postgres, embrulha com
    fallback markdown (resiliência). Fora dele, devolve o markdown direto."""
    markdown = markdown_factory()
    if use_postgres():
        return FallbackRepository(postgres_factory(), markdown)
    return markdown
