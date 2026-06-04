"""Testes do Settings de runtime (lê env por chamada; seguro com monkeypatch)."""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from laboratorio.settings import get_settings  # noqa: E402


def test_defaults(monkeypatch):
    for var in ("DATA_BACKEND", "DB_DUAL_WRITE", "MAESTRO_API_TOKEN"):
        monkeypatch.delenv(var, raising=False)
    s = get_settings()
    assert s.data_backend == "markdown"
    assert not s.use_postgres()
    assert s.dual_write_flag() is None  # auto
    assert s.maestro_api_token == ""
    assert s.db_connect_timeout == 8


def test_env_overrides(monkeypatch):
    monkeypatch.setenv("DATA_BACKEND", "postgres")
    monkeypatch.setenv("DB_DUAL_WRITE", "0")
    monkeypatch.setenv("MAESTRO_API_TOKEN", "segredo")
    s = get_settings()
    assert s.use_postgres()
    assert s.dual_write_flag() is False
    assert s.maestro_api_token == "segredo"
