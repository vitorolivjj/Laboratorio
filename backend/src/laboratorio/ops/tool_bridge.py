"""Núcleo compartilhado das tools — WhatsApp LLM, CrewAI e API."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

from laboratorio.config import MEMORIA_DIR, TASKS_DIR
from laboratorio.ops import crm_lp_store, memory_store, tasks_store
from laboratorio.ops.markdown_io import read_text

TASK_REF_RE = re.compile(r"\b((?:LP-PINTOR-\d{3}[A-Z]?)|(?:TASK-\d{3}))\b", re.I)


def list_tasks(*, tasks_dir: Path = TASKS_DIR) -> str:
    return tasks_store.list_tasks(tasks_dir=tasks_dir)


def move_task(
    task_id: str,
    to_state: str,
    nota: str = "",
    *,
    force: bool = False,
    tasks_dir: Path = TASKS_DIR,
) -> str:
    return tasks_store.move_task(
        task_id, to_state, nota, tasks_dir=tasks_dir, force=force
    )


def registrar_decisao(
    *,
    titulo: str,
    contexto: str,
    decisao: str,
    responsavel: str = "Vitor",
    impactados: str = "ronaldo_maestro",
) -> str:
    return memory_store.registrar_decisao(
        titulo=titulo,
        contexto=contexto,
        decisao=decisao,
        responsavel=responsavel,
        impactados=impactados,
    )


def ler_crm_lp() -> str:
    return crm_lp_store.render_leads_lp()


def ler_memoria(name: str) -> str:
    return memory_store.read_memory(name)


def _normalize_title(title: str) -> str:
    nfkd = unicodedata.normalize("NFD", title.lower())
    folded = "".join(c for c in nfkd if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", folded).strip()


def _grep_decisoes(query: str, *, max_hits: int = 3) -> list[dict]:
    path = MEMORIA_DIR / "decisoes.md"
    text = read_text(path)
    if not text:
        return []

    keywords = [w for w in _normalize_title(query).split() if len(w) > 2]
    if not keywords:
        keywords = query.lower().split()[:4]

    blocks = re.split(r"(?=^### )", text, flags=re.MULTILINE)
    scored: list[tuple[int, dict]] = []
    for block in blocks:
        if not block.strip().startswith("###"):
            continue
        first = block.split("\n", 1)[0].strip()
        body_fold = _normalize_title(block)
        score = sum(1 for k in keywords if k in body_fold)
        if score == 0:
            continue
        scored.append(
            (
                score,
                {
                    "heading": first.lstrip("# ").strip(),
                    "excerpt": block.strip()[:500],
                },
            )
        )
    scored.sort(key=lambda x: (-x[0], x[1]["heading"]))
    return [h for _, h in scored[:max_hits]]


def consultar_decisoes(query: str, *, top_k: int = 4) -> str:
    """Recall semântico + grep em decisoes.md com citação."""
    lines: list[str] = []
    semantic_note = ""

    try:
        from laboratorio.memory.semantic import is_memory_enabled, recall

        if is_memory_enabled():
            hits = recall(query, top_k=top_k, namespace=None)
            if hits:
                lines.append("Memória semântica:")
                for h in hits[:top_k]:
                    ref = h.source_ref or h.namespace
                    snippet = h.content.strip().replace("\n", " ")[:200]
                    lines.append(f"• ({ref}, sim={h.similarity:.2f}) {snippet}")
                semantic_note = hits[0].source_ref or hits[0].namespace
    except Exception as exc:
        lines.append(f"(semântica indisponível: {exc})")

    grep_hits = _grep_decisoes(query)
    if grep_hits:
        lines.append("")
        lines.append("decisoes.md:")
        for h in grep_hits:
            lines.append(f"📌 {h['heading']}")
            excerpt = h["excerpt"].split("\n", 3)
            body = "\n".join(excerpt[1:4]) if len(excerpt) > 1 else h["excerpt"][:280]
            lines.append(body[:320])
            if semantic_note:
                lines.append(f"(memória semântica: {semantic_note})")
            lines.append("")

    if not lines:
        return f"Nenhuma decisão encontrada para: {query[:80]}"
    return "\n".join(lines).strip()


def kanban_task_ids(*, tasks_dir: Path = TASKS_DIR) -> set[str]:
    from laboratorio.ops.governance_audit import _kanban_map

    return set(_kanban_map(tasks_dir).keys())


def find_orphan_memoria_refs(
    *,
    memoria_dir: Path | None = None,
    tasks_dir: Path | None = None,
) -> list[dict]:
    """Refs TASK-* / LP-PINTOR-* em memoria/**/*.md fora do kanban."""
    memoria_dir = memoria_dir or MEMORIA_DIR
    tasks_dir = tasks_dir or TASKS_DIR
    known = kanban_task_ids(tasks_dir=tasks_dir)
    orphans: list[dict] = []
    seen: set[tuple[str, str]] = set()

    for mp in sorted(memoria_dir.rglob("*.md")):
        if "_arquivo" in mp.parts:
            continue
        rel = str(mp.relative_to(memoria_dir.parent))
        text = read_text(mp)
        for tid in TASK_REF_RE.findall(text):
            tid = tid.upper()
            key = (tid, rel)
            if tid in known or key in seen:
                continue
            seen.add(key)
            orphans.append({"task_id": tid, "file": rel})
    return orphans
