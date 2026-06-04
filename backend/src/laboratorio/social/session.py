"""Estado da sessão Donizete — grupos visitados, perfis analisados, rodízio de posts."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from laboratorio.config import LOGS_DIR

SESSION_FILE = LOGS_DIR / "donizete_fb_session.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_session() -> dict:
    if not SESSION_FILE.is_file():
        return {}
    try:
        return json.loads(SESSION_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def save_session(data: dict) -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    data["updated_at"] = _now_iso()
    SESSION_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def reset_session(*, task_id: str = "LP-PINTOR-001", rodada: int = 3) -> dict:
    data = {
        "task_id": task_id,
        "rodada": rodada,
        "restarted_at": _now_iso(),
        "visited_groups": [],
        "analyzed_profiles": [],
        "captured_leads": [],
        "posts_hoje": 0,
        "ultimo_modo": None,
    }
    save_session(data)
    return data


def mark_group_visited(url: str, name: str) -> None:
    data = load_session()
    visited = data.setdefault("visited_groups", [])
    norm = url.split("?")[0].rstrip("/")
    if not any(v.get("url", "").rstrip("/") == norm for v in visited):
        visited.append({"url": norm, "name": name, "at": _now_iso()})
    save_session(data)


def mark_profile_analyzed(url: str) -> None:
    data = load_session()
    profiles = data.setdefault("analyzed_profiles", [])
    norm = url.split("?")[0].rstrip("/")
    if norm not in profiles:
        profiles.append(norm)
    save_session(data)


def was_profile_analyzed(url: str) -> bool:
    norm = url.split("?")[0].rstrip("/")
    return norm in (load_session().get("analyzed_profiles") or [])
