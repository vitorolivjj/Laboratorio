# centralvitor — Referência técnica

## Tabelas (migration 001)

| Tabela | Campos principais |
|--------|-------------------|
| `perfil` | id (auth.users), nome, timezone |
| `projetos` | nome, status, prioridade, frente, user_id |
| `tasks` | titulo, status (kanban), prioridade, projeto_id, user_id |
| `rabiscos` | texto, status (Solto/Vinculado/Arquivado), user_id |
| `sugestoes` | texto, status, origem (Negão), user_id |

## RPC

`snapshot_estado()` → JSON KPIs (projetos_ativos, tasks_abertas, etc.)

## Kanban statuses (TASK-011)

**Tasks:** `backlog` | `planejando` | `executando` | `revisao` | `concluido` | `arquivado`

**Rabiscos:** `solto` | `vinculado` | `arquivado`

## Frentes

`negao`, `laboratorio`, `vs_rota`, `appvs`, `consultoria`, `saude_familiar`, `financas`, `sitio`

## VPS nginx

Root: `/opt/centralvitor/public` · SSL Let's Encrypt · domínios vitoroliv.com + www
