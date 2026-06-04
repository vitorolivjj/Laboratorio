"""Testes da lógica pura das ferramentas (sem CrewAI).

Roda com pytest OU diretamente:
  PYTHONPATH=src python3 tests/test_stores.py
Opera sobre cópias temporárias dos arquivos reais — nunca toca no repo.
"""

from __future__ import annotations

import inspect
import os
import shutil
import sys
import tempfile
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

_REPO = Path(__file__).resolve().parents[2]

from laboratorio.ops import crm_lp_store, crm_store, markdown_io, memory_store  # noqa: E402
from laboratorio.ops import parsers, retrieval, task_kanban_api, tasks_store, usage  # noqa: E402
from laboratorio.evolution import propose as evolution_propose  # noqa: E402


def test_markdown_insert_helpers():
    text = "## Log\n\n### antigo\n- a\n"
    out = markdown_io.insert_after_heading(text, "## Log", "### novo\n- b\n")
    assert out.index("### novo") < out.index("### antigo"), "mais recente no topo"
    assert "## Log" in out

    text2 = "x\n<!-- MARK -->\n"
    out2 = markdown_io.insert_before_marker(text2, "<!-- MARK -->", "BLOCO")
    assert out2.index("BLOCO") < out2.index("<!-- MARK -->")


def test_crm_add_and_update(tmp: Path):
    crm = tmp / "leads.md"
    shutil.copy(_REPO / "crm" / "leads.md", crm)

    msg = crm_store.add_lead(
        nome="Maria Teste", contato="5511999", origem="indicacao",
        score="4", temperatura="quente", status="qualificado", path=crm,
    )
    assert "LEAD-001" in msg
    leads = parsers.parse_lead_sections(markdown_io.read_text(crm))
    assert any(l["id"] == "LEAD-001" and l["nome"] == "Maria Teste" for l in leads)

    crm_store.add_lead(nome="João Teste", path=crm)
    assert crm_store.next_lead_id(markdown_io.read_text(crm)) == "LEAD-003"

    upd = crm_store.update_lead_status("LEAD-001", "convertido", nota="fechou", path=crm)
    assert "convertido" in upd
    leads = parsers.parse_lead_sections(markdown_io.read_text(crm))
    maria = next(l for l in leads if l["id"] == "LEAD-001")
    assert maria["status"] == "convertido"

    bad = False
    try:
        crm_store.update_lead_status("LEAD-001", "estado_invalido", path=crm)
    except ValueError:
        bad = True
    assert bad, "status inválido deve falhar"


def test_crm_lp_add_and_update(tmp: Path):
    crm = tmp / "crm_landing_pintor.md"
    shutil.copy(_REPO / "crm" / "crm_landing_pintor.md", crm)
    expected_id = crm_lp_store.next_lead_id(markdown_io.read_text(crm))
    lead = crm_lp_store.add_lead_lp(
        nome="Pintor Teste FB",
        cidade="Viçosa — MG",
        status="prospectado",
        link_origem="https://facebook.com/teste",
        path=crm,
    )
    assert lead["id"] == expected_id
    assert "pintor-teste-fb" in lead["slug"]
    crm_lp_store.update_lead_lp(lead["id"], "pronto_pra_pagina", nota="3 fotos", path=crm)
    text = markdown_io.read_text(crm)
    assert "pronto_pra_pagina" in text
    assert crm_lp_store.slugify("João Silva!!!") == "joao-silva"


