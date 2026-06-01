"""Orquestra inbound → Caio → outbound."""

from __future__ import annotations

import logging

from laboratorio.whatsapp.caio_handler import generate_caio_reply
from laboratorio.whatsapp.client import send_text_message
from laboratorio.whatsapp.dedup import mark_if_new
from laboratorio.whatsapp.logger import log_exchange
from laboratorio.whatsapp.owner import generate_owner_reply, is_owner
from laboratorio.whatsapp.parser import InboundMessage

logger = logging.getLogger("laboratorio.whatsapp.handler")


def process_inbound_message(msg: InboundMessage) -> None:
    # Marca ANTES de processar (atômico): descarta a 2ª entrega da Meta mesmo
    # enquanto a 1ª ainda está gerando a resposta — evita resposta duplicada.
    if not mark_if_new(msg.message_id):
        logger.info("Ignorando duplicata message_id=%s", msg.message_id)
        return

    try:
        if is_owner(msg.from_wa_id):
            # Dono: Caio responde amplo sobre o laboratório (status, tasks, andamento).
            logger.info("Mensagem de dono %s — modo ampla (laboratório)", msg.from_wa_id)
            reply = generate_owner_reply(msg.text)
            status = "ok (dono)"
        else:
            # Demais números: Caio comercial (produtos, projetos, leads do CRM).
            reply = generate_caio_reply(msg.from_wa_id, msg.text)
            status = "ok"

        send_text_message(msg.from_wa_id, reply)
        log_exchange(
            from_wa_id=msg.from_wa_id,
            inbound=msg.text,
            outbound=reply,
            message_id=msg.message_id,
            status=status,
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
