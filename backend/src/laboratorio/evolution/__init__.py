"""Fase 4 — autoevolução supervisionada (resumo diário + propostas)."""

__all__ = ["run_daily_digest"]


def run_daily_digest(*args, **kwargs):
    from laboratorio.evolution.digest import run_daily_digest as _run

    return _run(*args, **kwargs)
