# Supabase — Laboratório (memória semântica)

Projeto compartilhado com VitorOS: **`pwlpdpwxxhbsmkclrpoa`**

## Variáveis no `backend/.env`

```bash
SUPABASE_URL=https://pwlpdpwxxhbsmkclrpoa.supabase.co
SUPABASE_PUBLISHABLE_KEY=sb_publishable_...   # frontend VitorOS
SUPABASE_DB_URL=postgresql://postgres:SUA_SENHA@db.pwlpdpwxxhbsmkclrpoa.supabase.co:5432/postgres
MEMORY_ENABLED=1
```

> O backend usa **`SUPABASE_DB_URL`** (Postgres direto) para pgvector. A publishable key não basta no servidor.

## Aplicar migration

**Opção A — Dashboard:** SQL Editor → colar `migrations/20260601000001_lab_semantic_memory.sql` → Run

**Opção B — CLI (na raiz do repo):**

```bash
supabase login
supabase link --project-ref pwlpdpwxxhbsmkclrpoa
supabase db push
```

## Comandos Lab

```bash
cd backend
./run.sh memory-check      # testa conexão + extensão vector
./run.sh memory-sync         # indexa memoria/ e contexto/
./run.sh memory-recall "como funciona aprovação whatsapp"
```
