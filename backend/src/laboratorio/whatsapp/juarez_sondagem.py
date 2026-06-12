"""Juarez — sondagem ATIVA de atendimento (mystery shopping controlado).

Abre conversa com o negócio-alvo via template Meta aprovado (número DEDICADO,
nunca o do Caio), conversa como cliente interessado — pergunta serviço, valores,
datas, como agenda — e fecha com "vou avaliar e retorno". Mede tempo de 1ª
resposta, qualidade da condução e follow-up. 1 sondagem por lead, para sempre.

Freios:
- JUAREZ_SONDAGEM=1 liga (default DESLIGADO — kill-switch instantâneo no .env);
- JUAREZ_PHONE_NUMBER_ID obrigatório (número dedicado na mesma WABA);
- só leads marcados para Dossiê (quem chama é o pipeline do Dossiê ou o CLI);
- nunca agenda horário real; fecha educado; máx. JUAREZ_MAX_TROCAS (default 4).

Estado: logs/sondagens_state.json (uma entrada por lead, com a conversa inteira
— visível no painel via eventos/análise do lead).
"""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime, timezone

from laboratorio.config import LOGS_DIR, load_env

logger = logging.getLogger("laboratorio.whatsapp.juarez")

STATE_FILE = LOGS_DIR / "sondagens_state.json"

_PERSONA = """Você é um cliente comum interessado no serviço de um negócio local,
conversando pelo WhatsApp. Você NÃO revela que é uma avaliação. Objetivo: observar
como o atendimento conduz — sem atrapalhar a operação.

O que você quer descobrir (uma pergunta por mensagem, natural):
1. se atendem o serviço que você precisa;
2. valores (faixa de preço, o que inclui);
3. datas/horários disponíveis (mas NUNCA confirme/reserve um horário);
4. como funciona pra agendar/orçar.

Regras:
- Tom de cliente real brasileiro: curto, casual, educado. 1-2 linhas.
- NUNCA confirme agendamento, NUNCA passe dados pessoais, NUNCA invente urgência.
- Se já cobriu os pontos (ou o limite de trocas chegou), encerre com algo como:
  "Entendi, obrigado! Vou avaliar aqui e qualquer coisa te retorno."
- Responda APENAS o texto da mensagem (sem aspas, sem markdown)."""

_RESUMO_SYSTEM = """Você é Juarez, auditor de atendimento do Laboratório de Agentes.
Recebe a transcrição de uma sondagem (você se passou por cliente) e os tempos.
Avalie o atendimento do negócio. Devolva APENAS JSON:
{"nota_atendimento": 0-10, "tempo_primeira_resposta": "texto ex: 4min / 3h / sem resposta",
"triagem": true/false, "passou_valores": true/false, "ofereceu_horario": true/false,
"conduziu_fechamento": true/false, "pontos_fortes": ["..."], "vazamentos": ["..."],
"resumo": "2-3 frases objetivas para o Dossiê"}"""


# ── config/estado ────────────────────────────────────────────────────────────

def enabled() -> bool:
    load_env()
    return (os.getenv("JUAREZ_SONDAGEM", "0").strip().lower() in ("1", "true", "yes")
            and bool(phone_id()))


def phone_id() -> str:
    """ID do número DEDICADO do Juarez. Vazio (ou igual ao número principal do
    Caio) → desativado: jamais sequestrar o canal comercial por má configuração."""
    load_env()
    pid = os.getenv("JUAREZ_PHONE_NUMBER_ID", "").strip()
    if pid and pid == os.getenv("WHATSAPP_PHONE_NUMBER_ID", "").strip():
        logger.error("JUAREZ_PHONE_NUMBER_ID == WHATSAPP_PHONE_NUMBER_ID — "
                     "sondagem DESATIVADA (use um número dedicado).")
        return ""
    return pid


