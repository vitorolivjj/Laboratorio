"""Testes da autenticação por token do painel (api/auth.py)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from fastapi import HTTPException  # noqa: E402

from laboratorio.api.auth import require_panel_token  # noqa: E402


def test_open_when_token_unset(monkeypatch):
    """Sem MAESTRO_API_TOKEN → libera (compat dev)."""
    monkeypatch.delenv("MAESTRO_API_TOKEN", raising=False)
    require_panel_token(authorization="")  # não levanta
    require_panel_token(authorization="Bearer seja-o-que-for")


def test_enforced_when_token_set(monkeypatch):
    monkeypatch.setenv("MAESTRO_API_TOKEN", "segredo123")
    # Correto passa.
    require_panel_token(authorization="Bearer segredo123")
    # Errado e ausente falham.
    for bad in ("Bearer errado", "", "segredo123", "Basic x"):
        with pytest.raises(HTTPException) as exc:
            require_panel_token(authorization=bad)
        assert exc.value.status_code == 403
