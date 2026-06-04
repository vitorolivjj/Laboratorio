# Plano de refatoração e evolução — Laboratorio

> Diagnóstico de engenharia reversa + plano de execução em fases.
> **Sem cronograma** — a ordem importa, as datas não. Marque os `[ ]` conforme avança.
> Regra de ouro: **nada quebra de uma vez**. Cada passo preserva o comportamento atual.

---

## Status de execução

| Fase | Estado | Commit(s) |
|---|---|---|
| 0 — Saneamento | ✅ feito | `fase 0` |
| (bugs latentes achados via lint) | ✅ feito | `fix: 3 bugs latentes` |
| 2 — Rede de testes | ✅ feito (25→30 testes, CI) | `fase 2` |
| 1 — Tirar duplicação | ✅ feito | `fase 1` |
| 3 — Segurança | ✅ feito (maestro+tasks; donizete já tinha) | `fase 3` |
| 4 — Concorrência + cache | ✅ feito | `fase 4` |
| 5 — Camada de repositório | ✅ tasks, projetos, leads, eventos, **CRM/funil** | `fase 5` + `expansao` |
| 6 — Migração banco (1-2, 4-5) | ✅ **aplicado no Supabase** + verify + flip de leitura | `fase 6` |
| 6 — degrau 3 (escrita dupla) | ✅ **tempo real** (dual_write) + timer de segurança | `banco fonte de verdade` |
| Funil de lead no banco | ✅ `lab_crm_segments` + CrmRepository | `funil de lead no banco` |
| 7.3 — consolidação config | ✅ `use_postgres()` (parcial) | `fase 7` |
| 7.4 — Observabilidade (maestro) | ✅ feito + smoke da god function | `fase 7.4 (parcial)` |
| 7.1 — orquestração | ✅ **ADR** (decisão: fronteira clara, não unificar) | `fase 7 (adr)` |
| 7.2 + resto do 7.4 | ⏳ pendente (CLI registry, `Settings` completo, demais `except: pass`) | — |

Cobertura: **36 testes**. `laboratorio check` saindo 0. Tudo em commits separados
sobre o `checkpoint` (revertível); comportamento do app preservado (default `markdown`).

**Migração markdown→Postgres APLICADA e provada**, banco como cópia autoritativa
sempre-atual (escrita dupla). Operação/sync/rollback em
[migracao_banco.md](migracao_banco.md). Ligue a leitura do banco com
`DATA_BACKEND=postgres`.

---

## Princípios (as regras do jogo)

1. **Nada quebra de uma vez.** Muda-se *como* funciona por dentro, não *o que* faz.
2. **Passos pequenos e reversíveis.** Cada item entra sozinho, dá pra testar e desfazer.
3. **Rede de segurança antes do perigoso.** Testes automáticos primeiro, refactor depois.
4. **Markdown não é inimigo.** É ótimo pra humano ler e pro git versionar. O problema é
   usá-lo como *banco de dados*. Vamos rebaixá-lo a *visão/exportação*.

---

## Visão geral das fases

| Fase | Nome | O que resolve | Risco | Ganho |
|---|---|---|---|---|
| 0 | Saneamento | Código morto, lixo, doc errada | ~Zero | Clareza imediata |
| 1 | Tirar duplicação | 5 cópias de parsing, etc. | Baixo | Menos lugares pra errar |
| 2 | Rede de testes | ~2% de cobertura | Baixo | Refatorar sem medo |
| 3 | Segurança | API sem senha | Baixo | Fecha porta aberta |
| 4 | Concorrência + cache | Brigas de escrita, lentidão | Médio | Estabilidade e velocidade |
| 5 | Camada de dados ("porta única") | Acesso espalhado ao markdown | Médio | **Habilita o banco** |
| 6 | Migração markdown → Postgres | Markdown como banco | Médio | Transações, consultas, escala |
| 7 | Consolidações estratégicas | 2 frameworks, front, config | Variado | Menos paradigmas |

