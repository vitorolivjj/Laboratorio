"""Caracterização dos helpers de identificação de agente.

Trava o comportamento de parsers._normalize_agent_id e maestro.re_split_agents
antes/depois da unificação (Fase 1.4).
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from laboratorio.ops import parsers  # noqa: E402


def test_normalize_agent_id():
    assert parsers._normalize_agent_id("Ronaldo") == "ronaldo_maestro"
    assert parsers._normalize_agent_id("caio manteiga") == "caio_manteiga"
    assert parsers._normalize_agent_id("DONIZETE") == "donizete_social"
    assert parsers._normalize_agent_id("dev") == "dev"
    assert parsers._normalize_agent_id("Juarez") == "juarez"
    assert parsers._normalize_agent_id("loide") == "loide"
    # Desconhecido: fallback lowercase + espaços->underscore
    assert parsers._normalize_agent_id("Fulano X") == "fulano_x"


def test_re_split_agents():
    from laboratorio.ops.maestro import re_split_agents

    assert re_split_agents("ronaldo_maestro · dev") == ["ronaldo_maestro", "dev"]
    assert re_split_agents("Caio, Donizete") == ["caio_manteiga", "donizete_social"]
    assert re_split_agents("dev; dev") == ["dev", "dev"]  # duplicatas preservadas
    assert re_split_agents("juarez · fulano") == ["juarez"]  # desconhecido ignorado
    assert re_split_agents("") == []


def test_build_maestro_snapshot_smoke(monkeypatch):
    """Fumaça da god function: monta o snapshot real sem explodir nem escrever.

    Neutraliza efeitos colaterais (métricas, subprocess systemctl, cadência) e
    confere a estrutura de topo. Roda contra os arquivos reais do repo (leitura).
    """
    from laboratorio.ops import maestro

    monkeypatch.setattr(maestro, "append_metric_from_overview", lambda *a, **k: None)
    monkeypatch.setattr(maestro, "check_vps_service", lambda: True)
    monkeypatch.setattr(
        maestro,
        "_task_cadence",
        lambda ids: {
            "interval_min": 2, "minutes_since_last": None, "can_start_next": True,
            "next_start_in_min": 0, "last_task": None, "violation": False,
        },
    )

    snap = maestro.build_maestro_snapshot()

    for key in (
        "generated_at", "overview", "agents", "projects", "crms",
        "kanban", "leads", "logs", "delegations", "pending_tasks",
    ):
        assert key in snap, f"chave ausente: {key}"
    assert isinstance(snap["agents"], list) and len(snap["agents"]) == 6
    assert "system_online" in snap["overview"]
