"""Orquestra inbound → Caio → outbound."""

from __future__ import annotations

import logging

from laboratorio.whatsapp.caio_handler import generate_caio_reply
from laboratorio.whatsapp.client import send_text_message
from laboratorio.whatsapp.dedup import already_processed, mark_processed
from laboratorio.whatsapp.logger import log_exchange
from laboratorio.whatsapp.parser import InboundMessage

logger = logging.getLogger("laboratorio.whatsapp.handler")


def process_inbound_message(msg: InboundMessage) -> None:
    if already_processed(msg.message_id):
        logger.info("Ignorando duplicata message_id=%s", msg.message_id)
        return

    try:
        reply = generate_caio_reply(msg.from_wa_id, msg.text)
        send_text_message(msg.from_wa_id, reply)
        mark_processed(msg.message_id)
        log_exchange(
            from_wa_id=msg.from_wa_id,
            inbound=msg.text,
            outbound=reply,
            message_id=msg.message_id,
            status="ok",
        )
    except Exception as exc:
        logger.exception("Falha ao processar mensagem %s", msg.message_id)
        log_exchange(
            from_wa_id=msg.from_wa_id,
            inbound=msg.text,
            outbound="",
            message_id=msg.message_id,
            status=f"erro: {exc}",
        )
        raise
