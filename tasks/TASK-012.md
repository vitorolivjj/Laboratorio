# TASK-012 — VitorOS A1: Home cockpit + KPIs derivados

## Metadados

| Campo | Valor |
|-------|-------|
| **ID** | TASK-012 |
| **Status** | arquivado (cancelada) |
| **Dependências** | TASK-011 ✅ · PROJ-002 pausado |
| **Iniciada em** | 2026-05-31 |
| **Kanban** | tasks/aguardando.md |

## Objetivo

Home/Camada 1 com KPIs calculados (nunca digitados): financeiro, projetos, tasks, negócios.

## Critérios de aceite

- [ ] Abrir cockpit em ~10s: Vitor entende situação, atenção, travamentos, avanços
- [x] KPIs derivados de `snapshot_estado()` expandido (migration 002)
- [x] Blocos atenção + tasks por coluna na camada Macro
- [x] Placeholder Negão mantido
- [x] Só `centralvitor` / deploy vitoroliv.com

## Escopo ref

Escopo §11–12

---

## Briefings (Ronaldo → agentes) — 2026-05-31

### Briefing — Dev — TASK-012
- **Objetivo desta rodada:** KPIs reais na camada Macro via `snapshot_estado()` expandido
- **Entregável esperado:** cards KPI + blocos atenção/travamento derivados de dados
- **Restrições:** só `centralvitor`; KPIs nunca digitados manualmente; skill `dev-vitoros`
- **Critério de pronto:** Vitor lê Macro em ~10s e entende situação
- **Não fazer:** finanças completas (TASK-013); alterar Lab

### Briefing — Loide — TASK-012
- **Objetivo desta rodada:** Hierarquia visual Macro — o que Vitor vê primeiro
- **Entregável esperado:** spec + mockup opcional em `docs/ux/vitoros/`
- **Restrições:** skill `loide-ux`; artefatos só no Laboratório
- **Critério de pronto:** Dev implementa camada 1 alinhada à spec

**Protocolo:** [protocolo_delegacao_conferencia.md](../memoria/ronaldo_maestro/protocolo_delegacao_conferencia.md)
