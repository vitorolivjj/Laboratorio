#!/usr/bin/env python3
"""Captura ROTATIVA (Donizete escolhe os grupos) com scroll profundo + observação.

Observa, a cada ciclo: leads novos, grupos visitados, e quantos foram capturados
VIA PERFIL (stalk → salva imagens) vs SEM-URL (sem imagem). Serve pra calibrar a
melhoria de visita de perfil + scroll de posts antigos.
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

_B = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(_B / "src"))
os.environ.setdefault("DONIZETE_FB_ENABLED", "1")
os.environ.setdefault("FB_NAV_SCROLL_PASSES", "24")  # scroll profundo → posts antigos
from laboratorio.config import REPO_ROOT, load_env  # noqa: E402

load_env()
from laboratorio.ops import donizete_runner as dr  # noqa: E402
from laboratorio.ops import parsers  # noqa: E402

DURATION = int(os.getenv("DUR", "1200"))
INTERVAL = int(os.getenv("ITV", "120"))
LOG = REPO_ROOT / "logs" / "captura_rotativa.log"
CRM = REPO_ROOT / "crm" / "crm_landing_pintor.md"
STATE = REPO_ROOT / "logs" / "donizete_busca_state.json"


def log(m: str) -> None:
    line = f"[{datetime.now().strftime('%H:%M:%S')}] {m}"
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def leads() -> dict:
    try:
        return {x["id"]: x for x in parsers.parse_crm_segment(CRM.read_text(encoding="utf-8")).get("leads", [])}
    except Exception:  # noqa: BLE001
        return {}


def main() -> int:
    LOG.write_text("", encoding="utf-8")
    log("=== CAPTURA ROTATIVA · scroll profundo (24) · observação ===")
    try:
        d = json.load(open(STATE))
        for k in ("cycles", "leads_captured", "lock_group_url", "last_group", "active_task_id", "last_summary"):
            d.pop(k, None)
        d["running"] = False
        json.dump(d, open(STATE, "w"), indent=2, ensure_ascii=False)
    except Exception:  # noqa: BLE001
        pass

    before = leads()
    log(f"Leads antes: {len(before)}")
    msg = dr.start_busca(allow_arm_without_cdp=False, skip_validation=True)  # SEM grupo = rotativo
    log(f"start → {(msg or '?').splitlines()[0]}")
    time.sleep(2)
    if not dr.is_running():
        log("❌ busca não ativou — abortando.")
        return 1
    log("Busca ATIVA (rotativo). Monitorando…")

    stalk_hits, nourl_hits, img_hits, groups_seen = set(), set(), set(), set()

    def scan() -> None:
        try:
            summ = json.load(open(STATE)).get("last_summary", "")
        except Exception:  # noqa: BLE001
            return
        for ln in summ.splitlines():
            s = ln.strip()
            if "Grupo" in s and "http" in s:
                groups_seen.add(s[:90])
            if "Stalk LEAD-" in s:
                stalk_hits.add(s[:90])
            if "sem URL perfil" in s:
                nourl_hits.add(s[:90])
            if "foto" in s.lower() and "salva" in s.lower():
                img_hits.add(s[:90])

    t0 = time.time()
    while time.time() - t0 < DURATION:
        time.sleep(INTERVAL)
        scan()
        snap = dr.busca_snapshot_for_panel()
        log(f"+{int((time.time()-t0)/60):>2}min · ciclos={snap.get('cycles','?')} "
            f"· contador={snap.get('leads_captured','?')} · leads_crm={len(leads())} "
            f"· via_perfil={len(stalk_hits)} · sem_url={len(nourl_hits)} · imgs={len(img_hits)} "
            f"· grupos={len(groups_seen)}")
        if not dr.is_running():
            log("busca parou sozinha")
            break

    log("stop: " + dr.stop_busca().splitlines()[0])
    scan()
    after = leads()
    new_ids = sorted(set(after) - set(before))
    log("=== RESULTADO ===")
    log(f"leads NOVOS: {len(new_ids)}")
    for i in new_ids:
        x = after[i]
        log(f"   {i}: {x['nome'][:26]:<26} · {x.get('cidade', '')[:14]} · tel={x.get('contato', '—')}")
    log(f"via PERFIL (stalk → c/ imagens): {len(stalk_hits)}")
    for h in sorted(stalk_hits):
        log(f"   {h}")
    log(f"imagens de post salvas: {len(img_hits)}")
    for h in sorted(img_hits):
        log(f"   {h}")
    log(f"SEM perfil (sem imagem): {len(nourl_hits)}")
    log(f"grupos visitados: {len(groups_seen)}")
    for g in sorted(groups_seen):
        log(f"   {g}")
    log("FIM")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
