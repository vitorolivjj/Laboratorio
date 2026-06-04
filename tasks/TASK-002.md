# TASK-002 — Validação captação orgânica Donizete → Caio

**ID:** TASK-002  
**Projeto:** PROJ-001 (Laboratório multiagente)  
**Status:** `arquivado` (cancelada) (cancelada — teste descartado 2026-05-31)  
**Prioridade:** alta  
**Criada em:** 2026-05-28  
**Cancelada em:** 2026-05-31  
**Atualizada em:** 2026-05-31

> Task persistente · Modelo: [docs/modelo-task.md](../docs/modelo-task.md) · Workflow: [docs/workflow-captacao-comercial.md](../docs/workflow-captacao-comercial.md) · CRM: [crm/leads.md](../crm/leads.md)

**Agente responsável:** ronaldo_maestro (coord.)  
**Agentes auxiliares:** donizete_social, caio_manteiga  

---

## Objetivo

Validar o **fluxo operacional orgânico controlado** ponta a ponta:

**Donizete → CRM → Caio → feedback → aprendizado**

Critério de sucesso: o mecanismo funcionar do início ao fim **sem caos**.

## Contexto

- TASK-001 entregou landing e oferta (R$ 49, pintores autônomos).
- Donizete Social e workflow comercial criados ([workflow-captacao-comercial.md](../docs/workflow-captacao-comercial.md)).
- Esta TASK **não escala volume** — prova o processo com **máximo 3 leads**.
- Complementa TASK-001 (E7 contatos) via captação orgânica discreta.

## Escopo

| Item | Definição |
|------|-----------|
| **Volume máximo** | 3 leads qualificados |
| **ICP** | Pintores autônomos (PF), 1–3 pessoas |
| **Região inicial** | Grande SP (capital + ABC) — ajustável pelo Vitor |
| **Canais** | Grupos Facebook compra/venda e serviços |
| **Modo** | Captação discreta, humana, sem spam |
| **Proibido** | Automação agressiva, flood, DMs em massa |
| **Oferta de referência** | Página R$ 49 — TASK-001 · URL: https://vitorolivjj.github.io/Laboratorio/ |

## Responsáveis

| Agente | Papel nesta TASK |
|--------|------------------|
| **Ronaldo Maestro** | Briefings, auditoria, gargalos, memória compartilhada |
| **Donizete Social** | Captura, qualificação, CRM, handoff Caio |
| **Caio Manteiga** | Abordagem humana, registro resultado, feedback |
| **Vitor** | Validar região/grupos se necessário; não bloqueia início |

## KPIs (validação)

| KPI | Meta |
|-----|------|
| Leads qualificados no CRM | 3 (máx.) |
| Leads com score + temperatura + tags | 100% |
| Handoff Donizete → Caio formalizado | 100% |
| Abordagem Caio dentro do SLA (4h úteis) | ≥ 2 de 3 |
| Feedback Caio registrado | 1 resumo mínimo |
| Auditoria Ronaldo concluída | 1 |
| Violações anti-spam | 0 |

## Entregáveis

| # | Entregável | Dono | Status |
|---|------------|------|--------|
| E1 | Brief + escopo desta TASK | Ronaldo | ✅ |
| E2 | Até 3 leads no CRM (score, temp, tags, contexto) | Donizete | ⬜ |
| E3 | Abordagem + resposta + objeções + resultado (3 leads) | Caio | ⬜ |
| E4 | Feedback comercial para Ronaldo | Caio | ⬜ |
| E5 | Auditoria + aprendizados em memória compartilhada | Ronaldo | ⬜ |

## Rodada operacional 1 — 2026-05-28

**Orquestrador:** Ronaldo Maestro  
**Status:** `executando`

### Plano de execução

| Ordem | Ação | Agente | Entregável |
|-------|------|--------|------------|
| 1 | Captar e qualificar até 3 leads | Donizete | E2 |
| 2 | Handoff no CRM + evento log | Donizete | E2 |
| 3 | Abordar leads (SLA 4h úteis) | Caio | E3 |
| 4 | Feedback comercial | Caio | E4 |
| 5 | Auditar fluxo + registrar aprendizados | Ronaldo | E5 |

---

## Briefings (Ronaldo → agentes)

### Briefing — Donizete Social — TASK-002

**Objetivo desta rodada:** Entregar **E2** — até **3 leads qualificados** no CRM.

**ICP:**
- Pintor autônomo, atuação local (Grande SP)
- Sinais: pede indicação, reclama de clientes, sem presença online, posta serviços

**Onde captar:**
- Grupos Facebook de **compra e venda** e **serviços** (região SP/ABC)
- Monitoramento passivo — **não comentar em massa, não DM em massa**

**Entregável por lead em `crm/leads.md`:**
- ID, nome, cidade, serviço, contato público, origem detalhada
- **Score** (0–5, mín. 3 para handoff)
- **Temperatura** (frio | morno | quente)
- **Tags** (ex.: `#pintor` `#autonomo` `#grupo-fb` `#sem-site`)
- **Observações:** contexto + gancho para Caio
- Status: `entregue_caio` · TASK: `TASK-002`

