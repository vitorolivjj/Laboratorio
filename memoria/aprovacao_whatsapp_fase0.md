# Aprovação WhatsApp — Fase 0

**Ativada em:** 2026-06-01  
**Titular:** Vitor Oliveira · WA `5533999353242`

## O que exige OK antes de executar

| Ação | Gatilho | Como aprovar |
|------|---------|--------------|
| Mensagem a cliente | Agente inicia envio proativo (não resposta inbound) | `APROVAR XXXX` / `RECUSAR XXXX` |
| Gasto alto | Custo estimado ≥ `APPROVAL_COST_THRESHOLD_USD` (padrão US$ 1) | Idem |

## O que NÃO passa pela trava

- Resposta automática do Caio a quem mandou mensagem primeiro (inbound)
- Canal operacional Vitor ↔ Ronaldo
- Alertas proativos Ronaldo → Vitor (`notify_vitor`)

## Módulos

| Arquivo | Função |
|---------|--------|
| `whatsapp/approvals.py` | Fila pendente · notificação · parse APROVAR/RECUSAR |
| `whatsapp/outbound.py` | `send_to_recipient(..., proactive=True/False)` |
| `logs/approvals_pending.json` | Estado runtime (não commitar pendências sensíveis) |

## API para agentes

```python
from laboratorio.whatsapp.outbound import send_to_recipient

# Proativo a lead — pede aprovação
send_to_recipient("5511999999999", "Olá!", proactive=True, requested_by="caio_manteiga")

# Resposta inbound — direto
send_to_recipient(wa_id, reply, proactive=False)
```

## Próximas fases (plano)

1. ~~Memória semântica (Supabase)~~ ✅
2. ~~LangGraph piloto (LAB-003)~~ ✅ — `./run.sh graph-pilot LAB-003`
3. ~~Skills com autonomia graduada~~ ✅ — `./run.sh agent-action`
4. ~~Autoevolução supervisionada~~ ✅ — resumo 1×/dia · `./run.sh evolution-digest`
