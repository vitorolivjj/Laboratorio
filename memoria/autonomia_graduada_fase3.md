# Autonomia graduada — Fase 3

**Ativada em:** 2026-06-02

## Regra

| Tier | Comportamento |
|------|----------------|
| **auto** | Executa na hora |
| **approval** | WhatsApp → `APROVAR XXXX` / `RECUSAR XXXX` |

## Catálogo (CLI e agentes)

| Ação | Tier | Uso |
|------|------|-----|
| `log_event` | auto | Evento em `logs/eventos.md` |
| `memory_recall` | auto | Busca semântica |
| `patrol_check` | auto | Patrulha dry-run |
| `notify_vitor` | auto | Alerta operacional |
| `append_task_note` | auto | Nota em `tasks/TASK.md` |
| `send_client_message` | approval | Proativo a lead |
| `run_graph_pilot` | approval | Piloto LangGraph |

## CLI

```bash
./run.sh agent-action log_event --json '{"title":"Marco","detail":"Fase 3"}'
./run.sh agent-action memory_recall --json '{"query":"langgraph piloto"}'
./run.sh agent-action send_client_message --json '{"to_wa_id":"5511999999999","body":"Olá"}'
```

## Código

- `backend/src/laboratorio/autonomy/` — registry, gateway, executor
- Aprovações: `whatsapp/approvals.py` · tipo `agent_action`

## Próximo (Fase 4)

Autoevolução supervisionada — propostas semanais + OK do Vitor antes de mudar memória/processos.