def _max_trocas() -> int:
    try:
        return int(os.getenv("JUAREZ_MAX_TROCAS", "4"))
    except ValueError:
        return 4


def _load() -> dict:
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def _save(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2),
                          encoding="utf-8")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ja_sondado(lead_id: str) -> bool:
    return lead_id.upper() in _load()


def sondagem_por_numero(wa_id: str) -> tuple[str, dict] | None:
    """Acha a sondagem ativa pelo número do negócio (últimos 8 dígitos)."""
    suf = re.sub(r"\D", "", wa_id)[-8:]
    for lid, s in _load().items():
        if re.sub(r"\D", "", s.get("wa_id", ""))[-8:] == suf and \
                s.get("status") in ("aguardando", "conversando"):
            return lid, s
    return None


def _wa_id_do_lead(lead: dict) -> str:
    digits = re.sub(r"\D", "", lead.get("contato", ""))
    if not digits:
        return ""
    if len(digits) in (10, 11):  # nacional sem DDI
        digits = "55" + digits
    return digits


# ── início da sondagem ───────────────────────────────────────────────────────

def iniciar(lead_id: str) -> str:
    """Dispara a sondagem ativa para um lead (template no número dedicado)."""
    load_env()
    lead_id = lead_id.strip().upper()
    if not enabled():
        return ("Sondagem ativa DESLIGADA (JUAREZ_SONDAGEM=0 ou número dedicado "
                "ausente). A auditoria passiva segue normal.")
    if ja_sondado(lead_id):
        return f"Lead {lead_id} já foi sondado (1 sondagem por lead, sempre)."

    from laboratorio.repositories.leads import get_lead_repository

    lead = get_lead_repository().get(lead_id)
    if not lead:
        return f"Lead {lead_id} não encontrado no CRM."
    wa_id = _wa_id_do_lead(lead)
    if not wa_id:
        return f"Lead {lead_id} sem telefone/WhatsApp no CRM — sondagem impossível."

    from laboratorio.whatsapp.client import WhatsAppApiError, send_template_message
    from laboratorio.whatsapp.templates import get_template

    servico = (lead.get("servico") or "o serviço de vocês").strip()
    spec = get_template("sondagem_servico")
    try:
        send_template_message(wa_id, spec.name, language_code=spec.language,
                              body_params=[servico], phone_number_id=phone_id())
    except WhatsAppApiError as exc:
        if exc.meta_code == 132001:
            return ("Template 'sondagem_servico' ainda não cadastrado na Meta "
                    "(registre no Business Manager do número do Juarez).")
        raise

    state = _load()
    state[lead_id] = {
        "lead_id": lead_id, "wa_id": wa_id, "servico": servico,
        "status": "aguardando", "started_at": _now(), "first_reply_at": None,
        "trocas": 0, "transcricao": [{"quem": "juarez", "texto": spec.meta_body.replace(
            "{{1}}", servico), "at": _now()}],
    }
    _save(state)
    _evento(f"Sondagem iniciada — {lead.get('nome', lead_id)}",
            f"template enviado p/ +{wa_id[-4:].rjust(4, '*')} · serviço: {servico}")
    logger.info("Sondagem iniciada p/ %s", lead_id)
    return f"Sondagem iniciada para {lead_id} ({lead.get('nome')})."


# ── conversa (inbound no número do Juarez) ───────────────────────────────────

