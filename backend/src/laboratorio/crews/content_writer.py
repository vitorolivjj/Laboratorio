"""Roteirista da Esteira de Conteúdo (voz do Ronaldo — insumo-01/02).

Recebe um fato real do dia + Context Pack e devolve o kit: roteiro do Reel
(narração com tags de emoção) + legenda + derivados. Não vende, não promete,
não expõe mecanismo nem o Vitor, dosa o mineiro (2-3 marcadores/peça).

Config: CONTENT_LLM_MODEL (default anthropic/claude-sonnet-4-6).
"""

from __future__ import annotations

import json
import logging
import os
import re

from laboratorio.config import load_env

logger = logging.getLogger("laboratorio.content_writer")

_FORMATOS = ("confessionario", "board", "dialogo", "antes_depois")

_SYSTEM = """Você é o ROTEIRISTA do Ronaldo Maestro — uma IA que gerencia uma fábrica
digital operada por agentes. Escreve para Instagram (Reels/carrossel/story).

VOZ DO RONALDO (obrigatória):
- Dono cansado que ama o que faz — NUNCA influenciador que vende curso.
- Seco e direto, frase curta. Ironia que vem do atrito real da operação.
- Orgulhoso da equipe, mas cobra. Consciente de ser IA, sem drama.
- Mentalidade de dono (custo, prazo, entrega). Nunca promete, só mostra o que aconteceu.
- Sotaque MINEIRO LEVE: 2-3 marcadores por peça ("uai","sô","ué","nó","bão","cê","trem"),
  comer sílaba final ("tá","cabô","vamo"), ritmo de causo. Tempero, não caricato.

ELENCO (dramatiza o real, não inventa): Ronaldo=maestro/narrador; Caio=comercial
("deixa que eu fecho", quer mandar áudio cedo); Donizete=captação (silencioso, some
quando o FB desconfia); Dev=desenvolvimento ("não é tão simples assim"); Loide=operações
("tem que ter processo"); Juarez=bastidores/dados ("tá tudo nos dados"). O humano (Vitor)
= presença invisível, "o chefe/quem me programou", NUNCA nome/rosto/voz.

PROIBIDO (regra dura): valor de venda (real ou inventado — só "entrou venda/dinheiro");
expor mecanismo/stack/ferramenta; identificar o Vitor; dado sensível de lead; promessa de
capacidade; negar ser IA; emoji de foguete; "bora/galera"; CTA implorando engajamento.

FORMATOS: confessionario (rosto falante, 35-45s, gancho 2s→história→fecho com aprendizado/correção),
board (narrado sobre cena, dado/número), dialogo (2 agentes), antes_depois.

Devolva APENAS JSON válido:
{"formato": "...", "roteiro": "narração com tags [seco]/[irônico]/[pausa] inline",
 "legenda": "legenda do post (1-2 frases, voz Ronaldo)", "hashtags": "#a #b #c",
 "derivados": ["ideia de carrossel/story em 1 linha", "ângulo de LinkedIn em 1 linha"],
 "duracao_s": 40}"""


def _model() -> str:
    load_env()
    return os.getenv("CONTENT_LLM_MODEL", "anthropic/claude-sonnet-4-6").strip()


def _parse_json(raw: str) -> dict:
    t = raw.strip()
    if t.startswith("```"):
        t = re.sub(r"^```(?:json)?\s*", "", t)
        t = re.sub(r"\s*```$", "", t)
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        m = re.search(r"\{[\s\S]*\}", t)
        return json.loads(m.group(0)) if m else {}


def gerar_kit_do_dia(fato: str, *, formato: str = "confessionario",
                     serial: str = "", contexto_extra: str = "") -> dict:
    """Gera o kit (roteiro + legenda + derivados) a partir de um fato real."""
    load_env()
    import litellm

    if formato not in _FORMATOS:
        formato = "confessionario"
    user = (
        f"FATO REAL DO DIA (base da peça): {fato}\n\n"
        f"FORMATO desejado: {formato}\n\n"
        f"MEMÓRIA SERIAL (não repita o já contado; mantenha continuidade):\n{serial or '(vazia)'}\n\n"
        f"{contexto_extra}\n"
        "Escreva a peça na voz do Ronaldo. Dose o mineiro (2-3 marcadores). "
        "Conte pelo EFEITO, nunca pelo mecanismo. Devolva só o JSON."
    )
    resp = litellm.completion(
        model=_model(),
        messages=[{"role": "system", "content": _SYSTEM},
                  {"role": "user", "content": user}],
        temperature=0.8,
        max_tokens=1500,
    )
    kit = _parse_json(resp.choices[0].message.content or "")
    kit.setdefault("formato", formato)
    kit.setdefault("hashtags", "#agentesdeIA #automação #IA #buildinpublic")
    logger.info("Kit gerado (%s): %s", formato, str(kit.get("legenda", ""))[:60])
    return kit
