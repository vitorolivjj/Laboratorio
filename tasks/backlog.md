# Backlog

Tarefas **ainda não iniciadas**, priorizadas de cima para baixo.

**Estado:** `backlog` · Pipeline: [workflows/pipeline_operacional.md](../workflows/pipeline_operacional.md)

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

### TASK-001 — Validar crew de exemplo no backend

- **Prioridade:** media
- **Projeto:** PROJ-001
- **Agente:** dev
- **Descrição:** Configurar `.env`, rodar `python -m laboratorio check` e `run-sample`.
- **Critério de pronto:** Comando executa sem erro de import; LLM responde (se key configurada).
- **Criada em:** 2026-05-28

### TASK-002 — Primeiro ciclo de orquestração documentado

- **Prioridade:** media
- **Projeto:** PROJ-001
- **Agente:** ronaldo_maestro
- **Descrição:** Pedido real do Vitor → plano → delegação → registro em `historico_de_orquestracao.md`.
- **Critério de pronto:** Entrada completa no histórico + tarefa em `concluidas.md`.
- **Criada em:** 2026-05-28

---

<!-- Novas tarefas acima desta linha -->
