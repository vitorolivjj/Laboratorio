# Dashboard — Métricas operacionais

Visão centralizada da operação do Laboratório multiagente.

**Dono:** Ronaldo Maestro · **Atualização:** manual + automática (GitHub Actions) · **Frequência:** rodada ou diária

> Fontes: `tasks/` · `crm/leads.md` · `memoria/aprendizados.md` · `memoria/hipoteses_testadas.md` · `logs/eventos.md`  
> Snapshot: `scripts/update_dashboard_snapshot.py` · `.github/workflows/update-dashboard.yml`

**Última atualização manual:** 2026-05-30 (TASK-006 — arquitetura modelos v1)  
**Última atualização automática:** 2026-05-31 (GitHub Actions)

---

## 0. Snapshot automático

<!-- AUTO-SNAPSHOT:START -->
> **Snapshot automático** · gerado em **2026-05-31 02:06 UTC** · script `scripts/update_dashboard_snapshot.py`

### Resumo

| Indicador | Valor |
|-----------|-------|
| TASKs em execução (WIP) | 1 / 3 |
| Entregáveis (TASKs `executando`) | 10 / 18 |
| Total leads CRM | 0 |
| Hipóteses `a_testar` | 2 |
| Taxa lead → convertido | — |
| Taxa entregue → abordado | — |

### Pipeline Kanban

| Status | Qtd | TASKs |
|--------|-----|-------|
| `executando` | 1 | TASK-001 |
| `planejando` | 0 | — |
| `aguardando` | 0 | — |
| `backlog` | 1 | TASK-004 |
| `concluído` (kanban) | 6 | TASK-008, TASK-007, TASK-006, TASK-005, TASK-003, TASK-000 |

### TASKs (arquivos persistentes)

| TASK | Status | Entregáveis | Progresso |
|------|--------|-------------|-----------|
| [TASK-001](../tasks/TASK-001.md) | `executando` | 5/8 | 62% |
| [TASK-002](../tasks/TASK-002.md) | `executando` | 1/5 | 20% |
| [TASK-003](../tasks/TASK-003.md) | `executando` | 4/5 | 80% |
| [TASK-005-relatorio-modelos](../tasks/TASK-005-relatorio-modelos.md) | `desconhecido` | 0/0 | — |
| [TASK-005](../tasks/TASK-005.md) | `concluido` | 6/6 | 100% |
| [TASK-006](../tasks/TASK-006.md) | `concluido` | 6/6 | 100% |
| [TASK-007](../tasks/TASK-007.md) | `concluido` | 7/7 | 100% |
| [TASK-008](../tasks/TASK-008.md) | `concluido` | 5/5 | 100% |

### Funil CRM

| Status | Qtd |
|--------|-----|
| `novo` | 0 |
| `qualificado` | 0 |
| `entregue_caio` | 0 |
| `abordado` | 0 |
| `convertido` | 0 |
| `sem_resposta` | 0 |
| `descartado` | 0 |
| **Total** | **0** |

### Leads (índice)

| ID | Nome | Score | Status |
|----|------|-------|--------|
| _—_ | _nenhum lead_ | — | — |

<!-- AUTO-SNAPSHOT:END -->

---

## 1. Resumo executivo (leitura 30s)

| Indicador | Valor | Status |
|-----------|-------|--------|
| TASKs em execução | 2 / 3 WIP | 🟢 |
| Entregáveis concluídos (TASKs ativas) | 6 / 13 | 🟡 |
| Leads no CRM | 0 | ⚪ |
| Landing no ar | ✅ | 🟢 |
| Bloqueios críticos | 0 | 🟢 |
| Automação LLM por agente | ✅ TASK-006 v1 | 🟢 |
| Hipóteses em teste | 2 | 🟡 |
| Taxa conversão operacional | — (sem leads) | ⚪ |

**Foco imediato:** TASK-002 captação (Donizete) · TASK-001 WA real + teste funil (Vitor/Caio)

---

## 2. Métricas de TASKs

### 2.1 Pipeline Kanban

| Status | Qtd | TASKs |
|--------|-----|-------|
| `executando` | 2 | TASK-001, TASK-002 |
| `planejando` | 0 | — |
| `aguardando` | 0 | — |
| `backlog` | 1+ | TASK-004 |
| `concluído` | 0 | — |

**WIP:** 2/3 · **Capacidade livre:** 1 slot

### 2.2 TASKs ativas — detalhe

| TASK | Rodada | Entregáveis | Progresso | Bloqueio |
|------|--------|-------------|-----------|----------|
| [TASK-001](../tasks/TASK-001.md) | 5 | E1–E5 ✅ · E7–E8 ⬜ | 63% (5/8) | WA placeholder |
| [TASK-002](../tasks/TASK-002.md) | 1 | E1 ✅ · E2–E5 ⬜ | 20% (1/5) | nenhum |

### 2.3 Throughput de execução

| Métrica | Período | Valor |
|---------|---------|-------|
| Rodadas operacionais concluídas | TASK-001 | 5 |
| Rodadas operacionais concluídas | TASK-002 | 0 (Rodada 1 em curso) |
| Entregáveis fechados | 2026-05-28 | 6 |
| Deploys | 2026-05-28 | 1 (GitHub Pages) |
| TASKs criadas | 2026-05-28 | 2 |
| Tempo médio rodada | — | _a medir_ |

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

**Total leads:** 0 · **Meta TASK-002:** 3

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
