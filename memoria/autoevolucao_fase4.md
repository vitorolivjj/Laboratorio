# Autoevolução supervisionada — Fase 4

**Cadência inicial:** 1× por dia (09:00 BRT na VPS)  
**Regra:** o sistema **propõe**; só **aplica** após `APROVAR XXXX` no WhatsApp.

## Fluxo

1. Timer `evolution-digest` coleta eventos, tasks, patrulha, memória semântica
2. LLM gera **resumo** + até 4 **propostas** (append em `aprendizados` ou `decisoes`)
3. WhatsApp → você recebe o lote com ID `[XXXX]`
4. `APROVAR XXXX` → grava propostas · reindexa Supabase automaticamente · `RECUSAR XXXX` → descarta
5. Sem propostas → só alerta informativo (nada a aprovar)

## Comandos

```bash
./run.sh evolution-digest --dry-run   # preview
./run.sh evolution-digest --force     # força mesmo dia (teste)
./run.sh evolution-digest             # envia ao Vitor (dedup 1x/dia)
```

## Arquivos

| Path | Função |
|------|--------|
| `backend/src/laboratorio/evolution/` | collector, generate, digest, apply |
| `logs/evolution_state.json` | última data executada |
| `deploy/vps/evolution-digest.timer` | agendamento VPS |

## Depois de aprovar

Ao `APROVAR`, o sistema roda **sync automático** dos arquivos alterados (`aprendizados.md` / `decisoes.md`) no Supabase. A resposta no WhatsApp confirma quantos trechos foram indexados.
