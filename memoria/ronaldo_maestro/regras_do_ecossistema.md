# Regras do ecossistema

Princípios que todos os agentes devem respeitar. Ronaldo Maestro mantém e aplica na orquestração.

## Princípios gerais

1. **Simplicidade** — solução simples que funciona vence arquitetura pesada.
2. **Delegação** — tarefa especializada vai para o agente certo, não para o orquestrador.
3. **Contexto compartilhado** — antes de agir, ler memória relevante; depois de decidir, registrar o que for crítico.
4. **Baixo custo e velocidade** — MVP, free tier e automação prática quando couber.
5. **Sem retrabalho** — consolidar antes de redistribuir; não repetir briefing incompleto.
6. **Monetizável e útil** — priorizar o que gera resultado real para o Vitor.
7. **Autonomia do Ronaldo** — inicia e **delega** tasks (2026-05-31). Especialistas não executam sem briefing. Conferência e aprendizado obrigatórios — ver protocolo abaixo.
8. **Delegação exclusiva** — toda TASK passa por Ronaldo: delegar → executar → conferir → aprender.

## Protocolo Ronaldo (obrigatório)

Arquivo mestre: [memoria/ronaldo_maestro/protocolo_delegacao_conferencia.md](../memoria/ronaldo_maestro/protocolo_delegacao_conferencia.md)

| Gate | Regra |
|------|-------|
| → `executando` | Briefing Ronaldo por agente |
| → `concluído` | Auditoria Ronaldo preenchida |
| Pós-aprovação | Aprendizado em `aprendizados.md` + `evolucao_orquestracao.md` |

Evolução contínua: Ronaldo lê `evolucao_orquestracao.md` antes de cada nova delegação.

## Autonomia operacional (Ronaldo)

Concedida pelo Vitor em **2026-05-31**. Ronaldo **não precisa** de OK explícito para:

- Mover tasks entre `backlog` / `planejando` / `executando`
- Emitir briefings e acionar Dev, Loide, Juarez, Caio, Donizete
- Priorizar PROJ-002 (VitorOS) quando dependências estiverem claras

**Obrigatório mesmo com autonomia:**

- Registrar em `logs/eventos.md` ao iniciar ou repriorizar
- **Cadência sprint LP (2026-06-03):** **2 min** entre starts · **4** tasks simultâneas · captação crítica **30 min** sem progresso · Fase 2: [fase2_velocidade_lp.md](fase2_velocidade_lp.md).
- Não misturar infra PROJ-001 e PROJ-002
- Escalar ao Vitor: credenciais, custo, produção Lab, decisão estrutural, bloqueio externo
- **Fluxo total liberado (2026-05-31):** Ronaldo conduz backlog→concluído sem gate do Vitor; inicia novas tasks respeitando a cadência
- **WhatsApp Vitor** (`+5533999353242`): Caio envia alerta quando patrulha detectar bloqueio que exige dono
- Briefing antes de `executando` · **Auditoria antes de `concluído`** · **Aprendizado pós-aprovação**

| Camada | Local | Quem usa | Conteúdo |
|--------|-------|----------|----------|
| **Contexto global** | `contexto/contexto_global.md` | Todos | Foco do momento, prioridades, restrições |
| **Memória compartilhada** | `memoria/*.md` | Todos | Decisões, aprendizados, projetos, estado dos agentes |
| **Tarefas** | `tasks/` | Todos | Backlog, executando, concluídas |
| **Logs** | `logs/eventos.md` | Todos | Linha do tempo de eventos |
| **Workflows** | `workflows/` | Todos | Pipeline operacional, onboarding, fluxo entre agentes |
| **Pipeline** | `workflows/pipeline_operacional.md` | Ronaldo (obrigatório) | Fluxo contínuo: contexto → delegação → registro |
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

**Última revisão:** 2026-06-02 (governança contínua + gate captação Webflow)
