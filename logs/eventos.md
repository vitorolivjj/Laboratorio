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
