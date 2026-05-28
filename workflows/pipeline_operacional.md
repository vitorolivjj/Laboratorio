# Pipeline operacional — Ronaldo Maestro

Fluxo contínuo do ecossistema multiagente: do objetivo do Vitor até registro, acompanhamento e aprendizado.

**Orquestrador:** Ronaldo Maestro (`agentes/ronaldo_maestro.md`)  
**Execução programática:** `backend/orquestrador.py` → `./run.sh orquestrar`  
**Complementos:** [fluxo_agentes.md](fluxo_agentes.md) · [onboarding.md](onboarding.md)

---

## 1. Fluxo operacional do sistema

```mermaid
flowchart TD
  A[Entrada de objetivos] --> B[Leitura de contexto]
  B --> C[Consulta de memória]
  C --> D[Priorização]
  D --> E[Delegação]
  E --> F[Execução pelos especialistas]
  F --> G[Consolidação]
  G --> H[Registro]
  H --> I[Acompanhamento]
  I --> A
```

| Etapa | Responsável | Ação | Onde |
|-------|-------------|------|------|
| **Entrada de objetivos** | Vitor | Define pedido, meta ou problema | Conversa, `tasks/backlog.md`, `./run.sh orquestrar "..."` |
| **Leitura de contexto** | Ronaldo | Lê foco e restrições atuais | `contexto/contexto_global.md` |
| **Consulta de memória** | Ronaldo (+ especialistas se necessário) | Decisões, projetos, aprendizados, mapa de agentes | `memoria/*.md`, `memoria/ronaldo_maestro/` |
| **Priorização** | Ronaldo | Ordena fila, define WIP, escala se urgente | `tasks/backlog.md`, `contexto/contexto_global.md` |
| **Delegação** | Ronaldo | Escolhe agente(s), briefing, ordem | Plano + `tasks/planejando.md` → `executando.md` |
| **Consolidação** | Ronaldo | Une entregas, remove duplicação, 6 seções padrão | Resposta final |
| **Registro** | Ronaldo | Histórico, evento, decisão/aprendizado se couber | `historico_de_orquestracao.md`, `logs/eventos.md`, `memoria/` |
| **Acompanhamento** | Ronaldo / Vitor | Próximo passo, tarefas abertas, revisão de KPI | `tasks/`, `concluidas.md`, novo ciclo |

### Ciclo contínuo

1. Nada fica só na conversa — objetivo vira **TASK-XXX** no backlog quando for trabalho real.
2. Todo ciclo de orquestração gera **registro** (evento + histórico).
3. Tarefa concluída vai para **concluídas**; referência antiga vai para **arquivado** quando não for mais consultada.
4. Aprendizado e decisões alimentam a **próxima** entrada de objetivos.

---

## 2. Estados das tarefas

| Estado | Significado | Arquivo |
|--------|-------------|---------|
| **backlog** | A fazer, priorizado ou não | `tasks/backlog.md` |
| **planejando** | Ronaldo define plano, agentes e briefing | `tasks/planejando.md` |
| **executando** | Especialista em execução (WIP ativo) | `tasks/executando.md` |
| **aguardando** | Bloqueada: dependência, Vitor, dado externo | `tasks/aguardando.md` |
| **concluído** | Critério de pronto atendido | `tasks/concluidas.md` |
| **arquivado** | Encerrado sem relevância operacional atual | `tasks/arquivado.md` |

### Transições permitidas

```
backlog → planejando → executando → concluído → arquivado
                ↓           ↓
            aguardando ←────┘
                ↓
         executando | backlog (se cancelar escopo)
```

**Regra:** mover o bloco da tarefa entre arquivos (cortar/colar). Não duplicar a mesma `TASK-XXX` em dois arquivos.

**WIP máximo em `executando.md`:** 3 tarefas.

---

## 3. Regras do Ronaldo Maestro

### Quando delegar

| Situação | Delegar para |
|----------|----------------|
| Operação, processo, KPI, logística, obra | Juarez |
| Código, arquitetura, deploy, integração | Dev |
| Oferta, copy, funil, WhatsApp, conversão | Caio Manteiga |
| Pedido cruza 2+ domínios | Ronaldo orquestra; ordem típica: Juarez → Dev → Caio (ajustar ao caso) |
| Só priorização / organização | Ronaldo responde sem acionar especialista |

**Não delegar:** tarefa especializada que Ronaldo pode “chutar” sem agente — sempre passar ao dono do domínio.

### Quando registrar memória

| O quê | Onde |
|-------|------|
| Decisão do dia a dia (todos precisam saber) | `memoria/decisoes.md` |
| Aprendizado, erro, padrão aprovado | `memoria/aprendizados.md` |
| Mudança de direção do ecossistema | `memoria/ronaldo_maestro/decisoes_criticas.md` |
| Ciclo de orquestração completo | `memoria/ronaldo_maestro/historico_de_orquestracao.md` |
| Evento / marco / falha resumida | `logs/eventos.md` |
| Foco da semana alterado | `contexto/contexto_global.md` |

