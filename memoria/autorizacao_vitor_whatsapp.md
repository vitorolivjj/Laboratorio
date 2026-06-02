# Autorização — Vitor no WhatsApp (canal operacional)

**Concedida em:** 2026-05-31 · **Ampliada em:** 2026-05-31  
**Titular:** Vitor Oliveira  
**WhatsApp:** +55 33 99935-3242 · WA ID `5533999353242`  
**Canal:** Caio Manteiga (API) → **Ronaldo operador completo**

---

## Escopo (canal dono)

Equivalente ao **Cursor + Painel Maestro**. Sem limite comercial.

| Capacidade | Vitor | Leads |
|------------|-------|-------|
| Status, WIP, agentes, tasks | ✅ | ❌ |
| Delegações, logs, decisões | ✅ | ❌ |
| **Executar patrulha** | ✅ | ❌ |
| **Agendar lembretes** | ✅ | ❌ |
| **Registrar eventos** | ✅ | ❌ |
| **Alertas proativos** | ✅ | ❌ |
| **LLM operador livre** | ✅ | ❌ |
| Vendas / funil | ❌ | ✅ |

---

## Comandos WhatsApp

```
status · tasks · agentes · delegações · logs
patrulha agora · teste alerta
registrar: [texto]
agendar em 30 min: status
agendar amanhã 9h: patrulha
agenda · ajuda
```

+ **pergunta livre** (priorizar, explicar TASK, VitorOS, Lab)

---

## Arquitetura

| Módulo | Função |
|--------|--------|
| `vitor_whatsapp.py` | Router: exec → fast → LLM + histórico |
| `vitor_actions.py` | Patrulha, eventos, alertas |
| `vitor_schedule.py` | Agenda + timer 1 min |
| `ronaldo_patrol.py` | Check 30 min + escalacao |

**Timers VPS:** `ronaldo-patrol.timer` (30 min) · `vitor-schedule.timer` (1 min)

---

## Escalacao automática (alertas)

Credencial · custo · prod Lab · estrutural · bloqueio >48h · erro crítico  
→ Caio envia `🔔 Ronaldo (via Caio)` · dedup 4 h

---

## Revogação

Remover `VITOR_WHATSAPP_WA_ID` do `.env` ou registrar revogação aqui.
