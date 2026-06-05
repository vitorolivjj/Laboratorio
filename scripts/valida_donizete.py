#!/usr/bin/env python3
"""Valida o fix de dedup: captura curta TRAVADA num grupo fixo, conta duplicatas.

Não cria task (evita a resolução por-task virar rotativo). Aborta se não travar
no grupo. Esperado pós-fix: cada perfil capturado 1× (DUPLICATAS=0) e o contador
leads_captured batendo com os novos leads.
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
from laboratorio.config import REPO_ROOT, load_env  # noqa: E402

load_env()
from laboratorio.ops import donizete_runner as dr  # noqa: E402
from laboratorio.ops import parsers  # noqa: E402

GROUP = "https://www.facebook.com/groups/1726982011023476"
DURATION = int(os.getenv("DUR", "360"))
INTERVAL = int(os.getenv("ITV", "60"))
LOG = REPO_ROOT / "logs" / "valida_donizete.log"
CRM = REPO_ROOT / "crm" / "crm_landing_pintor.md"


def log(m: str) -> None:
    line = f"[{datetime.now().strftime('%H:%M:%S')}] {m}"
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def _norm_phone(v: str) -> str:
    import re
    d = re.sub(r"\D", "", str(v or ""))
    return d if len(d) >= 8 else ""


def leads() -> dict:
    """{lead_id: (nome, telefone_normalizado)}."""
    try:
        return {
            x["id"]: (x["nome"], _norm_phone(x.get("contato", "")))
            for x in parsers.parse_crm_segment(CRM.read_text(encoding="utf-8")).get("leads", [])
        }
    except Exception:  # noqa: BLE001
        return {}


def main() -> int:
    LOG.write_text("", encoding="utf-8")
    log(f"=== VALIDAÇÃO DEDUP · grupo fixo {GROUP} ===")
    # estado/sessão limpos
    for f, keys in [
        ("logs/donizete_busca_state.json", ("cycles", "leads_captured", "lock_group_url", "last_group", "active_task_id")),
        ("logs/donizete_fb_session.json", ("captured_leads", "analyzed_profiles", "visited_groups")),
    ]:
        p = REPO_ROOT / f
        try:
            d = json.load(open(p))
        except Exception:  # noqa: BLE001
            d = {}
        for k in keys:
            d.pop(k, None)
        if "busca" in f:
            d["running"] = False
        json.dump(d, open(p, "w"), indent=2, ensure_ascii=False)

    before = leads()
    log(f"Leads antes: {len(before)}")
    msg = dr.start_busca(group_url=GROUP, allow_arm_without_cdp=False, skip_validation=True)
    log(f"start → {(msg or '?').splitlines()[0]}")
    time.sleep(2)
    st = json.load(open(REPO_ROOT / "logs" / "donizete_busca_state.json"))
    log(f"lock: {st.get('lock_group_url','—')} · modo: {st.get('modo','—')}")
    if "1726982011023476" not in str(st.get("lock_group_url", "")):
        log("❌ NÃO travou no grupo certo — abortando.")
        dr.stop_busca()
        return 1
    if not dr.is_running():
        log("❌ busca não ficou ativa — abortando.")
        return 1
    log("Busca ATIVA travada no grupo. Monitorando…")

    state_path = REPO_ROOT / "logs" / "donizete_busca_state.json"
    phone_dedup_hits: set[str] = set()  # linhas únicas "dedup telefone" vistas

    def scan_dedup() -> None:
        try:
            summ = json.load(open(state_path)).get("last_summary", "")
        except Exception:  # noqa: BLE001
            return
        for ln in summ.splitlines():
            if "dedup telefone" in ln.lower():
                phone_dedup_hits.add(ln.strip())

    t0 = time.time()
    while time.time() - t0 < DURATION:
        time.sleep(INTERVAL)
        scan_dedup()
        snap = dr.busca_snapshot_for_panel()
        log(f"+{int((time.time()-t0)/60)}min · ciclos={snap.get('cycles','?')} "
            f"· contador={snap.get('leads_captured','?')} · leads_crm={len(leads())} "
            f"· dedup_tel={len(phone_dedup_hits)}")
        if not dr.is_running():
            log("busca parou sozinha")
            break

    log("stop: " + dr.stop_busca().splitlines()[0])
    scan_dedup()
    after = leads()
    new_ids = set(after) - set(before)
    new = [(i, *after[i]) for i in new_ids]  # (id, nome, telefone)
    names = {n.strip().lower() for _, n, _ in new}
    phones = [p for _, _, p in new if p]
    name_dupes = len(new) - len(names)
    phone_dupes = len(phones) - len(set(phones))  # mesmo telefone 2× entre novos = falha
    log("=== RESULTADO ===")
    log(f"novos={len(new)} · nomes únicos={len(names)} · dup_nome={name_dupes} "
        f"· telefones={len(phones)} · únicos={len(set(phones))} · DUP_TELEFONE={phone_dupes}")
    for i, n, p in sorted(new):
        log(f"   {i}: {n[:30]:<30} tel={p or '—'}")
    if phone_dedup_hits:
        log(f"dedup-telefone disparou {len(phone_dedup_hits)}× ao vivo:")
        for h in sorted(phone_dedup_hits):
            log(f"   · {h[:90]}")
    snap = dr.busca_snapshot_for_panel()
    log(f"ciclos={snap.get('cycles','?')} · contador leads_captured={snap.get('leads_captured','?')}")
    ok = phone_dupes == 0 and name_dupes == 0
    log("VEREDITO: " + (
        "✅ DEDUP OK (0 dup nome, 0 dup telefone)" if ok
        else f"❌ FALHA (dup_nome={name_dupes}, dup_telefone={phone_dupes})"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
