# Migração markdown → Postgres (Supabase) — runbook

Estado atual, como operar e como reverter. Mesmo banco da memória semântica
(`SUPABASE_DB_URL`). Tabelas operacionais com prefixo `lab_`.

## O que já foi feito ✅

| Degrau | Estado |
|---|---|
| 1. Schema | Aplicado — 6 tabelas `lab_*` criadas no Supabase |
| 2. Backfill | Carregado (6 projetos, 37 tasks, 64 leads, 64 eventos, 29 decisões) |
| 4. Conferência | Consistente (`scripts/verify_markdown_vs_db.py`) |
| 5. Flip de leitura | Provado — `DATA_BACKEND=postgres` faz o repositório ler tasks do banco |

Markdown continua **fonte da verdade na escrita**; o banco é leitura opcional.

## Peças

| Arquivo | Função |
|---|---|
| `supabase/migrations/20260604120000_lab_core_tables.sql` | Schema (idempotente) |
| `backend/src/laboratorio/db/core.py` | Conexão + checagem de tabelas |
| `backend/src/laboratorio/db/markdown_sync.py` | `collect_markdown()` + `apply_to_db()` |
| `scripts/backfill_markdown_to_db.py` | Carrega markdown → banco (`--apply`) |
| `scripts/verify_markdown_vs_db.py` | Confere contagens markdown × banco |
| `backend/src/laboratorio/repositories/tasks.py` | `TaskRepository` (markdown/postgres) |

## Como ligar a leitura pelo banco

```bash
# no backend/.env (ou no ambiente)
DATA_BACKEND=postgres     # default é "markdown"
```

Com isso, `maestro.build_maestro_snapshot` lê as TASKs do banco (via
`PostgresTaskRepository`). Para voltar: `DATA_BACKEND=markdown` (ou remover a var).

## Manter o banco em sincronia (importante)

A **escrita** ainda vai só para o markdown (kanban em `tasks/*.md`, com lock).
O banco **não se atualiza sozinho** — ele reflete o último backfill. Opções:

1. **Re-backfill periódico (recomendado p/ piloto):** o backfill é idempotente
   (upsert), então rode-o numa rotina (ex.: timer systemd a cada 5 min, como os
   outros em `deploy/vps/`):
   ```bash
   python scripts/backfill_markdown_to_db.py --apply
   ```
2. **Escrita dupla (degrau 3, futuro):** fazer o `MarkdownTaskRepository.move/create`
   gravar também no banco (best-effort, sem quebrar a escrita markdown). Mais
   trabalho e adiciona latência/risco de rede na escrita — só quando o banco for
   virar a fonte da verdade de fato.

Enquanto a leitura estiver em `markdown` (default), nada disso é necessário.

## Conferir a qualquer momento

```bash
python scripts/verify_markdown_vs_db.py
```
Mostra contagens dos dois lados e avisa divergências. (Hoje aponta **15 entradas
de task repetidas em `tasks/arquivado.md`** — o banco as colapsa via PK; vale uma
limpeza no markdown quando sobrar tempo, mas não é crítico.)

## Rollback total

Nada destrutivo foi feito ao que já existia. Para remover as tabelas novas:
```sql
drop table if exists lab_tasks, lab_projects, lab_leads, lab_events,
                     lab_decisions, lab_runtime_state cascade;
```
E garantir `DATA_BACKEND=markdown`. A memória semântica (`lab_semantic_memories`)
não é afetada.

## Próximos degraus (quando quiser)

- Estender o repositório para **leads/eventos/projetos** (hoje só tasks lê do banco).
- Escrita dupla → virar o banco em fonte da verdade → markdown vira exportação.
- Substituir as ~5 leituras de arquivo da snapshot por consultas SQL (perf).
