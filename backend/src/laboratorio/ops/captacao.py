"""Captação do Donizete por célula (segmento × área) via Google Places.

Fluxo: varrer célula → pontuar cada negócio (matriz 0–10 do plano: dor,
pagamento, vazamento, canal, potencial — 0–2 cada) → registrar os 6+ no CRM
oficial (crm_laboratorio) com sinais e contato preenchidos → notificar resumo.

Quem dispara: aprovação do Vitor (kind celula_captacao, sugerida pelo Ronaldo)
ou CLI `captacao-celula`. Idempotente por nome (não duplica lead existente).

Config: GOOGLE_PLACES_API_KEY · CAPTACAO_LLM_MODEL (default herda o padrão)
· CAPTACAO_MAX_RESULTS (default 40) · CAPTACAO_SCORE_MINIMO (default 6).
"""

from __future__ import annotations

import json
import logging
import os
import re
import unicodedata
from datetime import datetime, timezone

from laboratorio.config import LOGS_DIR, REPO_ROOT, load_env

logger = logging.getLogger("laboratorio.ops.captacao")

CELULAS_STATE = LOGS_DIR / "celulas_state.json"
CRM_LAB_MD = REPO_ROOT / "crm" / "crm_laboratorio.md"

_SCORE_SYSTEM = """Você é Donizete, caçador de vazamentos do Laboratório de Agentes.
Recebe os sinais públicos de UM negócio local (Google Maps) e pontua o potencial
dele como lead, pela matriz oficial (0–2 cada critério):

- dor: sinais de que perde cliente por desorganização (reviews citando demora,
  falta de resposta, dificuldade de contato; canal fraco) — 0 sem sinal · 1 provável · 2 evidente
- pagamento: capacidade de pagar (volume de avaliações, nota, porte aparente,
  segmento com ticket) — 0 baixa · 1 média · 2 boa
- vazamento: vazamento VISÍVEL (sem site, perfil incompleto, sem horário,
  reviews sem resposta, presença mal cuidada apesar de demanda) — 0 não · 1 provável · 2 claro
- canal: canal de atendimento existe e importa (telefone/WhatsApp visível,
  negócio que vive de agendamento/orçamento) — 0 fraco · 1 existe · 2 forte
- potencial: potencial de virar Sprint depois (processo a organizar) — 0 baixo · 1 médio · 2 alto

Regra do plano: negócio COM demanda aparente e presença mal cuidada é o alvo.
Negócio sem operação visível ou sem canal de contato pontua baixo.

Devolva APENAS JSON:
{"dor":0-2,"pagamento":0-2,"vazamento":0-2,"canal":0-2,"potencial":0-2,
"sinais":["até 4 sinais concretos observados"],"resumo":"1 frase do porquê"}"""


def _model() -> str | None:
    load_env()
    return os.getenv("CAPTACAO_LLM_MODEL", "").strip() or None


