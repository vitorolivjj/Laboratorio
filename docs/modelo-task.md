# Modelo padrão de TASK

Copie este arquivo para `tasks/TASK-XXX.md` ao criar uma task persistente.

**Ciclo de vida:** [ciclo-de-vida-tasks.md](ciclo-de-vida-tasks.md) · **Kanban:** mover bloco resumido em `tasks/backlog.md` (etc.)

---

```markdown
# TASK-XXX — [Título curto]

## Metadados

| Campo | Valor |
|-------|-------|
| **ID** | TASK-XXX |
| **Título** | [Título curto] |
| **Status** | backlog \| planejando \| executando \| aguardando \| concluído \| arquivado |
| **Projeto** | PROJ-XXX |
| **Prioridade** | alta \| media \| baixa |
| **Agente responsável** | ronaldo_maestro \| juarez \| dev \| caio_manteiga |
| **Agentes auxiliares** | (lista ou —) |
| **Criada em** | YYYY-MM-DD |
| **Atualizada em** | YYYY-MM-DD |
| **Kanban atual** | tasks/[backlog\|planejando\|executando\|aguardando\|concluidas\|arquivado].md |

---

## Objetivo

(Uma frase — resultado de negócio ou validação que esta TASK deve alcançar.)

---

## Contexto

- Por que esta TASK existe agora
- Links: `contexto/contexto_global.md`, `memoria/projetos.md`, decisões relevantes
- TASKs dependentes: TASK-YYY ou nenhuma

---

## Entregáveis

| ID | Entregável | Dono | Status |
|----|------------|------|--------|
| E1 | | | ⬜ |
| E2 | | | ⬜ |
| E3 | | | ⬜ |

Status: ⬜ pendente · 🔄 em progresso · ✅ concluído · ❌ cancelado

---

## Critérios de aceite

Lista verificável — Ronaldo usa na auditoria:

- [ ] 
- [ ] 
- [ ] 

---

## Registros por agente

Atualizar após cada sessão. Resposta **em função desta TASK**, não genérica.

### Ronaldo Maestro
- **Última ação:**
- **Briefings emitidos:**
- **Data:**

### Juarez
- **Última ação:**
- **Entrega:**
- **Data:**

### Dev
- **Última ação:**
- **Entrega:**
- **Data:**

### Caio Manteiga
- **Última ação:**
- **Entrega:**
- **Data:**

---

## Briefings (Ronaldo → agentes)

### Briefing — [Agente] — TASK-XXX
- **Objetivo desta rodada:**
- **Entregável esperado:**
- **Restrições:**
- **Critério de pronto:**
- **Não fazer:**

---

## Bloqueios (se status = aguardando)

| Campo | Valor |
|-------|-------|
| **Motivo** | |
| **Desde** | YYYY-MM-DD |
| **Quem desbloqueia** | Vitor \| agente \| externo |
| **Próxima checagem** | |

---

## Auditoria do Ronaldo

Preencher **antes** de mover para `concluído`.

| Campo | Valor |
|-------|-------|
| **Data auditoria** | YYYY-MM-DD |
| **Entregas recebidas** | (sim/não por entregável) |
| **Critérios de aceite** | atendidos / parcial / não |
| **Convergências** | |
| **Divergências e decisão** | |
| **Decisão registrada** | `memoria/decisoes.md` — sim/não — link |
| **Aprendizado registrado** | `memoria/aprendizados.md` — sim/não |
| **Hipótese atualizada** | `memoria/hipoteses_testadas.md` — H-XXX — status |
| **Veredito** | aprovado \| retrabalho \| cancelado |

### Notas da auditoria

(Texto curto — o que funcionou, o que corrigir.)

---

## Próximos passos

1. (ação única — preferência 24h)
2. 
3. 

---

## Histórico de status

| Data | De → Para | Motivo | Responsável |
|------|-----------|--------|-------------|
| YYYY-MM-DD | backlog → planejando | | Ronaldo |
```

---

## Bloco resumido para Kanban

Cole em `backlog.md` / `executando.md` etc. (cortar ao mudar status):

```markdown
### TASK-XXX — [Título]
- **Status:** executando
- **Projeto:** PROJ-XXX
- **Responsável:** dev
- **Auxiliares:** caio_manteiga, juarez
- **Documento:** [TASK-XXX.md](TASK-XXX.md)
- **Próxima ação:**
- **Atualizada em:** YYYY-MM-DD
```

---

## Exemplo no repositório

[tasks/TASK-001.md](../tasks/TASK-001.md) — primeira TASK oficial (estrutura legada; migrar seções para este modelo conforme evoluir).

---

**Última revisão:** 2026-05-28