---

## Fase 0 — Saneamento (risco ~zero)

**Em palavras simples:** jogar fora o que está morto e arrumar a papelada.

- [ ] 0.1 Apagar a função morta `build_orchestration_crew` + `_load_contexto_extra`
      (referenciam símbolos não importados — quebrariam se chamadas). `backend/orquestrador.py:49-153`
- [ ] 0.2 Remover `social_executor/src/__pycache__` (bytecode órfão sem fonte) e marcar o
      módulo como arquivado no `social_executor/README.md`
- [ ] 0.3 Corrigir o docstring do autopilot: dizer a verdade ("ligado por padrão").
      `backend/src/laboratorio/ops/autopilot.py:8`
- [ ] 0.4 Adicionar `pyproject.toml` (instalar com `pip install -e .`) e parar de depender
      de `PYTHONPATH=src`

**Pronto quando:** `./run.sh check` continua passando; o app sobe igual.

---

## Fase 1 — Tirar a duplicação (risco baixo)

**Em palavras simples:** a mesma ideia escrita em 5 lugares vira 5 consertos. Uma fonte só.

- [ ] 1.1 Unir os 5 extratores de campo (`_field`, `_bullet`, 2× `fld`, `_field` do lp_leads)
      em `markdown_io.extract_field()` (+ `extract_cell()` para o formato de tabela)
- [ ] 1.2 Apagar o `read_text` duplicado (fica só o de `markdown_io.py`)
- [ ] 1.3 `orquestrador` passa a usar `insert_after_heading` (atômico); remover
      `_insert_after_section` inseguro
- [ ] 1.4 Unificar "qual agente neste texto" (`_normalize_agent_id`, `re_split_agents`,
      loop do maestro) em `agent_id_from_text()`
- [ ] 1.5 Padronizar o regex de ID de task num lugar só (`TASK_ID_RE`)

**Pronto quando:** os testes da Fase 2 sobre essas funções continuam verdes.

---

## Fase 2 — Rede de testes

**Em palavras simples:** antes de mexer no motor, instalar o cinto. Teste automático avisa
"você quebrou algo" em 2 segundos, em vez de você descobrir em produção.

- [ ] 2.1 `pytest` + `ruff` no `requirements-dev.txt` e no GitHub Actions
- [ ] 2.2 Testes de caracterização com **markdown real** para `parsers.py` e `tasks_store.py`
- [ ] 2.3 Teste de fumaça: montar `build_maestro_snapshot()` inteiro sem explodir
- [ ] 2.4 Meta inicial: ~40% nos módulos de dados (não precisa cobrir LLM)

**Pronto quando:** `pytest` roda no CI; PR que quebra parsing fica vermelho.

---

## Fase 3 — Segurança (risco baixo)

**Em palavras simples:** o painel é uma casa sem fechadura. Quem sabe o endereço vê
CRM/leads/conversas e até manda o Ronaldo executar comando. Pôr uma fechadura simples.

- [ ] 3.1 Exigir `PANEL_TOKEN` em todas as rotas `/api/maestro/*` via `Depends`
- [ ] 3.2 O painel envia o token no header (guardado no navegador)
- [ ] 3.3 Proteger `/ronaldo/command` (executa ações!)
- [ ] 3.4 Trocar defaults "fail-open" por "fail-closed" onde fizer sentido
      (assinatura do webhook em produção)

**Compatível com dev:** se `PANEL_TOKEN` estiver vazio, segue aberto (não quebra o local).

---

## Fase 4 — Concorrência + cache (risco médio)

**Em palavras simples:** hoje três "pessoas" (autopilot, webhook, cron de auditoria)
escrevem no mesmo caderno ao mesmo tempo. Não rasga a página, mas um apaga o que o outro
acabou de escrever. Pôr uma "senha de banheiro" (lock): um escreve por vez.