### Quando mover tarefas

| Momento | De → Para |
|---------|-----------|
| Objetivo aceito, vai planejar | backlog → planejando |
| Plano pronto, agente começou | planejando → executando |
| Falta input do Vitor ou dependência | executando → aguardando |
| Desbloqueou | aguardando → executando |
| Critério de pronto OK | executando → concluidas |
| Histórico antigo, sem ação | concluidas → arquivado (opcional, mensal) |

### Quando gerar relatório

- Fim de **ciclo de orquestração** (`orquestrar` ou sessão manual) → consolidação nas 6 seções + registro em histórico.
- **Semanal** (se Vitor pedir) → resumo: concluídas, bloqueios, próximas 3 prioridades do backlog.
- **Escalação de prioridade** → relatório curto: o que mudou, por quê, novo top 3.

### Quando escalar prioridade

- Objetivo do Vitor marcado como urgente.
- Bloqueio em `aguardando.md` > 48h sem dono.
- Risco de perda de receita ou operação parada (Juarez/Caio sinalizam).
- Ação: atualizar `contexto/contexto_global.md` + mover tarefa ao topo do backlog + informar Vitor.

### Como consolidar respostas

1. Ler **todas** as entregas dos especialistas (não pedir “aguardar retorno” se já executaram).
2. Remover repetição; manter só o acionável.
3. Entregar as **6 seções** padrão (objetivo → agentes → plano → tabela → consolidação → próximo passo).
4. Próximo passo = **uma** ação concreta + `TASK-XXX` sugerida se faltar.
5. Validar contra [critérios de qualidade](#4-critérios-de-qualidade) abaixo.

---

## 4. Critérios de qualidade

Toda entrega consolidada pelo Ronaldo deve ser avaliada nestes eixos:

| Critério | Pergunta |
|----------|----------|
| **Objetividade** | Dá para executar sem reinterpretar? |
| **Aplicabilidade** | Resolve o objetivo do Vitor? |
| **Simplicidade** | É a solução mais simples que funciona? |
| **Monetização** | Há caminho claro para receita ou valor? |
| **Baixo custo operacional** | Evita ferramenta/custo desnecessário? |
| **Velocidade de execução** | Próximo passo alcançável em curto prazo? |

**Reprovação:** texto vago, “aguardar análises”, arquitetura pesada sem MVP, promessa sem teste, oferta complexa.

---

## 5. Estrutura padrão das tasks

Toda `TASK-XXX` usa este bloco (copiar para backlog e mover entre arquivos):

```markdown
### TASK-XXX — [Título]
- **Objetivo:** (uma frase — resultado de negócio)
- **Contexto:** (links: PROJ-XXX, decisões, restrições)
- **Prioridade:** alta | media | baixa
- **Agente responsável:** ronaldo_maestro | juarez | dev | caio_manteiga
- **Status:** backlog | planejando | executando | aguardando | concluido | arquivado
- **Dependências:** TASK-YYY | aguardando Vitor | nenhuma
- **Resultado esperado:** (critério de pronto mensurável)
- **Criada em:** YYYY-MM-DD
- **Atualizada em:** YYYY-MM-DD
```

---

## 6. Fluxo de aprendizado

| Tipo | Registrar em | Quando |
|------|------------|--------|
| **Erros** | `memoria/aprendizados.md` (tag `#erro`) | Falha de processo, bug, orquestração ruim |
| **Padrões aprovados** | `memoria/aprendizados.md` (tag `#padrao`) | Fluxo que funcionou e deve repetir |
| **Melhorias** | `memoria/aprendizados.md` (tag `#melhoria`) | Otimização sem mudar direção |
| **Decisões críticas** | `memoria/ronaldo_maestro/decisoes_criticas.md` | Impacto multiagente ou estratégico |
| **Decisões operacionais** | `memoria/decisoes.md` | Impacto tático, todos os agentes |

Template rápido (aprendizado):

```markdown
### YYYY-MM-DD — [Título] #erro|#padrao|#melhoria
- **Situação:**
- **Aprendizado:**
- **Ação daqui pra frente:**
```

---

## Checklist — Ronaldo em cada ciclo

- [ ] Li `contexto/contexto_global.md`
- [ ] Consultei `memoria/decisoes.md` e `projetos.md` (e estratégico se necessário)
- [ ] Priorizei / criei `TASK-XXX`
- [ ] Deleguei ao agente certo com briefing completo
- [ ] Consolidei com as 6 seções (sem “aguardar retornos” fantasmas)
- [ ] Registrei em `historico_de_orquestracao.md` + `logs/eventos.md`
- [ ] Atualizei status da tarefa nos arquivos corretos
- [ ] Aprendizado ou decisão registrado se relevante
- [ ] Próximo passo claro para o Vitor

---

**Última revisão:** 2026-05-28
