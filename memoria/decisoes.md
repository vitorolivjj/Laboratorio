# Decisões (memória compartilhada)

Registro de **decisões** visíveis a **todos os agentes**.

> Arquitetura completa: [docs/arquitetura-agentes.md](../docs/arquitetura-agentes.md)  
> Decisões **estratégicas de longo prazo** (Ronaldo): também `memoria/ronaldo_maestro/decisoes_criticas.md`  
> Memória de domínio por agente: `memoria_*_<agente>.md` — não duplicar aqui salvo impacto global

## Como usar

1. Uma entrada por decisão relevante.
2. Das mais recentes para as mais antigas.
3. Se afetar prioridade global, o Ronaldo deve espelhar ou referenciar em `decisoes_criticas.md`.

## Template

```markdown
### [Título] — YYYY-MM-DD
- **Contexto:**
- **Decisão:**
- **Responsável:** Vitor | agente
- **Agentes impactados:**
- **Validade / revisar em:**
```

---

## Decisões

### TASK-007 — Migração modelo Anthropic + WhatsApp em produção — 2026-05-31

- **Contexto:** TASK-007 em produção na VPS Hetzner; API Anthropic retornou `not_found` para `claude-sonnet-4-20250514` (snapshot descontinuado).
- **Decisão:**
  - **Especialistas (Caio, Juarez, Dev, Donizete):** migrar para `anthropic` / **`claude-sonnet-4-6`**.
  - **Ronaldo Maestro:** mantém `openai` / `gpt-5`.
  - **WhatsApp produção:** `https://api.laboratorioagentes.com.br/webhook/whatsapp` · VPS CPX21 · systemd `laboratorio-api`.
  - Atualizar `.env`, `.env.example`, `llm_config.py` DEFAULT_MODEL e docs operacionais.
- **Responsável:** Dev · Vitor (validação teste real)
- **Agentes impactados:** Caio (crítico — WhatsApp), demais especialistas
- **Validade / revisar em:** Quando Anthropic deprecar `claude-sonnet-4-6` ou nova evidência por agente

### TASK-006 — Arquitetura oficial de modelos v1 — 2026-05-30

- **Contexto:** TASK-005 implementou roteamento LLM; Vitor aprovou ajuste final antes dos testes operacionais reais.
- **Decisão:**
  - **Princípio:** camada estratégica do Grupo = padrão **Ronaldo** (OpenAI); especialistas = modelos distintos conforme função e evidência.
  - **Ronaldo Maestro:** `openai` / `gpt-5` — estratégia, coordenação, priorização, governança.
  - **Caio, Juarez, Dev, Donizete:** `anthropic` / `claude-sonnet-4-20250514` _(especialistas migrados para `claude-sonnet-4-6` em 2026-05-31 — ver decisão TASK-007 abaixo)_.
  - Fase atual: aprender, validar, medir, acumular histórico — não otimizar custo.
  - Verificação: `./run.sh llm-config`.
- **Responsável:** Vitor (aprovação) · Ronaldo Maestro (consolidação) · Dev (E6 TASK-005)
- **Agentes impactados:** Todos
- **Validade / revisar em:** Após ciclo de testes operacionais reais ou nova evidência por agente

### TASK-005 — Modelos LLM por agente (Anthropic Sonnet) — 2026-05-30

- **Contexto:** Relatório TASK-005 aprovado pelo Vitor; `*_PROVIDER` no `.env` não eram lidos pelo backend.
- **Decisão:**
  - Todos os agentes passam a usar **anthropic / claude-sonnet-4-20250514** _(supersedido parcialmente por TASK-006 — Ronaldo passa a OpenAI gpt-5)_.
  - Implementar roteamento em `backend/src/laboratorio/agents/llm_config.py` + `builder.py`.
  - Fallback: `DEFAULT_PROVIDER` + `DEFAULT_MODEL` quando variável específica ausente.
  - Comando de verificação: `./run.sh llm-config`.
  - Caio e Juarez: mantidos em Anthropic (já performavam bem).
  - Dev e Ronaldo: migrados de OpenAI para Anthropic.
  - Donizete: provider definido pela primeira vez.
- **Responsável:** Vitor (aprovação) · Dev (E6)
- **Agentes impactados:** Todos
- **Validade / revisar em:** Após checklist validação §4.3 TASK-005-relatorio-modelos.md

### TASK-001 — número WA adiado; deploy desacoplado — 2026-05-28

- **Contexto:** Vitor autorizou prosseguir sem configurar WhatsApp agora.
- **Decisão:**
  - Publicar landing **antes** do número real (placeholder mantido).
  - Número WA entra quando Vitor disponibilizar — editar `index.html` e redeploy.
  - E5 fecha com **URL pública**, não com WA configurado.
- **Responsável:** Vitor
- **Agentes impactados:** Dev, Caio Manteiga
- **Validade / revisar em:** Antes de tráfego real (E7)

### TASK-001 Gateway v0 — somente WhatsApp — 2026-05-28

- **Contexto:** Vitor respondeu escalonamento da Rodada 1; objetivo v0 é velocidade, baixa fricção, validar interesse/conversão.
- **Decisão:**
  - **v0:** único CTA ativo = **WhatsApp** (sem checkout na landing).
  - **v1 (futuro):** CTA secundário **Mercado Pago** — Dev reserva estrutura em `frontend/LANDING.md`, oculta na v0.
  - KPI v0: cliques e respostas WhatsApp; pagamentos online ficam para após validação de interesse.
- **Responsável:** Vitor
- **Agentes impactados:** Dev, Caio Manteiga, Juarez
- **Validade / revisar em:** Após 100 visitas ou 20 conversas WhatsApp (H-001)

### TASK-001 Rodada 1 — escopo MVP fechado — 2026-05-28

- **Contexto:** TASK-001 em `executando`; bloqueio parcial (gateway pagamento); necessidade de plano imediato sem código ainda.
- **Decisão:**
  - Preço **R$ 49** na v1 (H-001 permanece `a_testar` com 20 leads).
  - Landing **HTML estático** em `frontend/` — uma página, sem login, sem CMS.
  - **CTA primário:** WhatsApp; **CTA secundário:** adiado — Mercado Pago na v1 (placeholder Dev).
  - Escopo fixo: 5 seções (hero, serviços, prova social leve, preço, CTA).
  - Execução **paralela** 48h: Dev → E2 | Caio → E3 | Juarez → E4.
- **Responsável:** Ronaldo Maestro (coord.) — confirmação gateway: Vitor
- **Agentes impactados:** Dev, Caio Manteiga, Juarez, Vitor
- **Validade / revisar em:** Após entregas E2–E4 ou decisão de gateway (2026-05-30)

### Sistema de memória multiagente — 2026-05-28

- **Contexto:** Necessidade de camadas de memória por agente com auditoria do Ronaldo.
- **Decisão:** Arquivos `memoria_*_<agente>.md` + compartilhados (`decisoes`, `aprendizados`, `hipoteses_testadas`).
- **Responsável:** Dev
- **Agentes impactados:** Todos
- **Validade / revisar em:** Após TASK-001

### Estrutura operacional do ecossistema — 2026-05-28

- **Contexto:** Necessidade de memória, contexto, tarefas e workflows compartilhados.
- **Decisão:** Pastas `memoria/`, `contexto/`, `tasks/`, `logs/`, `workflows/` na raiz do repositório.
- **Responsável:** Dev
- **Agentes impactados:** Todos
- **Validade / revisar em:** Após primeiro ciclo real de orquestração

---

<!-- Novas entradas acima desta linha -->
