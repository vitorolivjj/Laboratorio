# Arquivado

Tarefas **concluídas há tempo**, **canceladas** ou sem relevância operacional — histórico preservado, fora da fila ativa.

Origem: `concluidas.md` (revisão periódica) ou cancelamento explícito.

---

## Arquivo

## Reset kanban — 2026-06-03

Todas as tasks ativas foram **canceladas e arquivadas** a pedido do Vitor. Kanban zerado (`backlog`, `executando`, `standby`, `aguardando`, `concluidas`). Documentos `TASK-*.md` / `LP-PINTOR-*.md` preservados com status `arquivado (cancelada)`.

- **Captura Donizete:** interrompida (`StopDonizete` + estado limpo)
- **Próximo passo:** criar novas tasks (ex.: captura com grupo fixo)


### TASK-000 — Estrutura inicial do repositório

- **Concluída em:** 2026-05-28
- **Agente:** dev
- **Projeto:** PROJ-001
- **Resultado:** Pastas agentes, backend, memoria/ronaldo_maestro, definições dos quatro agentes; pastas `contexto/`, `tasks/`, `logs/`, `workflows/` e README operacional.
- **Aprendizado:** —
- **Nota movimentação:** Arquivada — reset kanban (2026-06-03); histórico preservado (2026-06-03)

### TASK-005 — Revisão Estratégica dos Modelos dos Agentes

- **Concluída em:** 2026-05-30
- **Agente:** ronaldo_maestro (relatório) · dev (E6)
- **Projeto:** PROJ-001
- **Resultado:** Roteamento LLM por agente — todos anthropic/claude-sonnet-4-20250514 · `./run.sh llm-config`
- **Aprendizado:** Variáveis `*_PROVIDER` sem código = config decorativa. Ver [TASK-005-relatorio-modelos.md](TASK-005-relatorio-modelos.md)
- **Nota movimentação:** Arquivada — reset kanban (2026-06-03); histórico preservado (2026-06-03)

### TASK-006 — Ajuste Final da Arquitetura de Modelos

- **Concluída em:** 2026-05-30
- **Agente:** ronaldo_maestro
- **Projeto:** PROJ-001
- **Resultado:** Arquitetura v1 — Ronaldo `openai/gpt-5` · especialistas `anthropic/sonnet` · `llm-config` OK
- **Aprendizado:** Camada estratégica separada da execução; ver `memoria/decisoes.md`
- **Nota movimentação:** Arquivada — reset kanban (2026-06-03); histórico preservado (2026-06-03)

### TASK-007 — Conectar Caio ao WhatsApp

- **Concluída em:** 2026-05-31
- **Agente:** dev · caio_manteiga
- **Projeto:** PROJ-001
- **Resultado:** WhatsApp → VPS → Caio → WhatsApp em produção · webhook Meta · número real · primeira conversa humana validada
- **Aprendizado:** Modelo `claude-sonnet-4-20250514` descontinuado — migrar para `claude-sonnet-4-6`
- **Nota movimentação:** Arquivada — reset kanban (2026-06-03); histórico preservado (2026-06-03)

### TASK-008 — Painel Maestro v1

- **Concluída em:** 2026-05-31
- **Agente:** dev
- **Projeto:** PROJ-001
- **Resultado:** Dashboard operacional dark/neon · API snapshot · 6 seções · deploy VPS `/painel/`
- **Aprendizado:** Agregar markdown existente evita duplicar CRM/tasks em banco
- **Nota movimentação:** Arquivada — reset kanban (2026-06-03); histórico preservado (2026-06-03)

### TASK-010 — VitorOS A0: Esqueleto (Supabase, Auth, shell PWA, deploy VPS)

- **Concluída em:** 2026-05-31
- **Agente:** dev · loide
- **Projeto:** PROJ-002
- **Resultado:** Supabase + migration · shell PWA 3 camadas · Auth · deploy `vitoroliv.com` · login validado pelo Vitor
- **Aprendizado:** Configurar Site URL Supabase = domínio prod; skills aceleram próximas telas (TASK-022)
- **Nota movimentação:** Arquivada — reset kanban (2026-06-03); histórico preservado (2026-06-03)

