"""Caio v2 — SDR do novo negócio (Dossiê → Plano de Ataque → Sprint).

Regra de ouro: CRM PRIMEIRO. Antes de responder, o handler localiza o lead no
funil oficial (crm_laboratorio) pelo telefone, monta o contexto (status, score,
sinais do Donizete, sondagem do Juarez, ângulo/Dossiê do Ronaldo, conversa
recente) e instrui o objetivo do ESTÁGIO. Lead desconhecido vira lead novo no
CRM (status `respondeu`).

O cérebro completo vive em memoria/caio_manteiga/cerebro_comercial.md (editável
sem deploy). Marcador [LINK_PAGAMENTO] na resposta é trocado pelo link real de
cobrança do lead (ops/pagamentos). Revisor (CAIO_REVIEW) continua na saída.
"""

from __future__ import annotations

import logging
import os
import re

from laboratorio.config import MEMORIA_DIR, REPO_ROOT, load_env
from laboratorio.ops.review import review_text

logger = logging.getLogger("laboratorio.whatsapp.caio")

CEREBRO_MD = MEMORIA_DIR / "caio_manteiga" / "cerebro_comercial.md"
CRM_LAB_MD = REPO_ROOT / "crm" / "crm_laboratorio.md"

_REVIEW_CRITERIA = (
    "Máximo 4 linhas. Português natural e humano, sem tom robótico/corporativo. "
    "Sem markdown, sem aspas. Não inventar fatos. Preservar links intactos. "
    "Uma pergunta no máximo."
)

_OBJETIVOS = {
    "novo": "Lead recém-captado falou primeiro: acolha, descubra o negócio e comece a qualificar.",
    "pesquisado": "Acolha, conecte com o que sabemos do negócio e comece a qualificar.",
    "vazamento_provavel": "Acolha; se houver Dossiê pronto, ofereça mandar o link; senão qualifique.",
    "dossie_enviado": "Reaja, mande o LINK DO DOSSIÊ se ainda não foi enviado na conversa, e abra a qualificação.",
    "aguardando_resposta": "Ele respondeu! Mande o link do Dossiê se ainda não foi, e abra a qualificação.",
    "respondeu": "Abra a qualificação: UMA pergunta (como chegam os clientes? quem responde? acompanham orçamento?).",
    "qualificando": "Continue qualificando com UMA pergunta. Com 3+ sinais (dor real, WhatsApp importante, perde retorno, pode pagar), avance pra oferta.",
    "pronto_plano_ataque": "Apresente e oferte o Plano de Ataque (R$450, antecipado) usando o ângulo do vazamento dele.",
    "plano_ataque_enviado": "Contorne objeções com calma. Se ele aceitar avançar, inclua [LINK_PAGAMENTO] na resposta.",
    "plano_ataque_pago": "NÃO venda nada. Confirme o pagamento e avise que o Vitor vai chamar pra agendar a call de coleta.",
    "call_agendada": "Só confirme/tire dúvida logística. A condução agora é do Vitor.",
    "plano_em_producao": "Diga que a análise está em produção e o retorno vem em breve.",
    "plano_entregue": "Colha a reação ao Plano entregue e, se positiva, mencione que a Sprint é o próximo passo (proposta vem do Vitor).",
    "pausado": "Follow-up leve: lembre o problema (não implore) e pergunte se faz sentido retomar.",
}
_OBJETIVO_PADRAO = ("Responda com utilidade, descubra contexto e conduza um passo "
                    "no funil (Dossiê → Plano de Ataque).")


def _review_enabled() -> bool:
    return os.getenv("CAIO_REVIEW", "1").strip().lower() not in ("0", "false", "no")


def _clean_reply(raw: str) -> str:
    text = raw.strip()
    text = re.sub(r"^```(?:\w*\n)?", "", text)
    text = re.sub(r"\n?```$", "", text)
    return text.strip().strip('"').strip("'")


def _digits(s: str) -> str:
    return re.sub(r"\D", "", s or "")


