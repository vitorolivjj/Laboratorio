# Patrulha operacional — Ronaldo Maestro

Check periódico do ecossistema: tasks, estrutura, infra e erros. Mantém **andamento constante** sem microgerenciar especialistas.

**Relacionados:** [protocolo_delegacao_conferencia.md](protocolo_delegacao_conferencia.md) · [regras_do_ecossistema.md](regras_do_ecossistema.md) · [autorizacao_vitor_whatsapp.md](../autorizacao_vitor_whatsapp.md)

---

## Objetivo

A cada ciclo (30 min padrão):

1. Ler snapshot Maestro (kanban, agentes, logs, delegações)
2. Verificar WIP, bloqueios, erros, infra (VPS, WhatsApp)
3. Registrar resumo em `logs/ronaldo_patrol.md`
4. Se precisar **Vitor** → Caio envia WhatsApp `+5533999353242`
5. Se só operacional → registrar evento; Ronaldo age na próxima delegação

---

## Checklist da patrulha

| # | Verificação | Ação se falhar |
|---|-------------|----------------|
| 1 | WIP ≤ 3 em `executando.md` | Alerta se > 3; repriorizar na próxima rodada |
| 2 | TASKs em `executando` com briefing | Mover para `planejando` ou emitir briefing |
| 3 | Bloqueio citando Vitor / credencial / autorização | **WhatsApp Vitor** |
| 4 | VPS (`laboratorio-api`) online | **WhatsApp Vitor** se off |
| 5 | WhatsApp API operacional | **WhatsApp Vitor** se off |
| 6 | Erros recentes em `logs/eventos.md` | **WhatsApp** se crítico e não resolvido |
| 7 | Delegações alinhadas com briefings | Registrar; corrigir na próxima delegação |
| 8 | `sync_meta` dos arquivos-fonte recente | Registrar se VPS desatualizada |

---

## Formato do alerta WhatsApp (Caio → Vitor)

```
🔔 Ronaldo (via Caio)

[Título curto — 1 linha]

[Detalhe — máx. 3 linhas]

Ação sugerida: [o que Vitor precisa fazer/responder]

Ref: TASK-XXX · painel/logs
```

Tom: direto, sem pitch comercial, sem markdown.

---

## Deduplicação

Mesmo alerta **não** reenvia em 4 h (`logs/ronaldo_patrol_state.json`).

---

## Execução

```bash
# Manual
cd backend && ./run.sh ronaldo-patrol

# VPS (automático)
systemctl status ronaldo-patrol.timer   # a cada 15 min

**Task parada:** se em `executando` >24h (`TASK_STALE_HOURS`), patrulha pede checkpoint — fatiar, concluir parcial ou backlog.
```

**Última revisão:** 2026-05-31
