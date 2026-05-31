# TASK-020 — Negão B3+B4: Chat + sugestões + memória viva

## Metadados

| Campo | Valor |
|-------|-------|
| **ID** | TASK-020 |
| **Status** | backlog |
| **Projeto** | PROJ-002 |
| **Prioridade** | alta |
| **Agente responsável** | dev |
| **Dependências** | TASK-019, TASK-012 |
| **Criada em** | 2026-05-31 |

## Objetivo

Loop de chat em `ia.vitoroliv.com`: perfil + retrieval + `snapshot_estado()` + gravação `sugestoes`.

## Critérios de aceite

- [ ] Negão nunca escreve direto no cockpit — só `sugestoes` (proposta → aceita/recusada)
- [ ] Contexto = perfil + trechos + snapshot + conversa atual
- [ ] Conversas novas viram memória episódica incremental
- [ ] App Negão hospedado em `ia.vitoroliv.com` na VPS `5.78.215.136` (nginx subdomínio)
- [ ] **Não** reutilizar stack WhatsApp/Caio do Laboratório

## Escopo ref

Escopo §5–6, B3–B4
