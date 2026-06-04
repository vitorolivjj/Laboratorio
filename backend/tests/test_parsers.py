"""Testes de caracterização do parsing markdown (ops/parsers.py).

Travam o comportamento ATUAL antes da deduplicação dos extratores de campo
(Fase 1). Se o refactor preservar o comportamento, estes testes seguem verdes.
Funções puras, sem efeito colateral em disco.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from laboratorio.ops import parsers  # noqa: E402


def test_parse_event_blocks():
    md = (
        "## Log\n\n"
        "### 2026-06-01 10:00 — [marco] Lancamento do painel\n"
        "- **Agente(s):** dev · loide\n"
        "- **Detalhe:** subiu o painel novo\n"
        "- **Ref:** TASK-001\n"
        "- **Status:** aberto\n\n"
        "### 2026-06-01 09:00 — [erro] Falha no webhook\n"
        "- **Agente(s):** caio_manteiga\n"
        "- **Detalhe:** timeout\n"
        "- **Status:** resolvido\n"
    )
    events = parsers.parse_event_blocks(md)
    assert len(events) == 2
    e0 = events[0]
    assert e0["datetime"] == "2026-06-01 10:00"
    assert e0["type"] == "marco"
    assert e0["title"] == "Lancamento do painel"
    assert e0["agents"] == "dev · loide"
    assert e0["detail"] == "subiu o painel novo"
    assert e0["ref"] == "TASK-001"
    # erro com status resolvido vira tipo "resolvido"
    assert events[1]["type"] == "resolvido"
    assert not parsers.event_is_open_error(events[1])


def test_parse_whatsapp_log():
    md = (
        "### 2026-06-01 12:00 UTC — 5511999998888\n"
        "- **inbound:** oi\n"
        "- **outbound:** ola, tudo bem?\n"
        "- **status:** ok\n"
        "- **message_id:** `wamid.ABC`\n"
    )
    log = parsers.parse_whatsapp_log(md)
    assert len(log) == 1
    row = log[0]
    assert row["phone"] == "5511999998888"
    assert row["inbound"] == "oi"
    assert row["outbound"] == "ola, tudo bem?"
    assert row["status"] == "ok"
    assert row["message_id"] == "wamid.ABC"  # crases removidas


def test_parse_executando_tasks():
    md = (
        "## Em andamento\n\n"
        "### TASK-042 — Implementar X\n"
        "- **Agente:** dev\n"
        "- **Auxiliares:** loide\n"
        "- **Status:** em_progresso\n"
        "- **Projeto:** PROJ-001\n"
        "- **Próxima ação:** escrever o teste\n"
        "- **Bloqueio:** —\n"
        "- **Entregáveis:** código + teste\n"
    )
    tasks = parsers.parse_executando_tasks(md)
    assert len(tasks) == 1
    t = tasks[0]
    assert t["id"] == "TASK-042"
    assert t["title"] == "Implementar X"
    assert t["agents"] == "dev · loide"  # agente + auxiliares juntos
    assert t["proxima_acao"] == "escrever o teste"
    assert t["projeto"] == "PROJ-001"
    assert t["entregaveis"] == "código + teste"


def test_parse_decisions():
    md = (
        "## Decisões\n\n"
        "### Migrar para Postgres — 2026-06-01\n"
        "Vamos usar o Supabase existente.\n\n"
        "### Manter markdown como export — 2026-05-30\n"
        "Híbrido: banco fonte da verdade.\n"
    )
    decs = parsers.parse_decisions(md)
    assert len(decs) == 2
    assert decs[0]["title"] == "Migrar para Postgres"
    assert decs[0]["date"] == "2026-06-01"
    assert "Supabase" in decs[0]["body"]


def test_parse_crm_leads_sections():
    md = (
        "## LEAD-007 — João Pintor\n"
        "| Campo | Valor |\n"
        "|---|---|\n"
        "| **Nome** | João Pintor |\n"
        "| **Cidade** | São Paulo |\n"
        "| **Serviço** | pintura residencial |\n"
        "| **Status** | `prospectado` |\n"
        "| **Score** | 4 |\n"
    )
    leads = parsers.parse_crm_leads(md)
    assert len(leads) == 1
    lead = leads[0]
    assert lead["id"] == "LEAD-007"
    assert lead["nome"] == "João Pintor"
    assert lead["cidade"] == "São Paulo"
    assert lead["status"] == "prospectado"  # crases removidas
    assert lead["score"] == "4"


def test_parse_projects_and_resolve_task():
    md = (
        "## Projetos\n\n"
        "### Landing Pintor\n"
        "- **ID:** PROJ-002\n"
        "- **Prefixo:** LP-PINTOR\n"
        "- **Natureza:** comercial\n"
        "- **Status:** ativo\n"
        "- **Legado:** TASK-010 a TASK-012\n"
    )
    projs = parsers.parse_projects_registry(md)
    assert len(projs) == 1
    assert projs[0]["id"] == "PROJ-002"
    assert projs[0]["prefix"] == "LP-PINTOR"

    # Resolução por prefixo do ID da task
    p = parsers.project_for_task({"id": "LP-PINTOR-005"}, projs)
    assert p and p["id"] == "PROJ-002"

    # Resolução por faixa de legado (TASK-011 está em 010..012)
    p2 = parsers.project_for_task({"id": "TASK-011"}, projs)
    assert p2 and p2["id"] == "PROJ-002"

    # Task sem vínculo → None
    assert parsers.project_for_task({"id": "ZZZ-999"}, projs) is None


def test_group_whatsapp_threads_and_count_today():
    rows = [
        {"phone": "111", "inbound": "a", "outbound": "b", "datetime": "2026-06-01 10:00 UTC", "status": "ok"},
        {"phone": "111", "inbound": "c", "outbound": "d", "datetime": "2026-06-01 11:00 UTC", "status": "ok"},
        {"phone": "222", "inbound": "e", "outbound": "f", "datetime": "2026-06-01 09:00 UTC", "status": "ok"},
    ]
    threads = parsers.group_whatsapp_threads(rows)
    assert len(threads) == 2
    by_phone = {t["phone"]: t for t in threads}
    assert by_phone["111"]["message_count"] == 2
