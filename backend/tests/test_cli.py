"""Testes do registry de comandos da CLI (Fase 7.2).

Importar laboratorio.main é leve (os imports pesados são locais aos handlers),
então este teste roda rápido e trava a completude do registry.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from laboratorio.main import COMMANDS  # noqa: E402

EXPECTED = {
    "check", "llm-config", "run-sample", "orchestrate", "whatsapp-check", "autopilot",
    "ronaldo-patrol", "donizete-captura", "donizete-fb", "ronaldo-audit", "governanca-audit",
    "orphan-memoria-audit", "donizete-mac-prepare", "donizete-busca-local", "vitor-schedule",
    "content-run", "memory-check", "memory-sync", "memory-recall", "graph-pilot", "graph-run",
    "agent-action", "evolution-digest",
}


def test_registry_complete_and_callable():
    assert set(COMMANDS) == EXPECTED, f"diferença: {set(COMMANDS) ^ EXPECTED}"
    assert all(callable(h) for h in COMMANDS.values())