def _find_lead(from_wa_id: str) -> dict | None:
    from laboratorio.repositories.leads import get_lead_repository

    suf = _digits(from_wa_id)[-8:]
    if not suf:
        return None
    try:
        for ld in get_lead_repository().all():
            d = _digits(ld.get("contato", ""))
            if d and d[-8:] == suf:
                return ld
    except Exception as exc:  # noqa: BLE001
        logger.warning("Busca de lead por telefone falhou: %s", exc)
    return None


def _auto_lead_enabled() -> bool:
    # default DESLIGADO: número aleatório que chama o WhatsApp NÃO vira lead no
    # CRM oficial (markdown é fonte da verdade — evita poluição/spam). O funil é
    # alimentado pela captação do Donizete. Ligue com CAIO_AUTO_LEAD=1 se quiser.
    return os.getenv("CAIO_AUTO_LEAD", "0").strip().lower() in ("1", "true", "yes")


def _criar_lead_inbound(from_wa_id: str) -> dict | None:
    """Número desconhecido que chamou o canal comercial → lead novo no CRM."""
    if not _auto_lead_enabled():
        return None
    try:
        from laboratorio.ops.crm_store import add_lead_segment

        lead = add_lead_segment(
            CRM_LAB_MD,
            nome=f"Contato WhatsApp …{_digits(from_wa_id)[-4:]}",
            contato=from_wa_id,
            origem="whatsapp_inbound",
            status="respondeu",
        )
        logger.info("Lead inbound criado: %s", lead["id"])
        return lead
    except Exception as exc:  # noqa: BLE001
        logger.warning("Não criou lead inbound: %s", exc)
        return None


def _analise_do_lead(lead_id: str) -> dict:
    try:
        from laboratorio.db import lead_assets

        return (lead_assets.get_analysis(lead_id) or {}).get("analise") or {}
    except Exception:  # noqa: BLE001
        return {}


def _conversa_recente(from_wa_id: str, limit: int = 6) -> str:
    """Últimas trocas com este número, em ordem cronológica.

    O log é mais-antigo-no-topo, então pegamos a CAUDA (mais recentes). Exclui
    as mensagens da sondagem do Juarez (mesmo número, papel diferente)."""
    try:
        from laboratorio.config import LOGS_DIR
        from laboratorio.ops import parsers

        log = parsers.parse_whatsapp_log(
            parsers.read_text(LOGS_DIR / "whatsapp_mensagens.md") or "", limit=4000)
        suf = _digits(from_wa_id)[-8:]
        msgs = [m for m in log
                if _digits(m.get("phone", ""))[-8:] == suf
                and "juarez" not in str(m.get("status", "")).lower()][-limit:]
        out = []
        for m in msgs:  # já cronológico (mais antigo → mais recente)
            if m.get("inbound"):
                out.append(f"LEAD: {m['inbound'][:200]}")
            if m.get("outbound"):
                out.append(f"CAIO: {m['outbound'][:200]}")
        return "\n".join(out)
    except Exception:  # noqa: BLE001
        return ""


def _cerebro() -> str:
    try:
        return CEREBRO_MD.read_text(encoding="utf-8")
    except OSError:
        logger.warning("cerebro_comercial.md ausente — usando resumo embutido")
        return ("Você é Caio, assistente comercial do Laboratório de Agentes. "
                "Conduza negócios locais com bagunça em captação/atendimento/comercial "
                "para o Plano de Ataque (R$450, antecipado). Não venda IA; mostre "
                "vazamento. Não invente fatos nem prometa resultados.")


def _inserir_link_pagamento(reply: str, lead: dict | None) -> str:
    if "[LINK_PAGAMENTO]" not in reply:
        return reply
    if not lead:
        return reply.replace("[LINK_PAGAMENTO]", "").strip()
    try:
        from laboratorio.ops.pagamentos import criar_link

        link = criar_link(lead.get("id", ""), lead.get("nome", ""))
        if link.get("url"):
            return reply.replace("[LINK_PAGAMENTO]", link["url"])
        return reply.replace("[LINK_PAGAMENTO]", link.get("texto", "")).strip()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Link de pagamento indisponível: %s", exc)
        return reply.replace(
            "[LINK_PAGAMENTO]",
            "te mando o link de pagamento em instantes").strip()


