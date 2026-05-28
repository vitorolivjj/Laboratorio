# Laboratório

Ambiente de testes de IA, automações e desenvolvimento de software — **ecossistema multiagente coordenado** com memória, contexto, tarefas e workflows compartilhados.

## Ecossistema multiagente

Quatro agentes especializados + um orquestrador. Todos leem o **contexto global** e a **memória compartilhada**; o **Ronaldo Maestro** mantém a **memória estratégica** para coordenação.

```
Pedido do Vitor
      │
      ▼
Ronaldo Maestro ──delega──► Juarez | Dev | Caio Manteiga
      │                            │
      └──────── consolida ◄────────┘
                  │
                  ▼
    contexto/ + memoria/ + tasks/ + logs/ + workflows/
```

| Papel | Agente | Definição |
|-------|--------|-----------|
| Orquestrador | Ronaldo Maestro | `agentes/ronaldo_maestro.md` |
| Operação | Juarez | `agentes/juarez.md` |
| Software | Dev | `agentes/dev.md` |
| Comercial | Caio Manteiga | `agentes/caio_manteiga.md` |

**Pipeline contínuo (Ronaldo):** [workflows/pipeline_operacional.md](workflows/pipeline_operacional.md)  
Fluxo entre agentes: [workflows/fluxo_agentes.md](workflows/fluxo_agentes.md)  
Primeira sessão: [workflows/onboarding.md](workflows/onboarding.md)

## Estrutura do projeto

```
Laboratorio/
├── agentes/                    # Prompts e regras de cada agente
├── memoria/                    # Memória compartilhada (todos)
│   ├── decisoes.md
│   ├── aprendizados.md
│   ├── agentes.md
│   ├── projetos.md
│   └── ronaldo_maestro/        # Memória estratégica (orquestrador)
├── contexto/                   # Verdade do momento
│   └── contexto_global.md
├── tasks/                      # Fila de trabalho (6 estados)
│   ├── backlog.md
│   ├── planejando.md
│   ├── executando.md
│   ├── aguardando.md
│   ├── concluidas.md
│   └── arquivado.md
├── logs/                       # Linha do tempo de eventos
│   └── eventos.md
├── workflows/                  # Processos do ecossistema
│   ├── pipeline_operacional.md # Fluxo contínuo do Ronaldo Maestro
│   ├── onboarding.md
│   └── fluxo_agentes.md
├── backend/                    # Runtime Python + CrewAI
├── dashboard/
├── frontend/
└── docs/                       # Documentação técnica longa
```

## Memória: compartilhada vs estratégica

| | Memória compartilhada | Memória estratégica (Ronaldo) |
|---|------------------------|-------------------------------|
| **Onde** | `memoria/*.md` + `memoria/ronaldo_maestro/` (subpasta separada) | `memoria/ronaldo_maestro/*.md` |
| **Quem usa** | **Todos** os agentes | **Ronaldo Maestro** (prioritário) |
| **Conteúdo** | Decisões do dia a dia, aprendizados, projetos, estado dos agentes | Objetivos de longo prazo, decisões críticas, mapa de delegação, histórico de orquestração, regras do ecossistema |
| **Exemplo** | "API de estoque usa planilha até MVP" | "Prioridade do trimestre é SaaS low ticket" |

**Regra prática:** se qualquer agente precisa saber → `memoria/decisoes.md`, `aprendizados.md`, etc. Se só muda **como coordenar** o ecossistema → pasta do Ronaldo.

Arquivos compartilhados:

| Arquivo | Função |
|---------|--------|
| `memoria/decisoes.md` | Decisões operacionais visíveis a todos |
| `memoria/aprendizados.md` | O que funcionou / falhou |
| `memoria/agentes.md` | Quem existe e quando acionar |
| `memoria/projetos.md` | Portfólio e status (`PROJ-XXX`) |

Arquivos estratégicos (Ronaldo): `contexto_estrategico.md`, `decisoes_criticas.md`, `mapa_dos_agentes.md`, `historico_de_orquestracao.md`, `regras_do_ecossistema.md`.

## Pastas operacionais

### `contexto/`

**Verdade do momento** — foco atual, prioridades e restrições. Leitura obrigatória no início de sessão.

- `contexto_global.md` — alinhamento rápido de todo o ecossistema

Complementa (não substitui) `memoria/ronaldo_maestro/contexto_estrategico.md`, que é visão de longo prazo.

### `tasks/`

**Fila de trabalho** — Kanban em markdown, gerido pelo Ronaldo Maestro.

| Arquivo | Estado |
|---------|--------|
| `backlog.md` | A fazer |
| `planejando.md` | Ronaldo define plano e delegação |
| `executando.md` | Em execução (máx. 3 WIP) |
| `aguardando.md` | Bloqueada |
| `concluidas.md` | Concluída |
| `arquivado.md` | Histórico inativo |

IDs: `TASK-XXX`. Estrutura padrão e transições: [workflows/pipeline_operacional.md](workflows/pipeline_operacional.md).

### `logs/`

**Linha do tempo** — eventos, marcos, erros, orquestrações (resumo). Detalhe de ciclo longo fica no histórico do Ronaldo.

### `workflows/`

**Como operar** o ecossistema.

| Arquivo | Função |
|---------|--------|
| `pipeline_operacional.md` | Fluxo contínuo do Ronaldo: contexto → memória → delegação → registro |
| `fluxo_agentes.md` | Handoff entre Juarez, Dev e Caio |
| `onboarding.md` | Primeira sessão, novo projeto ou agente |

### `agentes/`

Definições completas (personalidade, formato de resposta, instrução de sistema).

### `backend/`

Runtime **Python + CrewAI** para orquestração programática. Ver [backend/README.md](backend/README.md).

### `dashboard/` · `frontend/` · `docs/`

Código de produto e documentação técnica extensa (ADRs, setup). Fatos operacionais curtos ficam em `memoria/` e `contexto/`, não em `docs/`.

## Ciclo operacional (resumo)

Documento completo: [workflows/pipeline_operacional.md](workflows/pipeline_operacional.md).

1. **Entrada** — Vitor define objetivo → `tasks/backlog.md` ou `./run.sh orquestrar`
2. **Contexto + memória** — Ronaldo lê `contexto/` + `memoria/`
3. **Priorização** — ordena fila; escala se urgente
4. **Delegação** — `planejando` → `executando` → especialista (Juarez / Dev / Caio)
5. **Consolidação** — Ronaldo nas 6 seções padrão
6. **Registro** — `logs/eventos.md`, `historico_de_orquestracao.md`, decisões/aprendizados
7. **Acompanhamento** — `concluidas` → próximo `TASK-XXX` ou `arquivado`

## Como começar

1. Leia [workflows/onboarding.md](workflows/onboarding.md).
2. Atualize [contexto/contexto_global.md](contexto/contexto_global.md) com seu foco atual.
3. Coloque a próxima ação em [tasks/backlog.md](tasks/backlog.md).
4. Para pedidos amplos, acione **Ronaldo Maestro** (`agentes/ronaldo_maestro.md`).
5. Backend: `cd backend` → venv → `pip install -r requirements.txt` → ver README do backend.
