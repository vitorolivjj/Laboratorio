"""Memória semântica (Fase 1) — Supabase pgvector."""

from laboratorio.memory.context import augment_with_semantic_memory
from laboratorio.memory.semantic import (
    is_memory_enabled,
    recall,
    remember,
)

__all__ = [
    "augment_with_semantic_memory",
    "is_memory_enabled",
    "recall",
    "remember",
]
