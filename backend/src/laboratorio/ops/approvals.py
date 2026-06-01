"""Aprovação humana por WhatsApp para ações sensíveis (human-in-the-loop).

Um agente, em vez de executar uma ação grande (ex.: mandar mensagem a um cliente),
chama `request_approval(...)`. Isso registra um pedido pendente e manda um WhatsApp
ao dono (Vitor) com um código. Quando o dono responde "APROVAR <código>" /
"RECUSAR <código>", `try_resolve_from_text(...)` resolve e executa (ou cancela).

Seguro por padrão: nada sensível acontece sem o "OK" do dono.
"""

from __future__ import annotations

import json
import logging
import re
import threading
import uuid
from datetime import datetime, timezone

from laboratorio.config import DATA_DIR

logger = logging.getLogger("laboratorio.approvals")

_FILE = DATA_DIR / "approvals.json"
_LOCK = threading.Lock()

_APPROVE_RE = re.compile(r"^\s*(aprovar|aprovado|aprova)\b\s*([A-Za-z0-9]{4})?", re.IGNORECASE)
_REJECT_RE = re.compile(r"^\s*(recusar|recuso|recusado|negar|nega)\b\s*([A-Za-z0-9]{4})?", re.IGNORECASE)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _load() -> list[dict]:
    if not _FILE.is_file():
        return []
    try:
        data = json.loads(_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def _save(rows: list[dict]) -> None:
    _FILE.parent.mkdir(parents=True, exist_ok=True)
    _FILE.write_text(json.dumps(rows[-500:], ensure_ascii=False, indent=2), encoding="utf-8")


def _short_id() -> str:
    return uuid.uuid4().hex[:4].upper()


def _notify_owner(text: str) -> None:
    try:
        from laboratorio.whatsapp.client import send_text_message
        from laboratorio.whatsapp.owner import owner_ids

        for wid in owner_ids():
            send_text_message(wid, text)
    except Exception as exc:  # noqa: BLE001 — não quebra o fluxo do agente
        logger.warning("Falha ao notificar dono sobre aprovação: %s", exc)


def request_approval(*, kind: str, summary: str, payload: dict | None = None, notify: bool = True) -> dict:
    """Registra um pedido de aprovação e avisa o dono no WhatsApp."""
    rec = {
        "id": _short_id(),
        "kind": kind,
        "summary": summary,
        "payload": payload or {},
        "status": "pending",
        "created_at": _now(),
        "resolved_at": None,
    }
    with _LOCK:
        rows = _load()
        rows.append(rec)
        _save(rows)
    if notify:
        _notify_owner(
            f"🔔 Preciso da sua aprovação [{rec['id']}]\n\n{summary}\n\n"
            f"Responda: APROVAR {rec['id']}  ou  RECUSAR {rec['id']}"
        )
    logger.info("Aprovação solicitada %s (%s)", rec["id"], kind)
    return rec


def pending() -> list[dict]:
    return [r for r in _load() if r.get("status") == "pending"]


def _set_status(approval_id: str, status: str) -> dict | None:
    with _LOCK:
        rows = _load()
        for r in rows:
            if r["id"] == approval_id and r["status"] == "pending":
                r["status"] = status
                r["resolved_at"] = _now()
                _save(rows)
                return r
        return None


def _execute(rec: dict) -> str:
    """Executa a ação aprovada conforme o tipo."""
    kind = rec.get("kind")
    p = rec.get("payload") or {}
    if kind == "whatsapp_message":
        try:
            from laboratorio.whatsapp.client import send_text_message

            send_text_message(p.get("to", ""), p.get("body", ""))
            return f"Mensagem enviada para {p.get('to')}."
        except Exception as exc:  # noqa: BLE001
            return f"(falha ao enviar: {exc})"
    return "Ação marcada como aprovada."


def try_resolve_from_text(text: str) -> str | None:
    """Se o texto do dono for APROVAR/RECUSAR, resolve e retorna confirmação. Senão None."""
    t = (text or "").strip()
    m_ok = _APPROVE_RE.match(t)
    m_no = _REJECT_RE.match(t)
    if not (m_ok or m_no):
        return None

    approve = bool(m_ok)
    code = (m_ok or m_no).group(2)
    pend = pending()
    if not pend:
        return "Não há nada pendente de aprovação agora."

    if code:
        code = code.upper()
        target = next((r for r in pend if r["id"] == code), None)
        if not target:
            return f"Não achei o código {code}. Pendentes: " + ", ".join(r["id"] for r in pend)
    elif len(pend) == 1:
        target = pend[0]
    else:
        return "Há mais de um pedido pendente — diga o código: " + " | ".join(
            f"{r['id']}: {r['summary'][:40]}" for r in pend
        )

    rec = _set_status(target["id"], "approved" if approve else "rejected")
    if not rec:
        return "Esse pedido já tinha sido resolvido."
    if approve:
        return f"✅ Aprovado [{rec['id']}]. {_execute(rec)}"
    return f"❌ Recusado [{rec['id']}]. Ação cancelada."
