"""Respostas WhatsApp do Vitor — canal operacional (Ronaldo)."""

from __future__ import annotations

import logging

from laboratorio.whatsapp.vitor_whatsapp import process_vitor_message

logger = logging.getLogger("laboratorio.whatsapp.vitor")


def generate_vitor_reply(from_wa_id: str, user_message: str) -> str:
    """Ronaldo responde o Vitor — operador completo Lab + alertas + agenda."""
    return process_vitor_message(from_wa_id, user_message)
