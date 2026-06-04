"""Busca intermitente Donizete — loop em background (WhatsApp Play/Stop)."""

from __future__ import annotations

import json
import logging
import os
import random
import re
import threading
import time
from datetime import datetime, timezone

from laboratorio.config import LOGS_DIR
from laboratorio.ops.donizete_capture_task import find_capture_tasks_in_kanban, load_capture_config
from laboratorio.ops.donizete_task_standby import pause_executando_for_busca, resume_standby_tasks
from laboratorio.social import cycle, facebook_cdp
from laboratorio.social import session as fb_session
from laboratorio.social.groups import FbGroup, group_from_url

logger = logging.getLogger("laboratorio.donizete_runner")

BUSCA_STATE = LOGS_DIR / "donizete_busca_state.json"
# Canal WhatsApp PlayDonizete — independente de kanban, cadência, WIP e autopilot.
INDEPENDENT_MODE = True
_stop = threading.Event()
_thread: threading.Thread | None = None
_lock = threading.Lock()


def _parse_iso(ts: str) -> datetime | None:
    if not ts or ts == "—":
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


def _last_cycle_recent(st: dict, *, minutes: int = 20) -> bool:
    """True se houve ciclo recente (Mac grava estado sem thread na VPS)."""
    at = _parse_iso(st.get("last_cycle_at") or "")
    if not at:
        return False
    if at.tzinfo is None:
        at = at.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - at).total_seconds() < minutes * 60


def capture_active() -> bool:
    """Busca ativa: thread local, estado recente no JSON ou sessão FB."""
    if is_running():
        return True
    st = _load_busca_state()
    if bool(st.get("armed_vps")):
        return True
    if st.get("running") and _last_cycle_recent(st):
        return True
    try:
        return bool(fb_session.load_session().get("busca_ativa"))
    except Exception:
        return False


def busca_ativa() -> bool:
    """Alias — prioridade sobre autopilot Donizete."""
    return capture_active()


def _mac_stale_armed(st: dict, *, minutes: int = 3) -> bool:
    """VPS armada sem thread local e sem ciclo Mac recente no JSON."""
    if not st.get("armed_vps") or is_running():
        return False
    if _last_cycle_recent(st, minutes=minutes):
        return False
    return True


def mac_hint_from_snapshot(snap: dict) -> str:
    if snap.get("mac_stale_armed"):
        return (
            "⚠️ Mac sem ciclo há 3+ min — rode no Mac:\n"
            "  ./scripts/donizete-mac-executor.sh --watch"
        )
    if snap.get("mac_should_run") or snap.get("armed_vps"):
        return (
            "No Mac: ./scripts/donizete-mac-executor.sh --watch\n"
            "(ou ./run.sh donizete-mac-prepare + donizete-busca-local)"
        )
    return ""


def busca_snapshot_for_panel() -> dict:
    """Estado da busca para painel Maestro / API (lê logs/donizete_busca_state.json)."""
    st = _load_busca_state()
    active = capture_active()
    standby = st.get("standby_tasks") or []
    modo = st.get("modo") or "—"
    if active and modo in ("—", "parado"):
        modo = "independente"
    source = "vps_thread" if is_running() else (
        "mac_state" if st.get("running") and _last_cycle_recent(st) else (
            "armed" if st.get("armed_vps") else "idle"
        )
    )
    stale_running = (
        bool(st.get("running")) and not _last_cycle_recent(st, minutes=25) and not is_running()
    )
    mac_stale = _mac_stale_armed(st, minutes=3)
    stale = stale_running or mac_stale
    mac_stale_zero = mac_stale and int(st.get("cycles") or 0) == 0
    return {
        "active": active,
        "source": source,
        "stale_warning": stale,
        "mac_stale_armed": mac_stale_zero,
        "mac_should_run": bool(st.get("armed_vps")) or active,
        "modo": modo,
        "active_task_id": st.get("active_task_id") or "",
        "lock_group_url": st.get("lock_group_url") or "",
        "last_group": (st.get("last_group") or "—")[:80],
        "cycles": int(st.get("cycles") or 0),
        "leads_captured": int(st.get("leads_captured") or 0),
        "last_cycle_at": st.get("last_cycle_at") or "—",
        "last_error": (st.get("last_error") or "")[:120],
        "standby_tasks": standby,
        "armed_vps": bool(st.get("armed_vps")),
        "mac_hint": mac_hint_from_snapshot(
            {
                "armed_vps": bool(st.get("armed_vps")),
                "mac_should_run": bool(st.get("armed_vps")) or active,
                "mac_stale_armed": mac_stale_zero,
            }
        ),
        "summary": (
            f"{'▶️' if active else '⏹'} Busca · {modo} · {int(st.get('cycles') or 0)} ciclos"
            + (f" · {st.get('active_task_id')}" if st.get("active_task_id") else "")
            + (f" · standby {', '.join(standby)}" if standby else "")
        ),
    }


