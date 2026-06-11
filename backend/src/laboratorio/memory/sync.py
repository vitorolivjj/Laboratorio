"""Indexação inicial — markdown do repo → memória semântica."""

from __future__ import annotations

import re
from pathlib import Path

from laboratorio.config import CONTEXTO_GLOBAL, MEMORIA_DIR, MEMORIA_RONALDO_DIR, REPO_ROOT
from laboratorio.memory.semantic import is_memory_enabled, remember

# Arquivos/pastas indexados no sync padrão
# (memórias do piloto pintor → memoria/arquivo/pintor-legado/, fora do índice — 2026-06-10)
SYNC_PATHS: list[tuple[Path, str]] = [
    (MEMORIA_DIR / "decisoes.md", "decisoes"),
    (MEMORIA_DIR / "aprendizados.md", "aprendizados"),
    (CONTEXTO_GLOBAL, "contexto"),
    (MEMORIA_DIR / "aprovacao_whatsapp_fase0.md", "global"),
    (MEMORIA_DIR / "plano_negocio.md", "global"),
]

RONALDO_MEMORY_FILES = (
    "regras_do_ecossistema.md",
    "decisoes_criticas.md",
    "protocolo_delegacao_conferencia.md",
    "evolucao_orquestracao.md",
)


def chunk_markdown(text: str, *, max_chars: int = 900) -> list[str]:
    """Divide por headings ## ou parágrafos grandes."""
    text = text.strip()
    if not text:
        return []

    sections = re.split(r"(?=^## )", text, flags=re.MULTILINE)
    chunks: list[str] = []

    for section in sections:
        section = section.strip()
        if not section:
            continue
        if len(section) <= max_chars:
            chunks.append(section)
            continue
        paragraphs = [p.strip() for p in re.split(r"\n\n+", section) if p.strip()]
        buf = ""
        for para in paragraphs:
            if len(buf) + len(para) + 2 <= max_chars:
                buf = f"{buf}\n\n{para}".strip() if buf else para
            else:
                if buf:
                    chunks.append(buf)
                if len(para) <= max_chars:
                    buf = para
                else:
                    for i in range(0, len(para), max_chars):
                        chunks.append(para[i : i + max_chars])
                    buf = ""
        if buf:
            chunks.append(buf)

    return chunks


def sync_file(path: Path, namespace: str, *, dry_run: bool = False) -> int:
    if not path.is_file():
        return 0
    rel = str(path.relative_to(REPO_ROOT))
    text = path.read_text(encoding="utf-8")
    chunks = chunk_markdown(text)
    if dry_run:
        return len(chunks)

    import time

    count = 0
    for i, chunk in enumerate(chunks):
        ref = f"{rel}#chunk-{i}"
        remember(chunk, namespace=namespace, source_ref=ref, metadata={"file": rel})
        count += 1
        time.sleep(1.5)
    return count


def sync_all(*, dry_run: bool = False) -> dict[str, int]:
    if not is_memory_enabled():
        raise RuntimeError(
            "Memória desabilitada — configure SUPABASE_DB_URL + OPENAI_API_KEY e MEMORY_ENABLED=1"
        )

    stats: dict[str, int] = {"chunks": 0, "files": 0}

    import time

    paths: list[tuple[Path, str]] = list(SYNC_PATHS)
    for name in RONALDO_MEMORY_FILES:
        paths.append((MEMORIA_RONALDO_DIR / name, "ronaldo_maestro"))

    for path, namespace in paths:
        n = sync_file(path, namespace, dry_run=dry_run)
        if n:
            stats["files"] += 1
            stats["chunks"] += n
            if not dry_run:
                time.sleep(2.0)

    return stats


def sync_after_evolution(proposals: list[dict]) -> str:
    """Reindexa só os arquivos alterados por propostas aprovadas."""
    if not is_memory_enabled():
        return "Memória semântica desligada — sync não executado."

    targets = {(p.get("target") or "").strip().lower() for p in proposals}
    paths: list[tuple[Path, str]] = []
    if "aprendizados" in targets:
        paths.append((MEMORIA_DIR / "aprendizados.md", "aprendizados"))
    if "decisoes" in targets:
        paths.append((MEMORIA_DIR / "decisoes.md", "decisoes"))

    if not paths:
        return "Nenhum arquivo para indexar."

    import time

    chunks = 0
    files = 0
    for path, namespace in paths:
        n = sync_file(path, namespace)
        if n:
            files += 1
            chunks += n
        time.sleep(1.0)

    return f"Memória indexada: {chunks} trecho(s) em {files} arquivo(s)."