- [ ] 4.1 Lock por arquivo nas escritas dos `*_store.py` (`filelock`)
- [ ] 4.2 Construir o índice de projetos **1 vez** por snapshot (hoje é O(n²) por task)
- [ ] 4.3 Carregar `.env` 1 vez (hoje `resolve_agent_llm_config` relê o disco a cada agente)
- [ ] 4.4 Rotação do `agent_interactions.jsonl` (hoje cresce pra sempre, lido inteiro)

> A partir da Fase 6 (banco), o item 4.1 some — o banco já resolve concorrência. O lock é
> a ponte até lá.

---

## Fase 5 — Camada de dados: a "porta única" (risco médio) — *habilita o banco*

**Em palavras simples:** hoje código de toda parte abre o markdown direto, cada um do seu
jeito (30 pessoas mexendo no estoque sem balcão). Criar **um balcão único** (*Repository*):
todo mundo pede ao balcão. Quem está atrás (markdown? banco?) o resto do código nem sabe.

```
ANTES:  maestro/autopilot/tools ─► abrem tasks/*.md (regex)   ← cada um do seu jeito
DEPOIS: maestro/autopilot/tools ─► TaskRepository ─► (markdown HOJE, banco AMANHÃ)
```

- [ ] 5.1 Definir interfaces: `TaskRepository`, `LeadRepository`, `EventRepository`,
      `ProjectRepository` (métodos `list_by_state`, `move`, `add_lead`…)
- [ ] 5.2 Implementação `Markdown*Repository` — só mover o código que já existe pra dentro
      do balcão. **Zero mudança de comportamento.**
- [ ] 5.3 Trocar os chamadores (maestro, autopilot, tools) para usar o balcão

**Por que é a chave:** depois disto, migrar pro banco é escrever uma 2ª implementação do
balcão e virar uma chave. O resto do sistema não muda.

---

## Fase 6 — Migração markdown → Postgres (a grande migração)

**Em palavras simples:** trocar o "caderno" (markdown) por um "fichário com índice e travas"
(banco), sem perder nada e sem parar a operação. Como trocar agenda de papel por digital:
copia tudo, usa as duas em paralelo, confere que batem, e só então aposenta o papel.

**Já temos:** Supabase Postgres conectado (`SUPABASE_DB_URL`), `psycopg` + `pgvector`,
padrão de conexão (`memory/semantic.py::_connection()`) e pasta `supabase/migrations/`.

### 6.a — O que vira tabela

| Markdown hoje | Tabela |
|---|---|
| `tasks/*.md` (kanban + `TASK-XXX.md`) | `tasks` (coluna `state`) + `task_briefings` |
| `projetos/projetos.md` | `projects` |
| `crm/*.md` (segmentado) | `leads` (coluna `segment`) |
| `logs/eventos.md` | `events` |
| `memoria/decisoes.md` | `decisions` |
| `logs/whatsapp_mensagens.md` | `whatsapp_messages` |
| `logs/agent_interactions.jsonl` | `interactions` |
| `backend/data/usage.jsonl` | `usage` |
| `*_state.json` (cadência, dedup, autopilot) | `runtime_state` (chave→valor) |

### 6.b — Esquema núcleo (nova migration em `supabase/migrations/`)

```sql
create table projects (
  id text primary key, name text not null, prefix text, nature text,
  status text default 'ativo', crm text, repo text, description text,
  created_at timestamptz default now()
);
create table tasks (
  id text primary key, title text not null, state text not null,
  project_id text references projects(id), agent text, priority text default 'media',
  objetivo text, proxima_acao text, bloqueio text,
  started_at timestamptz, created_at timestamptz default now(), updated_at timestamptz default now()
);
create index on tasks(state);
create index on tasks(project_id);
create table leads (
  id text primary key, segment text not null, nome text, cidade text, servico text,
  contato text, status text default 'novo', score text, temperatura text, prioridade text,
  responsavel text, project_id text references projects(id), origem text, tags text,
  observacoes text, captura timestamptz default now()
);
create index on leads(segment, status);
create table events (
  id bigserial primary key, at timestamptz not null, type text, title text,
  agents text, detail text, ref text, status text
);
-- decisions, whatsapp_messages, interactions, usage, runtime_state: mesma ideia
```

