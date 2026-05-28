# Agentes (memória compartilhada)

Estado operacional do ecossistema: quem existe, quando usar e links.

> Definições completas (prompt, personalidade, regras): pasta `agentes/*.md`  
> Mapa de delegação e fluxos: `memoria/ronaldo_maestro/mapa_dos_agentes.md`

## Agentes ativos

| ID | Nome | Arquivo | Domínio | Acionar quando |
|----|------|---------|---------|----------------|
| `ronaldo_maestro` | Ronaldo Maestro | `agentes/ronaldo_maestro.md` | Orquestração | Coordenar, priorizar, consolidar, registrar decisão estratégica |
| `juarez` | Juarez | `agentes/juarez.md` | Operação | Processos, KPIs, gargalos, logística, obras |
| `dev` | Dev | `agentes/dev.md` | Software | Código, arquitetura, APIs, deploy, MVP técnico |
| `caio_manteiga` | Caio Manteiga | `agentes/caio_manteiga.md` | Comercial | Vendas, WhatsApp, funis, copy, conversão |

## Status

| Agente | Status | Observação |
|--------|--------|------------|
| Ronaldo Maestro | Ativo | Orquestrador central |
| Juarez | Ativo | — |
| Dev | Ativo | Backend CrewAI em `backend/` |
| Caio Manteiga | Ativo | — |

## Convenções

- **Orquestrador primeiro** em pedidos que cruzam domínios.
- **Um especialista por vez** quando possível; Ronaldo consolida depois.
- Atualizar esta tabela se entrar ou sair agente.

## Última atualização

- **Data:** 2026-05-28
- **Por:** Dev
