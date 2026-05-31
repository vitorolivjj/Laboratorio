# TASK-008 — Painel Maestro v1

**ID:** TASK-008  
**Projeto:** PROJ-001  
**Status:** `concluido`  
**Prioridade:** alta  
**Criada em:** 2026-05-31  
**Concluída em:** 2026-05-31  
**Responsável:** dev  

---

## Objetivo

Frontend operacional para Vitor visualizar a operação dos agentes em tempo real.

**Nome:** Painel Maestro

## Entregáveis

| ID | Entregável | Status |
|----|------------|--------|
| E1 | API `/api/maestro/snapshot` | ✅ |
| E2 | Frontend dark + azul neon | ✅ |
| E3 | 6 seções (overview, agentes, delegações, WA, leads, logs) | ✅ |
| E4 | Deploy VPS | ✅ |
| E5 | Documentação de uso | ✅ |

## URLs

| Ambiente | URL |
|----------|-----|
| **Produção (recomendado)** | https://maestro.laboratorioagentes.com.br/painel/ |
| **Alternativa** | https://api.laboratorioagentes.com.br/painel/ |
| **API** | `/api/maestro/snapshot` |

## DNS (Registro.br)

| Tipo | Nome | Valor |
|------|------|-------|
| A | `maestro` | IP da VPS (`5.78.232.71`) |

Depois: `certbot --nginx -d maestro.laboratorioagentes.com.br`

## Uso

1. Abrir o Painel Maestro no browser.
2. Responder em 30 segundos:
   - Sistema online? → cards Visão Geral
   - Quem trabalha? → cards Agentes
   - Tarefas pendentes? → WIP + Delegações
   - Leads? → seção Leads
   - Caio respondeu? → Conversas WhatsApp
   - Erros? → card Último erro + Logs

**Auto-refresh:** 30 segundos · botão **Atualizar** manual.

## Arquitetura

```
frontend/painel-maestro/  → HTML/CSS/JS estático
backend/ops/              → parsers markdown (CRM, tasks, logs)
backend/api/routes/maestro.py → JSON snapshot
FastAPI mount /painel + nginx maestro.*
```

## Fontes de dados

- `tasks/executando.md` — WIP, agentes, delegações
- `tasks/TASK-*.md` — tabelas rodada operacional
- `crm/leads.md` — leads
- `logs/eventos.md` — eventos, erros
- `logs/whatsapp_mensagens.md` — conversas Caio
- `memoria/decisoes.md` — decisões
- `llm_config.py` — modelo por agente

## Comandos

```bash
# Local
cd backend && ./run.sh serve
# Abrir http://127.0.0.1:8000/painel/

# Deploy VPS
./deploy/vps/update-from-mac.sh
ssh root@IP "certbot --nginx -d maestro.laboratorioagentes.com.br"
```

## Critério de aceite

✅ Vitor responde em 30s: online, agentes, tarefas, leads, WhatsApp, erros.

---

**Relacionada:** TASK-003 (snapshot dashboard), TASK-007 (WhatsApp)
