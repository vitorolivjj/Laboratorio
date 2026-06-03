# Dashboard — Métricas operacionais

Visão centralizada da operação do Laboratório multiagente.

**Dono:** Ronaldo Maestro · **Atualização:** manual + automática (GitHub Actions) · **Frequência:** rodada ou diária

> Fontes: `tasks/` · `crm/crm_*.md` (segmentado) · `memoria/aprendizados.md` · `memoria/hipoteses_testadas.md` · `logs/eventos.md`  
> Snapshot: `scripts/update_dashboard_snapshot.py` · `.github/workflows/update-dashboard.yml`

**Última atualização manual:** 2026-05-30 (TASK-006 — arquitetura modelos v1)  
**Última atualização automática:** 2026-06-03 (script local / GitHub Actions)

---

## 0. Snapshot automático

<!-- AUTO-SNAPSHOT:START -->
> **Snapshot automático** · gerado em **2026-06-03 16:47 UTC** · script `scripts/update_dashboard_snapshot.py`  
> **CRM:** segmentado (`crm/crm_*.md`) — alinhado ao Painel Maestro

### Resumo

| Indicador | Valor |
|-----------|-------|
| TASKs em execução | 1 (cadência 2min entre starts) |
| TASKs em planejamento | 0 |
| Entregáveis (tasks `executando`) | 0 / 0 |
| **Total leads (todos CRMs)** | **2** |
| KPI LP — ativos | 1 |
| KPI LP — taxa ativação | 100% |
| Hipóteses `a_testar` | 2 |

### Pipeline Kanban

| Status | Qtd | Tasks |
|--------|-----|-------|
| `executando` | 1 | LP-PINTOR-001 |
| `planejando` | 0 | — |
| `aguardando` | 3 | LP-PINTOR-006, TASK-012, TASK-013 |
| `backlog` | 13 | LP-PINTOR-001, LP-PINTOR-009, LP-PINTOR-008, LP-PINTOR-003, LP-PINTOR-005, TASK-014, TASK-015, TASK-016, TASK-017, TASK-018, TASK-019, TASK-020, TASK-021 |
| `concluído` (kanban) | 17 | LP-PINTOR-007, LP-PINTOR-004, LAB-006, LP-PINTOR-002, LAB-005, LAB-004, LAB-003, LAB-002, TASK-022, TASK-003, TASK-011, TASK-010, TASK-008, TASK-007, TASK-006, TASK-005, TASK-000 |
| `arquivado` (canceladas) | 2 | TASK-001, TASK-002 |

### Tasks (arquivos persistentes)

