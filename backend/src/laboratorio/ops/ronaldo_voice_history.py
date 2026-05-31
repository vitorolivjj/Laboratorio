"""Histórico persistente de comandos de voz do Ronaldo (TASK-009 v2)."""

from __future__ import annotations

import re
from datetime import datetime, timezone

from laboratorio.config import LOGS_DIR

RONALDO_VOICE_LOG = LOGS_DIR / "ronaldo_voz_comandos.md"
_MARKER = "<!-- Novas entradas acima desta linha -->"


def _ensure_log_file() -> None:
    if RONALDO_VOICE_LOG.is_file():
        return
    RONALDO_VOICE_LOG.parent.mkdir(parents=True, exist_ok=True)
    RONALDO_VOICE_LOG.write_text(
        "# Ronaldo — comandos de voz (Painel Maestro)\n\n"
        "Registro de comandos transcritos e respostas do Maestro (TASK-009).\n\n"
        "---\n\n"
        f"{_MARKER}\n",
        encoding="utf-8",
    )


def append_voice_command(*, command: str, normalized: str, reply: str) -> None:
    """Persiste comando e resposta no log markdown."""
    _ensure_log_file()
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    safe_reply = reply.replace("\n", " ").strip()
    if len(safe_reply) > 600:
        safe_reply = safe_reply[:600] + "…"
    entry = (
        f"### {stamp}\n"
        f"- **comando:** {command.strip()}\n"
        f"- **normalizado:** {normalized.strip()}\n"
        f"- **resposta:** {safe_reply}\n\n"
    )
    text = RONALDO_VOICE_LOG.read_text(encoding="utf-8")
    if _MARKER in text:
        text = text.replace(_MARKER, entry + _MARKER)
    else:
        text = entry + text
    RONALDO_VOICE_LOG.write_text(text, encoding="utf-8")


def list_voice_history(limit: int = 30) -> list[dict]:
    """Retorna entradas recentes do histórico (mais recente primeiro)."""
    _ensure_log_file()
    text = RONALDO_VOICE_LOG.read_text(encoding="utf-8")
    blocks = re.split(r"\n### ", text)
    entries: list[dict] = []

    for block in blocks[1:]:
        header, _, body = block.partition("\n")
        stamp = header.strip()
        cmd_m = re.search(r"\*\*comando:\*\*\s*(.+)", body)
        norm_m = re.search(r"\*\*normalizado:\*\*\s*(.+)", body)
        rep_m = re.search(r"\*\*resposta:\*\*\s*(.+)", body)
        if not cmd_m:
            continue
        entries.append(
            {
                "at": stamp,
                "command": cmd_m.group(1).strip(),
                "normalized": (norm_m.group(1).strip() if norm_m else ""),
                "reply": (rep_m.group(1).strip() if rep_m else ""),
            }
        )

    return entries[:limit]
