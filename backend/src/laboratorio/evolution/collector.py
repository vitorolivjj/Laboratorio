"""Coleta sinais do repo para o resumo diário."""

from __future__ import annotations

import re
from datetime import datetime, timezone

from laboratorio.config import LOGS_DIR, MEMORIA_DIR, TASKS_DIR
from laboratorio.memory.context import augment_with_semantic_memory
from laboratorio.ops import parsers


def _tail_sections(path, marker: str, max_blocks: int = 5) -> str:
    if not path.is_file():
        return ""
    text = path.read_text(encoding="utf-8")
    if marker not in text:
        return text[-2000:] if len(text) > 2000 else text
    part = text.split(marker, 1)[-1]
    blocks = re.split(r"(?=^### )", part, flags=re.MULTILINE)
    blocks = [b.strip() for b in blocks if b.strip()][:max_blocks]
    return "\n\n".join(blocks)


def collect_daily_context() -> str:
    """Monta contexto das últimas ~24h para o LLM."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    parts = [f"Data UTC: {today}"]

    eventos = LOGS_DIR / "eventos.md"
    if eventos.is_file():
        text = eventos.read_text(encoding="utf-8")
        entries = re.findall(r"^### \d{4}-\d{2}-\d{2} —.*?(?=^### |\Z)", text, re.MULTILINE | re.DOTALL)
        recent = entries[-8:]
        if recent:
            parts.append("## Eventos recentes\n" + "\n".join(e[:400] for e in recent))

    parts.append("## Concluídas recentes\n" + _tail_sections(TASKS_DIR / "concluidas.md", "## Concluídas", 4))

    exec_md = parsers.read_text(TASKS_DIR / "executando.md")
    active = parsers.parse_executando_tasks(exec_md)
    if active:
        lines = [f"- {t['id']}: {t['title']}" for t in active]
        parts.append("## Em execução\n" + "\n".join(lines))
    else:
        parts.append("## Em execução\n(nenhuma)")

    parts.append(
        "## Decisões (trecho)\n"
        + _tail_sections(MEMORIA_DIR / "decisoes.md", "## Decisões", 4)
    )

    parts.append(
        "## Aprendizados (trecho)\n"
        + _tail_sections(MEMORIA_DIR / "aprendizados.md", "## Aprendizados", 4)
    )

    from laboratorio.evolution.propose import list_pending_proposals

    pending = list_pending_proposals(limit=8)
    if pending:
        lines = [
            f"- #{p['id']} [{p.get('target')}]: {p.get('title')} (via {p.get('source', '?')})"
            for p in pending
        ]
        parts.append(
            "## Propostas WhatsApp pendentes (não aplicar sem APROVAR)\n" + "\n".join(lines)
        )

    patrol = LOGS_DIR / "ronaldo_patrol.md"
    if patrol.is_file():
        parts.append("## Patrulha (fim do arquivo)\n" + patrol.read_text(encoding="utf-8")[-1200:])

    semantic = augment_with_semantic_memory(
        "aprendizados operação laboratório últimas decisões", top_k=4
    )
    if semantic.strip():
        parts.append(semantic.strip())

    return "\n\n".join(parts)
