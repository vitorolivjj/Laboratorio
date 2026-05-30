# Eventos (log operacional)

Linha do tempo de **acontecimentos** do ecossistema: orquestrações, deploys, decisões rápidas, falhas, marcos.

Não substitui `tasks/` (tarefas) nem `memoria/decisoes.md` (decisões formais).

## Como usar

- Entrada cronológica: **mais recente no topo**.
- Uma linha ou bloco curto por evento.
- Ronaldo pode registrar ciclos longos em `memoria/ronaldo_maestro/historico_de_orquestracao.md` e deixar resumo aqui.

## Template

```markdown
### YYYY-MM-DD HH:MM — [Tipo] Título
- **Agente(s):**
- **Detalhe:**
- **Ref:** TASK-XXX | PROJ-XXX (opcional)
```

**Tipos sugeridos:** `orquestracao` | `deploy` | `decisao` | `erro` | `marco` | `tarefa`

---

## Log

### 2026-05-30 — [decisao] TASK-006 — Arquitetura oficial modelos v1
- **Agente(s):** ronaldo_maestro, vitor
- **Detalhe:** Ronaldo openai/gpt-5 · especialistas anthropic/sonnet · `./run.sh llm-config` validado
- **Ref:** TASK-006, memoria/decisoes.md

### 2026-05-30 — [deploy] TASK-005 E6 — roteamento LLM por agente
- **Agente(s):** dev, ronaldo_maestro
- **Detalhe:** builder.py + llm_config.py · todos anthropic/sonnet · `./run.sh llm-config` · decisão memoria/decisoes.md
- **Ref:** TASK-005

### 2026-05-30 — [orquestracao] TASK-005 — relatório modelos entregue
- **Agente(s):** ronaldo_maestro
- **Detalhe:** E1–E4 concluídos · recomenda anthropic/sonnet · Dev+Ronaldo alterar · Caio/Juarez manter · `*_PROVIDER` não wired no backend
- **Ref:** TASK-005, TASK-005-relatorio-modelos.md

### 2026-05-30 — [tarefa] TASK-005 criada — Revisão Estratégica dos Modelos
- **Agente(s):** ronaldo_maestro
- **Detalhe:** Vitor solicita análise crítica de providers por agente · relatório E1–E4 · `.env` bloqueado até aprovação
- **Ref:** TASK-005, backend/.env

### 2026-05-28 — [tarefa] TASK-003 criada — automação snapshot dashboard
- **Agente(s):** Ronaldo Maestro, Dev, Juarez
- **Detalhe:** script stdlib + workflow GitHub Actions; snapshot seção 0
- **Ref:** TASK-003

### 2026-05-28 — [marco] Dashboard operacional criado
- **Agente(s):** Ronaldo Maestro
- **Detalhe:** dashboard/metricas_operacionais.md — visão TASKs, leads, SLA, gargalos
- **Ref:** PROJ-001

### 2026-05-28 — [tarefa] TASK-002 criada — validação captação orgânica
- **Agente(s):** Ronaldo Maestro
- **Detalhe:** Fluxo Donizete → CRM → Caio → feedback; máx. 3 leads pintores Grande SP
- **Ref:** TASK-002, docs/workflow-captacao-comercial.md

### 2026-05-28 — [deploy] TASK-001 landing publicada — GitHub Pages
- **Agente(s):** Dev, Ronaldo Maestro
- **Detalhe:** Push main → Action `deploy-pages.yml` success; URL https://vitorolivjj.github.io/Laboratorio/ · E5 ✅
- **Ref:** TASK-001 · [Action run](https://github.com/vitorolivjj/Laboratorio/actions/runs/26605297208)

### 2026-05-28 — [decisao] TASK-001 WA adiado — deploy desacoplado
- **Agente(s):** Vitor, Ronaldo Maestro
- **Detalhe:** Landing pode publicar com placeholder; número WA entra depois
- **Ref:** TASK-001, memoria/decisoes.md

### 2026-05-28 — [tarefa] TASK-001 Rodada 4 — pipeline deploy
- **Agente(s):** Ronaldo Maestro, Dev
- **Detalhe:** GitHub Actions Pages, netlify.toml, deploy.sh; URL pendente execução Vitor
- **Ref:** TASK-001

### 2026-05-28 — [tarefa] TASK-001 Rodada 3 — E3 + E4
- **Agente(s):** Ronaldo Maestro, Caio Manteiga, Juarez, Dev
- **Detalhe:** Copy aplicada no HTML; checklists pré/pós-fechamento; vercel.json; deploy pendente
- **Ref:** TASK-001

### 2026-05-28 — [tarefa] TASK-001 Rodada 2 — HTML v0
- **Agente(s):** Ronaldo Maestro, Dev
- **Detalhe:** frontend/index.html + styles.css; CTA WhatsApp; MP comentado; E5 parcial — deploy pendente
- **Ref:** TASK-001

### 2026-05-28 — [decisao] TASK-001 gateway v0 WhatsApp only
- **Agente(s):** Vitor, Ronaldo Maestro
- **Detalhe:** v0 sem checkout; validar interesse/conversão; Dev reserva Mercado Pago em frontend/LANDING.md para v1
- **Ref:** TASK-001

### 2026-05-28 — [tarefa] TASK-001 Rodada operacional 1
- **Agente(s):** Ronaldo Maestro
- **Detalhe:** Plano 48h; briefings Dev (E2), Caio (E3), Juarez (E4); decisão MVP R$ 49 HTML estático em decisoes.md; status mantido executando
- **Ref:** TASK-001

### 2026-05-28 16:50 — [orquestracao] Ciclo multiagente
- **Agente(s):** Ronaldo Maestro, Juarez, Dev, Caio Manteiga
- **Detalhe:** Objetivo: Criar uma oferta low ticket de página simples para pintores autônomos. | Resumo: ```
## 1. Objetivo identificado
Criar uma oferta low ticket de página simples para pintores autônomos, visando facilitar a captação de clientes.

## 2. Agentes envolvidos
- Juarez (Operação) - para definir e otimizar processos operacionais relacionados à oferta.
- Dev (Desenvolvimento) - para criar a parte técnica da página de vendas.
- Caio Manteiga (Comercial) - para estruturar a comunicação de …
- **Ref:** PROJ-001

### 2026-05-28 16:33 — [orquestracao] Ciclo multiagente
- **Agente(s):** Ronaldo Maestro, Juarez, Dev, Caio Manteiga
- **Detalhe:** Objetivo: Criar uma oferta low ticket de página simples para pintores autônomos. | Resumo: ```
## 1. Objetivo identificado
Criar uma oferta low ticket de página simples para pintores autônomos.

## 2. Agentes envolvidos
- Juarez (primeiro, para revisar a operação e logística da oferta)
- Dev (depois, para a parte técnica e desenvolvimento da página)
- Caio Manteiga (por último, para elaborar a estratégia de vendas e follow-up)

## 3. Plano de execução
1. Juarez analisará a viabilidade o…
- **Ref:** PROJ-001

### 2026-05-28 — [marco] Infra operacional multiagente

- **Agente(s):** Dev
- **Detalhe:** Criadas pastas memoria (compartilhada), contexto, tasks, logs, workflows.
- **Ref:** PROJ-001

### 2026-05-28 — [marco] Agentes e memória estratégica

- **Agente(s):** Dev
- **Detalhe:** Juarez, Dev, Caio Manteiga, Ronaldo Maestro + `memoria/ronaldo_maestro/`.
- **Ref:** PROJ-001

---

<!-- Novos eventos acima desta linha -->
