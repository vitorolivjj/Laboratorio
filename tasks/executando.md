# Executando

Tarefas **em andamento agora**. Manter poucas (WIP baixo, máx. 3).

**Estado:** `executando` · Ciclo de vida: [docs/ciclo-de-vida-tasks.md](../docs/ciclo-de-vida-tasks.md)

## Regra

- Máximo recomendado: **3** tarefas simultâneas no ecossistema.
- Ao concluir → mover para `concluidas.md`.
- Se pausar → voltar para `backlog.md` com nota.

## Template

```markdown
### TASK-XXX — [Título]
- **Iniciada em:** YYYY-MM-DD
- **Agente:**
- **Projeto:**
- **Status:** em_progresso | bloqueada
- **Bloqueio:** (se houver)
- **Próxima ação:**
```

---

## Em andamento

### TASK-003 — Automação snapshot dashboard operacional

- **Iniciada em:** 2026-05-28
- **Agente:** ronaldo_maestro (coord.) · dev · juarez
- **Projeto:** PROJ-001
- **Status:** em_progresso
- **Documento oficial:** [TASK-003.md](TASK-003.md)
- **Rodada ativa:** 1 — script + workflow (2026-05-28)
- **Entregáveis:** E1–E4 ✅ · E5 🔄
- **Bloqueio:** nenhum — aguarda push Actions
- **Próxima ação:** Push main → validar workflow

### TASK-012 — VitorOS A1: Home cockpit + KPIs derivados

- **Iniciada em:** 2026-05-31
- **Agente:** dev · loide
- **Projeto:** PROJ-002
- **Status:** em_progresso
- **Documento:** [TASK-012.md](TASK-012.md)
- **Depende:** TASK-011 ✅
- **Próxima ação:** KPIs derivados na camada Macro · expandir `snapshot_estado()`

### TASK-022 — Biblioteca Skills Dev + Loide

- **Iniciada em:** 2026-05-31
- **Agente:** dev · loide · ronaldo_maestro
- **Projeto:** PROJ-001 (transversal)
- **Status:** em_progresso — E1–E6 ✅ · protocolo Ronaldo integrado
- **Próxima ação:** Fechar TASK-022 após TASK-012 auditada · expandir skills Negão/finanças

---

<!-- Tarefas ativas abaixo -->
