"""Dossiê de Vazamentos — análise do Ronaldo + página (design Loide, build Dev).

Pipeline: junta o que o Donizete coletou (captação/Places) + auditoria de
atendimento do Juarez (passiva e, se houver, ativa) → o RONALDO produz o
diagnóstico (score, áreas, vazamentos, oportunidade) → a página HTML é
renderizada do template (assets/dossie_template.html) e publicada em
frontend/dossies/ (servida pela API em /d/{slug}.html) → aprovação do Vitor
(kind dossie_aprovacao) → APROVAR dispara a abordagem do Caio e move o lead
para `dossie_enviado`.

Config: DOSSIE_BASE_URL (default https://api.laboratorioagentes.com.br/d)
· LAB_WHATSAPP_PUBLICO (número p/ CTA "Quero meu Plano de Ataque"; sem ele o
botão não aparece) · DOSSIE_LLM_MODEL (default herda o padrão).
"""

from __future__ import annotations

import html
import json
import logging
import os
import re
import unicodedata
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from laboratorio.config import REPO_ROOT, load_env

logger = logging.getLogger("laboratorio.ops.dossie")

DOSSIES_DIR = REPO_ROOT / "frontend" / "dossies"
TEMPLATE = (REPO_ROOT / "backend" / "src" / "laboratorio" / "assets"
            / "dossie_template.html")

_SYSTEM = """Você é RONALDO MAESTRO, estrategista do Laboratório de Agentes.
Recebe MÉTRICAS objetivas de um negócio local (Google/Places: nota, nº de
avaliações, % negativas da amostra, nº de fotos, faixa de preço, horário; sinais
técnicos do site; textos de avaliações reais) e monta o DIAGNÓSTICO do Dossiê de
Vazamentos: onde o negócio perde cliente por falta de processo.

REGRAS INEGOCIÁVEIS:
- CADA vazamento DEVE ancorar num NÚMERO/MÉTRICA concreto dos dados (ex.:
  "nota 4,5 mas 40% das avaliações recentes são negativas", "apenas 1 foto para
  204 avaliações", "site sem HTTPS", "sem horário cadastrado") E, quando houver
  avaliação relevante, UMA citação LITERAL e curta entre aspas.
- NUNCA invente. Você NÃO sabe se o negócio responde avaliações, nem nada fora
  dos dados recebidos. Sem dado → não afirme. Proibido alegar "não responde
  avaliações" ou suposições sem métrica.
- 3 a 5 vazamentos, do mais grave ao menos. Foco na PERDA provável, tom
  respeitoso (nunca ridiculariza). Linguagem de dono (zero jargão de IA).
- O Dossiê abre os olhos mas NÃO entrega a solução (isso é o Plano de Ataque).

Devolva APENAS JSON válido:
{"score": 0-100 (quão provável que esse negócio perca cliente por falta de
processo — alto = mais vazamento),
"resumo": "2-3 frases do cenário, com pelo menos 1 número concreto",
"vazamentos": [{"nome": "título curto", "evidencia": "o que os DADOS mostram —
com número e/ou citação entre aspas", "impacto": "como isso perde cliente/dinheiro",
"risco": "Baixo|Médio|Alto"}],
"oportunidade": "a oportunidade principal em 1-2 frases",
"angulo_abordagem": "qual dor o Caio deve puxar na 1ª mensagem"}"""


def _slug(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:60] or "dossie"


def _model() -> str | None:
    load_env()
    return os.getenv("DOSSIE_LLM_MODEL", "").strip() or None


def _coletar_contexto(lead_id: str) -> tuple[dict, dict]:
    from laboratorio.repositories.leads import get_lead_repository

    lead = get_lead_repository().get(lead_id)
    if not lead:
        raise ValueError(f"Lead {lead_id} não encontrado no CRM.")
    analise: dict = {}
    try:
        from laboratorio.db import lead_assets

        analise = (lead_assets.get_analysis(lead_id) or {}).get("analise") or {}
    except Exception as exc:  # noqa: BLE001
        logger.warning("Sem análise no DB p/ %s (%s)", lead_id, exc)
    return lead, analise


def _diagnostico(lead: dict, analise: dict) -> dict:
    from laboratorio.graph.llm import chat

    cap = analise.get("captacao") or {}
    contexto = {
        "negocio": {k: lead.get(k) for k in
                    ("nome", "servico", "cidade", "contato", "observacoes")},
        "metricas_google": cap.get("metricas") or {},
        "site_probe": cap.get("site_probe"),
        "avaliacoes_amostra": cap.get("reviews") or [],
        "sinais_donizete": cap.get("sinais") or [],
        "auditoria_atendimento": analise.get("auditoria_atendimento") or {},
        "sondagem_ativa_juarez": {
            k: v for k, v in (analise.get("sondagem_ativa") or {}).items()
            if k != "transcricao"
        },
    }
    raw, _cost = chat(_SYSTEM, json.dumps(contexto, ensure_ascii=False),
                      model=_model(), max_tokens=1800)
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip())
    m = re.search(r"\{[\s\S]*\}", t)
    if not m:
        raise RuntimeError("Ronaldo não devolveu JSON válido no diagnóstico.")
    d = json.loads(m.group(0))
    if not d.get("vazamentos"):
        raise RuntimeError("Diagnóstico sem vazamentos — dados insuficientes p/ Dossiê.")
    return d