| Task | Status | Entregáveis | Progresso |
|------|--------|-------------|-----------|
| [LAB-002](../tasks/LAB-002.md) | `desconhecido` | 0/0 | — |
| [LAB-003](../tasks/LAB-003.md) | `concluido` | 0/3 | 0% |
| [LAB-004](../tasks/LAB-004.md) | `concluido` | 4/4 | 100% |
| [LAB-005](../tasks/LAB-005.md) | `concluido` | 0/0 | — |
| [LAB-006](../tasks/LAB-006.md) | `concluido` | 0/0 | — |
| [LP-PINTOR-001](../tasks/LP-PINTOR-001.md) | `executando` | 0/0 | — |
| [LP-PINTOR-002](../tasks/LP-PINTOR-002.md) | `concluido` | 0/0 | — |
| [LP-PINTOR-003](../tasks/LP-PINTOR-003.md) | `backlog` | 0/0 | — |
| [LP-PINTOR-004](../tasks/LP-PINTOR-004.md) | `concluido` | 0/0 | — |
| [LP-PINTOR-005](../tasks/LP-PINTOR-005.md) | `backlog` | 0/0 | — |
| [LP-PINTOR-006](../tasks/LP-PINTOR-006.md) | `aguardando` | 0/0 | — |
| [LP-PINTOR-007](../tasks/LP-PINTOR-007.md) | `**concluido**` | 0/0 | — |
| [LP-PINTOR-008](../tasks/LP-PINTOR-008.md) | `backlog` | 0/0 | — |
| [LP-PINTOR-009](../tasks/LP-PINTOR-009.md) | `backlog` | 0/0 | — |
| [TASK-001](../tasks/TASK-001.md) | `arquivado` | 5/8 | 62% |
| [TASK-002](../tasks/TASK-002.md) | `arquivado` | 1/5 | 20% |
| [TASK-003](../tasks/TASK-003.md) | `concluido` | 5/5 | 100% |
| [TASK-005](../tasks/TASK-005.md) | `concluido` | 6/6 | 100% |
| [TASK-006](../tasks/TASK-006.md) | `concluido` | 6/6 | 100% |
| [TASK-007](../tasks/TASK-007.md) | `concluido` | 7/7 | 100% |
| [TASK-008](../tasks/TASK-008.md) | `concluido` | 5/5 | 100% |
| [TASK-009](../tasks/TASK-009.md) | `concluido` | 0/0 | — |
| [TASK-010](../tasks/TASK-010.md) | `concluído` | 5/5 | 100% |
| [TASK-011](../tasks/TASK-011.md) | `concluído` | 4/4 | 100% |
| [TASK-012](../tasks/TASK-012.md) | `aguardando` | 0/0 | — |
| [TASK-013](../tasks/TASK-013.md) | `aguardando` | 0/0 | — |
| [TASK-014](../tasks/TASK-014.md) | `backlog` | 0/0 | — |
| [TASK-015](../tasks/TASK-015.md) | `backlog` | 0/0 | — |
| [TASK-016](../tasks/TASK-016.md) | `backlog` | 0/0 | — |
| [TASK-017](../tasks/TASK-017.md) | `backlog` | 0/0 | — |
| [TASK-018](../tasks/TASK-018.md) | `backlog` | 0/0 | — |
| [TASK-019](../tasks/TASK-019.md) | `backlog` | 0/0 | — |
| [TASK-020](../tasks/TASK-020.md) | `backlog` | 0/0 | — |
| [TASK-021](../tasks/TASK-021.md) | `backlog` | 0/4 | 0% |
| [TASK-022](../tasks/TASK-022.md) | `concluido` | 6/6 | 100% |
| [VITOR-001](../tasks/VITOR-001.md) | `**cancelada**` | 0/0 | — |

### CRM segmentado

#### CRM Laboratório (`crm_laboratorio.md`)

| Etapa | Qtd |
|-------|-----|
| `novo` | 0 |
| `qualificacao` | 0 |
| `diagnostico` | 1 |
| `proposta` | 0 |
| `negociacao` | 0 |
| `fechado` | 0 |
| `perdido` | 0 |
| **Total** | **1** |

#### CRM Landing Page Pintor (`crm_landing_pintor.md`)

| Etapa | Qtd |
|-------|-----|
| `prospectado` | 0 |
| `pronto_pra_pagina` | 0 |
| `previa_no_ar` | 0 |
| `abordado` | 0 |
| `ativo` | 1 |
| `recusou` | 0 |
| **Total** | **1** |

### Leads (todos os CRMs)

| ID | CRM | Nome | Status | Captura |
|----|-----|------|--------|---------|
| LEAD-VIOLA | CRM Laboratório | Dr. Viola | `diagnostico` | 2026-05-31 |
| LEAD-001 | CRM Landing Page Pintor | Stephanie Turnley | `ativo` | 2026-06-02 |

<!-- AUTO-SNAPSHOT:END -->

---

## 1. Resumo executivo (leitura 30s)

| Indicador | Valor | Status |
|-----------|-------|--------|
| TASKs em execução | 1 / 3 WIP | 🟢 |
| TASKs em planejamento | 1 (TASK-010 VitorOS) | 🟡 |
| Entregáveis concluídos (TASKs ativas) | 4 / 5 | 🟡 |
| Leads no CRM | 0 | ⚪ |
| Painel Maestro + WhatsApp Caio | ✅ produção | 🟢 |
| Bloqueios críticos | 0 | 🟢 |
| TASKs teste canceladas | TASK-001, TASK-002 (pintores) | ⚪ arquivadas |

**Foco imediato:** PROJ-002 VitorOS (TASK-010) · TASK-003 snapshot Actions · infra Lab estável

---

## 2. Métricas de TASKs

### 2.1 Pipeline Kanban

