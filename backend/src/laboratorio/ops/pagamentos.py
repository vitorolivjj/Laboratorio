"""Pagamentos — link de cobrança por lead (Plano de Ataque R$450).

Provider: Mercado Pago (Checkout Pro). Cria uma preferência por lead com
external_reference = LEAD-ID → link único e rastreável. O webhook
(/webhook/pagamentos) confirma o pagamento, move o lead para
`plano_ataque_pago` e avisa o Vitor (a call de coleta é dele).

Sem MP_ACCESS_TOKEN: cai no modo PIX manual (PIX_KEY no .env) — o Caio envia
a chave e o Vitor confirma o recebimento movendo o status no painel.

Config: MP_ACCESS_TOKEN · PIX_KEY · PLANO_ATAQUE_VALOR (default 450)
· PAGAMENTOS_WEBHOOK_BASE (default https://api.laboratorioagentes.com.br).
"""

from __future__ import annotations

import logging
import os
import re

import httpx

from laboratorio.config import load_env

logger = logging.getLogger("laboratorio.ops.pagamentos")

_MP_PREFS = "https://api.mercadopago.com/checkout/preferences"
_MP_PAYMENT = "https://api.mercadopago.com/v1/payments/{pid}"


def _valor() -> float:
    load_env()
    try:
        return float(os.getenv("PLANO_ATAQUE_VALOR", "450"))
    except ValueError:
        return 450.0


def _mp_token() -> str:
    load_env()
    return os.getenv("MP_ACCESS_TOKEN", "").strip()


def criar_link(lead_id: str, nome: str) -> dict:
    """Link de pagamento do Plano de Ataque p/ o lead. {modo, url|pix, texto}."""
    valor = _valor()
    token = _mp_token()
    if token:
        base = os.getenv("PAGAMENTOS_WEBHOOK_BASE",
                         "https://api.laboratorioagentes.com.br").rstrip("/")
        body = {
            "items": [{
                "title": f"Plano de Ataque Comercial/Operacional — {nome[:60]}",
                "quantity": 1,
                "unit_price": valor,
                "currency_id": "BRL",
            }],
            "external_reference": lead_id.strip().upper(),
            "notification_url": f"{base}/webhook/pagamentos",
        }
        with httpx.Client(timeout=30.0) as client:
            r = client.post(_MP_PREFS, json=body,
                            headers={"Authorization": f"Bearer {token}"})
            if not r.is_success:
                raise RuntimeError(f"Mercado Pago falhou ({r.status_code}): {r.text[:200]}")
            pref = r.json()
        url = pref.get("init_point") or pref.get("sandbox_init_point", "")
        logger.info("Link MP criado p/ %s", lead_id)
        return {"modo": "mercadopago", "url": url,
                "texto": f"Aqui está o link do Plano de Ataque (R${valor:.0f}): {url}"}

    pix = os.getenv("PIX_KEY", "").strip()
    if pix:
        return {"modo": "pix_manual", "pix": pix,
                "texto": (f"O Plano de Ataque é R${valor:.0f}, pagamento antecipado. "
                          f"Chave PIX: {pix} — me manda o comprovante por aqui que "
                          "a gente já agenda a coleta.")}
    raise RuntimeError(
        "Nenhum meio de pagamento configurado (MP_ACCESS_TOKEN ou PIX_KEY no .env)."
    )


def confirmar_pagamento_mp(payment_id: str) -> dict | None:
    """Consulta o pagamento na API do MP; se aprovado, processa. (webhook)"""
    token = _mp_token()
    if not token:
        return None
    with httpx.Client(timeout=30.0) as client:
        r = client.get(_MP_PAYMENT.format(pid=payment_id),
                       headers={"Authorization": f"Bearer {token}"})
        if not r.is_success:
            logger.warning("MP payment %s consulta falhou: %s", payment_id, r.status_code)
            return None
        pay = r.json()
    status = pay.get("status", "")
    lead_id = (pay.get("external_reference") or "").strip().upper()
    logger.info("MP payment %s: status=%s lead=%s", payment_id, status, lead_id)
    if status != "approved" or not lead_id.startswith("LEAD"):
        return {"status": status, "lead_id": lead_id, "processed": False}

    return processar_pagamento_aprovado(lead_id, origem=f"mp:{payment_id}")


def processar_pagamento_aprovado(lead_id: str, *, origem: str = "manual") -> dict:
    """Plano de Ataque PAGO: status → plano_ataque_pago + avisa o Vitor."""
    detalhe = []
    try:
        from laboratorio.ops import crm_lp_store
        from laboratorio.ops.captacao import CRM_LAB_MD

        crm_lp_store.update_lead_fields(lead_id, path=CRM_LAB_MD,
                                        status="plano_ataque_pago")
        detalhe.append("status → plano_ataque_pago")
    except Exception as exc:  # noqa: BLE001
        detalhe.append(f"não moveu status: {exc}")
    try:
        from laboratorio.ops import memory_store

        memory_store.registrar_evento(
            titulo=f"💰 Plano de Ataque PAGO — {lead_id}",
            tipo="deploy", agentes="Caio",
            detalhe=f"origem {origem}", ref=lead_id,
        )
    except Exception:  # noqa: BLE001
        pass
    try:
        from laboratorio.whatsapp.notify import notify_vitor

        notify_vitor(f"💰 Plano de Ataque PAGO — {lead_id}",
                     "Pagamento confirmado. Próximo passo é SEU: agendar a call "
                     "de coleta com o cliente.",
                     action="Agendar call de coleta", ref=lead_id)
    except Exception:  # noqa: BLE001
        pass
    logger.info("Pagamento processado p/ %s (%s)", lead_id, origem)
    return {"status": "approved", "lead_id": lead_id, "processed": True,
            "detalhe": "; ".join(detalhe)}


def normalizar_telefone(contato: str) -> str:
    d = re.sub(r"\D", "", contato or "")
    if len(d) in (10, 11):
        d = "55" + d
    return d