def _norm_nome(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def _parse_json(raw: str) -> dict:
    t = raw.strip()
    t = re.sub(r"^```(?:json)?\s*", "", t)
    t = re.sub(r"\s*```$", "", t)
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        m = re.search(r"\{[\s\S]*\}", t)
        return json.loads(m.group(0)) if m else {}


def pontuar(place: dict, reviews: list[dict]) -> dict:
    """Pontua um negócio (LLM lê os sinais + reviews). Devolve score + sinais."""
    from laboratorio.graph.llm import chat

    sinais_obj = {
        "nome": place.get("nome"),
        "tem_site": bool(place.get("site")),
        "tem_telefone": bool(place.get("telefone")),
        "nota": place.get("nota"),
        "n_avaliacoes": place.get("n_avaliacoes"),
        "horario_preenchido": place.get("horario_preenchido"),
        "endereco": place.get("endereco"),
        "reviews": [
            {"nota": r.get("nota"), "texto": r.get("texto", "")[:300]} for r in reviews[:5]
        ],
    }
    try:
        raw, _cost = chat(_SCORE_SYSTEM, json.dumps(sinais_obj, ensure_ascii=False),
                          model=_model(), max_tokens=500)
        d = _parse_json(raw)
    except Exception as exc:  # noqa: BLE001 — sem LLM, pontua só pelo objetivo
        logger.warning("Pontuação LLM falhou (%s) — usando fallback objetivo", exc)
        d = {}

    def _c(key: str, fallback: int) -> int:
        try:
            return max(0, min(2, int(d.get(key, fallback))))
        except (TypeError, ValueError):
            return fallback

    # fallback objetivo (sem LLM): vazamento por ausências; canal por telefone
    fb_vaz = 2 if not place.get("site") and not place.get("horario_preenchido") else 1
    fb_canal = 2 if place.get("telefone") else 0
    fb_pag = 2 if (place.get("n_avaliacoes") or 0) >= 50 else 1

    comp = {
        "dor": _c("dor", 1),
        "pagamento": _c("pagamento", fb_pag),
        "vazamento": _c("vazamento", fb_vaz),
        "canal": _c("canal", fb_canal),
        "potencial": _c("potencial", 1),
    }
    return {
        "score": sum(comp.values()),
        "componentes": comp,
        "sinais": [str(s)[:140] for s in (d.get("sinais") or [])][:4],
        "resumo": str(d.get("resumo", ""))[:200],
    }


def _leads_existentes() -> set[str]:
    from laboratorio.repositories.leads import get_lead_repository

    try:
        return {_norm_nome(ld.get("nome", "")) for ld in get_lead_repository().all()}
    except Exception:  # noqa: BLE001
        return set()


def _save_celula(key: str, info: dict) -> None:
    try:
        state = json.loads(CELULAS_STATE.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        state = {}
    state[key] = info
    CELULAS_STATE.parent.mkdir(parents=True, exist_ok=True)
    CELULAS_STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2),
                             encoding="utf-8")


