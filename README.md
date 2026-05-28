# Laboratório

Ambiente de testes de IA, automações e desenvolvimento de software.

## Estrutura do projeto

```
Laboratorio/
├── agentes/    # Agentes de IA e automações inteligentes
├── dashboard/  # Painéis e visualizações de dados
├── backend/    # APIs, serviços e lógica de servidor
├── frontend/   # Interfaces web e aplicações cliente
└── docs/       # Documentação do projeto
```

## Pastas

### `agentes/`

Código e configuração de **agentes de IA**: prompts, skills, fluxos autônomos, integrações com LLMs e automações que tomam decisões ou executam tarefas em nome do sistema.

Use esta pasta para experimentos com Cursor agents, bots, pipelines de IA e orquestração de tarefas.

### `dashboard/`

**Painéis e dashboards** para monitoramento, métricas e visualização de dados. Inclui gráficos, tabelas, KPIs e telas de acompanhamento operacional.

Pode consumir APIs do `backend/` ou fontes de dados externas.

### `backend/`

**Servidor e APIs**: endpoints REST/GraphQL, regras de negócio, acesso a banco de dados, autenticação, jobs em background e integrações com serviços externos.

É a camada que expõe dados e operações para o `frontend/` e, quando necessário, para o `dashboard/`.

### `frontend/`

**Interface do usuário**: aplicações web (ou mobile, se aplicável), componentes de UI, rotas, estado da aplicação e chamadas às APIs do backend.

Tudo que o usuário final vê e interage fica aqui.

### `docs/`

**Documentação** do laboratório: arquitetura, decisões técnicas (ADRs), guias de setup, convenções de código, diagramas e notas de experimentos.

Mantenha aqui o que ajuda a entender e evoluir o projeto sem precisar ler o código-fonte.

## Como começar

1. Escolha a pasta do experimento ou feature que vai desenvolver.
2. Consulte `docs/` para convenções e contexto, quando existirem.
3. Conecte `frontend/` e `dashboard/` ao `backend/` via APIs definidas no backend.
4. Use `agentes/` para fluxos que dependem de IA ou automação inteligente.