### 6.c — Estratégia segura, em 5 degraus

```
Degrau 1  CRIAR ESQUEMA   → roda a migration; tabelas vazias. Nada usa ainda.
Degrau 2  BACKFILL        → script lê todo o markdown e INSERE no banco (1 vez, segundos).
Degrau 3  ESCRITA DUPLA   → o balcão (Fase 5) grava nos DOIS lugares: markdown E banco.
                            Leitura ainda vem do markdown.
Degrau 4  CONFERÊNCIA     → script compara markdown vs banco e aponta diferenças.
                            Bateu por alguns dias → confiança.
Degrau 5  VIRAR A CHAVE   → flag DATA_BACKEND=postgres: leitura passa a vir do banco.
                            Markdown vira EXPORTAÇÃO gerada do banco (git/humano).
```

**Escrita dupla é o segredo:** se o banco der problema, o markdown está intacto. Só depois
de confiar, inverte.

### 6.d — Decisão: matar o markdown ou manter como exportação?

Recomendado: **híbrido**. Banco = fonte da verdade (transações, consultas, concorrência).
Markdown = exportação automática gerada do banco (leitura humana + histórico no git).
Ganha o banco **sem perder** o que o markdown dava.

### 6.e — O que melhora na hora

- `build_maestro_snapshot` deixa de reparsear 12 arquivos → ~5 consultas SQL.
- Concorrência resolvida pelo banco (some o lock da Fase 4).
- Consultas hoje impossíveis viram `SELECT` ("leads quentes de SP desta semana").
- Dados operacionais + memória semântica (pgvector) no mesmo banco → dá pra cruzar.

- [ ] 6.1 Migration com o esquema núcleo
- [ ] 6.2 Script de backfill (markdown → banco)
- [ ] 6.3 Implementações `Postgres*Repository`
- [ ] 6.4 Escrita dupla (atrás de flag)
- [ ] 6.5 Script de conferência markdown × banco
- [ ] 6.6 Flag `DATA_BACKEND` para virar a leitura
- [ ] 6.7 Job de exportação banco → markdown (modo híbrido)

---

## Fase 7 — Consolidações estratégicas

**Em palavras simples:** parar de ter "dois de tudo".

- [ ] 7.1 **Orquestração:** escolher **um** entre CrewAI (`crews/`) e LangGraph (`graph/`).
      O LangGraph já tem trava de custo + checkpoint — bom alvo. Migrar crews aos poucos.
- [ ] 7.2 **CLI:** trocar o `if/elif` de ~280 linhas (`main.py`) por tabela de comandos (registry)
- [ ] 7.3 **Config/secrets:** um objeto `Settings` (pydantic-settings) carregado 1 vez
- [ ] 7.4 **Erros:** trocar os ~38 `except: pass` mudos por log + tabela/feed de erros visível
- [ ] 7.5 **Front painel:** (baixa prioridade) modularizar; obrigatório só o token da Fase 3
- [ ] 7.6 **social_executor:** apagar de vez (já tratado na Fase 0)

---

## Roteiro (a ordem importa)

```
Fase 0 → Fase 2 (testes) → Fase 1 (dedup, verificada pelos testes) →
Fase 3 (segurança) → Fase 4 (lock + cache) →
Fase 5 (porta única) → Fase 6 (banco: degraus 1→5) →
Fase 7 (consolidações)
```

**Regra de ouro: Fase 5 antes da 6.** Sem a "porta única", migrar pro banco vira mexer em
30 lugares; com ela, vira escrever 1 implementação nova e virar uma chave.
