"""Testes do cost gate diário do autopilot (convergência com o LangGraph).

Importar autopilot é leve (crewai só é importado dentro de _advance_task).
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


def test_budget_gate(monkeypatch):
    import laboratorio.ops.usage as usage_mod
    import laboratorio.whatsapp.notify as notify_mod
    from laboratorio.ops import autopilot

    sent: list = []
    monkeypatch.setattr(notify_mod, "notify_vitor", lambda *a, **k: sent.append(a))

    # Sem teto (default 0) -> sempre pode trabalhar.
    monkeypatch.delenv("AUTOPILOT_DAILY_BUDGET_USD", raising=False)
    assert autopilot._budget_gate({}) is True

    # Custo do dia abaixo do teto -> True.
    monkeypatch.setenv("AUTOPILOT_DAILY_BUDGET_USD", "5")
    monkeypatch.setattr(usage_mod, "summarize", lambda: {"today_cost_usd": 1.0})
    assert autopilot._budget_gate({}) is True

    # Custo acima do teto -> pausa (False) e notifica UMA vez no dia.
    monkeypatch.setattr(usage_mod, "summarize", lambda: {"today_cost_usd": 9.0})
    state: dict = {}
    assert autopilot._budget_gate(state) is False
    assert len(sent) == 1
    # 2ª chamada no mesmo dia: continua pausado, mas não re-notifica.
    assert autopilot._budget_gate(state) is False
    assert len(sent) == 1
