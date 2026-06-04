# TASK-003 — Automação snapshot dashboard operacional

**ID:** TASK-003  
**Projeto:** PROJ-001 (Laboratório multiagente)  
**Status:** `arquivado` (cancelada)  
**Prioridade:** media  
**Criada em:** 2026-05-28  
**Atualizada em:** 2026-05-31 (E5 — auditoria Ronaldo · Actions OK)

> Task persistente · Modelo: [docs/modelo-task.md](../docs/modelo-task.md) · Dashboard: [dashboard/metricas_operacionais.md](../dashboard/metricas_operacionais.md)

**Agente responsável:** ronaldo_maestro (coord.)  
**Agentes auxiliares:** dev, juarez  

---

## Objetivo

Automatizar a **atualização básica** do dashboard operacional via GitHub Actions — snapshot auditável de TASKs e leads **sem quebrar** o fluxo markdown-first atual.

**Critério de sucesso:** snapshot operacional atualizar automaticamente sem caos.

## Contexto

- Dashboard manual criado em `dashboard/metricas_operacionais.md`.
- TASK-001 e TASK-002 (pintores/leads) **canceladas** em 2026-05-31 — eram teste; TASK-003 permanece válida para snapshot geral.
- Necessidade de visão sistêmica atualizada sem backend, banco ou frontend.

## Escopo

| Incluído | Excluído |
|----------|----------|
| Leitura simples TASK-*.md | Banco de dados |
| Contagem status Kanban | Backend / API |
| Contagem leads CRM | Frontend dashboard |
| Snapshot seção 0 (auto) | Analytics landing |
| Workflow GitHub Actions | Dependências pip/npm |
| Script Python stdlib | Over-engineering |

## Responsáveis

| Agente | Papel |
|--------|-------|
| **Dev** | Script + workflow + estrutura técnica |
| **Juarez** | Validar clareza métricas e impacto operacional |
| **Ronaldo** | Auditar, integrar ao ecossistema, registrar aprendizado |

## Entregáveis

| # | Entregável | Dono | Status |
|---|------------|------|--------|
| E1 | Proposta técnica mínima | Dev | ✅ |
| E2 | `scripts/update_dashboard_snapshot.py` | Dev | ✅ |
| E3 | `.github/workflows/update-dashboard.yml` | Dev | ✅ |
| E4 | Validação operacional Juarez | Juarez | ✅ |
| E5 | Auditoria Ronaldo + registro | Ronaldo | ✅ |

## Estrutura técnica (Dev)

```
scripts/update_dashboard_snapshot.py   # stdlib — lê TASKs + CRM → snapshot
.github/workflows/update-dashboard.yml # push + cron diário + commit auto
dashboard/metricas_operacionais.md   # seção 0 entre AUTO-SNAPSHOT markers
```

### Triggers workflow

- Push em `main` alterando `tasks/**`, `crm/**`, `dashboard/**`, script ou workflow
- Schedule: 12:00 UTC diário
- `workflow_dispatch` manual

### O que o snapshot atualiza (automático)

- WIP e pipeline Kanban
- Entregáveis por TASK persistente
- Funil CRM e índice de leads
- Hipóteses `a_testar`
- Taxas simples (lead → convertido, entregue → abordado)

### O que permanece manual (Ronaldo)

- Seções 1–12: gargalos, bloqueios, aprendizados, saúde, foco imediato

---

## Validação Juarez (E4)

**Data:** 2026-05-28

| Critério | Veredito |
|----------|----------|
| Métricas legíveis em < 2 min | ✅ |
| Não duplica fontes canônicas (CRM/TASK) | ✅ |
| Impacto operacional baixo — só seção 0 auto | ✅ |
| Risco de confusão manual vs auto | mitigado — markers claros |
| SLA / throughput visíveis no snapshot | ✅ parcial (Kanban + entregáveis) |

**Observação Juarez:** Manter checklist seção 13 para Ronaldo atualizar gargalos manualmente. Automação não substitui auditoria humana.

Registro: [memoria/memoria_operacional_juarez.md](../memoria/memoria_operacional_juarez.md)

---

## Rodada operacional 1 — 2026-05-28

| Ordem | Ação | Agente | Status |
|-------|------|--------|--------|
| 1 | Script snapshot stdlib | Dev | ✅ |
| 2 | Workflow GitHub Actions | Dev | ✅ |
| 3 | Validar métricas operacionais | Juarez | ✅ |
| 4 | Teste local script | Dev | ✅ |
| 5 | Push + validar Action | Dev/Vitor | ✅ |
| 6 | Auditoria Ronaldo | Ronaldo | ✅ |

---

## Briefings

### Dev — TASK-003

**Entregue:** E1–E3. **Próximo:** confirmar Action no GitHub após push.

### Juarez — TASK-003

**Entregue:** E4. Snapshot não altera processos de entrega — apenas leitura.

### Ronaldo — TASK-003

**Próximo:** E5 — auditar após primeira execução Actions; registrar aprendizado.

---

## Critérios de aceite

- [x] Script Python stdlib lê TASKs e CRM
- [x] Workflow GitHub Actions configurado
- [x] Snapshot atualiza apenas bloco marcado (não sobrescreve dashboard inteiro)
- [x] Juarez validou clareza operacional
- [x] Action executou com sucesso no GitHub (pós-push)
- [x] Snapshot commit automático funciona sem conflito
- [x] Fluxo manual TASK/CRM/CRM intacto

---

## Status atual

| Campo | Valor |
|-------|-------|
| **Status** | arquivado (cancelada) |
| **Kanban** | [concluidas.md](concluidas.md) |
| **Bloqueios** | Nenhum |
| **Rodada** | 1 — encerrada |

---

## Registro de agentes

### Ronaldo Maestro
- **Última ação:** TASK-003 criada; briefings Dev + Juarez
- **Data:** 2026-05-28

### Dev
- **Última ação:** script + workflow + teste local OK
- **Próxima:** push e validar Action
- **Data:** 2026-05-28

### Juarez
- **Última ação:** E4 — validação operacional aprovada
- **Data:** 2026-05-28

---

## Auditoria do Ronaldo

| Campo | Valor |
|-------|-------|
| **Veredito** | ✅ aprovado — Actions + snapshot auto validados |
| **Qualidade** | simples ✅ · auditável ✅ · markdown-first ✅ |

---

## Histórico

| Data | Evento |
|------|--------|
| 2026-05-31 | Push main + Action OK (`fb102e2`); TASK concluída |
| 2026-05-28 | TASK-003 criada |
| 2026-05-28 | Dev entrega script + workflow; Juarez valida |

---

## Próximos passos

1. ~~Push para `main` — dispara workflow~~ ✅
2. ~~Validar commit automático do snapshot~~ ✅
3. ~~Ronaldo fecha E5 e registra aprendizado~~ ✅