### TASK-011 — VitorOS A1: Rabiscos + Projetos + Tasks kanban

- **Concluída em:** 2026-05-31
- **Agente:** dev · loide
- **Projeto:** PROJ-002
- **Resultado:** Kanban 6 colunas + CRUD rabiscos/projetos/tasks · Supabase · deploy `vitoroliv.com` · aceite Vitor
- **Aprendizado:** Specs UX na fábrica (Lab); código só no `centralvitor`
- **Nota movimentação:** Arquivada — reset kanban (2026-06-03); histórico preservado (2026-06-03)

### TASK-003 — Automação snapshot dashboard operacional

- **Concluída em:** 2026-05-31
- **Agente:** dev · juarez · ronaldo_maestro
- **Projeto:** PROJ-001
- **Resultado:** Script stdlib + workflow Actions · snapshot auto em `dashboard/metricas_operacionais.md` · commit `fb102e2` pós-push
- **Aprendizado:** Push bloqueado por `.venv` no commit — `.gitignore` raiz resolve; painel Maestro complementa snapshot (tempo real vs batch)
- **Nota movimentação:** Arquivada — reset kanban (2026-06-03); histórico preservado (2026-06-03)

### TASK-022 — Biblioteca Skills Dev + Loide

- **Concluída em:** 2026-05-31
- **Agente:** dev · loide · ronaldo_maestro
- **Projeto:** PROJ-001 (transversal PROJ-002)
- **Resultado:** 3 Cursor skills + índice + mockup kanban + protocolo delegação integrado
- **Aprendizado:** Skills na fábrica; briefings referenciam `skills-biblioteca.md`
- **Nota movimentação:** Arquivada — reset kanban (2026-06-03); histórico preservado (2026-06-03)

### LP-PINTOR-006 — Template Meta WhatsApp (abertura proativa)
- **Cancelada em:** 2026-06-03 · **Motivo:** reset kanban — Vitor inicia novas tasks

- **Concluída em:** 2026-06-03
- **Agente:** vitor · caio_manteiga · dev
- **Projeto:** PROJ-LP
- **Resultado:** Template `abertura_pintor_contato` aprovado Meta · `send_client_template` operacional
- **Ref:** `memoria/caio_manteiga/templates_meta_wa.md`
### LP-PINTOR-007 — Template produção LP in-house
- **Cancelada em:** 2026-06-03 · **Motivo:** reset kanban — Vitor inicia novas tasks

- **Concluída em:** 2026-06-03
- **Agente:** loide · dev · vitor
- **Projeto:** PROJ-LP
- **Resultado:** `/previas/exemplo-pintor/` no ar · Webflow revogado · captação Donizete liberada
- **Ref:** `memoria/ronaldo_maestro/producao_lp_pintor.md` · decisão 2026-06-03
### LP-PINTOR-004 — Venda WhatsApp + primeira ativação R$ 69
- **Cancelada em:** 2026-06-03 · **Motivo:** reset kanban — Vitor inicia novas tasks

- **Concluída em:** 2026-06-02
- **Agente:** caio_manteiga · vitor · dev
- **Projeto:** PROJ-LP
- **Resultado:** LEAD-001 Stephanie Turnley ativo · KPI vitrine 1/1 · playbook integrado
- **Ref:** `memoria/caio_manteiga/playbook_comercial_lp_pintor.md`
### LAB-006 — LangGraph opera funil comercial (PROJ-LP)
- **Cancelada em:** 2026-06-03 · **Motivo:** reset kanban — Vitor inicia novas tasks

- **Concluída em:** 2026-06-02
- **Agente:** dev · ronaldo_maestro
- **Projeto:** PROJ-LAB
- **Resultado:** `./run.sh graph-run LP-PINTOR-002` · nó execute com `run_action` · doc em `langgraph_piloto_fase2.md`
- **Ref:** `backend/src/laboratorio/graph/commercial.py`
### LP-PINTOR-002 — Template landing + host prévia
- **Cancelada em:** 2026-06-03 · **Motivo:** reset kanban — Vitor inicia novas tasks

