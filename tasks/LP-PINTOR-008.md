# LP-PINTOR-008 — Automação CRM → Webflow API + takedown

| Campo | Valor |
|-------|-------|
| **ID** | LP-PINTOR-008 |
| **Projeto** | PROJ-LP |
| **Status** | backlog |
| **Kanban** | tasks/backlog.md |
| **Dependências** | LP-PINTOR-007 |
| **Agente** | loide · dev · juarez |

## Objetivo

Script-ponte: CRM `pronto_pra_pagina` → IA copy → criar/publicar item Webflow → Juarez confere → `previa_no_ar`. Job diário despublica prévias vencidas (3–5 dias) → `recusou`.

## Critérios de aceite

- [ ] CLI ou job: criar item a partir de LEAD-XXX no CRM
- [ ] Publicar/despublicar item via API (sem rebuild site)
- [ ] Ativar lead: flag `Ativo` + CRM `ativo` (pós-PIX Vitor)
- [ ] Job takedown prévias expiradas
- [ ] Handoff documentado: Donizete → IA → Loide → Juarez

## Ref

`memoria/ronaldo_maestro/webflow_lp_pintor.md` · operacao §7
