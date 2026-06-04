# TASK-006 — Ajuste Final da Arquitetura de Modelos

**ID:** TASK-006  
**Projeto:** PROJ-001  
**Status:** `arquivado` (cancelada)  
**Prioridade:** alta  
**Criada em:** 2026-05-30  
**Concluída em:** 2026-05-30  
**Responsável:** ronaldo_maestro  

---

## Objetivo

Consolidar a **arquitetura oficial de modelos v1** do Laboratório antes dos testes operacionais reais.

## Princípio aprovado

- **Vitor conversa com Ronaldos** — camada estratégica = padrão Ronaldo (OpenAI).
- **Especialistas** executam com modelos distintos conforme função e evidência.

## Arquitetura oficial v1

```env
MAESTRO_PROVIDER=openai
MAESTRO_MODEL=gpt-5

CAIO_PROVIDER=anthropic
CAIO_MODEL=claude-sonnet-4-20250514

JUAREZ_PROVIDER=anthropic
JUAREZ_MODEL=claude-sonnet-4-20250514

DEV_PROVIDER=anthropic
DEV_MODEL=claude-sonnet-4-20250514

DONIZETE_PROVIDER=anthropic
DONIZETE_MODEL=claude-sonnet-4-20250514
```

## Entregáveis

| ID | Entregável | Status |
|----|------------|--------|
| E1 | `.env` local atualizado | ✅ |
| E2 | `.env.example` atualizado | ✅ |
| E3 | `memoria/decisoes.md` | ✅ |
| E4 | `logs/eventos.md` | ✅ |
| E5 | `dashboard/metricas_operacionais.md` §5.1 | ✅ |
| E6 | `./run.sh llm-config` validado | ✅ |

## Validação

```
[LLM] Ronaldo -> openai / gpt-5
[LLM] Caio -> anthropic / claude-sonnet-4-20250514
[LLM] Donizete -> anthropic / claude-sonnet-4-20250514
[LLM] Dev -> anthropic / claude-sonnet-4-20250514
[LLM] Juarez -> anthropic / claude-sonnet-4-20250514
```

## Diretriz permanente

A camada estratégica do Grupo utiliza o **padrão Ronaldo**. Especialistas poderão utilizar modelos distintos conforme função operacional e evidências futuras.

## Fase atual

Aprender · validar · medir · acumular histórico.

---

**Relacionada:** TASK-005 (roteamento LLM + relatório)