**Restrições:**
- Máx. **3 leads** nesta TASK (total, não por dia)
- Máx. **1 lead qualificado/hora**
- Só dados públicos
- Seguir [workflow-captacao-comercial.md](../docs/workflow-captacao-comercial.md)

**Critério de pronto E2:** 3 leads no CRM com handoff completo OU prazo acordado com 1–3 leads + motivo se < 3.

**Não fazer:** spam, flood, abordagem comercial, automação follow/unfollow.

---

### Briefing — Caio Manteiga — TASK-002

**Objetivo desta rodada:** Entregar **E3 + E4** — abordar leads handoff Donizete e registrar feedback.

**Entrada:** leads com status `entregue_caio` em `crm/leads.md` (TASK-002).

**Por lead, registrar no CRM:**
- Data/hora abordagem
- Mensagem enviada (resumo)
- **Resposta** (sim/não/parcial)
- **Objeções** levantadas
- **Resultado:** convertido | em_conversa | sem_resposta | descartado
- Atualizar status comercial

**Abordagem:**
- Humana, personalizada com contexto Donizete
- Oferta TASK-001: página R$ 49 · link landing se couber
- SLA: **≤ 4h úteis** após handoff (P1 quente: ≤ 2h)
- Follow-up: D+1, D+3 — máx. 3 toques ([workflow](../docs/workflow-captacao-comercial.md))

**Feedback E4 (template):**
```markdown
## Feedback TASK-002 — [data]
- Leads recebidos: N
- Abordados no SLA: N
- Respostas: N
- Objeções comuns: ...
- Qualidade contexto Donizete: alta | média | baixa
- Ajuste sugerido ICP/origem: ...
```

**Não fazer:** blast, copy idêntica em massa, pressão agressiva.

---

### Briefing — Ronaldo Maestro — TASK-002 (auto)

**Objetivo:** Auditar **E5** quando E2–E4 concluídos ou parcialmente.

**Auditar:**
- Fluxo CRM sem lacunas
- Limites anti-spam respeitados
- SLA Caio
- Qualidade handoff Donizete → Caio
- Gargalos (origem, ICP, script, timing)

**Registrar em:**
- `memoria/aprendizados.md` (tag `#captacao`)
- `memoria/hipoteses_testadas.md` se aplicável
- Seção Auditoria desta TASK

---

## Critérios de aceite

- [ ] Até 3 leads registrados no CRM com origem e contexto
- [ ] 100% dos leads handoff com score ≥ 3, temperatura e tags
- [ ] Caio abordou todos os leads handoff (ou registrou motivo de não abordar)
- [ ] Resposta, objeções e resultado documentados por lead
- [ ] Feedback Caio entregue ao Ronaldo
- [ ] Auditoria Ronaldo concluída — veredito sem caos operacional
- [ ] Zero violações anti-spam
- [ ] Aprendizado registrado em memória compartilhada

---

## Status atual

| Campo | Valor |
|-------|-------|
| **Status** | arquivado (cancelada) |
| **Arquivo Kanban** | [executando.md](executando.md) |
| **Bloqueios** | Nenhum |
| **Rodada ativa** | Rodada 1 — captação + abordagem |
| **Leads capturados** | 0 / 3 |
| **TASK relacionada** | [TASK-001](TASK-001.md) |

---

## Registro de agentes

### Ronaldo Maestro
- **Última ação:** TASK-002 criada; briefings Donizete + Caio
- **Próxima:** Auditar E2–E4; registrar E5
- **Data:** 2026-05-28

### Donizete Social
- **Última ação:** _Aguardando execução briefing_
- **Próxima:** E2 — captar até 3 leads no CRM
- **Data:** —

### Caio Manteiga
- **Última ação:** _Aguardando handoff Donizete_
- **Próxima:** E3 — abordagem humana + E4 feedback
- **Data:** —

---

## Auditoria do Ronaldo

_Preencher ao concluir E5._

| Campo | Valor |
|-------|-------|
| **Data auditoria** | — |
| **Entregáveis** | E1 ✅ · E2 ⬜ · E3 ⬜ · E4 ⬜ · E5 ⬜ |
| **Critérios de aceite** | pendente |
| **Gargalos identificados** | — |
| **Veredito** | em andamento |

### Notas da auditoria

—

---

## Histórico desta TASK

| Data | De → Para | Evento |
|------|-----------|--------|
| 2026-05-31 | executando → arquivado | **Cancelada** — teste captação pintores descartado pelo Vitor |
| 2026-05-28 | — → executando | TASK-002 criada — validação captação orgânica |
| 2026-05-28 | — | Rodada 1 — briefings Donizete + Caio |

---

## Próximos passos

1. **Donizete:** iniciar monitoramento grupos FB Grande SP → registrar leads no CRM.
2. **Caio:** aguardar handoff; abordar dentro do SLA.
3. **Ronaldo:** auditar ao receber E4.