def test_tasks_create_and_move(tmp: Path):
    tasks_dir = tmp / "tasks"
    shutil.copytree(_REPO / "tasks", tasks_dir)

    new_id = tasks_store.next_task_id(tasks_dir)
    msg = tasks_store.create_task(
        titulo="Teste tool", objetivo="validar", agente="dev", tasks_dir=tasks_dir,
    )
    assert new_id in msg
    assert (tasks_dir / f"{new_id}.md").is_file(), "doc da TASK criado"
    assert new_id in parsers.parsers_count(tasks_dir / "backlog.md", "## Fila")

    # force=True pula o gate de briefing — aqui validamos o mecanismo de mover,
    # não o gate (o gate tem teste próprio em test_tasks_briefing_gate).
    move_msg = tasks_store.move_task(
        new_id, "executando", nota="começando", tasks_dir=tasks_dir, force=True
    )
    assert "executando" in move_msg
    assert new_id not in parsers.parsers_count(tasks_dir / "backlog.md", "## Fila")
    exec_ids = parsers.parsers_count(tasks_dir / "executando.md", "## Em andamento")
    assert new_id in exec_ids, f"{new_id} deve estar em executando: {exec_ids}"

    tasks_store.move_task("TASK-012", "aguardando", tasks_dir=tasks_dir)
    assert "TASK-012" in parsers.parsers_count(tasks_dir / "aguardando.md", "## Bloqueadas")


def test_tasks_briefing_gate(tmp: Path):
    """Mover para executando exige seção Briefing (ou force=True)."""
    tasks_dir = tmp / "tasks"
    shutil.copytree(_REPO / "tasks", tasks_dir)
    new_id = tasks_store.create_task(
        titulo="Gate test", agente="dev", tasks_dir=tasks_dir
    ).split()[0]

    blocked = False
    try:
        tasks_store.move_task(new_id, "executando", tasks_dir=tasks_dir)
    except ValueError as exc:
        blocked = "briefing" in str(exc).lower()
    assert blocked, "mover para executando sem briefing deve falhar"

    doc = tasks_dir / f"{new_id}.md"
    doc.write_text(
        markdown_io.read_text(doc) + "\n## Briefing\n\nObjetivo: x\n", encoding="utf-8"
    )
    msg = tasks_store.move_task(new_id, "executando", tasks_dir=tasks_dir)
    assert "executando" in msg


def test_memory_registrar(tmp: Path):
    dec = tmp / "decisoes.md"
    apr = tmp / "aprendizados.md"
    evt = tmp / "eventos.md"
    shutil.copy(_REPO / "memoria" / "decisoes.md", dec)
    shutil.copy(_REPO / "memoria" / "aprendizados.md", apr)
    shutil.copy(_REPO / "logs" / "eventos.md", evt)

    memory_store.registrar_decisao(titulo="Teste D", contexto="ctx", decisao="fazer X", path=dec)
    assert any(d["title"] == "Teste D" for d in parsers.parse_decisions(markdown_io.read_text(dec)))

    memory_store.registrar_aprendizado(titulo="Teste A", situacao="s", aprendizado="ap", path=apr)
    assert "Teste A" in markdown_io.read_text(apr)

    memory_store.registrar_evento(titulo="Teste E", tipo="marco", agentes="dev", path=evt)
    events = parsers.parse_event_blocks(markdown_io.read_text(evt))
    assert any(e["title"] == "Teste E" and e["type"] == "marco" for e in events)


def test_read_memory_real():
    assert memory_store.read_memory("contexto_global")
    failed = False
    try:
        memory_store.read_memory("inexistente_xyz")
    except ValueError:
        failed = True
    assert failed


def test_retrieval():
    text = (
        "Parágrafo sobre gatos e jardinagem.\n\n"
        "Bloco crítico: o deploy do servidor de produção usa nginx e systemd.\n\n"
        "Outro parágrafo sobre culinária e receitas.\n\n"
    ) * 30
    out = retrieval.relevant_excerpt(text, "deploy servidor produção nginx", max_chars=300)
    assert "deploy" in out.lower() and "nginx" in out.lower()
    assert len(out) <= 320
    assert retrieval.relevant_excerpt("curto", "qualquer", 2000) == "curto"


def test_usage(tmp: Path):
    usage.USAGE_FILE = tmp / "usage.jsonl"
    c = usage.estimate_cost("gpt-4o-mini", 1_000_000, 1_000_000)
    assert abs(c - (0.15 + 0.60)) < 1e-6, c
    usage.record_usage(source="t", model="gpt-4o-mini", prompt_tokens=1000, completion_tokens=500)
    usage.record_usage(
        source="t", model="claude-sonnet-4-6",
        metrics={"prompt_tokens": 200, "completion_tokens": 100},
    )
    s = usage.summarize()
    assert s["total_tokens"] == 1800, s
    assert s["total_cost_usd"] > 0
    assert "gpt-4o-mini" in s["by_model"]


