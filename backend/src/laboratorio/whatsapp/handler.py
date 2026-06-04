"""Orquestra inbound → Caio / Vitor / Dono → outbound."""

from __future__ import annotations

import logging

from laboratorio.whatsapp.approvals import try_handle_approval_message
from laboratorio.whatsapp.caio_handler import generate_caio_reply
from laboratorio.whatsapp.client import send_text_message
from laboratorio.whatsapp.caio_session import is_duplicate_outbound, record_outbound
from laboratorio.whatsapp.dedup import mark_if_new
from laboratorio.whatsapp.outbound import send_to_recipient
from laboratorio.whatsapp.logger import log_exchange
from laboratorio.whatsapp.owner import generate_owner_reply, is_owner
from laboratorio.whatsapp.parser import InboundMessage
from laboratorio.whatsapp.vitor_auth import is_vitor_authorized
from laboratorio.whatsapp.vitor_handler import generate_vitor_reply
from laboratorio.whatsapp.vitor_whatsapp import vitor_needs_ack

logger = logging.getLogger("laboratorio.whatsapp.handler")


def process_inbound_message(msg: InboundMessage) -> None:
    if not mark_if_new(msg.message_id, wa_id=msg.from_wa_id, text=msg.text):
        logger.info(
            "Ignorando duplicata inbound de %s (id=%s)",
            msg.from_wa_id,
            msg.message_id,
        )
        return

    # Lembretes só via vitor-schedule.timer (evita disparo duplo com inbound)

    reply = ""
    channel = "erro"
    try:
        if is_vitor_authorized(msg.from_wa_id):
            approval_reply = try_handle_approval_message(msg.text)
            if approval_reply is not None:
                reply = approval_reply
                channel = "vitor_aprovacao"
            else:
                if vitor_needs_ack(msg.text):
                    send_text_message(msg.from_wa_id, "⏳ Consultando operação…")
                reply = generate_vitor_reply(msg.from_wa_id, msg.text)
                channel = "vitor_operacional"
        elif is_owner(msg.from_wa_id):
            logger.info("Mensagem de dono %s — modo Ronaldo (ações + status)", msg.from_wa_id)
            reply = generate_owner_reply(msg.text)
            channel = "owner_ronaldo"
        else:
            reply = generate_caio_reply(msg.from_wa_id, msg.text)
            channel = "caio_comercial"

        if is_duplicate_outbound(msg.from_wa_id, reply):
            logger.info("Outbound duplicado ignorado para %s", msg.from_wa_id)
            return

        send_to_recipient(msg.from_wa_id, reply, proactive=False)
        record_outbound(msg.from_wa_id, reply)
        log_exchange(
            from_wa_id=msg.from_wa_id,
            inbound=msg.text,
            outbound=reply,
            message_id=msg.message_id,
            status=f"ok:{channel}",
        )
    except Exception as exc:
        logger.exception("Falha ao processar mensagem %s", msg.message_id)
        err_msg = (
            f"⚠️ Falha ao processar sua mensagem.\n\n"
            f"{type(exc).__name__}: {str(exc)[:400]}\n\n"
            "Tente: status · ajuda · ou repita em instantes."
        )
        try:
            if is_vitor_authorized(msg.from_wa_id) and not is_duplicate_outbound(
                msg.from_wa_id, err_msg
            ):
                send_to_recipient(msg.from_wa_id, err_msg, proactive=False)
                record_outbound(msg.from_wa_id, err_msg)
        except Exception as send_exc:
            logger.warning("Não enviou erro ao usuário: %s", send_exc)
        log_exchange(
            from_wa_id=msg.from_wa_id,
            inbound=msg.text,
            outbound=err_msg,
            message_id=msg.message_id,
            status=f"erro: {exc}",
        )


