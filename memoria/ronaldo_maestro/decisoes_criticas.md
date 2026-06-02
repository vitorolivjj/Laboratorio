# Decisões críticas

Registro de decisões que afetam mais de um agente, a arquitetura do ecossistema ou a direção do negócio.

Formato por entrada:

```
### [Título curto] — YYYY-MM-DD
- **Contexto:**
- **Decisão:**
- **Motivo:**
- **Agentes impactados:**
- **Revisar em:**
```

---

## Decisões

### Fluxo total de tasks liberado — 2026-05-31

- **Contexto:** Vitor autoriza ciclo completo autônomo após patrulha + canal WhatsApp operacional.
- **Decisão:** Ronaldo conduz backlog→concluído sem gates do Vitor; auditoria técnica fecha TASK; escalacao só credencial/custo/prod Lab/estrutural; WIP repovoado automaticamente da fila VitorOS.
- **Motivo:** Andamento constante; Vitor foca em decisões estratégicas, não em aprovar cada movimento de kanban.
- **Agentes impactados:** Todos.
- **Revisar em:** Permanente até revogação.

### Autonomia operacional do Ronaldo — 2026-05-31

- **Contexto:** Vitor autorizou Ronaldo a iniciar tasks e delegar sem gate de aprovação por ciclo.
- **Decisão:** Ronaldo opera como diretor com mandato — prioriza, inicia, move kanban e aciona agentes dentro dos limites documentados em `agentes/ronaldo_maestro.md` § Autonomia operacional.
- **Motivo:** Reduzir atrito entre planejamento e execução; VitorOS (PROJ-002) não pode ficar parado aguardando OK formal.
- **Agentes impactados:** Todos.
- **Revisar em:** Se Vitor revogar ou houver abuso de escopo/custo.

### Estrutura do Laboratório — 2026-05-28

- **Contexto:** Início do repositório como ambiente de testes de IA e software.
- **Decisão:** Pastas `agentes/`, `dashboard/`, `backend/`, `frontend/`, `docs/` e memória estratégica em `memoria/ronaldo_maestro/`.
- **Motivo:** Separar código, documentação e orquestração com simplicidade.
- **Agentes impactados:** Todos.
- **Revisar em:** Quando o primeiro MVP sair do papel.

---

<!-- Adicionar novas decisões acima desta linha, das mais recentes para as mais antigas -->
