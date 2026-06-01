"""Rastreamento de custo/tokens reais por execução de agente/crew.

Grava JSONL em backend/data/usage.jsonl para dar visibilidade de quanto cada
agente/modelo consome — substitui a estimativa fixa do painel por dados reais.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from laboratorio.config import DATA_DIR

logger = logging.getLogger("laboratorio.usage")

USAGE_FILE = DATA_DIR / "usage.jsonl"

# Preço aproximado em USD por 1M de tokens (input, output). Ajuste conforme contrato.
_PRICES: dict[str, tuple[float, float]] = {
    "gpt-5": (1.25, 10.0),
    "gpt-4o-mini": (0.15, 0.60),
    "claude-opus-4-8": (5.0, 25.0),
    "claude-sonnet-4-6": (3.0, 15.0),
    "claude-haiku-4-5-20251001": (0.80, 4.0),
    "claude-haiku-4-5": (0.80, 4.0),
}
_DEFAULT_PRICE = (1.0, 5.0)


def _price_for(model: str) -> tuple[float, float]:
    name = (model or "").split("/")[-1]
    return _PRICES.get(name, _DEFAULT_PRICE)


def estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    pin, pout = _price_for(model)
    cost = (prompt_tokens * pin + completion_tokens * pout) / 1_000_000
    return round(cost, 6)


def _coerce(metrics: Any) -> tuple[int, int]:
    """Extrai (prompt, completion) tokens de formatos variados do CrewAI/OpenAI."""
    if metrics is None:
        return 0, 0
    data = metrics
    if hasattr(metrics, "model_dump"):
        data = metrics.model_dump()
    elif hasattr(metrics, "__dict__") and not isinstance(metrics, dict):
        data = vars(metrics)
    if not isinstance(data, dict):
        return 0, 0
    p = data.get("prompt_tokens") or data.get("input_tokens") or 0
    c = data.get("completion_tokens") or data.get("output_tokens") or 0
    return int(p or 0), int(c or 0)


def record_usage(
    *,
    source: str,
    model: str = "",
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    metrics: Any = None,
    extra: dict | None = None,
) -> dict:
    """Registra uma linha de uso. Aceita métricas brutas do CrewAI via `metrics`."""
    if metrics is not None:
        prompt_tokens, completion_tokens = _coerce(metrics)
    cost = estimate_cost(model, prompt_tokens, completion_tokens)
    row = {
        "at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "source": source,
        "model": model,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
        "cost_usd": cost,
    }
    if extra:
        row.update(extra)
    try:
        USAGE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with USAGE_FILE.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    except OSError as exc:
        logger.warning("Falha ao gravar usage: %s", exc)
    logger.info("usage[%s] %s tokens=%d custo=$%.4f", source, model, row["total_tokens"], cost)
    return row


def summarize() -> dict:
    """Agrega tokens e custo do arquivo de uso (para o painel/relatórios)."""
    total_tokens = 0
    total_cost = 0.0
    by_model: dict[str, dict[str, float]] = {}
    if not USAGE_FILE.is_file():
        return {"total_tokens": 0, "total_cost_usd": 0.0, "by_model": {}}
    for line in USAGE_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        total_tokens += int(row.get("total_tokens", 0))
        total_cost += float(row.get("cost_usd", 0.0))
        m = row.get("model", "—")
        slot = by_model.setdefault(m, {"tokens": 0, "cost_usd": 0.0})
        slot["tokens"] += int(row.get("total_tokens", 0))
        slot["cost_usd"] += float(row.get("cost_usd", 0.0))
    return {
        "total_tokens": total_tokens,
        "total_cost_usd": round(total_cost, 4),
        "by_model": by_model,
    }