| Status | Qtd | TASKs |
|--------|-----|-------|
| `executando` | 1 | TASK-003 |
| `planejando` | 1 | TASK-010 |
| `aguardando` | 0 | — |
| `backlog` | 11+ | TASK-011–021, TASK-004 |
| `arquivado` | 2 | TASK-001, TASK-002 (canceladas) |
| `concluído` | 6 | TASK-005–008, … |

**WIP:** 1/3 · **Capacidade livre:** 2 slots

### 2.2 TASKs ativas — detalhe

| TASK | Projeto | Rodada | Entregáveis | Progresso | Bloqueio |
|------|---------|--------|-------------|-----------|----------|
| [TASK-003](../tasks/TASK-003.md) | PROJ-001 | 1 | E1–E4 ✅ · E5 🔄 | 80% | push Actions |
| [TASK-010](../tasks/TASK-010.md) | PROJ-002 | — | planejando | — | aguarda Dev+Loide |

### 2.3 Throughput de execução

| Métrica | Período | Valor |
|---------|---------|-------|
| TASKs concluídas (Lab) | 2026-05-31 | TASK-007, TASK-008 |
| TASKs canceladas (teste) | 2026-05-31 | TASK-001, TASK-002 |
| Deploys Painel Maestro | 2026-05-31 | VPS `/painel/` |
| PROJ-002 criado | 2026-05-31 | 12 tasks VitorOS |

### 2.4 SLA TASK (meta interna)

| Transição | SLA | Observação |
|-----------|-----|------------|
| backlog → executando | ≤ 48h após priorização | OK TASK-001/002 |
| Entregável por rodada | conforme briefing | TASK-001 acelerada |
| executando → concluído | após auditoria Ronaldo | nenhuma concluída ainda |

---

## 3. Métricas de leads

> Fonte canônica: [crm/leads.md](../crm/leads.md)

### 3.1 Funil CRM

| Etapa | Qtd | % do total |
|-------|-----|------------|
| Captados (`novo`) | 0 | — |
| Qualificados | 0 | — |
| Entregues Caio | 0 | — |
| Abordados | 0 | — |
| Convertidos | 0 | — |
| Sem resposta | 0 | — |
| Descartados | 0 | — |

**Total leads:** 0 · **Captação pintores:** encerrada (TASK-002 cancelada 2026-05-31)

### 3.2 Qualidade de captação

| Métrica | Valor | Meta |
|---------|-------|------|
| Score médio | — | ≥ 3 |
| Leads com tags completas | 0% | 100% |
| Leads com contexto handoff | 0% | 100% |
| Violações anti-spam | 0 | 0 |
| Limite 1 lead/hora respeitado | — | 100% |

### 3.3 Origem (quando houver dados)

| Origem | Captados | Qualificados | Convertidos |
|--------|----------|--------------|-------------|
| Grupo FB | 0 | 0 | 0 |
| Instagram | 0 | 0 | 0 |
| Indicação / Vitor | 0 | 0 | 0 |

---

## 4. Métricas comerciais

