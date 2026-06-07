"""Curadoria de pauta da Esteira (papel do Ronaldo).

Coleta fatos reais (log de eventos + banco semente do insumo-02) e escolhe a
peça-pilar do dia — "interessa a quem está de fora?" — sem repetir o já contado
(memória serial). Saída: 1 fato-pilar; o resto vira estoque.

Config: CONTENT_LLM_MODEL.
"""

from __future__ import annotations

import logging
import os

from laboratorio.config import MEMORIA_DIR, load_env

logger = logging.getLogger("laboratorio.content_pauta")

SERIAL_FILE = MEMORIA_DIR / "serial_content.md"

# Banco semente (insumo-02 §4) — fatos reais do projeto. Nunca o valor da venda.
BANCO_SEMENTE = [
    "Primeira venda real existe (LP Pintor, prova de conceito) — citar como 'entrou venda', nunca o valor.",
    "Captação do Donizete reiniciou várias vezes no mesmo dia (persistência vs. Facebook).",
    "Patrulha de madrugada acha tarefas paradas há +12h e cobra o responsável (que é um agente).",
    "WIP máximo de 3 tarefas — a fábrica se recusa a fazer tudo ao mesmo tempo.",
    "Regra do Caio: a primeira abordagem ao lead nunca é áudio.",
    "VitorOS (projeto interno) está pausado até a LP escalar — decisão de foco.",
    "Webflow foi abandonado; a produção da LP virou in-house.",
]


def _model() -> str:
    load_env()
    return os.getenv("CONTENT_LLM_MODEL", "anthropic/claude-sonnet-4-6").strip()


def ler_serial() -> str:
    try:
        return SERIAL_FILE.read_text(encoding="utf-8")
    except Exception:  # noqa: BLE001
        return ""


def coletar_fatos(limit_eventos: int = 25) -> list[str]:
    """Fatos candidatos: eventos recentes do log + banco semente."""
    fatos: list[str] = []
    try:
        from laboratorio.repositories.events import get_event_repository

        for e in get_event_repository().recent(limit=limit_eventos):
            t = str(e.get("title", "")).strip()
            d = str(e.get("detail", "")).strip()
            tipo = str(e.get("type", "")).lower()
            if not t or tipo in ("deploy",):  # deploy/infra não é pauta
                continue
            fatos.append(f"{t}{(' — ' + d) if d and d not in ('—', '') else ''}"[:200])
    except Exception as exc:  # noqa: BLE001
        logger.warning("coletar_fatos: log indisponível (%s)", exc)
    fatos.extend(BANCO_SEMENTE)
    # dedup preservando ordem
    seen, out = set(), []
    for f in fatos:
        k = f.lower()[:80]
        if k not in seen:
            seen.add(k)
            out.append(f)
    return out


def escolher_fato(*, fatos: list[str] | None = None) -> str:
    """Escolhe a peça-pilar do dia (LLM): o que mais interessa a quem está de fora,
    sem repetir o já contado (memória serial)."""
    load_env()
    import litellm

    fatos = fatos or coletar_fatos()
    if not fatos:
        return BANCO_SEMENTE[0]
    serial = ler_serial()
    lista = "\n".join(f"- {f}" for f in fatos[:30])
    sys = (
        "Você é o Ronaldo, curador de pauta da fábrica. Escolha UM fato para virar a "
        "peça-pilar do dia. Critério: 'interessa a quem está de FORA da operação?' — "
        "história com efeito, humor seco ou tensão real. NÃO repita o que já foi contado. "
        "Responda APENAS com o fato escolhido (uma linha), sem aspas nem explicação."
    )
    user = f"JÁ CONTADO (não repetir):\n{serial[:2000] or '(nada ainda)'}\n\nCANDIDATOS:\n{lista}"
    try:
        resp = litellm.completion(
            model=_model(),
            messages=[{"role": "system", "content": sys}, {"role": "user", "content": user}],
            temperature=0.5, max_tokens=200,
        )
        escolhido = (resp.choices[0].message.content or "").strip().lstrip("-").strip()
        return escolhido or fatos[0]
    except Exception as exc:  # noqa: BLE001
        logger.warning("escolher_fato falhou (%s) — usa o primeiro", exc)
        return fatos[0]


def registrar_publicado(fato: str, legenda: str) -> None:
    """Anexa o fato à seção 'Já contado' da memória serial (evita repetição)."""
    from datetime import datetime, timezone

    try:
        SERIAL_FILE.parent.mkdir(parents=True, exist_ok=True)
        head = SERIAL_FILE.read_text(encoding="utf-8") if SERIAL_FILE.exists() else "# Memória Serial — Esteira\n\n## Já contado\n"
        if "## Já contado" not in head:
            head += "\n## Já contado\n"
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        head += f"- [{stamp}] {fato[:160]} · legenda: {legenda[:80]}\n"
        SERIAL_FILE.write_text(head, encoding="utf-8")
    except Exception as exc:  # noqa: BLE001
        logger.warning("registrar_publicado falhou: %s", exc)
