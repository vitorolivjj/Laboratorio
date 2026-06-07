"""Auditoria de Conteúdo da Esteira (insumo-03) — o gate da credibilidade.

Classifica cada peça em verde / amarelo / vermelho. Roda 2x: no texto (antes de
gerar voz/vídeo) e na peça final. vermelho→descarta+log; amarelo→fila do Vitor
(approvals existente); verde→segue.

Config: CONTENT_LLM_MODEL.
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Literal

from laboratorio.config import load_env

logger = logging.getLogger("laboratorio.content_audit")

Cor = Literal["verde", "amarelo", "vermelho"]

_SYSTEM = """Você é a AUDITORIA DO RONALDO — o gate que protege a credibilidade do
Laboratório de Agentes IA. Classifica a peça em verde, amarelo ou vermelho.

TESTE ÚNICO: "Se a audiência descobrisse exatamente como esta peça foi feita, a
confiança aumentaria ou cairia?" Aumentaria→verde; cairia→vermelho; não sei→amarelo.

🔴 VERMELHO (descarta): mentira factual; VALOR de venda exposto (real ou inventado —
só vale "entrou venda/dinheiro", nunca cifra); expõe mecanismo interno (stack, ferramenta,
prompt, arquitetura, credencial); identifica o Vitor (nome/rosto/voz); dado sensível de
lead/cliente; promessa de capacidade que a fábrica não faz; Ronaldo nega ser IA / afirma
ser humano; exposição que gere risco real à operação.

🟡 AMARELO (sobe pro Vitor): menção a cliente/lead mesmo anonimizada; qualquer número/valor;
tema sensível (pode soar arrogante/polêmico); formato/série em 1º uso; post de estreia/marco;
resposta a crítica/pergunta comercial; cita projeto interno não público; tom no limite (ironia
que pode ler como deboche).

🟢 VERDE (publica direto): nasce de fato real (ou dramatização honesta); conta pelo EFEITO
(não pelo mecanismo); zero identificação do Vitor; zero dado sensível; nenhuma promessa;
mantém transparência (Ronaldo é IA); voz do Ronaldo + template aprovado.

Devolva APENAS JSON: {"cor": "verde|amarelo|vermelho", "motivo": "1 frase objetiva",
"gatilho": "qual regra disparou (ou 'nenhum')"}"""


def _model() -> str:
    load_env()
    return os.getenv("CONTENT_LLM_MODEL", "anthropic/claude-sonnet-4-6").strip()


def _parse(raw: str) -> dict:
    t = raw.strip()
    if t.startswith("```"):
        t = re.sub(r"^```(?:json)?\s*", "", t)
        t = re.sub(r"\s*```$", "", t)
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        m = re.search(r"\{[\s\S]*\}", t)
        return json.loads(m.group(0)) if m else {}


def classificar(peca: str, *, estagio: str = "texto") -> tuple[Cor, str]:
    """Classifica a peça. Retorna (cor, motivo). Default seguro = amarelo."""
    load_env()
    import litellm

    try:
        resp = litellm.completion(
            model=_model(),
            messages=[{"role": "system", "content": _SYSTEM},
                      {"role": "user", "content": f"Estágio: {estagio}\n\nPEÇA:\n{peca}"}],
            temperature=0.1,
            max_tokens=400,
        )
        d = _parse(resp.choices[0].message.content or "")
    except Exception as exc:  # noqa: BLE001 — na dúvida, segura no amarelo
        logger.warning("Auditoria falhou (%s) — defaulta amarelo", exc)
        return "amarelo", f"auditoria indisponível: {exc}"

    cor = str(d.get("cor", "amarelo")).strip().lower()
    if cor not in ("verde", "amarelo", "vermelho"):
        cor = "amarelo"
    motivo = str(d.get("motivo", "")).strip() or d.get("gatilho", "—")
    logger.info("Auditoria [%s]: %s — %s", estagio, cor, motivo[:80])
    return cor, motivo  # type: ignore[return-value]


def aplicar(cor: Cor, peca_resumo: str, *, ref: str = "") -> str:
    """Roteia conforme a cor: vermelho→log/descarte; amarelo→approvals; verde→segue."""
    if cor == "vermelho":
        _log_evento("Conteúdo DESCARTADO (vermelho)", peca_resumo, tipo="erro", ref=ref)
        return "descartado"
    if cor == "amarelo":
        _enfileira_aprovacao(peca_resumo, ref=ref)
        return "aprovacao"
    return "publicar"


def _log_evento(titulo: str, detalhe: str, *, tipo: str = "tarefa", ref: str = "") -> None:
    try:
        from laboratorio.ops import memory_store

        memory_store.registrar_evento(titulo=titulo[:160], tipo=tipo, agentes="Esteira",
                                      detalhe=detalhe[:400], ref=ref)
    except Exception:  # noqa: BLE001
        pass


def _enfileira_aprovacao(peca_resumo: str, *, ref: str = "") -> None:
    """Amarelo → fila de aprovação do Vitor (WhatsApp). Reusa o que existir."""
    try:
        from laboratorio.whatsapp.notify import notify_vitor

        notify_vitor("🟡 Conteúdo aguardando aprovação", peca_resumo[:300],
                     action="Aprovar/ajustar a peça", ref=ref)
    except Exception:  # noqa: BLE001
        _log_evento("Conteúdo amarelo (aprovação)", peca_resumo, ref=ref)
