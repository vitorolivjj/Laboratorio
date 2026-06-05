#!/usr/bin/env python3
"""Teste operacional: captura intermitente do Donizete num grupo fixo por 30 min.

Cria TESTE-001-DONIZETE, inicia a busca no grupo, monitora 30 min (log a cada 2 min),
para o Donizete e analisa (leads capturados no CRM LP). Roda como processo único.
"""
from __future__ import annotations

import os
import sys
import time
from datetime import datetime
from pathlib import Path

_B = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(_B / "src"))
os.environ.setdefault("DONIZETE_FB_ENABLED", "1")

from laboratorio.config import REPO_ROOT, TASKS_DIR, load_env  # noqa: E402

load_env()
from laboratorio.ops import donizete_runner as dr  # noqa: E402
from laboratorio.ops import parsers  # noqa: E402
from laboratorio.ops.markdown_io import insert_after_heading, read_text, write_text_atomic  # noqa: E402

GROUP = "https://www.facebook.com/groups/1726982011023476"
TASK_ID = "TESTE-001-DONIZETE"
DURATION = int(os.getenv("TESTE_DURATION_S", str(30 * 60)))
INTERVAL = int(os.getenv("TESTE_INTERVAL_S", "120"))
LOG = REPO_ROOT / "logs" / "teste_donizete.log"
CRM_LP = REPO_ROOT / "crm" / "crm_landing_pintor.md"


def log(msg: str) -> None:
    line = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    try:
        with LOG.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def lead_count() -> int:
    try:
        return parsers.parse_crm_segment(read_text(CRM_LP)).get("total", -1)
    except Exception:  # noqa: BLE001
        return -1


def lead_set() -> set:
    try:
        return {(x["id"], x["nome"]) for x in parsers.parse_crm_segment(read_text(CRM_LP)).get("leads", [])}
    except Exception:  # noqa: BLE001
        return set()


def main() -> int:
    LOG.write_text("", encoding="utf-8")
    log(f"=== TESTE DONIZETE · {TASK_ID} · grupo {GROUP} ===")

    # 1. task no kanban
    doc = (
        f"# {TASK_ID} — Teste de captura Donizete (grupo fixo)\n\n"
        "## Metadados\n\n| Campo | Valor |\n|-------|-------|\n"
        f"| **ID** | {TASK_ID} |\n| **Status** | executando |\n"
        "| **Agente responsável** | donizete_social |\n\n"
        f"## Captura\n\n- **modo:** grupo_fixo\n- **group_url:** {GROUP}\n\n"
        "## Objetivo\n\nTeste intermitente de captação no grupo fixo por 30 min.\n"
    )
    write_text_atomic(TASKS_DIR / f"{TASK_ID}.md", doc)
    block = (
        f"### {TASK_ID} — Teste captura Donizete\n"
        "- **Agente:** donizete_social\n- **Status:** executando\n"
        f"- **Próxima ação:** captação intermitente no grupo fixo\n- **Bloqueio:** —\n"
    )
    try:
        em = TASKS_DIR / "executando.md"
        write_text_atomic(em, insert_after_heading(read_text(em), "## Em andamento", block))
        log(f"Task {TASK_ID} criada em executando.")
    except Exception as exc:  # noqa: BLE001
        log(f"(aviso: não inseriu no kanban: {exc})")

    before = lead_count()
    before_set = lead_set()
    log(f"Leads CRM LP antes: {before}")

    # 2. inicia a busca
    msg = dr.start_busca(task_id=TASK_ID, group_url=GROUP, allow_arm_without_cdp=False, skip_validation=True)
    log(f"start_busca → {(msg or '?').splitlines()[0]}")
    time.sleep(3)
    if not dr.is_running():
        log("ERRO: thread da busca não ficou ativa. Abortando teste.")
        log(dr.status_line())
        return 1
    log("Busca ATIVA — monitorando por 30 min (log a cada 2 min).")

    # 3. monitora 30 min
    t0 = time.time()
    while time.time() - t0 < DURATION:
        time.sleep(INTERVAL)
        snap = {}
        try:
            snap = dr.busca_snapshot_for_panel()
        except Exception as exc:  # noqa: BLE001
            log(f"(snap err: {exc})")
        mins = int((time.time() - t0) / 60)
        log(
            f"+{mins:>2}min · running={dr.is_running()} · ciclos={snap.get('cycles','?')} "
            f"· leads_busca={snap.get('leads_captured','?')} · leads_crm={lead_count()}"
        )
        if not dr.is_running():
            log("Busca parou sozinha — encerrando monitor.")
            break

    # 4. para
    log("Tempo esgotado — parando o Donizete…")
    try:
        log("stop: " + dr.stop_busca().splitlines()[0])
    except Exception as exc:  # noqa: BLE001
        log(f"(stop err: {exc})")

    # 5. análise
    after = lead_count()
    new = lead_set() - before_set
    names = {n.strip().lower() for _, n in new}
    dupes = len(new) - len(names)
    log("=== ANÁLISE ===")
    log(f"Leads novos: {len(new)} · nomes ÚNICOS: {len(names)} · DUPLICATAS: {dupes}  (antes={before} depois={after})")
    for lid, nome in sorted(new):
        log(f"   {lid}: {nome[:34]}")
    try:
        fin = dr.busca_snapshot_for_panel()
        log(f"Ciclos: {fin.get('cycles','?')} · contador leads_captured: {fin.get('leads_captured','?')} "
            f"· último erro: {fin.get('last_error') or '—'}")
    except Exception as exc:  # noqa: BLE001
        log(f"(snap final err: {exc})")
    veredito = "✅ DEDUP OK (sem duplicatas)" if dupes == 0 else f"❌ AINDA DUPLICA ({dupes})"
    log(f"VEREDITO: {veredito}")
    log("FIM.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
