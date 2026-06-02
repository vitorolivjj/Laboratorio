"""Histórico de métricas do Painel Maestro (sparklines compartilhadas)."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from laboratorio.config import LOGS_DIR

METRICS_FILE = LOGS_DIR / "maestro_metrics.jsonl"
MIN_INTERVAL_SEC = 30
MAX_POINTS = 96


def _now_ms() -> int:
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def _last_append_ms() -> int | None:
    if not METRICS_FILE.is_file():
        return None
    try:
        lines = METRICS_FILE.read_text(encoding="utf-8").strip().splitlines()
        if not lines:
            return None
        last = json.loads(lines[-1])
        return int(last.get("t", 0))
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return None


def append_metric_from_overview(overview: dict[str, Any]) -> None:
    """Grava um ponto no jsonl (no máximo 1 a cada MIN_INTERVAL_SEC)."""
    now_ms = _now_ms()
    last = _last_append_ms()
    if last is not None and (now_ms - last) < MIN_INTERVAL_SEC * 1000:
        return

    point = {
        "t": now_ms,
        "wip": int(overview.get("wip_tasks") or 0),
        "msgs": int(overview.get("messages_today") or 0),
    }
    try:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        with METRICS_FILE.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(point, ensure_ascii=False) + "\n")
        _trim_file()
    except OSError:
        pass


def _trim_file() -> None:
    if not METRICS_FILE.is_file():
        return
    try:
        lines = METRICS_FILE.read_text(encoding="utf-8").splitlines()
        if len(lines) <= MAX_POINTS:
            return
        trimmed = lines[-MAX_POINTS:]
        METRICS_FILE.write_text("\n".join(trimmed) + "\n", encoding="utf-8")
    except OSError:
        pass


def get_metrics_history(hours: float = 24.0) -> dict[str, Any]:
    """Pontos das últimas N horas para sparklines (TV / multi-dispositivo)."""
    hours = max(0.5, min(hours, 168.0))
    cutoff_ms = int((datetime.now(timezone.utc) - timedelta(hours=hours)).timestamp() * 1000)
    points: list[dict[str, Any]] = []

    if METRICS_FILE.is_file():
        try:
            for line in METRICS_FILE.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    ts = int(obj.get("t", 0))
                    if ts >= cutoff_ms:
                        points.append(
                            {
                                "t": ts,
                                "wip": int(obj.get("wip", 0)),
                                "msgs": int(obj.get("msgs", 0)),
                            }
                        )
                except (json.JSONDecodeError, TypeError, ValueError):
                    continue
        except OSError:
            pass

    points.sort(key=lambda p: p["t"])
    return {
        "hours": hours,
        "points": points,
        "source": "server",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }
