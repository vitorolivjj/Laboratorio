# TASK-001 — Landing low ticket para pintores autônomos

**ID:** TASK-001  
**Projeto:** PROJ-001 (Laboratório multiagente)  
**Status:** `arquivado` (cancelada — teste descartado 2026-05-31)  
**Prioridade:** alta  
**Criada em:** 2026-05-28  
**Cancelada em:** 2026-05-31  
**Atualizada em:** 2026-05-31

> Task persistente oficial · Modelo: [docs/modelo-task.md](../docs/modelo-task.md) · Ciclo de vida: [docs/ciclo-de-vida-tasks.md](../docs/ciclo-de-vida-tasks.md) · Runtime: [runtime/ronaldo_runtime.md](../runtime/ronaldo_runtime.md)

**Agente responsável:** ronaldo_maestro (coord.)  
**Agentes auxiliares:** juarez, dev, caio_manteiga  

---

## Objetivo

Validar o **primeiro fluxo comercial real** do sistema multiagente: da orquestração à oferta publicada, com métricas mínimas de conversão.

## Contexto

- Ecossistema operacional com Ronaldo Maestro, Juarez, Dev e Caio Manteiga.
- Orquestrações já executadas via `./run.sh orquestrar` (objetivo pintores).
- Histórico: [memoria/ronaldo_maestro/historico_de_orquestracao.md](../memoria/ronaldo_maestro/historico_de_orquestracao.md)
- Infra técnica: `backend/` (CrewAI), pastas `frontend/` e `agentes/` prontas para evolução.

## Problema

Pintores autônomos precisam de presença digital simples para captar clientes, mas:

- Não têm página nem processo claro de divulgação.
- Soluções existentes são caras ou complexas demais.
- O ecossistema ainda não provou ponta a ponta: **ideia → landing → venda**.

## Solução

1. **Landing page** minimalista (serviços, prova social leve, CTA, checkout ou link de pagamento).
2. **Oferta low ticket** com entrega padronizada (template + publicação assistida).
3. **Operação** enxuta: captação → pagamento → onboarding do cliente em até 48h.
4. **Coordenação** via TASK-001 como fonte única — agentes não recomeçam do zero a cada sessão.

## Público alvo

- **Quem:** pintores autônomos (PF), 1–3 pessoas, atuação local/regional.
- **Consciência:** sabe que precisa “aparecer online”, pouco tempo e orçamento limitado.
- **Canal principal:** WhatsApp + indicação; landing como destino do anúncio/link.

## Oferta inicial

| Item | Definição |
|------|-----------|
| **Produto** | Página de vendas simples (template + personalização básica) |
| **Preço sugerido** | R$ 49 (validar teste A/B com R$ 97 se necessário) |
| **Promessa** | “Sua página no ar em poucos dias — sem complicação” |
| **CTA v0** | **Somente WhatsApp** (validar interesse) |
| **CTA v1** | Mercado Pago (estrutura reservada — Dev) |
| **Entrega** | Página publicada + 1 rodada de ajuste |

_Copy e script WhatsApp: ver última orquestração (Caio Manteiga) no histórico._

## Responsáveis

| Agente | Papel nesta TASK |
|--------|------------------|
| **Ronaldo Maestro** | Orquestra, consolida, prioriza, registra ciclos |
| **Juarez** | Fluxo operacional, prazo de entrega, KPIs, gargalos |
| **Dev** | MVP da landing (stack simples, deploy, integração pagamento) |
| **Caio Manteiga** | Oferta, copy, CTA, funil WhatsApp, follow-up |
| **Vitor** | Decisão final (preço, escopo), validação com 1–3 pintores reais |

## KPIs

| KPI | Como medir | Meta inicial (30 dias) |
|-----|------------|-------------------------|
| Landing no ar | URL acessível | 1 página publicada |
| Tráfego | Visitas únicas | 100 visitas |
| Conversão | Cliques CTA / visitas | ≥ 5% |
| Vendas | Pagamentos confirmados | 5 vendas |
| Tempo de entrega | Pedido → página no ar | ≤ 5 dias úteis |
| CAC operacional | Custo tempo + ferramentas / venda | Documentar (meta: baixo) |

## Entregáveis

| # | Entregável | Dono | Status |
|---|------------|------|--------|
| E1 | Brief consolidado (esta TASK + última orquestração) | Ronaldo | ✅ |
| E2 | Wireframe / estrutura da landing (seções) | Dev | ✅ |
| E3 | Copy final (headline, bullets, CTA WhatsApp) | Caio | ✅ |
| E4 | Fluxo operacional de entrega (checklist) | Juarez | ✅ |
| E5 | Landing HTML v0 + deploy URL pública | Dev | ✅ |
| E6 | Link Mercado Pago (CTA secundário) | Dev | ⏸ v1 — após validação v0 |
| E7 | 3 contatos de pintores para teste | Vitor | ⬜ |
| E8 | 1 ciclo `orquestrar` pós-deploy com métricas | Ronaldo | ⬜ |

## Rodada operacional 1 — 2026-05-28

**Orquestrador:** Ronaldo Maestro · **Runtime:** [ronaldo_runtime.md](../runtime/ronaldo_runtime.md)  
**Status mantido:** `executando` (sem auditoria — não mover status)

### Plano de execução imediato (48h)

| Ordem | Ação | Agente | Entregável | Prazo |
|-------|------|--------|------------|-------|
| 1 | Estrutura da landing (5 seções, markdown/wireframe) | Dev | E2 | D+2 |
| 2 | Copy final v1 (R$ 49, CTA WhatsApp) | Caio | E3 | D+2 |
| 3 | Checklist entrega pós-pagamento (5 passos) | Juarez | E4 | D+2 |
| — | ~~Gateway~~ **Decidido:** v0 WhatsApp only | Vitor | ✅ |
| 4 | Montar HTML + publicar v0 | Dev | E5 | D+7 (após E2+E3) |

**Decisão registrada:** [memoria/decisoes.md](../memoria/decisoes.md) — escopo MVP R$ 49, HTML estático, CTA WhatsApp primário.

### Convergências (orquestrações anteriores)

- Oferta simples, low ticket, pintores autônomos
- Baixo custo, free tier, sem over-engineering
- Funil: mensagem → interesse → pagamento → entrega operacional

### Divergência decidida

| Conflito | Decisão Ronaldo |
|----------|-----------------|
| Preço R$ 49 vs R$ 97 | **R$ 49** na v1; teste H-001 depois com tráfego real |
| React vs HTML estático | **HTML estático** (H-002); velocidade > flexibilidade |

---

## Briefings (Ronaldo → agentes)

### Decisão Vitor — gateway v0 (2026-05-28)

- **v0:** somente WhatsApp — velocidade, baixa fricção, validar interesse/conversão
- **Dev:** `frontend/LANDING.md` criado — CTA MP reservado oculto para v1
- **Caio:** copy e CTA **apenas WhatsApp** na v0
- **E6 Mercado Pago:** adiado para v1 pós-validação

---

## Rodada operacional 2 — 2026-05-28

**Orquestrador:** Ronaldo Maestro  
**Objetivo:** `LANDING.md` → landing HTML funcional v0  
**Delegado:** Dev — `frontend/index.html` + `styles.css`

### Entregas Dev (E5 parcial)

| Item | Status |
|------|--------|
| `frontend/index.html` | ✅ 5 seções, CTA WhatsApp (2 posições) |
| `frontend/styles.css` | ✅ responsivo, system fonts, sem deps |
| Mercado Pago | ✅ comentado no HTML (v1) |
| Deploy URL pública | ⬜ pendente Vitor/Dev |
| Número WhatsApp real | ⬜ placeholder `5511999999999` |

### Briefing — Dev — Rodada 2

**Objetivo:** HTML v0 funcional localmente.  
**Restrições:** sem MP, sem analytics, sem framework.  
**Critério:** abrir no browser; cliques WA montam link `wa.me`.

### Próxima ação pós-rodada 2

| Agente | Ação |
|--------|------|
| **Vitor** | Configurar `WHATSAPP_NUMBER` em `index.html` + deploy (Vercel/Netlify) |
| **Caio** | E3 — refinar copy (headline/depoimento placeholder hoje) |
| **Juarez** | E4 — checklist pós-conversa WhatsApp |
| **Dev** | Deploy E5 após número WA confirmado |
| **Ronaldo** | Auditar E3+E4; validar URL pública |

---

### Briefing — Dev — TASK-001 — 2026-05-28 (atualizado)

**Objetivo desta rodada:** **E5 parcial concluído** — HTML v0 local; próximo: deploy + número WA real.

**Contexto mínimo:**
- v0: **só WhatsApp** — sem checkout visível
- Reservar bloco `#cta-pagamento` / `data-enabled="false"` para Mercado Pago v1

**Entregável E5 restante:** URL publicada; `WHATSAPP_NUMBER` configurado.

**Restrições:** HTML estático; free tier; sem SDK MP na v0.

**Critério de pronto E5:** URL publicada; clique WhatsApp funciona; seção MP no DOM mas inativa.

**Consultar:** [frontend/index.html](../frontend/index.html), [frontend/README.md](../frontend/README.md)

---

### Briefing — Caio Manteiga — TASK-001 — 2026-05-28 (atualizado)

**Objetivo desta rodada:** **E3** — copy v0 **WhatsApp only** (sem botão “pagar”).

**Contexto mínimo:** R$ 49; validação = cliques e respostas WhatsApp; funil: landing → WhatsApp → conversa → fechamento manual.

**Entregável:** Headline, bullets, texto botão WhatsApp, script pré-mensagem `wa.me`, follow-ups D+1/D+3.

**Não fazer:** CTA de pagamento online na copy v0.

---

### Briefing — Juarez — TASK-001 — 2026-05-28

**Objetivo desta rodada:** Entregar **E4** — checklist operacional pós-venda (5 passos numerados).

**Contexto mínimo:**
- Cliente pagou R$ 49 → recebe página em até 5 dias úteis
- Dev publica; Caio não opera entrega

**Entregável esperado:** Checklist em `memoria/memoria_operacional_juarez.md` (seção TASK-001) + resumo de 5 linhas nesta TASK (Registros Juarez).

**Restrições:**
- Processo manual aceito; sem sistema novo
- SLA: 5 dias úteis

**Critério de pronto:** Checklist com dono, prazo e KPI (% entregas no prazo).

**Não fazer:**
- Não definir stack técnica (Dev)
- Não reescrever copy (Caio)

**Consultar:** `memoria/memoria_operacional_juarez.md`

---

## Próxima ação por agente (pós-rodada 4)

| Agente | Próxima ação objetiva |
|--------|------------------------|
| **Vitor** | Publicar (GitHub Pages / Vercel / Netlify) + E7 contatos; WA quando quiser |
| **Dev** | Registrar URL em TASK-001 após deploy |
| **Caio Manteiga** | Testar funil com lead real pós-deploy |
| **Juarez** | Operar 1º handoff quando venda fechar |
| **Ronaldo** | Auditar E5 URL; preparar E8 |

---

## Rodada operacional 4 — 2026-05-28

**Orquestrador:** Ronaldo Maestro  
**Objetivo:** Desbloquear E5 — pipeline deploy sem depender do número WA  
**Decisão Vitor:** número WhatsApp **depois**; pode publicar landing com placeholder

### Entregas Dev

| Item | Status |
|------|--------|
| `.github/workflows/deploy-pages.yml` | ✅ GitHub Pages |
| `frontend/netlify.toml` | ✅ Netlify drop/CLI |
| `frontend/deploy.sh` | ✅ script unificado |
| `frontend/vercel.json` | ✅ (Rodada 3) |
| URL pública registrada | ⬜ Vitor executa deploy |

### Como publicar (escolha uma)

1. **GitHub Pages** — push `main` → Settings → Pages → Source: **GitHub Actions**
2. Workflow: `.github/workflows/deploy-pages.yml`

**WhatsApp:** editar `WHATSAPP_NUMBER` em `index.html` a qualquer momento (antes ou depois do deploy).

### Próxima ação pós-rodada 4

| Agente | Ação |
|--------|------|
| **Vitor** | Executar deploy + registrar URL; WA e E7 quando disponível |
| **Dev** | Atualizar TASK-001 com URL |
| **Caio** | Primeiro teste de funil após URL |
| **Ronaldo** | Fechar E5 na auditoria quando URL existir |

---

## Rodada operacional 5 — 2026-05-28

**Orquestrador:** Ronaldo Maestro · **Dev:** deploy GitHub Pages  
**Objetivo:** Publicar `frontend/` e validar URL pública

### Resultado

| Item | Status |
|------|--------|
| Push `main` (commit `25eaae3`) | ✅ |
| Workflow `deploy-pages.yml` | ✅ [Action #26605297208](https://github.com/vitorolivjj/Laboratorio/actions/runs/26605297208) |
| URL pública | ✅ **https://vitorolivjj.github.io/Laboratorio/** |
| HTTP 200 + conteúdo landing | ✅ validado |
| Número WhatsApp real | ⬜ placeholder (Vitor) |

### Próxima ação pós-deploy

| Agente | Ação |
|--------|------|
| **Vitor** | Configurar `WHATSAPP_NUMBER` + E7 contatos pintores |
| **Caio** | Testar funil com lead real |
| **Juarez** | Handoff na 1ª venda |
| **Ronaldo** | E8 — ciclo orquestrar pós-métricas |

---

## Rodada operacional 3 — 2026-05-28

**Orquestrador:** Ronaldo Maestro  
**Objetivo:** Fechar E3 (copy) + E4 (checklist v0) · preparar E5 deploy  
**Delegados:** Caio (E3) · Juarez (E4) · Dev (aplicar copy + `vercel.json`)

### Entregas

| Item | Agente | Status |
|------|--------|--------|
| Copy landing aplicada em `index.html` | Caio + Dev | ✅ |
| Scripts WA + follow-ups + objeções | Caio | ✅ → [memoria_comercial_caio.md](../memoria/memoria_comercial_caio.md) |
| Checklist pré-fechamento (5 passos) | Juarez | ✅ |
| Checklist pós-pagamento (5 passos) | Juarez | ✅ → [memoria_operacional_juarez.md](../memoria/memoria_operacional_juarez.md) |
| `vercel.json` deploy estático | Dev | ✅ |
| Deploy URL pública | Vitor | ⬜ pipeline pronto — executar deploy |
| 3 contatos pintores | Vitor | ⬜ E7 |

### Próxima ação pós-rodada 3

| Agente | Ação |
|--------|------|
| **Vitor** | `WHATSAPP_NUMBER` em `index.html` + deploy Vercel/Netlify + E7 contatos |
| **Dev** | Publicar URL; registrar em TASK-001 |
| **Caio** | Testar script com 1 lead real após deploy |
| **Juarez** | Validar handoff Caio → operação na 1ª venda |
| **Ronaldo** | Auditar E5 completo; rodada E8 pós-deploy |

---

## Prioridades

| # | Ação | Agente | Prazo |
|---|------|--------|-------|
| 1 | Fechar preço e escopo mínimo da página (1 template) | Vitor + Caio | 2 dias |
| 2 | Definir stack e pasta em `frontend/` (MVP) | Dev | 3 dias |
| 3 | Checklist operacional de entrega pós-venda | Juarez | 3 dias |
| 4 | Publicar landing v0 com CTA | Dev | 7 dias |
| 5 | Rodar script WhatsApp com 10 leads teste | Caio | 10 dias |

## Próximos passos (pós-rodada 1)

1. **Dev, Caio, Juarez:** executar briefings acima (48h).
2. **Vitor:** definir gateway ou validar v0 só WhatsApp.
3. **Ronaldo (D+2):** auditar E2–E4; consolidar; decidir se E5 entra na fila imediata.

~~Seção anterior substituída pela Rodada operacional 1.~~

---

## Status atual

| Campo | Valor |
|-------|-------|
| **Status** | `executando` |
| **Arquivo Kanban** | [executando.md](executando.md) |
| **Bloqueios** | Nenhum crítico — WA placeholder |
| **Rodada ativa** | Rodada 5 — deploy concluído |
| **URL pública** | https://vitorolivjj.github.io/Laboratorio/ |
| **Último ciclo orquestração** | 2026-05-28 — pintores autônomos |

---

## Registro de agentes (atualizar a cada sessão)

### Ronaldo Maestro
- **Última ação:** Rodada 5 — E5 deploy validado; URL registrada
- **Data:** 2026-05-28

### Juarez
- **Última ação:** E4 — checklists pré-fechamento + pós-pagamento
- **Próxima:** Operar handoff na 1ª venda
- **Data:** 2026-05-28

### Dev
- **Última ação:** Push + GitHub Pages live (`deploy-pages.yml`)
- **Próxima:** Atualizar WA quando Vitor informar número
- **Data:** 2026-05-28

### Caio Manteiga
- **Última ação:** E3 — copy landing + scripts WA + follow-ups
- **Próxima:** Testar funil com URL pública
- **Data:** 2026-05-28

---

## Copy reservada (Caio Manteiga)

**E3 aprovado — 2026-05-28.** Copy completa em [memoria_comercial_caio.md](../memoria/memoria_comercial_caio.md).

```
Headline: Sua página no ar em poucos dias — sem complicação
CTA: Quero minha página — falar no WhatsApp
WhatsApp pré-mensagem: Oi! Vi a página de R$49 pro pintor. Quero saber como funciona.
Primeira resposta: Oi! Tudo bem? Vi que você se interessou pela página de pintor por R$ 49...
Follow-up D+1: Oi! Vi que você olhou a página. Ficou alguma dúvida?
Follow-up D+3: A oferta de R$ 49 ainda tá valendo. Quer garantir sua página essa semana?
```

---

## Critérios de aceite

- [x] CTA WhatsApp funcional (estrutura — número placeholder)
- [x] Copy validada por Caio (E3 — aplicada no HTML)
- [x] Checklist entrega pós-fechamento WhatsApp (Juarez — E4)
- [x] Landing publicada (URL pública — E5)
- [ ] Número WhatsApp real configurado (Vitor — quando disponível)
- [ ] ≥ 5% cliques WhatsApp / visitas OU 10 conversas iniciadas (meta v0)
- [ ] _v1:_ Mercado Pago + 5 vendas online

---

## Auditoria do Ronaldo

### Auditoria operacional — Rodada 5 — 2026-05-28

| Campo | Valor |
|-------|-------|
| **Entregáveis** | E5 ✅ |
| **URL** | https://vitorolivjj.github.io/Laboratorio/ |
| **Action** | completed success — [run #26605297208](https://github.com/vitorolivjj/Laboratorio/actions/runs/26605297208) |
| **Critérios de aceite** | 4/7 parcial (WA real + métricas pendentes) |
| **Veredito** | **E5 aprovado** — landing no ar |

### Auditoria operacional — Rodada 4 — 2026-05-28

| Campo | Valor |
|-------|-------|
| **Entregáveis** | E5 🔄 (pipeline ✅, URL ⬜) |
| **Decisão Vitor** | WA adiado — deploy não bloqueado |
| **Qualidade** | 3 opções deploy ✅ · zero deps ✅ |
| **Veredito** | **Pipeline aprovado** — E5 fecha com URL |

### Auditoria operacional — Rodada 3 — 2026-05-28

| Campo | Valor |
|-------|-------|
| **Entregáveis** | E3 ✅ · E4 ✅ · E5 🔄 (deploy ⬜) |
| **Critérios de aceite** | 3/6 parcial |
| **Convergências** | Copy Caio no HTML; dois fluxos Juarez (pré + pós); vercel.json pronto |
| **Divergências → decisão** | Deploy bloqueado por número WA — Vitor desbloqueia E5 |
| **Qualidade** | copy humana ✅ · operação aplicável ✅ · deploy pendente |
| **Veredito** | **E3+E4 aprovados** · E5 aguarda Vitor |

### Registros gerados (Rodada 3)
- [x] memoria_comercial_caio.md — E3 completo
- [x] memoria_operacional_juarez.md — E4 completo
- [x] aprendizados.md — funil v0 em dois checklists

### Auditoria técnica — Rodada 2 — 2026-05-28

| Campo | Valor |
|-------|-------|
| **Entregáveis** | E2 ✅ · E5 🔄 (HTML ✅, deploy ⬜) |
| **Critérios de aceite** | 1/5 parcial |
| **Convergências** | HTML estático; 5 seções; WA only; MP comentado |
| **Divergências → decisão** | Copy E3 atrasada → Dev usou placeholder alinhado ao wireframe; Caio refina depois |
| **Qualidade** | simples ✅ · aplicável ✅ · baixo custo ✅ · deploy pendente |
| **Veredito técnico** | **E5 parcial aprovado** — falta deploy + número WA + copy Caio |

### Registros gerados
- [x] aprendizados.md — HTML estático v0
- [ ] decisoes.md — N/A nesta rodada
- [x] hipoteses_testadas.md — H-002 parcial (HTML estático entregue)

### Auditoria final (TASK concluída)

| Campo | Valor |
|-------|-------|
| **Data auditoria final** | — |
| **Veredito final** | em andamento |

---

## Histórico desta TASK

| Data | De → Para | Evento |
|------|-----------|--------|
| 2026-05-31 | executando → arquivado | **Cancelada** — teste pintores/leads descartado pelo Vitor |
| 2026-05-28 | — → backlog | TASK-001 criada |
| 2026-05-28 | — | E5 ✅ — landing publicada GitHub Pages |
| 2026-05-28 | — | Rodada 4 — pipeline deploy; WA adiado por Vitor |
| 2026-05-28 | — | Rodada 3 — E3 copy + E4 checklist; E5 deploy pendente |
| 2026-05-28 | — | Rodada 2 — HTML v0 entregue (Dev); auditoria técnica E5 parcial |
| 2026-05-28 | — | Decisão Vitor: gateway v0 somente WhatsApp |
| 2026-05-28 | — | Rodada operacional 1 — plano + briefings (Ronaldo) |
| 2026-05-28 | backlog → executando | Primeira orquestração multiagente |