- **Concluída em:** 2026-06-02
- **Agente:** loide · dev
- **Projeto:** PROJ-LP
- **Resultado:** Template + build/deploy · prévia em `api.laboratorioagentes.com.br/previas/exemplo-pintor/`
- **Ref:** `docs/ux/landing-pintor/spec.md` · `frontend/lp-pintor/`
### LAB-005 — Autoevolução supervisionada (Fase 4)
- **Cancelada em:** 2026-06-03 · **Motivo:** reset kanban — Vitor inicia novas tasks

- **Concluída em:** 2026-06-02
- **Agente:** ronaldo_maestro · dev
- **Projeto:** PROJ-LAB
- **Resultado:** Resumo 1×/dia · timer VPS 09:00 BRT · sync automático pós-APROVAR · validado pelo Vitor
- **Ref:** `memoria/autoevolucao_fase4.md`
### LAB-004 — Autonomia graduada (Fase 3)
- **Cancelada em:** 2026-06-03 · **Motivo:** reset kanban — Vitor inicia novas tasks

- **Concluída em:** 2026-06-02
- **Agente:** dev · ronaldo_maestro
- **Projeto:** PROJ-LAB
- **Resultado:** Gateway `run_action` + CLI `agent-action` + aprovação `agent_action` · deploy VPS
- **Ref:** `memoria/autonomia_graduada_fase3.md`
### LAB-003 — Piloto LangGraph (motor paralelo ao CrewAI)
- **Cancelada em:** 2026-06-03 · **Motivo:** reset kanban — Vitor inicia novas tasks

- **Concluída em:** 2026-06-02
- **Agente:** dev · ronaldo_maestro
- **Projeto:** PROJ-LAB
- **Resultado:** Grafo LangGraph + checkpoints Sqlite + memória semântica no `load` · primeira execução OK · relatório em [LAB-003.md](LAB-003.md)
- **Aprendizado:** CrewAI permanece para inbound; LangGraph para tasks piloto via `./run.sh graph-pilot`
### LAB-002 — Separar organização por projeto (painel hierárquico)

- **Concluída em:** 2026-05-31
- **Agente:** dev · ronaldo_maestro
- **Projeto:** PROJ-LAB
- **Resultado:** Registry `projetos/projetos.md` + CRM segmentado (Laboratório/Landing Pintor) · painel com seções Projetos, Tasks por projeto (filtro) e CRM em abas · toda task com projeto, zero órfãs
- **Aprendizado:** Prefixos padronizados resolvidos por campo/prefixo/legado — convive com IDs `TASK-XXX` antigos. Ver [LAB-002.md](LAB-002.md)
- **Nota movimentação:** Arquivada — reset kanban (2026-06-03); histórico preservado (2026-06-03)

### TASK-021 — VitorOS (pausado PROJ-002)

- **Projeto:** PROJ-002 · **Status:** pausado · [TASK-021.md](TASK-021.md)
- **Nota movimentação:** Cancelada e arquivada — reset kanban (2026-06-03); Vitor cria novas tasks (2026-06-03)

### TASK-020 — VitorOS (pausado PROJ-002)

- **Projeto:** PROJ-002 · **Status:** pausado · [TASK-020.md](TASK-020.md)
- **Nota movimentação:** Cancelada e arquivada — reset kanban (2026-06-03); Vitor cria novas tasks (2026-06-03)

### TASK-019 — VitorOS (pausado PROJ-002)

- **Projeto:** PROJ-002 · **Status:** pausado · [TASK-019.md](TASK-019.md)
- **Nota movimentação:** Cancelada e arquivada — reset kanban (2026-06-03); Vitor cria novas tasks (2026-06-03)

### TASK-018 — VitorOS (pausado PROJ-002)