def generate_caio_reply(from_wa_id: str, user_message: str) -> str:
    """Resposta comercial guiada pelo CRM (estágio do funil → objetivo)."""
    load_env()
    lead = _find_lead(from_wa_id)
    if not lead:
        lead = _criar_lead_inbound(from_wa_id)
    status = (lead or {}).get("status", "")
    objetivo = _OBJETIVOS.get(status, _OBJETIVO_PADRAO)
    analise = _analise_do_lead(lead["id"]) if lead else {}
    dossie = analise.get("dossie") or {}
    captacao = analise.get("captacao") or {}
    historico = _conversa_recente(from_wa_id)

    contexto = []
    if lead:
        contexto.append(
            f"LEAD NO CRM: {lead.get('id')} · {lead.get('nome')} · "
            f"status={status or '—'} · score={lead.get('score', '—')} · "
            f"segmento={lead.get('servico', '—')} · cidade={lead.get('cidade', '—')}"
        )
        if lead.get("observacoes"):
            contexto.append(f"Sinais (Donizete): {lead['observacoes'][:300]}")
    if dossie.get("url"):
        contexto.append(f"DOSSIÊ PRONTO: {dossie['url']}")
    if dossie.get("angulo_abordagem"):
        contexto.append(f"Ângulo do Ronaldo: {dossie['angulo_abordagem'][:200]}")
    if captacao.get("resumo"):
        contexto.append(f"Resumo da captação: {captacao['resumo'][:200]}")
    if analise.get("sondagem_ativa", {}).get("resumo"):
        contexto.append(f"Sondagem (Juarez): {analise['sondagem_ativa']['resumo'][:200]}")
    if historico:
        contexto.append(f"CONVERSA RECENTE:\n{historico}")

    user = (
        f"{chr(10).join(contexto) if contexto else 'Lead sem registro no CRM.'}\n\n"
        f"OBJETIVO DESTA MENSAGEM (estágio {status or 'desconhecido'}): {objetivo}\n\n"
        f"Mensagem do lead agora:\n{user_message}\n\n"
        "Responda APENAS o texto da mensagem WhatsApp (máx. 4 linhas, sem markdown, "
        "sem aspas, uma pergunta no máximo). Se for incluir cobrança use o marcador "
        "[LINK_PAGAMENTO] no lugar do link."
    )

    from laboratorio.graph.llm import chat

    try:
        raw, cost = chat(_cerebro(), user, max_tokens=400)
        logger.info("Caio v2 → %s (estágio=%s, custo≈$%.4f)",
                    from_wa_id, status or "novo", cost)
    except Exception:  # noqa: BLE001
        logger.exception("Caio LLM falhou")
        return ("Opa, tive um problema técnico aqui agora. Já te respondo, "
                "ou se preferir me chama de novo em instantes!")

    reply = _clean_reply(raw)
    if not reply:
        reply = "Olá! Sou o Caio, assistente comercial do Laboratório de Agentes. Como posso ajudar?"

    # Revisor ANTES de inserir o link real — senão o LLM revisor pode mutilar a
    # URL de cobrança. O marcador [LINK_PAGAMENTO] (texto, não URL) passa intacto.
    tem_marcador = "[LINK_PAGAMENTO]" in reply
    if _review_enabled() and not tem_marcador:
        try:
            reply = review_text(reply, role="atendimento comercial WhatsApp",
                                criteria=_REVIEW_CRITERIA)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Revisor indisponível: %s", exc)
    reply = _inserir_link_pagamento(reply, lead)

    # pagamento confirmado por mensagem? (comprovante PIX manual) → avisa o Vitor
    if status == "plano_ataque_enviado" and re.search(
            r"comprovante|paguei|pago|pix feito|transferi", user_message, re.I):
        try:
            from laboratorio.whatsapp.notify import notify_vitor

            notify_vitor(f"💬 {lead.get('nome', from_wa_id)} diz que PAGOU",
                         "Confirme o recebimento e mova para plano_ataque_pago "
                         "no painel.", ref=(lead or {}).get("id", ""))
        except Exception:  # noqa: BLE001
            pass

    logger.info("Caio respondeu (%d chars)", len(reply))
    return reply
