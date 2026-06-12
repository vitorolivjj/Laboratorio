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
Recebe os dados públicos de um negócio local (coleta do Donizete via Google,
reviews, e — quando houver — sondagem de atendimento do Juarez) e monta o
DIAGNÓSTICO do Dossiê de Vazamentos: onde esse negócio está perdendo cliente
por falta de processo em captação, atendimento ou comercial.

Regras do produto (inegociáveis):
- só afirme o que tem EVIDÊNCIA nos dados; sem evidência → não inventar;
- linguagem de dono de negócio (zero jargão técnico, zero IA-hype);
- 3 a 5 vazamentos, cada um com evidência concreta e impacto provável;
- tom respeitoso: aponta a perda, nunca ridiculariza;
- o Dossiê abre os olhos mas NÃO entrega a solução (isso é o Plano de Ataque).

Devolva APENAS JSON válido:
{"score": 0-100, "resumo": "2-3 frases do cenário",
"areas": [{"nome": "Presença no Google|Site/Página|Instagram|WhatsApp|Atendimento|Prova social|...",
"status": "bom|atencao|critico", "obs": "frase curta"}],
"vazamentos": [{"nome": "...", "evidencia": "o que foi observado",
"impacto": "como isso perde cliente/dinheiro", "risco": "Baixo|Médio|Alto"}],
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

    contexto = {
        "negocio": {k: lead.get(k) for k in
                    ("nome", "servico", "cidade", "contato", "observacoes")},
        "captacao_donizete": analise.get("captacao") or {},
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


def _render(lead: dict, diag: dict) -> str:
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

    areas_html = "".join(
        f'<div class="area"><b>{esc(str(a.get("nome", "")))}</b>'
        f'<span class="st {esc(str(a.get("status", "atencao")))}">'
        f'{ {"bom": "Bom", "atencao": "Atenção", "critico": "Crítico"}.get(str(a.get("status")), "Atenção") }</span>'
        f'<p>{esc(str(a.get("obs", "")))}</p></div>'
        for a in (diag.get("areas") or [])[:8]
    )
    riscos = {"alto": "alto", "médio": "", "medio": "", "baixo": "baixo"}
    vaz_html = "".join(
        f'<div class="vaz {riscos.get(str(v.get("risco", "")).lower(), "")}">'
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
    else:
        cta = ""

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
    page = _render(lead, diag)

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
