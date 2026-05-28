# Workflow — Onboarding

Como **iniciar** um novo projeto, agente ou ciclo de trabalho no ecossistema.

## Quando usar

- Novo projeto no portfólio
- Novo agente em `agentes/`
- Novo colaborador humano usando o Laboratório
- Reinício após pausa longa

## Checklist — Novo projeto

1. [ ] Registrar em `memoria/projetos.md` (ID `PROJ-XXX`)
2. [ ] Atualizar `contexto/contexto_global.md` (foco/prioridades se relevante)
3. [ ] Criar tarefas iniciais em `tasks/backlog.md`
4. [ ] Se estratégico, Ronaldo atualiza `memoria/ronaldo_maestro/contexto_estrategico.md`
5. [ ] Registrar marco em `logs/eventos.md`

## Checklist — Novo agente

1. [ ] Criar `agentes/nome_agente.md` (papel, regras, formato de resposta)
2. [ ] Adicionar linha em `memoria/agentes.md`
3. [ ] Atualizar `memoria/ronaldo_maestro/mapa_dos_agentes.md`
4. [ ] Se usar CrewAI: registrar em `backend/src/laboratorio/config.py` (`AGENT_FILES`)
5. [ ] Documentar em `workflows/fluxo_agentes.md` se mudar delegação padrão

## Checklist — Nova sessão (qualquer agente)

1. [ ] Ler `contexto/contexto_global.md`
2. [ ] Ler `memoria/decisoes.md` (últimas entradas)
3. [ ] Ver `tasks/` (backlog, executando, aguardando)
4. [ ] Especialista: ler seu `.md` em `agentes/`
5. [ ] Ronaldo: ler [pipeline_operacional.md](pipeline_operacional.md) + `memoria/ronaldo_maestro/`

## Tempo alvo

- Onboarding de sessão: **< 2 min** de leitura
- Onboarding de projeto: **< 15 min** de documentação inicial

## Responsável

- **Humano (Vitor):** define objetivo e prioridade
- **Ronaldo Maestro:** valida alinhamento e distribui
- **Dev:** estrutura técnica no repo quando necessário