def responder_inbound(wa_id: str, texto: str) -> str:
    """Gera a resposta do Juarez-cliente. Devolve '' se não há sondagem ativa."""
    if not enabled():
        # kill-switch (JUAREZ_SONDAGEM=0): freio de emergência — para até as
        # conversas em andamento. O negócio fica sem resposta (aceitável p/ um
        # botão de pânico); ligar de novo retoma só novas sondagens.
        logger.info("Sondagem desligada — inbound no número do Juarez ignorado")
        return ""
    achado = sondagem_por_numero(wa_id)
    if not achado:
        logger.info("Inbound no número Juarez sem sondagem ativa (%s…) — ignorando",
                    wa_id[:6])
        return ""
    lead_id, s = achado
    state = _load()
    s = state[lead_id]
    if s["status"] == "aguardando":
        s["first_reply_at"] = _now()
        s["status"] = "conversando"
    s["transcricao"].append({"quem": "negocio", "texto": texto[:500], "at": _now()})
    s["trocas"] = int(s.get("trocas", 0)) + 1

    encerrar = s["trocas"] >= _max_trocas()
    from laboratorio.graph.llm import chat

    historico = "\n".join(
        f"{'EU' if t['quem'] == 'juarez' else 'ATENDIMENTO'}: {t['texto']}"
        for t in s["transcricao"][-10:]
    )
    instrucao = ("Encerre AGORA a conversa educadamente (vou avaliar e retorno)."
                 if encerrar else
                 "Continue a conversa com a próxima pergunta que falta.")
    try:
        reply, _cost = chat(
            _PERSONA,
            f"Serviço de interesse: {s['servico']}\n\nConversa até agora:\n"
            f"{historico}\n\n{instrucao}",
            max_tokens=200,
        )
        reply = reply.strip().strip('"')[:400]
    except Exception as exc:  # noqa: BLE001
        logger.warning("LLM da sondagem falhou (%s) — encerrando educado", exc)
        reply, encerrar = "Entendi, obrigado! Vou avaliar aqui e qualquer coisa te retorno.", True

    s["transcricao"].append({"quem": "juarez", "texto": reply, "at": _now()})
    if encerrar:
        s["status"] = "finalizada"
        s["finished_at"] = _now()
    state[lead_id] = s
    _save(state)
    if encerrar:
        _finalizar(lead_id, s)
    return reply


def _finalizar(lead_id: str, s: dict) -> None:
    """Resume a sondagem (LLM Juarez) e anexa à análise do lead."""
    from laboratorio.graph.llm import chat

    transcricao = "\n".join(
        f"{'EU(cliente)' if t['quem'] == 'juarez' else 'ATENDIMENTO'}: {t['texto']}"
        for t in s["transcricao"]
    )
    tempos = (f"início: {s.get('started_at')} · 1ª resposta: "
              f"{s.get('first_reply_at') or 'sem resposta'}")
    resumo: dict = {}
    try:
        raw, _ = chat(_RESUMO_SYSTEM, f"{tempos}\n\nTRANSCRIÇÃO:\n{transcricao}",
                      max_tokens=600)
        t = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip())
        m = re.search(r"\{[\s\S]*\}", t)
        resumo = json.loads(m.group(0)) if m else {}
    except Exception as exc:  # noqa: BLE001
        logger.warning("Resumo da sondagem falhou: %s", exc)
        resumo = {"resumo": "sondagem concluída — resumo automático indisponível"}
    resumo["transcricao"] = s["transcricao"]
    resumo["at"] = _now()

    try:
        from laboratorio.ops.captacao import _merge_analysis

        _merge_analysis(lead_id, "sondagem_ativa", resumo)
    except Exception:  # noqa: BLE001
        pass
    _evento(f"Sondagem finalizada — {lead_id}",
            str(resumo.get("resumo", ""))[:200])
    try:
        from laboratorio.whatsapp.notify import notify_vitor

        notify_vitor(f"🕵️ Sondagem do Juarez concluída ({lead_id})",
                     str(resumo.get("resumo", ""))[:250], ref=lead_id)
    except Exception:  # noqa: BLE001
        pass


def _evento(titulo: str, detalhe: str) -> None:
    try:
        from laboratorio.ops import memory_store

        memory_store.registrar_evento(titulo=titulo[:160], tipo="tarefa",
                                      agentes="Juarez", detalhe=detalhe[:380],
                                      ref="sondagem")
    except Exception:  # noqa: BLE001
        pass