def celulas_varridas() -> dict:
    try:
        return json.loads(CELULAS_STATE.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def _merge_analysis(lead_id: str, key: str, value: dict) -> None:
    """Anexa um bloco à análise do lead no DB (best-effort; markdown é a fonte).

    O dual_write markdown→Postgres é assíncrono, então a linha do lead pode ainda
    não existir quando este UPDATE roda (set_analysis é UPDATE puro → 0 linhas,
    silencioso). ensure_lead garante a linha (INSERT on-conflict-do-nothing) antes,
    e o mirror posterior completa os campos planos sem tocar a coluna `analise`."""
    try:
        from laboratorio.db import lead_assets

        lead_assets.ensure_lead(lead_id)
        atual = lead_assets.get_analysis(lead_id) or {}
        analise = atual.get("analise") or {}
        if not isinstance(analise, dict):
            analise = {}
        analise[key] = value
        if not lead_assets.set_analysis(lead_id, analise=analise):
            logger.warning("Análise '%s' de %s não persistiu (lead ausente em lab_leads)",
                           key, lead_id)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Sem DB p/ análise de %s (%s) — segue só no markdown", lead_id, exc)


def varrer_celula(segmento: str, area: str, *, dry: bool = False,
                  max_results: int | None = None) -> dict:
    """Varre a célula e registra leads 6+ no CRM. Devolve o resumo da varredura."""
    load_env()
    from laboratorio.ops import places
    from laboratorio.ops.crm_store import add_lead_segment

    segmento, area = segmento.strip(), area.strip()
    limite = max_results or int(os.getenv("CAPTACAO_MAX_RESULTS", "40"))
    minimo = int(os.getenv("CAPTACAO_SCORE_MINIMO", "6"))
    key = f"{segmento}|{area}".lower()

    negocios = places.buscar_celula(segmento, area, max_results=limite)
    existentes = _leads_existentes()
    registrados: list[dict] = []
    avaliados = 0

    for place in negocios:
        if not place.get("nome"):
            continue
        if _norm_nome(place["nome"]) in existentes:
            logger.info("Captação: '%s' já está no CRM — pulando", place["nome"])
            continue
        det = {"reviews": [], "n_fotos": 0}
        try:
            if place.get("place_id"):
                det = places.detalhes(place["place_id"])
        except Exception as exc:  # noqa: BLE001
            logger.warning("Detalhe falhou p/ %s: %s", place.get("nome"), exc)
        aval = pontuar(place, det.get("reviews", []))
        avaliados += 1
        if aval["score"] < minimo:
            continue

        sinais_txt = "; ".join(aval["sinais"]) or aval["resumo"]
        obs = (f"score {aval['score']}/10 · {sinais_txt} · "
               f"nota {place.get('nota', '—')} ({place.get('n_avaliacoes', 0)} aval.) · "
               f"{place.get('maps_url', '')}")[:380]
        if dry:
            registrados.append({"nome": place["nome"], "score": aval["score"],
                                "sinais": aval["sinais"], "dry": True})
            continue

        lead = add_lead_segment(
            CRM_LAB_MD,
            nome=place["nome"],
            contato=place.get("telefone", ""),
            cidade=area,
            servico=segmento,
            origem=f"places:{segmento}/{area}",
            status="vazamento_provavel",
            prioridade="P1" if aval["score"] >= 8 else "P2",
            score=str(aval["score"]),
            observacoes=obs,
        )
        existentes.add(_norm_nome(place["nome"]))
        _merge_analysis(lead["id"], "captacao", {
            "celula": {"segmento": segmento, "area": area},
            "place_id": place.get("place_id"),
            "maps_url": place.get("maps_url"),
            "site": place.get("site"),
            "nota": place.get("nota"),
            "n_avaliacoes": place.get("n_avaliacoes"),
            "n_fotos": det.get("n_fotos"),
            "horario_preenchido": place.get("horario_preenchido"),
            "componentes": aval["componentes"],
            "sinais": aval["sinais"],
            "resumo": aval["resumo"],
            "reviews": det.get("reviews", [])[:5],
        })
        registrados.append({"id": lead["id"], "nome": place["nome"],
                            "score": aval["score"], "sinais": aval["sinais"]})

    resumo = {
        "celula": {"segmento": segmento, "area": area},
        "encontrados": len(negocios),
        "avaliados": avaliados,
        "registrados": len(registrados),
        "leads": registrados,
        "dry": dry,
        "at": datetime.now(timezone.utc).isoformat(),
    }
    if not dry:
        _save_celula(key, {k: v for k, v in resumo.items() if k != "leads"} |
                     {"ids": [r.get("id") for r in registrados]})
        _log_evento(resumo)
        _notify(resumo)
    logger.info("Captação célula %s: %d encontrados · %d registrados",
                key, len(negocios), len(registrados))
    return resumo


def _log_evento(resumo: dict) -> None:
    try:
        from laboratorio.ops import memory_store

        c = resumo["celula"]
        memory_store.registrar_evento(
            titulo=f"Captação: célula {c['segmento']} / {c['area']}",
            tipo="tarefa", agentes="Donizete",
            detalhe=(f"{resumo['encontrados']} encontrados · "
                     f"{resumo['registrados']} registrados no CRM (score 6+)"),
            ref="captacao",
        )
    except Exception:  # noqa: BLE001
        pass


def _notify(resumo: dict) -> None:
    try:
        from laboratorio.whatsapp.notify import notify_vitor

        c = resumo["celula"]
        tops = " · ".join(f"{r['nome']} ({r['score']})" for r in resumo["leads"][:5])
        notify_vitor(
            f"🎯 Captação concluída — {c['segmento']} em {c['area']}",
            f"{resumo['encontrados']} negócios · {resumo['registrados']} leads 6+ no CRM. "
            f"Top: {tops}"[:280],
            action="Ver no painel (CRM → Captação)", ref="captacao",
        )
    except Exception:  # noqa: BLE001
        pass
