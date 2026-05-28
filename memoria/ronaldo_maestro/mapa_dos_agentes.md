# Mapa dos agentes

Referência rápida para orquestração. Definições completas em `agentes/`.

## Orquestrador

| Agente | Arquivo | Função resumida |
|--------|---------|-----------------|
| **Ronaldo Maestro** | `agentes/ronaldo_maestro.md` | Coordena, distribui tarefas, consolida, mantém contexto global |

## Especialistas

| Agente | Arquivo | Acionar quando |
|--------|---------|----------------|
| **Juarez** | `agentes/juarez.md` | Operação, logística, obras, KPIs, auditoria, gargalos, produtividade |
| **Dev** | `agentes/dev.md` | Código, arquitetura, APIs, Supabase, deploy, MVP técnico |
| **Caio Manteiga** | `agentes/caio_manteiga.md` | Vendas, WhatsApp, funis, copy, conversão, low ticket, follow-up |
| **Donizete Social** | `agentes/donizete_social.md` | Captação orgânica Facebook/Instagram, qualificação de leads, CRM |

## Fluxos comuns

| Situação | Ordem sugerida |
|----------|----------------|
| Novo produto digital | Dev → Caio Manteiga |
| Melhoria operacional + sistema | Juarez → Dev |
| Campanha com operação por trás | Caio Manteiga → Juarez (se houver entrega/logística) |
| Captação orgânica + abordagem | Donizete Social → Caio Manteiga · [workflow](../docs/workflow-captacao-comercial.md) |
| Projeto completo (ideia → venda → operação) | Ronaldo Maestro → Dev → Caio Manteiga → Juarez (conforme necessidade) |
| TASK com tráfego orgânico (ex.: TASK-001) | Ronaldo → Donizete (ICP + monitoramento) → Caio (abordagem) |

## Regra de ouro

Ronaldo **coordena**; especialistas **executam**. Um agente por domínio por vez, sempre com contexto mínimo no briefing.

## Última revisão do mapa

- **Data:** 2026-05-28
- **Alterações:** Donizete Social adicionado — captação orgânica → Caio.
