# Memória semântica — Fase 1

**Projeto Supabase:** `pwlpdpwxxhbsmkclrpoa` (compartilhado com VitorOS)  
**Tabela:** `public.lab_semantic_memories` (prefixo `lab_` — isolada do cockpit)

## Ativação

1. Dashboard Supabase → SQL Editor → rodar `supabase/migrations/20260601000001_lab_semantic_memory.sql`
2. `backend/.env` → `SUPABASE_DB_URL` com senha do Postgres
3. `cd backend && .venv/bin/pip install -r requirements.txt`
4. `./run.sh memory-check` → `./run.sh memory-sync`

**Requisito:** `OPENAI_API_KEY` com **quota ativa** (embeddings `text-embedding-3-small`). Erro `insufficient_quota` = billing OpenAI, não Supabase.

## Onde entra no sistema

| Canal | Uso |
|-------|-----|
| Orquestrador / `orchestrate` | Trechos relevantes ao objetivo do Vitor |
| WhatsApp Vitor (LLM) | Recall na pergunta livre |
| Markdown `memoria/` | Fonte indexada pelo sync |

## Namespaces

`decisoes` · `aprendizados` · `contexto` · `ronaldo_maestro` · `global`

## Comandos

```bash
./run.sh memory-check
./run.sh memory-sync
./run.sh memory-recall "aprovação whatsapp fase 0"
```