def _norm_status(s: str) -> str:
    """Normaliza o status p/ casar com as classes CSS (.st.bom/.atencao/.critico)."""
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()
    return s if s in ("bom", "atencao", "critico") else "atencao"


def _areas_dos_dados(analise: dict) -> list[dict]:
    """Áreas avaliadas DERIVADAS dos dados (não do LLM) — defensáveis e factuais."""
    cap = analise.get("captacao") or {}
    m = cap.get("metricas") or {}
    site = cap.get("site_probe") or {}
    areas: list[dict] = []

    nota, nav = m.get("nota"), m.get("n_avaliacoes") or 0
    fotos, horario = m.get("n_fotos"), m.get("horario_preenchido")
    if nota is not None:
        if (fotos == 0) or not horario:
            st = "critico"
        elif nota >= 4.5 and (fotos or 0) >= 10:
            st = "bom"
        else:
            st = "atencao"
        obs = f"Nota {nota} com {nav} avaliações"
        if fotos is not None:
            obs += f" · {fotos} foto(s)"
        if not horario:
            obs += " · sem horário cadastrado"
        areas.append({"nome": "Presença no Google", "status": st, "obs": obs})

    if not m.get("tem_site"):
        areas.append({"nome": "Site / Página", "status": "critico",
                      "obs": "Sem site vinculado ao perfil do Google"})
    elif site:
        if not site.get("no_ar"):
            st, obs = "critico", "Site fora do ar ou retornando erro"
        elif not site.get("https"):
            st, obs = "critico", "Site sem HTTPS (cadeado de segurança)"
        elif not site.get("tem_whatsapp"):
            st, obs = "atencao", "Site no ar, mas sem link de WhatsApp"
        else:
            st, obs = "bom", "Site no ar, com HTTPS e WhatsApp"
        areas.append({"nome": "Site / Página", "status": st, "obs": obs})

    tem_wpp = bool(m.get("tem_site") and site.get("tem_whatsapp"))
    if not tem_wpp:
        areas.append({"nome": "WhatsApp", "status": "atencao",
                      "obs": "Sem caminho claro de WhatsApp na presença pública"})

    pct = m.get("pct_negativas_amostra")
    if pct is not None and m.get("reviews_amostra"):
        st = "critico" if pct >= 40 else ("atencao" if pct >= 20 else "bom")
        areas.append({"nome": "Reputação / Atendimento", "status": st,
                      "obs": f"{pct}% das avaliações recentes (amostra) são negativas"})
    return areas[:6]


def _render(lead: dict, diag: dict, analise: dict) -> str:
    tpl = TEMPLATE.read_text(encoding="utf-8")
    esc = html.escape

    score = max(0, min(100, int(diag.get("score", 50))))
    if score <= 30:
        label, color = "baixo risco aparente", "#16a34a"
    elif score <= 60:
        label, color = "atenção", "#d97706"
    elif score <= 80:
        label, color = "vazamentos prováveis", "#ea580c"
    else:
        label, color = "vazamentos críticos", "#dc2626"

    _ROT = {"bom": "Bom", "atencao": "Atenção", "critico": "Crítico"}
    areas = _areas_dos_dados(analise) or (diag.get("areas") or [])
    areas_html = "".join(
        f'<div class="area"><b>{esc(str(a.get("nome", "")))}</b>'
        f'<span class="st {_norm_status(a.get("status"))}">'
        f'{_ROT[_norm_status(a.get("status"))]}</span>'
        f'<p>{esc(str(a.get("obs", "")))}</p></div>'
        for a in areas[:8]
    )
    riscos = {"alto": "alto", "médio": "medio", "medio": "medio", "baixo": "baixo"}
    vaz_html = "".join(
        f'<div class="vaz {riscos.get(str(v.get("risco", "")).lower(), "medio")}">'
        f'<span class="risco">risco {esc(str(v.get("risco", "Médio")))}</span>'
        f'<h3>{esc(str(v.get("nome", "")))}</h3>'
        f'<p><b>O que observamos:</b> {esc(str(v.get("evidencia", "")))}</p>'
        f'<p><b>Por que importa:</b> {esc(str(v.get("impacto", "")))}</p></div>'
        for v in (diag.get("vazamentos") or [])[:5]
    )

    zap = re.sub(r"\D", "", os.getenv("LAB_WHATSAPP_PUBLICO", ""))
    if zap:
        txt = "Recebi o Dossiê de Vazamentos e quero o Plano de Ataque."
        cta = (f'<a href="https://wa.me/{zap}?text={html.escape(txt)}">'
               "Quero meu Plano de Ataque</a>")
    else:  # sem número público: o Dossiê vai pelo WhatsApp do Caio → responder ali
        cta = ('<a href="#" onclick="return false" style="cursor:default">'
               "Responda esta conversa com <b>ATAQUE</b></a>")

    tz = ZoneInfo("America/Sao_Paulo")
    subs = {
        "{{NOME}}": esc(lead.get("nome", "")),
        "{{SEGMENTO_CIDADE}}": esc(" · ".join(
            x for x in (lead.get("servico", ""), lead.get("cidade", "")) if x)),
        "{{DATA}}": datetime.now(tz).strftime("%d/%m/%Y"),
        "{{SCORE}}": str(score),
        "{{SCORE_LABEL}}": esc(label),
        "{{SCORE_COLOR}}": color,
        "{{RESUMO}}": esc(str(diag.get("resumo", ""))),
        "{{AREAS_HTML}}": areas_html,
        "{{VAZAMENTOS_HTML}}": vaz_html,
        "{{OPORTUNIDADE}}": esc(str(diag.get("oportunidade", ""))),
        "{{CTA_LINK}}": cta,
    }
    out = tpl
    for k, v in subs.items():
        out = out.replace(k, v)
    return out


