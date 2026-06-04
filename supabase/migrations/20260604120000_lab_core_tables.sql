-- Tabelas operacionais núcleo (markdown -> Postgres) — Fase 6.
-- Mesmo banco da memória semântica (pgvector). Idempotente: create ... if not exists.
-- Backfill: scripts/backfill_markdown_to_db.py

create table if not exists lab_projects (
  id          text primary key,            -- PROJ-001
  name        text not null,
  prefix      text,
  nature      text,
  status      text default 'ativo',
  crm         text,
  repo        text,
  description text,
  legacy      text,
  updated_at  timestamptz default now()
);

create table if not exists lab_tasks (
  id           text primary key,           -- TASK-042 / LP-PINTOR-001 / LAB-3
  title        text not null,
  state        text not null,              -- backlog|planejando|executando|standby|aguardando|concluidas|arquivado
  project_id   text,
  agents       text,
  status       text,
  proxima_acao text,
  bloqueio     text,
  entregaveis  text,
  updated_at   timestamptz default now()
);
create index if not exists lab_tasks_state_idx on lab_tasks (state);
create index if not exists lab_tasks_project_idx on lab_tasks (project_id);

create table if not exists lab_leads (
  id           text primary key,           -- LEAD-001
  segment      text not null,              -- laboratorio|landing_pintor|appvs
  nome         text,
  cidade       text,
  servico      text,
  contato      text,
  origem       text,
  status       text default 'novo',
  etapa        text,
  responsavel  text,
  projeto      text,
  score        text,
  temperatura  text,
  prioridade   text,
  tags         text,
  observacoes  text,
  proxima_acao text,
  captura      text,
  updated_at   timestamptz default now()
);
create index if not exists lab_leads_segment_status_idx on lab_leads (segment, status);

-- Eventos e decisões não têm PK natural no markdown -> source_hash idempotente.
create table if not exists lab_events (
  id          bigserial primary key,
  at          text,
  type        text,
  title       text,
  agents      text,
  detail      text,
  ref         text,
  status      text,
  source_hash text unique
);

create table if not exists lab_decisions (
  id          bigserial primary key,
  title       text,
  date        text,
  body        text,
  source_hash text unique
);

-- Estados de runtime (cadência, dedup, autopilot) — chave -> valor JSON.
create table if not exists lab_runtime_state (
  key        text primary key,
  value      jsonb,
  updated_at timestamptz default now()
);
