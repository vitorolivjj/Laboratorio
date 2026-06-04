# TASK-010 — VitorOS A0: Esqueleto (Supabase, Auth, shell PWA, deploy VPS)

## Metadados

| Campo | Valor |
|-------|-------|
| **ID** | TASK-010 |
| **Status** | arquivado (cancelada) |
| **Concluída em** | 2026-05-31 |
| **Kanban** | tasks/concluidas.md |

## Objetivo

Entregar o esqueleto do VitorOS em `vitoroliv.com`: Supabase + Auth + shell PWA 3 camadas + deploy na VPS dedicada.

## Contexto

- Escopo: [contexto/escopo-vitoros.md](../contexto/escopo-vitoros.md) · Fase A0
- Delegação: [VITOROS-DELEGACAO-RONALDO.md](VITOROS-DELEGACAO-RONALDO.md)
- **Repo código:** `github.com/vitorolivjj/centralvitor` (workspace `02-CentralVitor/centralvitor`)
- **VPS:** `5.78.215.136` · `/opt/centralvitor` · **NÃO** VPS Laboratório
- **Supabase:** projeto `pwlpdpwxxhbsmkclrpoa` · migration `001_vitoros_initial.sql` aplicada

## Entregáveis

| ID | Entregável | Dono | Status |
|----|------------|------|--------|
| E1 | Projeto Supabase VitorOS (separado do Lab) | dev | ✅ |
| E2 | Migrations: tabelas base + `sugestoes` + stub `snapshot_estado()` | dev | ✅ |
| E3 | Shell PWA 3 camadas (macro/operacional/mapa) dark mode | dev + loide | ✅ |
| E4 | Supabase Auth (usuário único Vitor) | dev | ✅ |
| E5 | Deploy VPS `vitoroliv.com` substituindo página "em breve" | dev | ✅ |

## Critérios de aceite

- [x] `https://vitoroliv.com` serve app shell (não página estática "em breve")
- [x] Login Supabase funciona (testado via API)
- [x] Navegação entre 3 camadas visível
- [x] Código só no repo `centralvitor`, deploy só VPS `5.78.215.136`
- [x] Zero alteração na VPS/API do Laboratório

## Próximos passos

_(concluída — ver TASK-011)_

---

## Briefings (Ronaldo — retroativo) — 2026-05-31

Ver [VITOROS-DELEGACAO-RONALDO.md](VITOROS-DELEGACAO-RONALDO.md) § Briefing Dev/Loide TASK-010.

---

## Auditoria do Ronaldo

| Campo | Valor |
|-------|-------|
| **Data auditoria** | 2026-05-31 |
| **Entregas recebidas** | E1–E5 ✅ |
| **Critérios de aceite** | atendidos |
| **Aceite Vitor** | Login vitoroliv.com OK |
| **Aprendizado registrado** | sim — auth Site URL Supabase |
| **Veredito** | **aprovado** |
