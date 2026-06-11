"""Abordagem proativa do Caio — templates aprovados, sem aprovação por mensagem.

Decisão 2026-06-11 (Plano Comercial §6.2): abordagens proativas usam templates
aprovados pelo Vitor por segmento (aprovação única por template). Dentro do
template, o Caio dispara direto, respeitando o limite diário. Fora de template,
caso sensível ou negociação de valor seguem na trava individual (EnviarWhatsApp).

Na API oficial do WhatsApp a conversa proativa exige template registrado na Meta;
se o template ainda não estiver cadastrado (erro 132001), a abordagem cai para a
fila de aprovação individual (client_template) — nada é perdido.

Config: CAIO_DAILY_ABORDAGENS (default 10).
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from laboratorio.config import LOGS_DIR, load_env

logger = logging.getLogger("laboratorio.whatsapp.abordagem")

TZ = ZoneInfo("America/Sao_Paulo")
STATE_FILE = LOGS_DIR / "abordagens_state.json"


def daily_limit() -> int:
    load_env()
    try:
        return int(os.getenv("CAIO_DAILY_ABORDAGENS", "10"))
    except ValueError:
        return 10


def _today() -> str:
    return datetime.now(TZ).strftime("%Y-%m-%d")


def _load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def _save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    # mantém só os últimos 30 dias
    keep = dict(sorted(state.items())[-30:])
    STATE_FILE.write_text(json.dumps(keep, ensure_ascii=False, indent=2), encoding="utf-8")


def enviadas_hoje() -> int:
    return int(_load_state().get(_today(), 0))


def _registrar_envio() -> None:
    state = _load_state()
    state[_today()] = int(state.get(_today(), 0)) + 1
    _save_state(state)


def abordar(to_wa_id: str, template_name: str, nome_negocio: str) -> str:
    """Envia uma abordagem aprovada. Retorna mensagem de status p/ o agente."""
    from laboratorio.whatsapp.client import WhatsAppApiError, send_template_message
    from laboratorio.whatsapp.logger import log_exchange
    from laboratorio.whatsapp.owner import is_owner
    from laboratorio.whatsapp.templates import ABORDAGEM_TEMPLATES, get_template

    key = template_name.strip().lower()
    if key not in ABORDAGEM_TEMPLATES:
        return (
            f"Template '{template_name}' não está na lista de abordagens aprovadas "
            f"({', '.join(ABORDAGEM_TEMPLATES)}). Para mensagem fora de template, "
            "use enviar_whatsapp (vai para aprovação do Vitor)."
        )
    if is_owner(to_wa_id):
        return "Esse número é o canal do Vitor — abordagem comercial não se aplica."

    limite = daily_limit()
    feitas = enviadas_hoje()
    if feitas >= limite:
        return (
            f"Limite diário de abordagens atingido ({feitas}/{limite}). "
            "Retome amanhã ou peça ao Vitor para ampliar CAIO_DAILY_ABORDAGENS."
        )

    spec = get_template(key)
    params = [nome_negocio.strip() or "tudo bem"]
    try:
        send_template_message(to_wa_id, spec.name, language_code=spec.language,
                              body_params=params)
    except WhatsAppApiError as exc:
        if exc.meta_code == 132001:
            # Template ainda não cadastrado na Meta → cai pra aprovação individual.
            from laboratorio.whatsapp.approvals import request_client_template

            try:
                aid = request_client_template(to_wa_id, spec.name, params)
            except Exception as exc2:  # noqa: BLE001
                return (
                    f"Template '{spec.name}' não está cadastrado na Meta e o fallback "
                    f"de aprovação falhou: {exc2}"
                )
            return (
                f"Template '{spec.name}' ainda não cadastrado na Meta — abordagem "
                f"enviada para aprovação do Vitor (código {aid})."
            )
        raise

    _registrar_envio()
    log_exchange(
        from_wa_id=to_wa_id,
        inbound="(abordagem proativa — template aprovado)",
        outbound=f"[{spec.name}] {nome_negocio}",
        message_id=f"abordagem-{_today()}-{feitas + 1}",
        status="ok:abordagem_template",
    )
    logger.info("Abordagem %s → +%s (%d/%d hoje)", spec.name, to_wa_id[-4:],
                feitas + 1, limite)
    return (
        f"Abordagem '{spec.name}' enviada para {to_wa_id} "
        f"({feitas + 1}/{limite} hoje). Registre o lead no CRM com status "
        "'dossie_enviado' ou 'aguardando_resposta'."
    )
