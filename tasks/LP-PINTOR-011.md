# LP-PINTOR-011 — Monitor 20min — painel kanban

## Metadados

| Campo | Valor |
|-------|-------|
| **ID** | LP-PINTOR-011 |
| **Projeto** | PROJ-LP |
| **Status** | executando |
| **Prioridade** | alta |
| **Agente responsável** | donizete_social |
| **Criada em** | 2026-06-04 |

## Objetivo

Captura intermitente no grupo Facebook fixo abaixo — **não trocar de grupo** entre ciclos.

## Captura intermitente

| Campo | Valor |
|-------|-------|
| **Grupo Facebook** | https://www.facebook.com/groups/124168141645517/ |
| **Modo** | grupo_fixo |

### Briefing (Donizete)

- **Grupo fixo:** captura intermitente neste URL — não trocar entre ciclos.
- **Play/Stop:** painel kanban, WhatsApp PlayDonizete/StopDonizete ou API.
- **Mac:** `./scripts/donizete-mac-executor.sh --watch` quando VPS armada sem CDP local.

## Critérios de aceite

- [ ] Leads `pronto_pra_pagina` conforme meta do lote
- [ ] PlayDonizete / StopDonizete controlam a busca

## WhatsApp

- `PlayDonizete LP-PINTOR-011` — inicia captura neste grupo
- `StopDonizete LP-PINTOR-011` — para e restaura kanban