def blocks_autopilot_for_task(task_id: str, agent_id: str) -> bool:
    """Autopilot não compete com a busca WhatsApp na TASK ativa."""
    if not busca_ativa():
        return False
    st = _load_busca_state()
    active = (st.get("active_task_id") or "").upper()
    if active and task_id.upper() == active:
        return True
    if agent_id == "donizete_social" and active:
        return task_id.upper() == active
    return False


def _resolve_capture_config(
    *,
    task_id: str | None = None,
    group_url: str | None = None,
) -> dict:
    """Monta config da sessão: task_id, lock_group_url, modo."""
    cfg: dict = {
        "active_task_id": "",
        "lock_group_url": "",
        "lock_group_name": "",
        "lock_group": False,
        "modo": "rotativo",
    }
    tid = (task_id or "").strip().upper()
    if tid:
        tc = load_capture_config(tid)
        if tc:
            cfg["active_task_id"] = tid
            if tc.get("group_url"):
                cfg["lock_group_url"] = tc["group_url"]
                cfg["lock_group_name"] = tc.get("titulo") or tid
                cfg["lock_group"] = True
                cfg["modo"] = "grupo_fixo"
        else:
            cfg["active_task_id"] = tid

    if group_url:
        from laboratorio.ops.donizete_capture_task import normalize_group_url

        cfg["lock_group_url"] = normalize_group_url(group_url)
        cfg["lock_group"] = True
        cfg["modo"] = "grupo_fixo"

    return cfg


def _fixed_group_from_state(st: dict) -> FbGroup | None:
    url = (st.get("lock_group_url") or "").strip()
    if not url:
        return None
    return group_from_url(url, name=st.get("lock_group_name") or st.get("active_task_id") or "")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _pause_bounds() -> tuple[int, int]:
    lo = max(60, int(os.getenv("DONIZETE_BUSCA_PAUSE_MIN_SEC", "120")))
    hi = max(lo, int(os.getenv("DONIZETE_BUSCA_PAUSE_MAX_SEC", "300")))
    return lo, hi


