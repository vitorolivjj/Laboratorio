# Concluídas

Histórico de tarefas **finalizadas** (mais recentes no topo).

**Estado:** `concluido` · Arquivar depois em `arquivado.md` · Pipeline: [workflows/pipeline_operacional.md](../workflows/pipeline_operacional.md)

## Template

```markdown
### TASK-XXX — [Título]
- **Concluída em:** YYYY-MM-DD
- **Agente:**
- **Projeto:**
- **Resultado:** (1–3 linhas)
- **Aprendizado:** (opcional — pode linkar memoria/aprendizados.md)
```

---

## Concluídas

### TASK-008 — Painel Maestro v1

- **Concluída em:** 2026-05-31
- **Agente:** dev
- **Projeto:** PROJ-001
- **Resultado:** Dashboard operacional dark/neon · API snapshot · 6 seções · deploy VPS `/painel/`
- **Aprendizado:** Agregar markdown existente evita duplicar CRM/tasks em banco

### TASK-007 — Conectar Caio ao WhatsApp

- **Concluída em:** 2026-05-31
- **Agente:** dev · caio_manteiga
- **Projeto:** PROJ-001
- **Resultado:** WhatsApp → VPS → Caio → WhatsApp em produção · webhook Meta · número real · primeira conversa humana validada
- **Aprendizado:** Modelo `claude-sonnet-4-20250514` descontinuado — migrar para `claude-sonnet-4-6`

### TASK-006 — Ajuste Final da Arquitetura de Modelos

- **Concluída em:** 2026-05-30
- **Agente:** ronaldo_maestro
- **Projeto:** PROJ-001
- **Resultado:** Arquitetura v1 — Ronaldo `openai/gpt-5` · especialistas `anthropic/sonnet` · `llm-config` OK
- **Aprendizado:** Camada estratégica separada da execução; ver `memoria/decisoes.md`

### TASK-005 — Revisão Estratégica dos Modelos dos Agentes

- **Concluída em:** 2026-05-30
- **Agente:** ronaldo_maestro (relatório) · dev (E6)
- **Projeto:** PROJ-001
- **Resultado:** Roteamento LLM por agente — todos anthropic/claude-sonnet-4-20250514 · `./run.sh llm-config`
- **Aprendizado:** Variáveis `*_PROVIDER` sem código = config decorativa. Ver [TASK-005-relatorio-modelos.md](TASK-005-relatorio-modelos.md)

### TASK-003 — Infra operacional multiagente

- **Concluída em:** 2026-05-28
- **Agente:** dev
- **Projeto:** PROJ-001
- **Resultado:** Pastas `contexto/`, `tasks/`, `logs/`, `workflows/` e arquivos em `memoria/`; README e workflows documentados.
- **Aprendizado:** Ver `memoria/aprendizados.md` (memória compartilhada vs estratégica).

### TASK-000 — Estrutura inicial do repositório

- **Concluída em:** 2026-05-28
- **Agente:** dev
- **Projeto:** PROJ-001
- **Resultado:** Pastas agentes, backend, memoria/ronaldo_maestro e definições dos quatro agentes.
- **Aprendizado:** —

---

<!-- Novas conclusões acima desta linha -->