- **Projeto:** PROJ-002 · **Status:** pausado · [TASK-018.md](TASK-018.md)
- **Nota movimentação:** Cancelada e arquivada — reset kanban (2026-06-03); Vitor cria novas tasks (2026-06-03)

### TASK-017 — VitorOS (pausado PROJ-002)

- **Projeto:** PROJ-002 · **Status:** pausado · [TASK-017.md](TASK-017.md)
- **Nota movimentação:** Cancelada e arquivada — reset kanban (2026-06-03); Vitor cria novas tasks (2026-06-03)

### TASK-016 — VitorOS (pausado PROJ-002)

- **Projeto:** PROJ-002 · **Status:** pausado · [TASK-016.md](TASK-016.md)
- **Nota movimentação:** Cancelada e arquivada — reset kanban (2026-06-03); Vitor cria novas tasks (2026-06-03)

### TASK-015 — VitorOS (pausado PROJ-002)

- **Projeto:** PROJ-002 · **Status:** pausado · [TASK-015.md](TASK-015.md)
- **Nota movimentação:** Cancelada e arquivada — reset kanban (2026-06-03); Vitor cria novas tasks (2026-06-03)

### TASK-014 — VitorOS (pausado PROJ-002)

- **Projeto:** PROJ-002 · **Status:** pausado · [TASK-014.md](TASK-014.md)
- **Nota movimentação:** Cancelada e arquivada — reset kanban (2026-06-03); Vitor cria novas tasks (2026-06-03)

### LP-PINTOR-001B — Captação Facebook lote 2 (5 leads)
- **Cancelada em:** 2026-06-03 · **Motivo:** reset kanban — Vitor inicia novas tasks

- **Projeto:** PROJ-LP · **Agente:** donizete_social · **Após:** LP-PINTOR-001 · [LP-PINTOR-001B.md](LP-PINTOR-001B.md)
### LP-PINTOR-009 — Produzir prévia in-house (1 lead) — modelo repetível
- **Cancelada em:** 2026-06-03 · **Motivo:** reset kanban — Vitor inicia novas tasks

- **Projeto:** PROJ-LP · **Agentes:** loide · dev · juarez · **Dispara:** cada lead `pronto_pra_pagina` · [LP-PINTOR-009.md](LP-PINTOR-009.md)
### LP-PINTOR-008 — Automação CRM → build in-house + takedown
- **Cancelada em:** 2026-06-03 · **Motivo:** reset kanban — Vitor inicia novas tasks

- **Projeto:** PROJ-LP · **Agente:** dev · juarez · [LP-PINTOR-008.md](LP-PINTOR-008.md)
### LP-PINTOR-003 — CRM pintores + handoff Donizete→produção
- **Cancelada em:** 2026-06-03 · **Motivo:** reset kanban — Vitor inicia novas tasks

- **Projeto:** PROJ-LP · **Agente:** donizete_social · **Paralelo a:** LP-PINTOR-001 · [LP-PINTOR-003.md](LP-PINTOR-003.md)
### LP-PINTOR-005 — KPIs, escopo de alterações e auditoria

- **Projeto:** PROJ-LP · **Agente:** ronaldo_maestro · [LP-PINTOR-005.md](LP-PINTOR-005.md)
- **Nota movimentação:** Cancelada e arquivada — reset kanban (2026-06-03); Vitor cria novas tasks (2026-06-03)

### TASK-013 — VitorOS A2: Finanças

- **Bloqueio:** depende TASK-012 · PROJ-002 pausado
- **Desbloqueia:** Ronaldo
- **Agente:** dev · loide
- **Projeto:** PROJ-002
- **Documento:** [TASK-013.md](TASK-013.md)
- **Nota movimentação:** Cancelada e arquivada — reset kanban (2026-06-03); Vitor cria novas tasks (2026-06-03)

### TASK-012 — VitorOS A1: Home cockpit + KPIs derivados

