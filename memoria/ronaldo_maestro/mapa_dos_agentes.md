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
| **Loide** | `agentes/loide.md` | UX, usabilidade, fluxos, **mockups visuais** — skill `loide-ux` |
| **Dev** | `agentes/dev.md` | Código — skills `dev-vitoros` (PROJ-002) ou `dev-laboratorio` (PROJ-001) |
| **Caio Manteiga** | `agentes/caio_manteiga.md` | Vendas, WhatsApp, funis, copy, conversão, low ticket, follow-up |
| **Donizete Social** | `agentes/donizete_social.md` | Captação orgânica Facebook/Instagram, qualificação de leads, CRM |

## Projetos e infra (não misturar)

| Projeto | Domínio | VPS | Repo código |
|---------|---------|-----|-------------|
| **PROJ-001 Laboratório** | api.laboratorioagentes.com.br | 5.78.232.71 | Laboratorio |
| **PROJ-002 VitorOS** | vitoroliv.com · ia.vitoroliv.com | 5.78.215.136 | centralvitor |

Tasks PROJ-002 ficam em `tasks/` (orquestração Lab); **código/deploy só no repo `centralvitor`**.

## Fluxos comuns

| Situação | Ordem sugerida |
|----------|----------------|
| Novo produto digital (Lab) | Dev → Caio Manteiga |
| **VitorOS cockpit (PROJ-002)** | Loide (`loide-ux`) → Dev (`dev-vitoros`) · VPS vitoroliv.com only |
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
