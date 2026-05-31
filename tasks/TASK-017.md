# TASK-017 — Negão B0: Import + limpeza conversations.json

## Metadados

| Campo | Valor |
|-------|-------|
| **ID** | TASK-017 |
| **Status** | backlog |
| **Projeto** | PROJ-002 |
| **Prioridade** | media |
| **Agente responsável** | dev |
| **Dependências** | TASK-010 (Supabase pronto) |
| **Criada em** | 2026-05-31 |

## Objetivo

Pipeline de importação do export ChatGPT: limpeza, priorizar mensagens Vitor + decisões, descartar ruído.

## Critérios de aceite

- [ ] Script import no repo `centralvitor` ou subpasta `negao/`
- [ ] Tabela `memoria_bruta` populada com metadados
- [ ] Qualidade validada manualmente (amostra 50 trechos)
- [ ] Roda no Supabase PROJ-002 — **não** no backend Laboratório

## Escopo ref

Escopo §6, B0
