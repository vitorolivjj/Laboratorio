"""Agendamento de publicação da Esteira nos slots fixos.

Fila de peças aprovadas → publica via Postproxy nos CONTENT_PILLAR_SLOTS
(default 08:00,12:30,19:00, horário de São Paulo). Plugado no loop de 1 min do
`vitor-schedule`. Idempotente: no máximo 1 publicação por slot por dia.

Geração diária (generate_due): também plugada no loop de 1 min — 1×/dia em
CONTENT_GEN_SLOTS dispara `content-run` como processo destacado (não trava o
loop com os ~minutos do lip-sync). Idempotente por dia.

Config (env):
- CONTENT_PILLAR_SLOTS=08:00,12:30,19:00
- CONTENT_PUBLISH_ENABLED=1   (0 desliga a publicação automática)
- CONTENT_SLOT_WINDOW_MIN=20  (janela após o slot p/ capturar mesmo com atraso)
- CONTENT_AUTORUN=1           (0 desliga a geração diária automática)
- CONTENT_GEN_SLOTS=07:00     (horários de geração, antes dos slots de publicação)
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from laboratorio.config import LOGS_DIR, load_env

logger = logging.getLogger("laboratorio.ops.content_schedule")

TZ = ZoneInfo("America/Sao_Paulo")
QUEUE_FILE = LOGS_DIR / "content_queue.json"
GEN_STATE_FILE = LOGS_DIR / "content_gen_state.json"


def _enabled() -> bool:
    load_env()
    return os.getenv("CONTENT_PUBLISH_ENABLED", "1").strip().lower() not in ("0", "false", "no")


def _slots() -> list[tuple[int, int]]:
    load_env()
    raw = os.getenv("CONTENT_PILLAR_SLOTS", "08:00,12:30,19:00")
    out: list[tuple[int, int]] = []
    for s in raw.split(","):
        s = s.strip()
        if ":" in s:
            try:
                h, m = s.split(":")
                out.append((int(h), int(m)))
            except ValueError:
                continue
    return out


def _window_min() -> int:
    try:
        return int(os.getenv("CONTENT_SLOT_WINDOW_MIN", "20")) or 20
    except ValueError:
        return 20


def _load() -> list[dict]:
    try:
        return json.loads(QUEUE_FILE.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return []


def _save(items: list[dict]) -> None:
    QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
    QUEUE_FILE.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


def enqueue(mp4_url: str, caption: str, *, kind: str = "reel", roteiro: str = "") -> dict:
    """Adiciona uma peça APROVADA à fila de publicação."""
    items = _load()
    now = datetime.now(TZ)
    item = {
        "id": f"c{len(items) + 1}-{now.strftime('%Y%m%d%H%M%S')}",
        "mp4_url": mp4_url,
        "caption": caption,
        "kind": kind if kind in ("reel", "story", "carousel") else "reel",
        "roteiro": roteiro[:200],
        "status": "pending",
        "created_at": now.isoformat(),
    }
    items.append(item)
    _save(items)
    logger.info("Conteúdo enfileirado: %s (%s)", item["id"], item["kind"])
    return item


def list_queue(status: str | None = None) -> list[dict]:
    items = _load()
    return [i for i in items if (status is None or i.get("status") == status)]


def pending_count() -> int:
    return len(list_queue("pending"))


def _slot_key(now: datetime, h: int, m: int) -> str:
    return f"{now.strftime('%Y-%m-%d')} {h:02d}:{m:02d}"


def _due_slot(now: datetime, items: list[dict]) -> str | None:
    """Slot vencido (dentro da janela) e ainda não publicado hoje; senão None."""
    published = {i.get("slot") for i in items if i.get("status") == "published" and i.get("slot")}
    win = _window_min() * 60
    for h, m in _slots():
        slot_dt = now.replace(hour=h, minute=m, second=0, microsecond=0)
        key = _slot_key(now, h, m)
        if now >= slot_dt and (now - slot_dt).total_seconds() < win and key not in published:
            return key
    return None


def _log_event(piece: dict, slot: str, *, ok: bool, extra: str = "") -> None:
    try:
        from laboratorio.ops import memory_store

        memory_store.registrar_evento(
            titulo=f"Esteira {'publicou' if ok else 'falhou ao publicar'} ({piece.get('kind')})",
            tipo="deploy",
            agentes="Esteira",
            detalhe=f"slot {slot} · {extra} · {str(piece.get('caption',''))[:70]}",
            ref=str(piece.get("post_id", "")),
        )
    except Exception:  # noqa: BLE001
        pass


def _notify(msg: str, detail: str = "", ref: str = "") -> None:
    try:
        from laboratorio.whatsapp.notify import notify_vitor

        notify_vitor(msg, detail, ref=ref)
    except Exception:  # noqa: BLE001
        pass


def publish_due(now: datetime | None = None) -> dict | None:
    """Se um slot está vencido e há peça na fila, publica. Idempotente por slot/dia.

    Chamado pelo loop de 1 min do vitor-schedule. Retorna o resultado ou None.
    """
    if not _enabled():
        return None
    now = now or datetime.now(TZ)
    items = _load()
    slot = _due_slot(now, items)
    if not slot:
        return None

    piece = next((i for i in items if i.get("status") == "pending"), None)
    if not piece:
        # Fila vazia: só loga (sem notificar) — evita ruído diário enquanto a
        # esteira ainda não gera conteúdo. Aviso de buffer baixo fica para a P1.
        logger.info("Slot %s vencido mas fila vazia", slot)
        return {"slot": slot, "published": False, "reason": "fila vazia"}

    from laboratorio.ops import postproxy

    try:
        post_id = postproxy.publicar(piece["mp4_url"], piece.get("caption", ""), kind=piece.get("kind", "reel"))
    except Exception as exc:  # noqa: BLE001
        logger.warning("Falha ao publicar %s no slot %s: %s", piece["id"], slot, exc)
        _log_event(piece, slot, ok=False, extra=f"erro: {exc}")
        _notify("❌ Esteira falhou ao publicar", f"slot {slot}: {exc}"[:200], ref=piece["id"])
        return {"slot": slot, "published": False, "error": str(exc)}

    piece["status"] = "published"
    piece["published_at"] = now.isoformat()
    piece["post_id"] = post_id
    piece["slot"] = slot
    _save(items)
    _log_event(piece, slot, ok=True, extra=f"post {post_id}")
    _notify(f"📤 Esteira publicou ({piece.get('kind')})", f"slot {slot} · post {post_id}", ref=str(post_id))
    logger.info("Esteira publicou %s no slot %s (post %s)", piece["id"], slot, post_id)
    return {"slot": slot, "published": True, "post_id": post_id, "piece": piece["id"]}


# --- geração diária automática --------------------------------------------


def _autorun_enabled() -> bool:
    load_env()
    return os.getenv("CONTENT_AUTORUN", "1").strip().lower() not in ("0", "false", "no")


def _gen_slots() -> list[tuple[int, int]]:
    load_env()
    raw = os.getenv("CONTENT_GEN_SLOTS", "07:00")
    out: list[tuple[int, int]] = []
    for s in raw.split(","):
        s = s.strip()
        if ":" in s:
            try:
                h, m = s.split(":")
                out.append((int(h), int(m)))
            except ValueError:
                continue
    return out


def _gen_done() -> set[str]:
    try:
        return set(json.loads(GEN_STATE_FILE.read_text(encoding="utf-8")))
    except Exception:  # noqa: BLE001
        return set()


def _gen_mark(key: str) -> None:
    done = _gen_done()
    done.add(key)
    GEN_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    # mantém só os 30 mais recentes p/ não crescer indefinidamente
    keep = sorted(done)[-30:]
    GEN_STATE_FILE.write_text(json.dumps(keep, ensure_ascii=False), encoding="utf-8")


def _run_generation() -> dict:
    """Roda 1 ciclo da esteira (síncrono). Notifica o Vitor em caso de erro.

    Síncrono de propósito: o vitor-schedule é um systemd oneshot (KillMode=
    control-group), então um processo destacado seria morto ao fim do tick.
    Bloqueia o loop por alguns minutos 1×/dia — aceitável (em modo aprovação
    nenhuma publicação depende disso em tempo real)."""
    from laboratorio.ops import content_run

    try:
        return content_run.rodar_ciclo()
    except Exception as exc:  # noqa: BLE001
        logger.exception("Esteira: geração diária falhou")
        _notify("❌ Esteira falhou ao gerar conteúdo", str(exc)[:300],
                ref="content_run")
        return {"status": "erro", "motivo": str(exc)}


def generate_due(now: datetime | None = None) -> dict | None:
    """Se um horário de geração está vencido (e ainda não rodou hoje), gera 1 peça.
    Idempotente por dia. Chamado pelo loop de 1 min do vitor-schedule."""
    if not _autorun_enabled():
        return None
    now = now or datetime.now(TZ)
    done = _gen_done()
    win = _window_min() * 60
    for h, m in _gen_slots():
        slot_dt = now.replace(hour=h, minute=m, second=0, microsecond=0)
        key = _slot_key(now, h, m)
        if now >= slot_dt and (now - slot_dt).total_seconds() < win and key not in done:
            _gen_mark(key)  # marca antes de rodar: evita re-tentar em loop se falhar
            logger.info("Esteira: geração diária iniciada (%s)", key)
            res = _run_generation()
            return {"slot": key, "result": res}
    return None
