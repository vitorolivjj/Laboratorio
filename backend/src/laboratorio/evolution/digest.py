"""Resumo diário — 1x/dia, propostas só com OK do Vitor."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from laboratorio.config import LOGS_DIR, load_env
from laboratorio.evolution.apply import apply_proposals
from laboratorio.evolution.collector import collect_daily_context
from laboratorio.evolution.generate import generate_digest_package
from laboratorio.whatsapp.approvals import request_evolution_batch
from laboratorio.whatsapp.client import send_text_message
from laboratorio.whatsapp.logger import log_exchange
from laboratorio.whatsapp.notify import format_vitor_alert
from laboratorio.whatsapp.vitor_auth import get_vitor_wa_id

logger = logging.getLogger("laboratorio.evolution.digest")

STATE_FILE = LOGS_DIR / "evolution_state.json"


@dataclass
class DigestResult:
    date: str
    skipped: bool
    approval_id: str | None
    summary: str
    proposal_count: int
    notified: bool


def _load_state() -> dict[str, Any]:
    if not STATE_FILE.is_file():
        return {}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save_state(data: dict[str, Any]) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _format_whatsapp_body(
    date: str, summary: str, proposals: list[dict], approval_id: str
) -> str:
    lines = [
        f"📊 Resumo diário — Laboratório [{approval_id}]",
        f"📅 {date}",
        "",
        summary.strip(),
        "",
    ]
    if proposals:
        lines.append("Propostas (nada muda sem seu OK):")
        for p in proposals[:4]:
            pid = p.get("id", "?")
            tgt = p.get("target", "?")
            title = (p.get("title") or "")[:60]
            lines.append(f"{pid}. [{tgt}] {title}")
        lines.append("")
        lines.append(f"APROVAR {approval_id} → aplica todas")
        lines.append(f"RECUSAR {approval_id} → descarta")
    else:
        lines.append("(Sem propostas hoje — só informativo.)")
    return "\n".join(lines)


def run_daily_digest(*, dry_run: bool = False, force: bool = False) -> DigestResult:
    load_env()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    state = _load_state()

    if not force and state.get("last_digest_date") == today:
        logger.info("Resumo diário já gerado hoje")
        return DigestResult(today, True, None, "", 0, False)

    context = collect_daily_context()
    package = generate_digest_package(context)
    summary = package.get("summary", "")
    from laboratorio.evolution.propose import filter_digest_proposals

    proposals = filter_digest_proposals(package.get("proposals") or [])

    if dry_run:
        print(_format_whatsapp_body(today, summary, proposals, "DRY0"))
        return DigestResult(today, False, None, summary, len(proposals), False)

    approval_id: str | None = None
    if proposals:
        approval_id = request_evolution_batch(
            summary=summary,
            proposals=proposals,
            digest_date=today,
        )
    else:
        approval_id = None

    body = _format_whatsapp_body(
        today,
        summary,
        proposals,
        approval_id or "----",
    )
    if len(body) > 3800:
        body = body[:3770] + "\n…"

    wa = get_vitor_wa_id()
    if proposals and approval_id:
        send_text_message(wa, body)
    else:
        alert = format_vitor_alert(
            f"Resumo diário {today}",
            summary,
            action="Sem propostas — nenhuma ação necessária",
            ref="autoevolucao_fase4",
        )
        send_text_message(wa, alert)

    log_exchange(
        from_wa_id=wa,
        inbound="(resumo diário autoevolução)",
        outbound=body[:500],
        message_id=f"evolution-{today}",
        status="ok:evolution_digest",
    )

    state["last_digest_date"] = today
    state["last_run_at"] = datetime.now(timezone.utc).isoformat()
    if approval_id:
        state["last_approval_id"] = approval_id
    _save_state(state)

    logger.info("Resumo diário enviado — %d propostas", len(proposals))
    return DigestResult(today, False, approval_id, summary, len(proposals), True)


def apply_evolution_batch(item: dict[str, Any]) -> str:
    """Chamado ao APROVAR evolution_batch."""
    proposals = item.get("payload", {}).get("proposals") or []
    if not proposals:
        return "Nenhuma proposta no lote."
    results = apply_proposals(proposals)
    lines = list(results)

    try:
        from laboratorio.memory.sync import sync_after_evolution

        sync_msg = sync_after_evolution(proposals)
        lines.append(sync_msg)
        logger.info("Pós-aprovação: %s", sync_msg)
    except Exception as exc:
        logger.exception("Falha ao indexar memória pós-aprovação")
        lines.append(f"Memória: falha ao indexar ({exc})")

    return "\n".join(lines)
