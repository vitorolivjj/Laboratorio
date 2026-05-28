# Regras do ecossistema

Princípios que todos os agentes devem respeitar. Ronaldo Maestro mantém e aplica na orquestração.

## Princípios gerais

1. **Simplicidade** — solução simples que funciona vence arquitetura pesada.
2. **Delegação** — tarefa especializada vai para o agente certo, não para o orquestrador.
3. **Contexto compartilhado** — antes de agir, ler memória relevante; depois de decidir, registrar o que for crítico.
4. **Baixo custo e velocidade** — MVP, free tier e automação prática quando couber.
5. **Sem retrabalho** — consolidar antes de redistribuir; não repetir briefing incompleto.
6. **Monetizável e útil** — priorizar o que gera resultado real para o Vitor.

## Memória e contexto

| Camada | Local | Quem usa | Conteúdo |
|--------|-------|----------|----------|
| **Contexto global** | `contexto/contexto_global.md` | Todos | Foco do momento, prioridades, restrições |
| **Memória compartilhada** | `memoria/*.md` | Todos | Decisões, aprendizados, projetos, estado dos agentes |
| **Tarefas** | `tasks/` | Todos | Backlog, executando, concluídas |
| **Logs** | `logs/eventos.md` | Todos | Linha do tempo de eventos |
| **Workflows** | `workflows/` | Todos | Onboarding e fluxo entre agentes |
| **Memória estratégica** | `memoria/ronaldo_maestro/` | Ronaldo (prioritário) | Coordenação, decisões críticas, histórico de orquestração |

Ronaldo registra aqui o que orienta **coordenação e fluxo**. Fatos operacionais vão em `memoria/decisoes.md` (compartilhado); espelhar em `decisoes_criticas.md` só se mudar direção do ecossistema.

## Segurança e limites (todos)

- Não expor credenciais, tokens ou senhas
- Não alterar produção sem confirmação (Dev / operações)
- Não prometer o que não foi validado
- Não gerar spam nem promessas falsas (Caio Manteiga)
- Não apagar arquivos sem aviso (Dev)

## Qualidade de entrega

- Cada agente segue seu formato de resposta definido em `agentes/*.md`
- Ronaldo consolida em: objetivo → agentes → plano → distribuição → consolidação → próximo passo
- Decisões que mudam direção vão em `decisoes_criticas.md`

## Atualização deste arquivo

Só alterar regras com registro em `decisoes_criticas.md` quando a mudança for estrutural.

**Última revisão:** 2026-05-28 (infra operacional: contexto, tasks, logs, workflows)