- **Bloqueio:** PROJ-002 pausado — foco PROJ-LP (captação + produção in-house)
- **Desbloqueia:** Ronaldo após meta captação LP estável
- **Agente:** dev · loide
- **Projeto:** PROJ-002
- **Documento:** [TASK-012.md](TASK-012.md)
- **Nota movimentação:** Cancelada e arquivada — reset kanban (2026-06-03); Vitor cria novas tasks (2026-06-03)

### LP-PINTOR-001 — Captação Facebook lote 1 (5 leads)

- **Iniciada em:** 2026-06-03 · **Deploy rodada 4:** 2026-06-03
- **Agente:** donizete_social
- **Projeto:** PROJ-LP
- **Meta:** **5** leads `pronto_pra_pagina` · sprint 10 total (001B = +5)
- **Próxima ação:** Mac: `facebook-cdp-mac.sh` · WhatsApp `PlayDonizete busca inicia` / `StopDonizete`
- **Fluxo:** busca independente · standby automático · posts autônomos · template Meta ✓
- **Plano:** [plano_atuacao_donizete_lp.md](../memoria/ronaldo_maestro/plano_atuacao_donizete_lp.md)
- **Monitor:** `donizete-captura` · WhatsApp `captura` / `donizete busca`
- **Nota movimentação:** PlayDonizete — busca intermitente (task em standby) (2026-06-03)
- **Nota movimentação:** Cancelada e arquivada — reset kanban (2026-06-03); Vitor cria novas tasks (2026-06-03)

### TASK-001 — Landing low ticket para pintores autônomos

- **Cancelada em:** 2026-05-31
- **Motivo:** Teste de validação — escopo descartado pelo Vitor
- **Agente:** ronaldo_maestro (coord.) · juarez · dev · caio_manteiga
- **Projeto:** PROJ-001
- **Resultado parcial:** Landing publicada em GitHub Pages (referência histórica); funil pintores não será continuado
- **Documento:** [TASK-001.md](TASK-001.md)

---

### TASK-002 — Validação captação orgânica Donizete → Caio

- **Cancelada em:** 2026-05-31
- **Motivo:** Teste de captação/leads pintores — escopo descartado pelo Vitor
- **Agente:** ronaldo_maestro (coord.) · donizete_social · caio_manteiga
- **Projeto:** PROJ-001
- **Resultado parcial:** Workflow documentado; captação orgânica pintores encerrada
- **Documento:** [TASK-002.md](TASK-002.md)

---

## Reset Fase 0 — 2026-06-01

Kanban zerado para recomeço com trava de aprovação WhatsApp. Documentos `TASK-*.md` / `LP-PINTOR-*.md` intactos — só saíram das filas ativas.

