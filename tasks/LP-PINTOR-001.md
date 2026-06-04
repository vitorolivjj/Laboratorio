# LP-PINTOR-001 — Captação Facebook lote 1 (5 leads)

## Metadados

| Campo | Valor |
|-------|-------|
| **ID** | LP-PINTOR-001 |
| **Projeto** | PROJ-LP |
| **Status** | arquivado (cancelada) |
| **Kanban** | tasks/executando.md |
| **Prioridade** | alta |
| **Agente responsável** | donizete_social |
| **Dependências** | LP-PINTOR-007 ✓ (in-house) · modelo `/previas/exemplo-pintor/` |
| **Meta sprint** | **5 leads** `pronto_pra_pagina` (lote 1 de 10) |
| **Criada em** | 2026-05-31 |
| **Iniciada em** | 2026-06-03 (deploy rodada 4 — 2026-06-03) |

## Objetivo

Lote 1 de captação Facebook (Canal A + B) — **5 leads** `pronto_pra_pagina` com stalk e mídia completa. Lote 2: **LP-PINTOR-001B**.

**Plano:** [plano_atuacao_donizete_lp.md](../memoria/ronaldo_maestro/plano_atuacao_donizete_lp.md) · **Modo sprint** §4

## Ritmo (kanban)

- **Cada lead** `pronto_pra_pagina` = entregável → evento `logs/eventos.md` + abrir **LP-PINTOR-009** (produção) em paralelo
- Patrulha: crítico se **30 min** sem pronto/prospectado/pasta captura

## Critérios de aceite

- [ ] 10+ grupos mapeados
- [ ] 8 variações post-isca em uso
- [ ] Modo sprint: 6–8 posts/dia · 25–60 min entre posts · até 2 leads/h
- [ ] **5 leads** `pronto_pra_pagina` com captura/raw + manifest
- [ ] Zero ban

## Ref

[operacao_landing_pintor.md](../memoria/ronaldo_maestro/operacao_landing_pintor.md) · LP-PINTOR-001B · LP-PINTOR-009

### Briefing — Donizete — LP-PINTOR-001 — rodada 4 (deploy)

- **Objetivo:** 5 leads `pronto_pra_pagina` · modo sprint
- **WhatsApp Vitor:** `PlayDonizete busca inicia` / `StopDonizete` (task → standby ↔ executando)
- **Quem escolhe grupos:** Donizete (`fb_escolher_grupo` / `fb_ciclo_navegacao`)
- **2 atuações:** (1) navegação scroll lento + posts existentes → perfil → stalk (2) `fb_ciclo_post` publica isca (autorizado)
- **Mac:** Chrome CDP `./scripts/facebook-cdp-mac.sh` · API local ou VPS recebe WA
- **Caio:** template `abertura_pintor_contato` aprovado Meta — abordagem proativa liberada
- **Não fazer:** chutar URL · R$ 69 no FB · inventar leads
