-- Segmentos de CRM (metadados do funil) — Fase 6, expansão de leads.
-- O funil mora no bloco <!-- crm-meta --> de cada crm/*.md; aqui vira tabela
-- para o painel montar o funil a partir do banco (LeadRepository completo).

create table if not exists lab_crm_segments (
  segment     text primary key,   -- laboratorio | landing_pintor | appvs
  name        text,
  description text,
  funnel      text[],             -- estágios do funil, em ordem
  updated_at  timestamptz default now()
);