def gerar(lead_id: str, *, dry: bool = False) -> dict:
    """Gera o Dossiê do lead. dry=True só gera a página (sem aprovação/abordagem)."""
    load_env()
    lead_id = lead_id.strip().upper()
    lead, analise = _coletar_contexto(lead_id)

    # auditoria passiva do Juarez entra/atualiza antes do diagnóstico
    try:
        from laboratorio.ops import juarez_auditoria

        aud = juarez_auditoria.auditar(lead_id, analise=analise)
        if aud:
            analise["auditoria_atendimento"] = aud
    except Exception as exc:  # noqa: BLE001
        logger.warning("Auditoria passiva indisponível p/ %s: %s", lead_id, exc)

    diag = _diagnostico(lead, analise)
    page = _render(lead, diag, analise)

    slug = f"{lead_id.lower()}-{_slug(lead.get('nome', ''))}"
    DOSSIES_DIR.mkdir(parents=True, exist_ok=True)
    path = DOSSIES_DIR / f"{slug}.html"
    path.write_text(page, encoding="utf-8")
    base = os.getenv("DOSSIE_BASE_URL",
                     "https://api.laboratorioagentes.com.br/d").rstrip("/")
    url = f"{base}/{slug}.html"

    # registra o diagnóstico + url na análise do lead (Caio usa o ângulo)
    try:
        from laboratorio.ops.captacao import _merge_analysis

        _merge_analysis(lead_id, "dossie", {
            "url": url, "score": diag.get("score"),
            "angulo_abordagem": diag.get("angulo_abordagem"),
            "oportunidade": diag.get("oportunidade"),
            "vazamentos": [v.get("nome") for v in diag.get("vazamentos", [])],
            "gerado_em": datetime.now(timezone.utc).isoformat(),
        })
    except Exception:  # noqa: BLE001
        pass

    result = {"lead_id": lead_id, "url": url, "path": str(path),
              "score": diag.get("score"), "diag": diag, "dry": dry}
    if dry:
        return result

    from laboratorio.whatsapp.approvals import request_dossie_aprovacao

    aid = request_dossie_aprovacao(lead_id, lead.get("nome", lead_id), url,
                                   angulo=str(diag.get("angulo_abordagem", "")))
    result["approval_id"] = aid
    _evento(lead, url, diag)
    logger.info("Dossiê gerado p/ %s → %s (aprovação %s)", lead_id, url, aid)
    return result


def aprovar_e_abordar(lead_id: str, url: str) -> str:
    """Executado quando o Vitor APROVA o Dossiê: abordagem do Caio + status."""
    from laboratorio.repositories.leads import get_lead_repository
    from laboratorio.whatsapp.abordagem import abordar, template_para_segmento

    lead = get_lead_repository().get(lead_id)
    if not lead:
        return f"Dossiê aprovado, mas lead {lead_id} não está mais no CRM."

    partes = [f"Dossiê aprovado: {url}"]
    wa = re.sub(r"\D", "", lead.get("contato", ""))
    if wa:
        if len(wa) in (10, 11):
            wa = "55" + wa
        template = template_para_segmento(lead.get("servico", ""))
        partes.append(abordar(wa, template, lead.get("nome", "")))
    else:
        partes.append("Lead sem WhatsApp no CRM — abordagem manual necessária.")

    try:
        from laboratorio.ops import crm_lp_store
        from laboratorio.ops.captacao import CRM_LAB_MD

        crm_lp_store.update_lead_fields(lead_id, path=CRM_LAB_MD,
                                        status="dossie_enviado")
        partes.append("Status → dossie_enviado.")
    except Exception as exc:  # noqa: BLE001
        partes.append(f"(não moveu status: {exc})")
    return "\n".join(partes)


def _evento(lead: dict, url: str, diag: dict) -> None:
    try:
        from laboratorio.ops import memory_store

        memory_store.registrar_evento(
            titulo=f"Dossiê gerado — {lead.get('nome', '')}",
            tipo="tarefa", agentes="Ronaldo · Loide · Dev",
            detalhe=f"score {diag.get('score')}/100 · {url}",
            ref=str(lead.get("id", "")),
        )
    except Exception:  # noqa: BLE001
        pass