### TASK-012 — VitorOS A1: Home cockpit + KPIs derivados
- **Cancelada em:** 2026-06-03 · **Motivo:** reset kanban — Vitor inicia novas tasks
- **Arquivada em:** 2026-06-01 · estava em `executando.md`
- **Projeto:** PROJ-002 · **Documento:** [TASK-012.md](TASK-012.md)
### LP-PINTOR-001 — Captação Facebook (post-isca + garimpo) — histórico Fase 0
- **Cancelada em:** 2026-06-03 · **Motivo:** reset kanban — Vitor inicia novas tasks
- **Arquivada em:** 2026-06-01 · estava em `executando.md`
- **Nota:** reativada 2026-06-03 — kanban ativo só em `executando.md` (não duplicar aqui)
- **Projeto:** PROJ-LP · **Documento:** [LP-PINTOR-001.md](LP-PINTOR-001.md)
### LP-PINTOR-002 — Template landing (2×4) + host grátis
- **Cancelada em:** 2026-06-03 · **Motivo:** reset kanban — Vitor inicia novas tasks
- **Arquivada em:** 2026-06-01 · estava em `executando.md`
- **Projeto:** PROJ-LP · **Documento:** [LP-PINTOR-002.md](LP-PINTOR-002.md)
### LP-PINTOR-003 — CRM pintores (funil invertido) + handoff
- **Cancelada em:** 2026-06-03 · **Motivo:** reset kanban — Vitor inicia novas tasks
- **Arquivada em:** 2026-06-01 · estava em `planejando.md`
- **Projeto:** PROJ-LP · **Documento:** [LP-PINTOR-003.md](LP-PINTOR-003.md)
### TASK-013 — VitorOS A2: Finanças
- **Cancelada em:** 2026-06-03 · **Motivo:** reset kanban — Vitor inicia novas tasks
- **Arquivada em:** 2026-06-01 · estava em `planejando.md` / backlog
- **Projeto:** PROJ-002 · **Documento:** [TASK-013.md](TASK-013.md)
### LP-PINTOR-004 — Script de venda WhatsApp (ativação R$ 69)
- **Cancelada em:** 2026-06-03 · **Motivo:** reset kanban — Vitor inicia novas tasks
- **Arquivada em:** 2026-06-01 · estava em `backlog.md`
- **Projeto:** PROJ-LP · **Documento:** [LP-PINTOR-004.md](LP-PINTOR-004.md)
### LP-PINTOR-005 — KPIs, escopo de alterações e auditoria
- **Cancelada em:** 2026-06-03 · **Motivo:** reset kanban — Vitor inicia novas tasks
- **Arquivada em:** 2026-06-01 · estava em `backlog.md`
- **Projeto:** PROJ-LP · **Documento:** [LP-PINTOR-005.md](LP-PINTOR-005.md)
### TASK-014 — VitorOS A2: Objetivos macro
- **Cancelada em:** 2026-06-03 · **Motivo:** reset kanban — Vitor inicia novas tasks
- **Arquivada em:** 2026-06-01 · **Documento:** [TASK-014.md](TASK-014.md)
### TASK-015 — VitorOS A3: Motor alertas + eventos
- **Cancelada em:** 2026-06-03 · **Motivo:** reset kanban — Vitor inicia novas tasks
- **Arquivada em:** 2026-06-01 · **Documento:** [TASK-015.md](TASK-015.md)
### TASK-016 — VitorOS A3: Atalhos + Mapa + Busca
- **Cancelada em:** 2026-06-03 · **Motivo:** reset kanban — Vitor inicia novas tasks
- **Arquivada em:** 2026-06-01 · **Documento:** [TASK-016.md](TASK-016.md)
### TASK-017 — Negão B0: Import conversations.json
- **Cancelada em:** 2026-06-03 · **Motivo:** reset kanban — Vitor inicia novas tasks
- **Arquivada em:** 2026-06-01 · **Documento:** [TASK-017.md](TASK-017.md)
### TASK-018 — Negão B1: Perfil-semente
- **Cancelada em:** 2026-06-03 · **Motivo:** reset kanban — Vitor inicia novas tasks
- **Arquivada em:** 2026-06-01 · **Documento:** [TASK-018.md](TASK-018.md)
### TASK-019 — Negão B2: pgvector episódica
- **Cancelada em:** 2026-06-03 · **Motivo:** reset kanban — Vitor inicia novas tasks
- **Arquivada em:** 2026-06-01 · **Documento:** [TASK-019.md](TASK-019.md)
### TASK-020 — Negão B3+B4: Chat + sugestões
- **Cancelada em:** 2026-06-03 · **Motivo:** reset kanban — Vitor inicia novas tasks
- **Arquivada em:** 2026-06-01 · **Documento:** [TASK-020.md](TASK-020.md)
### TASK-021 — Integração + seed + DNS ia.
- **Cancelada em:** 2026-06-03 · **Motivo:** reset kanban — Vitor inicia novas tasks
- **Arquivada em:** 2026-06-01 · **Documento:** [TASK-021.md](TASK-021.md)
### TASK-004 — Validar crew de exemplo no backend
- **Cancelada em:** 2026-06-03 · **Motivo:** reset kanban — Vitor inicia novas tasks
- **Arquivada em:** 2026-06-01 · **Documento:** [TASK-004.md](TASK-004.md)

---

<!-- Mover de concluidas.md quando não precisar mais consulta frequente -->
