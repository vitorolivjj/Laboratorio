# TASK-011 — VitorOS A1: Rabiscos + Projetos + Tasks kanban

## Metadados

| Campo | Valor |
|-------|-------|
| **ID** | TASK-011 |
| **Status** | concluído |
| **Concluída em** | 2026-05-31 |
| **Kanban** | tasks/concluidas.md |

## Objetivo

Módulos de captura e organização: rabiscos (1 toque), projetos (frentes) e tasks com kanban 6 colunas.

## Entregáveis

| ID | Entregável | Status |
|----|------------|--------|
| E1 | CRUD rabiscos (Solto → Arquivado) | ✅ |
| E2 | CRUD projetos (status, prioridade, frente) | ✅ |
| E3 | Kanban tasks (Backlog → Arquivado) | ✅ |
| E4 | UX mobile captura rápida rabisco | ✅ |

## UX (Loide — Laboratório)

- Mockup kanban: `docs/ux/vitoros/TASK-011-kanban-v1.png`
- Spec: `docs/ux/vitoros/TASK-011-kanban-spec.md`
- Skill: `loide-ux` · **Implementação:** `centralvitor/public/` only

## Critérios de aceite

- [x] Criar/editar rabisco, projeto e task no cockpit
- [x] Troca de status/coluna via modal funcional
- [x] Dados persistem no Supabase PROJ-002
- [x] Deploy via `centralvitor` → VPS `vitoroliv.com`

## Escopo ref

Escopo §16–18 · Frentes iniciais: Negão, Laboratório, VS Rota, AppVS, Consultoria, Saúde Familiar, Finanças, Sítio

---

## Briefings (Ronaldo → agentes)

### Briefing — Dev — TASK-011 — 2026-05-31
- **Objetivo desta rodada:** CRUD tasks/rabiscos/projetos na camada Operacional
- **Entregável esperado:** E1–E4
- **Restrições:** só `centralvitor`; spec UX em `Laboratorio/docs/ux/vitoros/`; skill `dev-vitoros`
- **Critério de pronto:** Vitor valida CRUD em vitoroliv.com
- **Não fazer:** agentes/skills no repo produto

### Briefing — Loide — TASK-011 — 2026-05-31
- **Objetivo desta rodada:** Mockup + spec kanban mobile
- **Entregável esperado:** E4 UX
- **Restrições:** artefatos só no Laboratório; skill `loide-ux`
- **Critério de pronto:** Dev implementa a partir da spec

---

## Auditoria do Ronaldo

| Campo | Valor |
|-------|-------|
| **Data auditoria** | 2026-05-31 |
| **Entregas recebidas** | E1–E4 ✅ |
| **Critérios de aceite** | atendidos |
| **Aceite Vitor** | CRUD operacional validado |
| **Aprendizado registrado** | sim — `aprendizados.md`, `evolucao_orquestracao.md` |
| **Veredito** | **aprovado** |

### Notas da auditoria

Entrega sólida A1. Separar fábrica/produto formalizado após esta task. Próximo: TASK-012 KPIs Macro com briefing antes de codar.
