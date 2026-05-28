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

Fluxo detalhado: [workflows/fluxo_agentes.md](workflows/fluxo_agentes.md)  
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
├── tasks/                      # Fila de trabalho
│   ├── backlog.md
│   ├── executando.md
│   └── concluidas.md
├── logs/                       # Linha do tempo de eventos
│   └── eventos.md
├── workflows/                  # Processos do ecossistema
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

**Fila de trabalho** do ecossistema — Kanban em markdown.

| Arquivo | Estado |
|---------|--------|
| `backlog.md` | A fazer |
| `executando.md` | Em andamento (WIP baixo) |
| `concluidas.md` | Histórico |

IDs: `TASK-XXX`. Vincular a `PROJ-XXX` em `memoria/projetos.md`.

### `logs/`

**Linha do tempo** — eventos, marcos, erros, orquestrações (resumo). Detalhe de ciclo longo fica no histórico do Ronaldo.

### `workflows/`

**Como operar** — onboarding de projeto/agente/sessão e fluxo entre agentes.

### `agentes/`

Definições completas (personalidade, formato de resposta, instrução de sistema).

### `backend/`

Runtime **Python + CrewAI** para orquestração programática. Ver [backend/README.md](backend/README.md).

### `dashboard/` · `frontend/` · `docs/`

Código de produto e documentação técnica extensa (ADRs, setup). Fatos operacionais curtos ficam em `memoria/` e `contexto/`, não em `docs/`.

## Ciclo operacional (resumo)

1. Vitor define objetivo → `tasks/backlog.md`
2. Ronaldo lê `contexto/contexto_global.md` + memória estratégica → plano e delegação
3. Especialista executa → move tarefa para `executando.md` → `concluidas.md`
4. Registrar evento em `logs/eventos.md`; decisão relevante em `memoria/decisoes.md`
5. Aprendizado → `memoria/aprendizados.md`

## Como começar

1. Leia [workflows/onboarding.md](workflows/onboarding.md).
2. Atualize [contexto/contexto_global.md](contexto/contexto_global.md) com seu foco atual.
3. Coloque a próxima ação em [tasks/backlog.md](tasks/backlog.md).
4. Para pedidos amplos, acione **Ronaldo Maestro** (`agentes/ronaldo_maestro.md`).
5. Backend: `cd backend` → venv → `pip install -r requirements.txt` → ver README do backend.