def test_owner_detection():
    import importlib
    owner = importlib.import_module("laboratorio.whatsapp.owner")

    # Override por env (vários números).
    os.environ["OWNER_WA_IDS"] = "5511999998888, +55 11 77777-6666"
    try:
        assert owner.owner_ids() == {"5511999998888", "5511777776666"}
        assert owner.is_owner("5511999998888")
        assert owner.is_owner("+5511999998888")  # normaliza +
        assert owner.is_owner("55 11 77777-6666")  # normaliza espaços/traços
        assert not owner.is_owner("5511000000000")  # cliente comum
    finally:
        del os.environ["OWNER_WA_IDS"]

    # Sem env → usa o número default do Vitor.
    assert owner.owner_ids() == {"5533999353242"}
    assert owner.is_owner("+55 33 99935-3242")
    assert not owner.is_owner("5511000000000")

    # Desligado explicitamente → ninguém é dono.
    os.environ["OWNER_WA_IDS"] = "none"
    try:
        assert owner.owner_ids() == set()
        assert not owner.is_owner("5533999353242")
    finally:
        del os.environ["OWNER_WA_IDS"]

    # Detecção de ação vs consulta.
    assert owner._is_action("cria uma task de teste")
    assert owner._is_action("interrompe a TASK-012")
    assert not owner._is_action("qual o status?")


def test_task_kanban_api(tmp: Path):
    tasks_dir = tmp / "tasks"
    shutil.copytree(_REPO / "tasks", tasks_dir)

    board = task_kanban_api.build_kanban_board(tasks_dir=tasks_dir)
    assert "columns" in board
    assert "backlog" in board["columns"]

    created = task_kanban_api.create_task_api(
        titulo="API test", agente="dev", tasks_dir=tasks_dir
    )
    tid = created["task_id"]
    assert tid.startswith("TASK-")
    detail = task_kanban_api.get_task_detail(tid, tasks_dir=tasks_dir)
    assert detail["state"] == "backlog"

    task_kanban_api.move_task_api(tid, "planejando", tasks_dir=tasks_dir)
    detail2 = task_kanban_api.get_task_detail(tid, tasks_dir=tasks_dir)
    assert detail2["state"] == "planejando"


def test_evolution_propose_queue(tmp: Path):
    evolution_propose.QUEUE_FILE = tmp / "evolution_proposals_queue.jsonl"
    entry = evolution_propose.queue_proposal(
        title="Teste", body="Mudar fluxo X", target="aprendizados"
    )
    assert entry["id"] == 1
    pending = evolution_propose.list_pending_proposals()
    assert len(pending) == 1
    ack = evolution_propose.format_proposal_ack(entry)
    assert f"#{entry['id']}" in ack and "autoevolução" in ack


def test_parsers_count_distinct_lp_pintor_suffix(tmp: Path):
    backlog = tmp / "backlog.md"
    backlog.write_text(
        "## Fila\n\n"
        "### LP-PINTOR-001B — lote 2\n- x\n"
        "### LP-PINTOR-009 — produção\n- y\n",
        encoding="utf-8",
    )
    ids = parsers.parsers_count(backlog, "## Fila")
    assert ids == ["LP-PINTOR-001B", "LP-PINTOR-009"]
    assert "LP-PINTOR-001" not in ids


# pytest: expõe a fixture `tmp` se pytest estiver instalado
try:
    import pytest as _pt

    @_pt.fixture
    def tmp(tmp_path):
        return tmp_path
except ImportError:
    pass


def _run_all() -> int:
    fns = [
        v for k, v in sorted(globals().items())
        if k.startswith("test_") and inspect.isfunction(v)
    ]
    for fn in fns:
        if "tmp" in inspect.signature(fn).parameters:
            with tempfile.TemporaryDirectory() as d:
                fn(Path(d))
        else:
            fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)}/{len(fns)} testes passaram.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_run_all())
