"""Memória semântica — embeddings OpenAI + busca pgvector no Supabase."""

from __future__ import annotations

import hashlib
import logging
import os
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any

import httpx

from laboratorio.config import load_env

logger = logging.getLogger("laboratorio.memory.semantic")

OPENAI_EMBED_URL = "https://api.openai.com/v1/embeddings"
EMBED_DIM = 1536


@dataclass
class MemoryHit:
    content: str
    namespace: str
    source_ref: str | None
    similarity: float


def is_memory_enabled() -> bool:
    load_env()
    if os.getenv("MEMORY_ENABLED", "1").strip().lower() in ("0", "false", "no"):
        return False
    return bool(supabase_db_url() and os.getenv("OPENAI_API_KEY", "").strip())


def supabase_db_url() -> str | None:
    load_env()
    url = os.getenv("SUPABASE_DB_URL", "").strip()
    return url or None


def embedding_model() -> str:
    load_env()
    return os.getenv("MEMORY_EMBEDDING_MODEL", "text-embedding-3-small").strip()


def _content_hash(namespace: str, content: str) -> str:
    raw = f"{namespace}\n{content.strip()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def embed_texts(texts: list[str], *, batch_size: int = 1) -> list[list[float]]:
    load_env()
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY ausente — necessária para embeddings")

    if not texts:
        return []

    batch_size = max(1, min(batch_size, 20))
    all_embeddings: list[list[float]] = []

    with httpx.Client(timeout=90.0) as client:
        for start in range(0, len(texts), batch_size):
            batch = texts[start : start + batch_size]
            payload = {"model": embedding_model(), "input": batch}
            for attempt in range(10):
                resp = client.post(
                    OPENAI_EMBED_URL,
                    headers={"Authorization": f"Bearer {api_key}"},
                    json=payload,
                )
                if resp.status_code == 429:
                    try:
                        err = resp.json().get("error", {})
                        if err.get("code") == "insufficient_quota":
                            raise RuntimeError(
                                "OpenAI sem quota para embeddings — adicione créditos em "
                                "https://platform.openai.com/settings/organization/billing "
                                "e rode ./run.sh memory-sync novamente."
                            )
                    except (ValueError, AttributeError):
                        pass
                    wait = min(120, 5 * (2 ** attempt))
                    logger.warning("Embeddings 429 — aguardando %ss", wait)
                    time.sleep(wait)
                    continue
                resp.raise_for_status()
                break
            else:
                resp.raise_for_status()

            data = resp.json()["data"]
            ordered = sorted(data, key=lambda row: row["index"])
            all_embeddings.extend(row["embedding"] for row in ordered)
            if start + batch_size < len(texts):
                time.sleep(2.0)

    return all_embeddings


def embed_text(text: str) -> list[float]:
    return embed_texts([text])[0]


@contextmanager
def _connection():
    import psycopg
    from pgvector.psycopg import register_vector

    url = supabase_db_url()
    if not url:
        raise RuntimeError("SUPABASE_DB_URL não configurado no backend/.env")

    with psycopg.connect(url, autocommit=True) as conn:
        register_vector(conn)
        yield conn


def ensure_schema() -> None:
    """Verifica tabela e extensão (migration aplicada)."""
    with _connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "select 1 from information_schema.tables "
                "where table_schema = 'public' and table_name = 'lab_semantic_memories'"
            )
            if cur.fetchone() is None:
                raise RuntimeError(
                    "Tabela lab_semantic_memories ausente — aplique supabase/migrations/20260601000001_lab_semantic_memory.sql"
                )


def remember_batch(
    contents: list[str],
    *,
    namespace: str = "global",
    source_refs: list[str] | None = None,
    file_ref: str | None = None,
) -> int:
    """Grava vários trechos em lote (menos chamadas à API de embeddings)."""
    rows: list[tuple[str, str, str]] = []
    for i, raw in enumerate(contents):
        text = raw.strip()
        if not text:
            continue
        if len(text) > 8000:
            text = text[:8000]
        ref = (source_refs[i] if source_refs and i < len(source_refs) else None) or ""
        rows.append((text, ref, _content_hash(namespace, text)))

    if not rows:
        return 0

    texts = [r[0] for r in rows]
    vectors = embed_texts(texts, batch_size=6)

    with _connection() as conn:
        with conn.cursor() as cur:
            for (text, ref, chash), vec in zip(rows, vectors):
                meta = {"file": file_ref} if file_ref else {}
                cur.execute(
                    """
                    insert into public.lab_semantic_memories
                      (namespace, source_ref, content, metadata, embedding, content_hash, updated_at)
                    values (%s, %s, %s, %s::jsonb, %s, %s, now())
                    on conflict (namespace, content_hash)
                    do update set
                      content = excluded.content,
                      source_ref = excluded.source_ref,
                      metadata = excluded.metadata,
                      embedding = excluded.embedding,
                      updated_at = now()
                    """,
                    (
                        namespace,
                        ref or None,
                        text,
                        psycopg_json(meta),
                        vec,
                        chash,
                    ),
                )
    return len(rows)


def remember(
    content: str,
    *,
    namespace: str = "global",
    source_ref: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> str:
    """Grava ou atualiza um trecho na memória semântica. Retorna id UUID."""
    text = content.strip()
    if not text:
        raise ValueError("content vazio")
    if len(text) > 8000:
        text = text[:8000]

    remember_batch(
        [text],
        namespace=namespace,
        source_refs=[source_ref or ""],
        file_ref=(metadata or {}).get("file"),
    )
    chash = _content_hash(namespace, text)
    with _connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "select id::text from public.lab_semantic_memories "
                "where namespace = %s and content_hash = %s",
                (namespace, chash),
            )
            row = cur.fetchone()
            return row[0] if row else ""


def recall(
    query: str,
    *,
    top_k: int = 5,
    namespace: str | None = None,
    min_similarity: float = 0.25,
) -> list[MemoryHit]:
    """Busca trechos mais relevantes por significado."""
    q = query.strip()
    if not q:
        return []

    from pgvector import Vector

    vec = Vector(embed_text(q))
    limit = max(1, min(top_k, 20))

    sql = """
        select content, namespace, source_ref,
               1 - (embedding <=> %s) as similarity
        from public.lab_semantic_memories
        where embedding is not null
    """
    params: list[Any] = [vec]

    if namespace:
        sql += " and namespace = %s"
        params.append(namespace)

    sql += """
        order by embedding <=> %s
        limit %s
    """
    params.extend([vec, limit])

    hits: list[MemoryHit] = []
    with _connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            for content, ns, source_ref, sim in cur.fetchall():
                if sim is None or float(sim) < min_similarity:
                    continue
                hits.append(
                    MemoryHit(
                        content=content,
                        namespace=ns,
                        source_ref=source_ref,
                        similarity=float(sim),
                    )
                )
    return hits


def psycopg_json(obj: dict[str, Any]) -> Any:
    from psycopg.types.json import Jsonb

    return Jsonb(obj)
