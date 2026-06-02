# LangGraph piloto — Fase 2

**Task piloto:** `LAB-003` · **Projeto:** PROJ-LAB

## Motor

| Item | Valor |
|------|-------|
| Código | `backend/src/laboratorio/graph/` |
| Checkpoints | `logs/langgraph_pilot.sqlite` |
| CLI | `./run.sh graph-pilot LAB-003` |
| Retomar | `./run.sh graph-pilot LAB-003 --resume` |

## Fluxo do grafo

```
load → plan → work → cost_gate → finalize
```

- **load:** lê `tasks/LAB-003.md` + memória semântica
- **plan / work:** OpenAI (`GRAPH_PILOT_MODEL` ou `VOICE_LLM_MODEL`)
- **cost_gate:** se custo ≥ `APPROVAL_COST_THRESHOLD_USD` → WhatsApp Vitor
- **finalize:** grava em `LAB-003.md` + `logs/eventos.md`

## Coexistência com CrewAI

- **CrewAI:** Caio inbound, `orchestrate`, orquestrador.py
- **LangGraph:** tasks marcadas para piloto (começa por LAB-003)

## Próximo (Fase 3)

Skills com autonomia graduada; nós do grafo chamam ferramentas reais (deploy, WhatsApp proativo com trava).

---

## Grafo comercial — LAB-006 (PROJ-LP)

| Item | Valor |
|------|-------|
| Código | `backend/src/laboratorio/graph/commercial.py` |
| Checkpoints | mesmo `logs/langgraph_pilot.sqlite` (thread = task_id) |
| CLI | `./run.sh graph-run LP-PINTOR-002` |
| Retomar | `./run.sh graph-run LP-PINTOR-002 --resume` |

### Fluxo

```
load → plan → execute → cost_gate → finalize
```

- **load / plan:** reutiliza nós do piloto (`pilot.py`)
- **execute:** LLM propõe até 3 ações JSON → `run_action()` (append_task_note, notify_vitor, send_client_message)
- **cost_gate / finalize:** igual ao piloto

### Coexistência

- **graph-pilot:** tasks PROJ-LAB (ex.: LAB-003)
- **graph-run:** tasks PROJ-LP com `agent_action` real e trava WA no envio proativo
