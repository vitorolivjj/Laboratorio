-- CRM completo (comercial + produção) — análise estruturada do lead + arquivos.
--
-- Comercial precisa do PERFIL do lead e de COMO ABORDAR; produção precisa dos
-- ARQUIVOS (fotos de trabalho do pintor, ou material/playbook de um lead do
-- Laboratório) para montar a página/entregável. Antes isso morava em texto
-- livre (observacoes) e em pastas no disco (frontend/lp-pintor/leads/<slug>).
-- Aqui o banco vira fonte de verdade dos dois; os BYTES vão pro Supabase Storage
-- e esta tabela guarda só os metadados + a chave do arquivo no bucket.
--
-- Generaliza por natureza de projeto: pintor -> tipo='foto_trabalho';
-- laboratorio -> tipo='material'/'playbook'. Sem hardcode de "pintor".

-- 1) Análise estruturada no próprio lead (1:1, leitura direta pelo comercial)
alter table lab_leads add column if not exists perfil text;
-- ex.: "pintor residencial", "pintor comercial", "estúdio de design"
alter table lab_leads add column if not exists resumo_abordagem text;
-- texto pronto pro vendedor: dor, gancho, melhor momento/canal
alter table lab_leads add column if not exists analise jsonb not null default '{}'::jsonb;
-- estrutura flexível por segmento:
--   { "dor": "...", "gancho": "...", "objecoes": ["..."],
--     "melhor_canal": "whatsapp", "tom": "direto", "sinais": ["..."] }

comment on column lab_leads.perfil is 'Classificação do lead p/ abordagem (ex.: pintor residencial)';
comment on column lab_leads.resumo_abordagem is 'Texto pronto p/ o comercial: como abordar este lead';
comment on column lab_leads.analise is 'Análise estruturada (dor, gancho, objeções, canal, tom) — varia por segmento';

-- 2) Arquivos do lead (produção) — bytes no Storage, metadados aqui
create table if not exists lab_lead_files (
  id            bigint generated always as identity primary key,
  lead_id       text not null references lab_leads(id) on delete cascade,
  projeto       text,                                   -- denormalizado p/ filtro rápido
  tipo          text not null default 'outro',          -- ver CHECK abaixo
  storage_path  text not null,                          -- chave no bucket: <projeto>/<lead_id>/<arquivo>
  url           text,                                   -- url pública/assinada (cache; pode regenerar)
  mime          text,
  bytes         bigint,
  origem        text not null default 'donizete',       -- donizete | upload_manual | agente
  aprovado      boolean,                                 -- curadoria (Loide): null=pendente, true=usar, false=rejeitar
  ordem         int not null default 0,                  -- ordem de exibição na página
  metadata      jsonb not null default '{}'::jsonb,      -- {largura, altura, origem_url, hash, ...}
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now(),
  constraint lab_lead_files_tipo_chk check (
    tipo in ('foto_trabalho','screenshot_perfil','material','playbook','documento','logo','outro')
  )
);

create index if not exists idx_lab_lead_files_lead on lab_lead_files(lead_id);
create index if not exists idx_lab_lead_files_tipo on lab_lead_files(tipo);
create index if not exists idx_lab_lead_files_projeto on lab_lead_files(projeto);
-- mesmo arquivo (mesma chave no bucket) não duplica
create unique index if not exists uq_lab_lead_files_path on lab_lead_files(storage_path);

comment on table lab_lead_files is 'Arquivos do lead (fotos de trabalho, materiais, playbooks). Bytes no Supabase Storage; aqui só metadados + chave.';
