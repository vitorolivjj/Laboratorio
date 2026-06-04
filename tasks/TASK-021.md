# TASK-021 — Integração cockpit ↔ Negão + seed + DNS

## Metadados

| Campo | Valor |
|-------|-------|
| **ID** | TASK-021 |
| **Status** | arquivado (cancelada) |
| **Projeto** | PROJ-002 |
| **Prioridade** | alta |
| **Agente responsável** | dev |
| **Agentes auxiliares** | juarez |
| **Dependências** | TASK-016, TASK-020 |
| **Criada em** | 2026-05-31 |

## Objetivo

Marco de integração: Home exibe sugestões Negão, aceitar aplica mudança, seed inicial populado, DNS `ia.vitoroliv.com`.

## Entregáveis

| ID | Entregável | Dono | Status |
|----|------------|------|--------|
| E1 | UI "ações propostas pelo Negão" + aceitar/recusar | dev | ⬜ |
| E2 | `snapshot_estado()` completo e consumido pelo Negão | dev | ⬜ |
| E3 | Seed: projetos, caixas, objetivos, atalhos (lista Juarez) | juarez + dev | ⬜ |
| E4 | DNS A `ia.vitoroliv.com` → `5.78.215.136` + SSL certbot | dev | ⬜ |

## Critérios de aceite

- [ ] Fluxo completo: cockpit → Negão → sugestão → aceite → estado atualizado
- [ ] Seed reflete frentes reais do Vitor
- [ ] Dois domínios na mesma VPS, projetos Supabase único, zero dependência Lab VPS

## Escopo ref

Escopo §25 marco integração · seed inicial
