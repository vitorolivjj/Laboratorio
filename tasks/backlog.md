# Backlog

Tarefas **ainda não iniciadas**, priorizadas de cima para baixo.

**Estado:** `backlog` · Ciclo de vida: [docs/ciclo-de-vida-tasks.md](../docs/ciclo-de-vida-tasks.md) · Modelo: [docs/modelo-task.md](../docs/modelo-task.md)

## Como usar

1. Nova tarefa entra aqui com ID único `TASK-XXX`.
2. Ao iniciar, mover bloco para `executando.md` (não duplicar — cortar e colar).
3. Indicar agente responsável e projeto (`PROJ-XXX`) quando houver.

## Template

Ver estrutura completa em [pipeline_operacional.md](../workflows/pipeline_operacional.md#5-estrutura-padrão-das-tasks).

```markdown
### TASK-XXX — [Título]
- **Objetivo:**
- **Contexto:** PROJ-XXX
- **Prioridade:** alta | media | baixa
- **Agente responsável:**
- **Status:** backlog
- **Dependências:**
- **Resultado esperado:**
- **Criada em:** YYYY-MM-DD
- **Atualizada em:** YYYY-MM-DD
```

---

## Fila

> **Prioridade transversal:** [TASK-022](TASK-022.md) — Skills Dev+Loide · em [executando.md](executando.md)

> **PROJ-002 VitorOS** — tasks TASK-012–021 · VPS `vitoroliv.com` only · [delegação](VITOROS-DELEGACAO-RONALDO.md)

### TASK-012 — VitorOS A1: Home cockpit + KPIs derivados
- **Objetivo:** Camada 1 — visão macro em 10s
- **Contexto:** PROJ-002 · depende TASK-011 ✅
- **Prioridade:** alta
- **Agente responsável:** dev · loide
- **Status:** → [executando.md](executando.md)
- **Documento:** [TASK-012.md](TASK-012.md)

### TASK-013 — VitorOS A2: Finanças
- **Contexto:** PROJ-002 · depende TASK-012
- **Prioridade:** media
- **Agente responsável:** dev · loide
- **Status:** backlog · [TASK-013.md](TASK-013.md)

### TASK-014 — VitorOS A2: Objetivos macro
- **Contexto:** PROJ-002 · depende TASK-013
- **Prioridade:** media
- **Agente responsável:** dev · loide
- **Status:** backlog · [TASK-014.md](TASK-014.md)

### TASK-015 — VitorOS A3: Motor alertas + eventos
- **Contexto:** PROJ-002 · depende TASK-014
- **Prioridade:** media
- **Agente responsável:** dev · juarez
- **Status:** backlog · [TASK-015.md](TASK-015.md)

### TASK-016 — VitorOS A3: Atalhos + Mapa + Busca
- **Contexto:** PROJ-002 · depende TASK-015
- **Prioridade:** media
- **Agente responsável:** dev · loide
- **Status:** backlog · [TASK-016.md](TASK-016.md)

### TASK-017 — Negão B0: Import conversations.json
- **Contexto:** PROJ-002 · depende TASK-010
- **Prioridade:** media
- **Agente responsável:** dev
- **Status:** backlog · [TASK-017.md](TASK-017.md)

### TASK-018 — Negão B1: Perfil-semente
- **Contexto:** PROJ-002 · depende TASK-017
- **Prioridade:** media
- **Agente responsável:** dev
- **Status:** backlog · [TASK-018.md](TASK-018.md)

### TASK-019 — Negão B2: pgvector episódica
- **Contexto:** PROJ-002 · depende TASK-018
- **Prioridade:** media
- **Agente responsável:** dev
- **Status:** backlog · [TASK-019.md](TASK-019.md)

### TASK-020 — Negão B3+B4: Chat + sugestões
- **Contexto:** PROJ-002 · `ia.vitoroliv.com` · depende TASK-019, TASK-012
- **Prioridade:** alta
- **Agente responsável:** dev
- **Status:** backlog · [TASK-020.md](TASK-020.md)

### TASK-021 — Integração + seed + DNS ia.
- **Contexto:** PROJ-002 · depende TASK-016, TASK-020
- **Prioridade:** alta
- **Agente responsável:** dev · juarez
- **Status:** backlog · [TASK-021.md](TASK-021.md)

---

> **TASK-003** em execução (Lab) · **PROJ-002** TASK-010+ → [executando.md](executando.md) · [planejando.md](planejando.md)

### TASK-004 — Validar crew de exemplo no backend

- **Objetivo:** Confirmar ambiente Python/CrewAI
- **Contexto:** PROJ-001
- **Prioridade:** baixa
- **Agente responsável:** dev
- **Status:** backlog
- **Dependências:** nenhuma
- **Resultado esperado:** `./run.sh check` OK; `run-sample` com API key
- **Criada em:** 2026-05-28
- **Atualizada em:** 2026-05-28

---

<!-- Novas tarefas acima desta linha -->
