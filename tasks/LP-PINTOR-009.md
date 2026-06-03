# LP-PINTOR-009 — Produzir prévia in-house (1 lead)

## Metadados

| Campo | Valor |
|-------|-------|
| **ID** | LP-PINTOR-009 |
| **Projeto** | PROJ-LP |
| **Status** | backlog |
| **Kanban** | tasks/backlog.md |
| **Prioridade** | alta |
| **Agentes** | loide · dev · juarez |
| **Modelo** | **1 task por lead** — pode haver até 3 em `executando` (WIP 4) |

## Objetivo

Por lead em `pronto_pra_pagina`: curadoria → `config.json` + `assets/` → build → `/previas/{slug}/` → QA → `previa_no_ar` no CRM.

## Critérios de aceite (por lead)

- [ ] `assets/` aprovados (Loide)
- [ ] Build: `python scripts/lp_publish_lead.py leads/{slug}`
- [ ] URL pública OK (Juarez)
- [ ] CRM status `previa_no_ar`

## Ref

[producao_lp_pintor.md](../memoria/ronaldo_maestro/producao_lp_pintor.md) · `scripts/lp_publish_lead.py`

### Briefing — Loide + Dev — LP-PINTOR-009

- **Entrada:** `frontend/lp-pintor/leads/{slug}/captura/` completo
- **Saída:** prévia em `api.laboratorioagentes.com.br/previas/{slug}/`
- **Não fazer:** aguardar lote inteiro — pipeline por lead assim que Donizete entrega
