"""Autorização do Vitor no canal WhatsApp."""

from __future__ import annotations

import os
import re

DEFAULT_VITOR_WA_ID = "5533999353242"
# Variante ocasional do webhook Meta (sem um dígito 9)
VITOR_WA_ID_ALIASES = frozenset({"553399353242"})


def normalize_wa_id(wa_id: str) -> str:
    return re.sub(r"\D", "", wa_id or "")


def get_vitor_wa_id() -> str:
    raw = os.getenv("VITOR_WHATSAPP_WA_ID", DEFAULT_VITOR_WA_ID).strip()
    return normalize_wa_id(raw) or DEFAULT_VITOR_WA_ID


def is_vitor_authorized(wa_id: str) -> bool:
    normalized = normalize_wa_id(wa_id)
    if not normalized:
        return False
    vitor = get_vitor_wa_id()
    if normalized == vitor or normalized in VITOR_WA_ID_ALIASES:
        return True
    if len(normalized) == 11 and vitor.endswith(normalized):
        return True
    if len(vitor) == 11 and normalized.endswith(vitor):
        return True
    return False
