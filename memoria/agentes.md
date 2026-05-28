# Agentes (memória compartilhada)

Índice do ecossistema: quem existe, memória de domínio e quando acionar.

> Definições completas: `agentes/*.md`  
> Arquitetura de memória: [docs/arquitetura-agentes.md](../docs/arquitetura-agentes.md)

## Agentes permanentes

| ID | Agente | Memória de domínio | Escopo | Definição |
|----|--------|-------------------|--------|-----------|
| `ronaldo_maestro` | Ronaldo Maestro | `memoria_estrategica_ronaldo.md` + `ronaldo_maestro/` | Longa (estratégica) | `agentes/ronaldo_maestro.md` |
| `juarez` | Juarez | `memoria_operacional_juarez.md` | Média (operacional) | `agentes/juarez.md` |
| `dev` | Dev | `memoria_tecnica_dev.md` | Por projeto | `agentes/dev.md` |
| `caio_manteiga` | Caio Manteiga | `memoria_comercial_caio.md` | Por oferta | `agentes/caio_manteiga.md` |
| `donizete_social` | Donizete Social | `crm/leads.md` | Por campanha / TASK | `agentes/donizete_social.md` |

## Subagentes temporários

- **Memória:** curta (sessão / TASK)
- **Entrada:** briefing enxuto produzido pelo Ronaldo
- **Saída:** entrega ao Ronaldo para auditoria — sem escrita em memória longa

## Memória compartilhada (todos leem)

| Arquivo | Função |
|---------|--------|
| `decisoes.md` | Decisões globais |
| `aprendizados.md` | Lições auditadas |
| `hipoteses_testadas.md` | Hipóteses H-XXX |
| `projetos.md` | Portfólio PROJ-XXX |

## Fluxo de memória (resumo)

1. Ronaldo lê memória **longa** + contexto + TASK
2. Ronaldo produz **briefing curto** para especialista ou subagente
3. Especialista executa usando memória de **domínio**
4. Ronaldo **audita** → `aprendizados`, `decisoes`, `hipoteses_testadas`

## Status

| Agente | Status |
|--------|--------|
| Ronaldo Maestro | Ativo |
| Juarez | Ativo |
| Dev | Ativo |
| Caio Manteiga | Ativo |
| Donizete Social | Ativo |

**Última atualização:** 2026-05-28
