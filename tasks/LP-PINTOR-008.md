# LP-PINTOR-008 — Automação CRM → build in-house + takedown

## Metadados

| Campo | Valor |
|-------|-------|
| **ID** | LP-PINTOR-008 |
| **Projeto** | PROJ-LP |
| **Status** | backlog |
| **Prioridade** | media |
| **Agentes** | dev · juarez |
| **Dependências** | LP-PINTOR-007 ✓ · LP-PINTOR-002 ✓ |

## Objetivo

Script-ponte: CRM `pronto_pra_pagina` → (opcional IA copy) → `config.json` + build → publish `/previas/{slug}/` → Juarez confere → `previa_no_ar`. Job diário remove ou expira prévias vencidas (3–5 dias sem PIX) → `recusou`.

**Nota:** escopo Webflow **cancelado** — automação só no pipeline in-house (`lp_publish_lead.py` / build / rsync).

## Critérios de aceite

- [ ] CLI ou job: lead slug → build + deploy prévia
- [ ] Ativação: `ativo: true` → rebuild sem tarja
- [ ] Takedown: prévia expirada ou `recusou` → remove dist ou 404 controlado
- [ ] Juarez checkpoint antes de `previa_no_ar`

## Ref

[producao_lp_pintor.md](../memoria/ronaldo_maestro/producao_lp_pintor.md) · operacao_landing_pintor §7
