-- Fase 1 — Memória semântica do Laboratório (projeto pwlpdpwxxhbsmkclrpoa)
-- Tabela isolada (prefixo lab_) — não conflita com VitorOS (tasks, rabiscos, etc.)

create extension if not exists vector with schema extensions;

create table if not exists public.lab_semantic_memories (
  id uuid primary key default gen_random_uuid(),
  namespace text not null default 'global',
  source_ref text,
  content text not null,
  metadata jsonb not null default '{}'::jsonb,
  embedding extensions.vector(1536),
  content_hash text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.lab_semantic_memories
  add constraint lab_semantic_memories_ns_hash_unique
  unique (namespace, content_hash);

create index if not exists lab_semantic_memories_namespace_idx
  on public.lab_semantic_memories (namespace);

create index if not exists lab_semantic_memories_embedding_idx
  on public.lab_semantic_memories
  using hnsw (embedding extensions.vector_cosine_ops);

comment on table public.lab_semantic_memories is
  'Memória semântica do Laboratório multiagente — busca por significado (OpenAI embeddings).';