def _load_busca_state() -> dict:
    if not BUSCA_STATE.is_file():
        return {}
    try:
        return json.loads(BUSCA_STATE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _save_busca_state(data: dict) -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    data["updated_at"] = _now_iso()
    BUSCA_STATE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    _maybe_push_state_to_vps(data)


def _push_payload_from_state(data: dict) -> dict:
    """Payload completo para VPS — inclui grupo fixo; Mac sempre desarma VPS."""
    return {
        "cycles": int(data.get("cycles") or 0),
        "leads_captured": int(data.get("leads_captured") or 0),
        "running": bool(data.get("running")),
        "modo": data.get("modo") or "",
        "active_task_id": data.get("active_task_id") or "",
        "lock_group_url": data.get("lock_group_url") or "",
        "last_group": data.get("last_group") or "",
        "last_cycle_at": data.get("last_cycle_at") or "",
        "last_error": (data.get("last_error") or "")[:200],
        "standby_tasks": data.get("standby_tasks") or [],
        "armed_vps": False,
    }


def _maybe_push_state_to_vps(data: dict) -> None:
    """Mac envia estado para VPS (painel lê o mesmo JSON que o executor)."""
    url = os.getenv("DONIZETE_STATE_PUSH_URL", "").strip()
    if not url:
        return
    token = os.getenv("DONIZETE_STATE_PUSH_TOKEN", "").strip()
    payload = _push_payload_from_state(data)
    try:
        import httpx

        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        resp = httpx.post(url, json=payload, headers=headers, timeout=12.0)
        if resp.status_code >= 400:
            logger.warning(
                "Push estado busca VPS HTTP %s: %s",
                resp.status_code,
                (resp.text or "")[:200],
            )
        else:
            logger.info(
                "Push busca VPS OK · ciclos=%s · task=%s",
                payload.get("cycles"),
                payload.get("active_task_id") or "—",
            )
    except Exception as exc:
        logger.warning("Push estado busca VPS falhou (%s): %s", url, exc)


def is_running() -> bool:
    return _thread is not None and _thread.is_alive() and not _stop.is_set()


def status_line() -> str:
    st = _load_busca_state()
    running = capture_active()
    cycles = int(st.get("cycles") or 0)
    leads = int(st.get("leads_captured") or 0)
    last = st.get("last_cycle_at") or "—"
    grupo = st.get("last_group") or "—"
    err = st.get("last_error") or ""
    modo = st.get("modo") or ("independente" if running else "—")
    standby = st.get("standby_tasks") or []
    task_id = st.get("active_task_id") or "—"
    lock_url = st.get("lock_group_url") or ""
    lines = [
        f"Busca Donizete: {'▶️ ATIVA' if running else '⏹ PARADA'} · {modo}",
        f"TASK: {task_id}",
    ]
    if lock_url:
        lines.append(f"Grupo fixo: {lock_url[:72]}")
    lines.append(f"TASK standby: {', '.join(standby) if standby else '—'}")
    lines.append("Independente: cadência/WIP/autopilot não bloqueiam PlayDonizete")
    lines.extend(
        [
            f"Ciclos: {cycles} · Leads capturados (sessão): {leads}",
            f"Último ciclo: {last}",
            f"Último grupo: {grupo[:60]}",
        ]
    )
    if err:
        lines.append(f"Último erro: {err[:120]}")
    lo, hi = _pause_bounds()
    lines.append(f"Pausa entre ciclos: {lo}–{hi}s (scroll lento)")
    lines.append("Criar: Criar captura <url> · PlayDonizete TASK · StopDonizete")
    return "\n".join(lines)


def _maybe_notify_vitor(summary: str) -> None:
    if not re.search(r"Lead LEAD-\d+ criado|pronto_pra_pagina|status=pronto", summary, re.I):
        return
    try:
        from laboratorio.whatsapp.notify import notify_vitor

        snippet = summary[:600]
        notify_vitor(f"🎯 Donizete capturou lead\n\n{snippet}")
    except Exception as exc:
        logger.warning("Notify Vitor falhou: %s", exc)


def _run_loop() -> None:
    global _thread
    st = _load_busca_state()
    st["started_at"] = _now_iso()
    st["running"] = True
    st.pop("stopped_at", None)
    st["armed_vps"] = False
    _save_busca_state(st)

    while not _stop.is_set():
        summary = ""
        try:
            if not facebook_cdp.facebook_available():
                raise RuntimeError("Chrome CDP offline — abra facebook-cdp-mac.sh")

            st = _load_busca_state()
            fixed = _fixed_group_from_state(st)
            summary = cycle.run_navigation_cycle(max_leads=1, fixed_group=fixed)
            st = _load_busca_state()
            st["cycles"] = int(st.get("cycles") or 0) + 1
            st["last_cycle_at"] = _now_iso()
            st["last_summary"] = summary[:2000]
            m = re.search(r"Grupo (?:fixo|escolhido): (.+)", summary)
            if m:
                st["last_group"] = m.group(1).strip()
            if "Lead LEAD-" in summary:
                st["leads_captured"] = int(st.get("leads_captured") or 0) + 1
                _maybe_notify_vitor(summary)
            st["last_error"] = ""
            _save_busca_state(st)
            logger.info("Donizete busca ciclo %s OK", st["cycles"])
        except Exception as exc:
            logger.warning("Donizete busca ciclo falhou: %s", exc)
            st = _load_busca_state()
            st["last_error"] = str(exc)[:300]
            _save_busca_state(st)

        if _stop.is_set():
            break

        lo, hi = _pause_bounds()
        wait = random.randint(lo, hi)
        logger.info("Donizete busca pausa %ss", wait)
        if _stop.wait(timeout=wait):
            break

    st = _load_busca_state()
    st["running"] = False
    st["stopped_at"] = _now_iso()
    _save_busca_state(st)
    _thread = None


def _arm_busca_without_thread(
    *,
    task_id: str | None = None,
    group_url: str | None = None,
) -> str:
    """VPS sem CDP: prepara standby + estado; ciclos rodam no Mac (`donizete-busca-local`)."""
    cap = _resolve_capture_config(task_id=task_id, group_url=group_url)
    st = _load_busca_state()
    prev_tid = (st.get("active_task_id") or "").upper()
    new_tid = (cap.get("active_task_id") or "").upper()
    keep_metrics = (
        new_tid
        and new_tid == prev_tid
        and int(st.get("cycles") or 0) > 0
        and _last_cycle_recent(st, minutes=45)
    )
    if not keep_metrics:
        st["cycles"] = 0
        st["leads_captured"] = 0
    st["last_error"] = ""
    st["modo"] = "aguardando_mac"
    st["armed_vps"] = True
    st["running"] = False
    st.update(cap)
    st["ignora"] = [
        "task_cadence",
        "wip_soft_max",
        "autopilot_donizete",
        "prioridade_kanban",
        "cooldown_autopilot",
    ]
    tid = cap.get("active_task_id") or None
    st["standby_tasks"] = pause_executando_for_busca(task_id=tid)
    data = fb_session.load_session()
    data["busca_ativa"] = True
    fb_session.save_session(data)
    _save_busca_state(st)

    standby = st.get("standby_tasks") or []
    standby_line = (
        f"• TASK(s) em standby: {', '.join(standby)}\n" if standby else ""
    )
    group_line = ""
    if cap.get("lock_group_url"):
        group_line = f"• Grupo fixo: {cap['lock_group_url']}\n"
    task_line = ""
    if cap.get("active_task_id"):
        task_line = f"• TASK: {cap['active_task_id']}\n"
    warn_lines = []
    if not cap.get("lock_group_url"):
        warn_lines.append(
            "⚠️ Grupo fixo não definido — envie antes:\n"
            "  Criar captura https://www.facebook.com/groups/SEU_ID\n"
            "  ou PlayDonizete https://…/groups/SEU_ID"
        )
    if not cap.get("active_task_id"):
        warn_lines.append(
            "⚠️ Nenhuma TASK ligada ao Play — kanban vazio ou ID não reconhecido."
        )
    warn_lines.append(
        "⚠️ Mac precisa rodar a busca (VPS só arma). Se 0 ciclos após 3 min:\n"
        "  ./scripts/donizete-mac-executor.sh --watch"
    )
    warn_block = "\n".join(warn_lines) + "\n" if warn_lines else ""
    return (
        "✓ PlayDonizete — ARMADO (VPS · captação no Mac).\n"
        + task_line
        + group_line
        + standby_line
        + warn_block
        + "StopDonizete no WhatsApp para parar."
    )


def validate_capture_start(
    *,
    task_id: str | None = None,
    group_url: str | None = None,
    allow_rotativo: bool = False,
) -> str | None:
    """
    Valida PlayDonizete — captura só LP-PINTOR-* com grupo fixo na task.
    Retorna mensagem de erro ou None se OK.
    """
    tid = (task_id or "").strip().upper()
    url = (group_url or "").strip()

    if tid.startswith("TASK-"):
        return (
            "⚠️ TASK-001 (e TASK-*) é histórico de landing — não use para captura.\n\n"
            "Crie: Criar captura https://www.facebook.com/groups/ID\n"
            "Depois: PlayDonizete LP-PINTOR-XXX"
        )
    if tid and not tid.startswith("LP-PINTOR"):
        return (
            f"⚠️ Captura intermitente só em LP-PINTOR-XXX (recebido: {tid}).\n\n"
            "Criar captura <url do grupo> gera o ID correto."
        )

    if tid:
        cfg = load_capture_config(tid)
        if not cfg:
            return f"⚠️ {tid} não encontrada em tasks/. Crie com Criar captura <url>."
        if not cfg.get("group_url") and not url:
            return (
                f"⚠️ {tid} sem grupo fixo no arquivo da task.\n\n"
                f"Criar captura <url>\n"
                f"ou PlayDonizete {tid} https://www.facebook.com/groups/ID"
            )

    if not tid and not url:
        tasks = [
            t
            for t in find_capture_tasks_in_kanban()
            if load_capture_config(t) and load_capture_config(t).get("group_url")
        ]
        if len(tasks) == 1:
            return None
        if not tasks:
            return (
                "⚠️ Nenhuma captura com grupo fixo no kanban.\n\n"
                "1) Criar captura https://www.facebook.com/groups/ID\n"
                "2) PlayDonizete LP-PINTOR-XXX\n\n"
                "(Modo rotativo só se pedir explicitamente «rotacionar grupos».)"
            )
        if len(tasks) > 1:
            return (
                "⚠️ Várias capturas ativas — informe o ID:\n"
                + "\n".join(f"• {t}" for t in tasks[:6])
                + "\n\nEx.: PlayDonizete LP-PINTOR-010"
            )
        if not allow_rotativo:
            return (
                "⚠️ PlayDonizete exige LP-PINTOR-XXX com grupo fixo.\n\n"
                "Criar captura <url> · depois PlayDonizete LP-PINTOR-XXX"
            )
    return None


def start_busca(
    *,
    allow_arm_without_cdp: bool = True,
    task_id: str | None = None,
    group_url: str | None = None,
    skip_validation: bool = False,
) -> str:
    """Inicia busca intermitente (thread daemon)."""
    global _thread
    if not skip_validation:
        err = validate_capture_start(task_id=task_id, group_url=group_url)
        if err:
            return err
    if not task_id and not group_url:
        fixed = [
            t
            for t in find_capture_tasks_in_kanban()
            if load_capture_config(t) and load_capture_config(t).get("group_url")
        ]
        if len(fixed) == 1:
            task_id = fixed[0]
    cap = _resolve_capture_config(task_id=task_id, group_url=group_url)
    if cap.get("active_task_id") and not cap.get("lock_group_url"):
        tc = load_capture_config(cap["active_task_id"])
        if tc and tc.get("group_url"):
            cap["lock_group_url"] = tc["group_url"]
            cap["lock_group"] = True
            cap["modo"] = "grupo_fixo"

    if not facebook_cdp.facebook_enabled():
        return "ERRO: DONIZETE_FB_ENABLED=0 no .env"
    if not facebook_cdp.cdp_reachable():
        if allow_arm_without_cdp:
            return _arm_busca_without_thread(
                task_id=cap.get("active_task_id") or None,
                group_url=cap.get("lock_group_url") or None,
            )
        return (
            "ERRO: Chrome CDP offline.\n"
            "Rode ./scripts/facebook-cdp-mac.sh e mantenha Facebook logado."
        )

    with _lock:
        if is_running():
            return f"Busca já está ativa.\n\n{status_line()}"

        _stop.clear()
        st = _load_busca_state()
        st["cycles"] = 0
        st["leads_captured"] = 0
        st["last_error"] = ""
        st.update(cap)
        st["modo"] = cap.get("modo") or "independente"
        st["ignora"] = [
            "task_cadence",
            "wip_soft_max",
            "autopilot_donizete",
            "prioridade_kanban",
            "cooldown_autopilot",
        ]
        tid = cap.get("active_task_id") or None
        st["standby_tasks"] = pause_executando_for_busca(task_id=tid)
        data = fb_session.load_session()
        data["busca_ativa"] = True
        fb_session.save_session(data)
        _save_busca_state(st)

        _thread = threading.Thread(target=_run_loop, name="donizete-busca", daemon=True)
        _thread.start()

    st = _load_busca_state()
    standby = st.get("standby_tasks") or []
    standby_line = (
        f"• TASK(s) em standby: {', '.join(standby)}\n" if standby else "• Nenhuma TASK em executando para pausar\n"
    )
    lo, hi = _pause_bounds()
    modo_desc = (
        "grupo fixo (sem troca)"
        if st.get("lock_group_url")
        else "rotativo (Donizete escolhe grupos)"
    )
    task_line = f"• TASK: {st.get('active_task_id')}\n" if st.get("active_task_id") else ""
    group_line = (
        f"• Grupo: {st.get('lock_group_url')}\n" if st.get("lock_group_url") else ""
    )
    return (
        f"✓ PlayDonizete — busca INICIADA ({modo_desc}).\n"
        + task_line
        + group_line
        + standby_line
        + "• StopDonizete para a captura e restaura kanban\n"
        f"• Pausa {lo}–{hi}s entre ciclos\n"
        "Mac: mantenha donizete-mac-executor ou busca-local rodando."
    )


def stop_busca(*, task_id: str | None = None) -> str:
    """Interrompe busca intermitente."""
    global _thread
    st = _load_busca_state()
    was_armed = bool(st.get("armed_vps"))
    active = (st.get("active_task_id") or "").upper()
    if task_id and active and task_id.upper() != active:
        return (
            f"Busca ativa é {active}, não {task_id.upper()}.\n"
            f"Use StopDonizete ou StopDonizete {active}\n\n{status_line()}"
        )

    with _lock:
        if not is_running() and _thread is None and not was_armed:
            return f"Busca já estava parada.\n\n{status_line()}"

        _stop.set()
        if _thread is not None:
            _thread.join(timeout=8.0)
        _thread = None

    st = _load_busca_state()
    standby_ids = list(st.get("standby_tasks") or [])
    resumed = resume_standby_tasks(standby_ids) if standby_ids else []
    st["standby_tasks"] = []
    st["resumed_tasks"] = resumed
    st["armed_vps"] = False
    st["modo"] = "parado"
    st.pop("active_task_id", None)
    st.pop("lock_group_url", None)
    st.pop("lock_group_name", None)
    st["lock_group"] = False
    _save_busca_state(st)

    data = fb_session.load_session()
    data["busca_ativa"] = False
    fb_session.save_session(data)

    resume_line = (
        f"• TASK(s) de volta em executando: {', '.join(resumed)}\n" if resumed else ""
    )
    return f"✓ StopDonizete — busca INTERROMPIDA.\n{resume_line}\n{status_line()}"


def match_whatsapp_command(text: str) -> str | None:
    """Delegado — matching estrito em donizete_whatsapp."""
    from laboratorio.ops.donizete_whatsapp import match_donizete_whatsapp

    return match_donizete_whatsapp(text)
