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

> **TASK-001–003** em execução → [executando.md](executando.md)

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