| Métrica | Valor | Meta TASK-001 | Meta TASK-002 |
|---------|-------|---------------|---------------|
| Landing URL | [live](https://vitorolivjj.github.io/Laboratorio/) | 1 | — |
| Visitas landing | _não instrumentado_ | 100 (30d) | — |
| Cliques CTA WhatsApp | _não instrumentado_ | ≥ 5% | — |
| Conversas WhatsApp iniciadas | 0 | 10 (v0) | — |
| Vendas / PIX confirmados | 0 | 5 (30d) | — |
| Leads abordados (Caio) | 0 | — | 3 |
| Respostas Caio | 0 | — | _a medir_ |
| Taxa resposta abordagem | — | — | ≥ 33% (meta soft) |

### Taxa de conversão operacional

Fórmulas simples — atualizar quando houver volume:

| Funil | Fórmula | Valor atual |
|-------|---------|-------------|
| Lead → abordado | abordados / entregues_caio | — |
| Abordado → resposta | respostas / abordados | — |
| Resposta → convertido | convertidos / respostas | — |
| **Lead → convertido (end-to-end)** | convertidos / captados | — |
| Landing → clique WA | cliques / visitas | _sem analytics_ |

---

## 5. Métricas por agente

| Agente | TASK ativa | Última entrega | Próxima ação | Carga |
|--------|------------|----------------|--------------|-------|
| **Ronaldo Maestro** | 001, 002 | TASK-002 criada; audit E5 | Auditar TASK-002; E8 | média |
| **Donizete Social** | 002 | — | E2 — captar 3 leads | baixa |
| **Caio Manteiga** | 001, 002 | E3 TASK-001 | Handoff TASK-002; teste funil | média |
| **Dev** | 001 | E5 deploy | WA config (com Vitor) | baixa |
| **Juarez** | 001 | E4 checklist | Handoff 1ª venda | baixa |
| **Vitor** | 001, 002 | Gateway v0 WA | Número WA + E7 | decisão |

### Entregas por agente (2026-05-28)

| Agente | Entregas ✅ | Pendentes |
|--------|------------|-----------|
| Ronaldo | E1 (001), E1 (002), auditorias | E5 (002), E8 (001) |
| Dev | E2, E5 (001) | — |
| Caio | E3 (001) | E3–E4 (002) |
| Juarez | E4 (001) | — |
| Donizete | — | E2 (002) |
| Vitor | decisão gateway; TASK-005 LLM | E7 (001) |

### 5.1 Configuração LLM (TASK-006 v1 · atualizado TASK-007)

> Verificação: `cd backend && ./run.sh llm-config` · Decisão: [memoria/decisoes.md](../memoria/decisoes.md)

| Agente | Camada | Provider | Model | Status |
|--------|--------|----------|-------|--------|
| Ronaldo | Estratégica | openai | gpt-5 | ✅ v1 |
| Caio | Especialista | anthropic | claude-sonnet-4-6 | ✅ prod WA |
| Donizete | Especialista | anthropic | claude-sonnet-4-6 | ✅ v1.1 |
| Dev | Especialista | anthropic | claude-sonnet-4-6 | ✅ v1.1 |
| Juarez | Especialista | anthropic | claude-sonnet-4-6 | ✅ v1.1 |

**Princípio:** camada estratégica = padrão Ronaldo (OpenAI) · especialistas = Anthropic Sonnet.

**Fallback:** `DEFAULT_PROVIDER=anthropic` · `DEFAULT_MODEL=claude-sonnet-4-6`

**WhatsApp (TASK-007):** `https://api.laboratorioagentes.com.br/webhook/whatsapp` · VPS Hetzner

**Fase:** aprender · validar · medir · acumular histórico

---

## 6. SLA operacional

| Processo | SLA | Cumprimento | Responsável |
|----------|-----|-------------|-------------|
| Handoff Donizete → Caio | imediato (registro CRM) | — | Donizete |
| Primeira abordagem Caio | ≤ 4h úteis pós-handoff | — | Caio |
| Lead P1 quente | ≤ 2h úteis | — | Caio |
| Follow-up 1 | D+1 | — | Caio |
| Follow-up 2 | D+3 | — | Caio |
| Entrega pós-venda (TASK-001) | 5 dias úteis | — | Juarez/Dev |
| Auditoria pós-rodada | ≤ 24h após entregas | parcial | Ronaldo |

**SLA estourados (período atual):** 0 registrados

---

## 7. Gargalos atuais

| # | Gargalo | Impacto | Mitigação | Dono |
|---|---------|---------|-----------|------|
| G1 | WhatsApp placeholder na landing | CTA não converte de verdade | Vitor configura número | Vitor |
| G2 | Sem analytics na landing | Não mede visitas/cliques | v1: link curto ou contagem manual | Dev |
| G3 | TASK-002 aguarda Donizete | Funil orgânico parado | Iniciar captação grupos FB | Donizete |
| G4 | E7 TASK-001 (contatos Vitor) | Validação comercial lenta | Vitor indica 3 contatos ou Donizete suplementa | Vitor |
| G5 | Memória TASK-001 vs deploy | Doc parcialmente desatualizado | Ronaldo sync na próxima auditoria | Ronaldo |

---

## 8. Bloqueios

| TASK | Bloqueio | Severidade | Desde | Quem desbloqueia |
|------|----------|------------|-------|------------------|
| TASK-001 | WA número real (não crítico para URL) | baixa | 2026-05-28 | Vitor |
| TASK-002 | nenhum | — | — | — |

**Bloqueios críticos:** 0

---

## 9. Aprendizados recentes

> Detalhe: [memoria/aprendizados.md](../memoria/aprendizados.md)

| Data | Aprendizado (resumo) | Tags |
|------|----------------------|------|
| 2026-05-28 | Funil v0: separar checklist pré-fechamento e pós-pagamento | `#operacao` |
| 2026-05-28 | HTML v0 pode ir antes da copy final | `#dev` |
| 2026-05-28 | Memória separada evita ruído entre agentes | `#orquestracao` |
| 2026-05-28 | Deploy desacoplado do número WA | `#dev` |

---

## 10. Hipóteses em teste

> Detalhe: [memoria/hipoteses_testadas.md](../memoria/hipoteses_testadas.md)

| ID | Hipótese | TASK | Status | Próximo sinal |
|----|----------|------|--------|---------------|
| H-001 | R$ 49 converte > R$ 97 | TASK-001 | `a_testar` | 20 leads contactados |
| H-002 | HTML estático > MVP Next.js (velocidade) | TASK-001 | `a_testar` | deploy OK ✅ — falta tráfego |
| H-003 | Consolidação 2 etapas Ronaldo | PROJ-001 | `inconclusa` | 3 ciclos orquestrar |

---

## 11. Eventos recentes

> Detalhe: [logs/eventos.md](../logs/eventos.md)

| Data | Tipo | Evento |
|------|------|--------|
| 2026-05-30 | decisao | TASK-006 — arquitetura modelos v1 (Ronaldo gpt-5) |
| 2026-05-30 | deploy | TASK-005 E6 — LLM anthropic/sonnet por agente |
| 2026-05-28 | tarefa | TASK-002 criada |
| 2026-05-28 | deploy | Landing GitHub Pages live |
| 2026-05-28 | decisao | WA adiado — deploy desacoplado |
| 2026-05-28 | tarefa | TASK-001 Rodadas 2–5 |

---

## 12. Saúde do ecossistema

| Dimensão | Nota | Comentário |
|----------|------|------------|
| Clareza operacional | 🟢 | TASKs + workflow + CRM definidos |
| WIP | 🟢 | 2/3 — dentro do limite |
| Dados comerciais | 🔴 | Sem leads, sem analytics |
| Disciplina anti-spam | 🟢 | Regras documentadas |
| Aprendizado | 🟡 | Aprendizados registrados; hipóteses abertas |
| Automação deploy | 🟢 | GitHub Pages OK |

---

## 13. Como atualizar este dashboard

**Automático (seção 0):** GitHub Actions roda em push (`tasks/`, `crm/`) e diariamente (12:00 UTC). Atualiza apenas o bloco entre `AUTO-SNAPSHOT` markers.

**Manual (seções 1–12):** Ronaldo Maestro

**Quando:**
- Fim de rodada operacional
- Handoff Donizete → Caio
- Fechamento de entregável
- Evento em `logs/eventos.md`

**Checklist de atualização (5 min):**

1. [ ] Contar TASKs e entregáveis em `executando.md`
2. [ ] Copiar totais de `crm/leads.md`
3. [ ] Recalcular taxas de conversão (seção 4)
4. [ ] Atualizar gargalos e bloqueios
5. [ ] Puxar 3 aprendizados + hipóteses ativas
6. [ ] Atualizar **Última atualização** no topo

**Não fazer:** duplicar CRM ou TASK inteiras — linkar fontes canônicas.

---

## 14. Referências

| Recurso | Caminho |
|---------|---------|
| TASKs | [tasks/](../tasks/) |
| CRM leads | [crm/leads.md](../crm/leads.md) |
| Workflow captação | [docs/workflow-captacao-comercial.md](../docs/workflow-captacao-comercial.md) |
| Aprendizados | [memoria/aprendizados.md](../memoria/aprendizados.md) |
| Hipóteses | [memoria/hipoteses_testadas.md](../memoria/hipoteses_testadas.md) |
| Eventos | [logs/eventos.md](../logs/eventos.md) |
| Mapa agentes | [memoria/ronaldo_maestro/mapa_dos_agentes.md](../memoria/ronaldo_maestro/mapa_dos_agentes.md) |

---

**Versão:** 1.0 · **Criado:** 2026-05-28 · **Próxima revisão:** após primeiro lead TASK-002
