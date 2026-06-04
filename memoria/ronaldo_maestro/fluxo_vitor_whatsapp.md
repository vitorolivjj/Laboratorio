# Fluxo Vitor → Ronaldo (WhatsApp e Painel)

**Dono:** Ronaldo Maestro · **Canal:** WhatsApp autorizado do Vitor (via Caio) · **Atualizado:** 2026-06-03

---

## Hierarquia

| Papel | Função |
|-------|--------|
| **Vitor** | Intenção, prioridade, OK em autoevolução (`APROVAR`) |
| **Ronaldo** | Interpreta, cria/move TASKs, delega, audita, registra decisões |
| **Donizete** | Captura Facebook no Mac (CDP) — só com TASK `LP-PINTOR-*` + grupo fixo |
| **Caio** | WhatsApp comercial (leads LP) |
| **Dev / Loide / Juarez** | Produto e operação Lab |

Nada importante fica só no chat do LLM: vira **TASK no kanban** (`tasks/*.md`), **decisão** em `memoria/decisoes.md` ou **proposta** na fila de autoevolução.

---

## Ordem de processamento (WhatsApp)

1. **Aprovações** (`APROVAR` / `REJEITAR`) — digest, gastos, etc.
2. **`ronaldo_bridge`** — intents estruturados (task, captura, play/stop, decisão, proposta)
3. **Comandos explícitos** — patrulha, agenda, `PlayDonizete` estrito
4. **Fast-path** — status, tasks, agentes (dados do snapshot)
5. **LLM** — só com system prompt restrito (não inventar IDs)

Implementação: `backend/src/laboratorio/whatsapp/ronaldo_bridge.py` · `vitor_whatsapp.py`

---

## Captura intermitente (regra fixa)

| Pedido | Ação Ronaldo |
|--------|----------------|
| URL de grupo + intenção de captura | `create_capture_task` → `LP-PINTOR-XXX` em `executando` + `## Captura intermitente` |
| `PlayDonizete LP-PINTOR-XXX` | Valida grupo fixo no `.md` → arma busca (VPS) → Mac executor |
| `PlayDonizete` sem ID válido | **Recusa** — não arma modo rotativo silencioso |
| `TASK-001` / `TASK-*` para captura | **Recusa** — legado landing; usar `LP-PINTOR-*` |
| Rotacionar grupos | Só se Vitor pedir explicitamente «rotacionar grupos» |

Comandos: `Criar captura <url>` · `PlayDonizete LP-PINTOR-010` · `StopDonizete` · `listar capturas`

Sync estado: Mac → `POST /api/donizete/busca-state` · painel lê `logs/donizete_busca_state.json`

---

## Decisões e autoevolução

| Tipo | Canal WhatsApp | Onde grava | Aplicação |
|------|----------------|------------|-----------|
| **Operacional** | `Decisão: título \| texto` | `memoria/decisoes.md` + `logs/eventos.md` | Imediata (memória) |
| **Mudança de processo** | `Proposta: título \| descrição` | `logs/evolution_proposals_queue.jsonl` | Só após `APROVAR` no digest diário |

O digest (`./run.sh evolution-digest`) consolida propostas pendentes — **nunca** aplica sozinho.

---

## Painel Kanban

- **API:** `GET/POST/PATCH /api/tasks` — fonte `tasks_store` + `task_kanban_api`
- **UI:** `/painel/tasks.html` — colunas, drag-and-drop, drawer, nova task/captura
- **Snapshot:** invalida cache Maestro após mutação (`invalidate_maestro_snapshot`)

Mutations opcionais: header `Authorization: Bearer $MAESTRO_API_TOKEN`

---

## Gates delegação / conferência

Ver [protocolo_delegacao_conferencia.md](protocolo_delegacao_conferencia.md):

- `executando` com briefing Ronaldo
- `concluídas` com auditoria registrada
- Patrulha: `./run.sh governanca-audit` → `logs/governanca_auditoria.md`

---

## Pós-reset do kanban (2026-06-03)

Decisão registrada: kanban operacional reiniciado; **capturas novas** usam apenas prefixo **`LP-PINTOR-*`** com grupo Facebook fixo no markdown da task; `TASK-001` e similares permanecem como histórico de produto/landing, não como canal PlayDonizete.

Auditoria memória: `./run.sh governanca-audit` (drift kanban, captura sem grupo, docs órfãos, decisões sem data).

---

## Referências

- [protocolo_delegacao_conferencia.md](protocolo_delegacao_conferencia.md)
- [memoria/donizete_social/operacao_mac_captacao.md](../donizete_social/operacao_mac_captacao.md)
- [workflows/pipeline_operacional.md](../../workflows/pipeline_operacional.md)
- Plano técnico: fluxo Ronaldo + Kanban (Cursor plan, não editar no repo)
