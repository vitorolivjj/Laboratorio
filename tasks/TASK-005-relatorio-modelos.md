# TASK-005 — Relatório: Revisão Estratégica dos Modelos dos Agentes

**Autor:** Ronaldo Maestro  
**Data:** 2026-05-30  
**Status:** `arquivado` (cancelada)
**Regra aplicada:** desempenho operacional > economia > preferência pessoal

---

## Sumário executivo

A configuração atual **funciona parcialmente** — Caio e Juarez em Anthropic entregam acima da média. Dev em OpenAI entrega código funcional com **qualidade visual e documentação abaixo do esperado**. Donizete sem provider definido e com **mistura de contexto** no garimpo.

**Recomendação principal:** padronizar arquitetura multi-provider com **Anthropic (Claude Sonnet)** para todos os agentes de raciocínio e relacionamento, e **implementar roteamento real no backend** — hoje as variáveis `*_PROVIDER` existem no `.env` mas **não são lidas** por `builder.py`.

**Mudanças propostas vs. atual:**

| Agente | Atual | Recomendado | Ação |
|--------|-------|-------------|------|
| Ronaldo | openai | anthropic | **Alterar** |
| Caio | anthropic | anthropic | Manter |
| Juarez | anthropic | anthropic | Manter |
| Dev | openai | anthropic | **Alterar** |
| Donizete | _(ausente)_ | anthropic | **Definir** |

---

## 1. Configuração recomendada

### Providers (`.env`)

```env
# API keys (já existentes)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Providers por agente
MAESTRO_PROVIDER=anthropic
CAIO_PROVIDER=anthropic
JUAREZ_PROVIDER=anthropic
DEV_PROVIDER=anthropic
DONIZETE_PROVIDER=anthropic

# Modelos por agente (novo — ver seção 4.1)
MAESTRO_MODEL=claude-sonnet-4-20250514
CAIO_MODEL=claude-sonnet-4-20250514
JUAREZ_MODEL=claude-sonnet-4-20250514
DEV_MODEL=claude-sonnet-4-20250514
DONIZETE_MODEL=claude-sonnet-4-20250514
```

### Reserva OpenAI (opcional, fase 2)

Manter `OPENAI_API_KEY` ativa para:

- Fallback se Anthropic indisponível
- Testes A/B pontuais (Dev em `gpt-4o` para código puro)

---

## 2. Justificativa individual

### Ronaldo Maestro — `anthropic` · Claude Sonnet

| Dimensão | Análise |
|----------|---------|
| **Função** | Coordenação, priorização, consolidação de 3 especialistas, decisão em divergências |
| **Raciocínio** | Estratégico, multi-perspectiva, síntese longa |
| **Contexto** | Alto — lê memória, TASKs, entregas de Juarez/Dev/Caio |
| **Criatividade** | Média — precisa decidir, não inventar |
| **Relacionamento** | Baixo — output interno/executivo |

**Por que mudar de OpenAI:** consolidação exige comparar nuances, cortar redundância e decidir conflitos. Caio e Juarez já performam bem em Anthropic — alinhar o orquestrador ao mesmo stack reduz inconsistência de tom e raciocínio entre delegação e consolidação.

**Por que Sonnet (não Opus):** Sonnet equilibra profundidade e latência para ciclos frequentes de orquestração. Opus reservar para revisões trimestrais ou TASKs estratégicas excepcionais.

---

### Caio Manteiga — `anthropic` · Claude Sonnet · **MANTER**

| Dimensão | Análise |
|----------|---------|
| **Função** | Conversas WhatsApp, abordagem, objeções, follow-up |
| **Raciocínio** | Empático, contextual, adaptativo |
| **Contexto** | Médio — histórico do lead, oferta, CRM |
| **Criatividade** | Alta — copy natural, tom humano |
| **Relacionamento** | **Crítico** |

**Evidência operacional:** Vitor reportou **excelente desempenho em comunicação** com configuração atual Anthropic.

**Decisão:** não alterar provider. Reforçar via skill `skills/caio/SKILL.md` e briefing curto por lead (TASK-006).

---

### Juarez — `anthropic` · Claude Sonnet · **MANTER**

| Dimensão | Análise |
|----------|---------|
| **Função** | Auditoria, SLA, conferência, identificação de falhas |
| **Raciocínio** | Crítico, checklist, evidência vs. critério |
| **Contexto** | Médio — TASK + entregáveis + critérios aceite |
| **Criatividade** | Baixa — precisa ser rigoroso |
| **Relacionamento** | Baixo |

**Evidência operacional:** **boa capacidade analítica** nos testes.

**Decisão:** manter Anthropic. Juarez beneficia do mesmo modelo que já provou capacidade de auditoria estruturada.

---

### Dev — `anthropic` · Claude Sonnet · **ALTERAR** (openai → anthropic)

| Dimensão | Análise |
|----------|---------|
| **Função** | Código, landing pages, CSS, documentação, automações |
| **Raciocínio** | Técnico + estético (UX/visual) |
| **Contexto** | Alto — repo, TASK, arquitetura existente |
| **Criatividade** | Média-alta — layout, copy técnica, README |
| **Execução técnica** | **Crítica** |

**Evidência operacional:** resultados **funcionais**, porém **inferiores em qualidade visual e documentação** com OpenAI atual.

**Hipótese:** Dev provavelmente rodando com tier inferior (ex.: `gpt-4o-mini` default) ou OpenAI fraco em prose/layout comparado a Claude para entregas mistas código+visual.

**Por que Anthropic Sonnet para Dev:**

- Site institucional (TASK recente) exige CSS refinado, hierarquia visual e docs legíveis — área onde Claude Sonnet consistentemente supera mini-tier OpenAI em entregas front-end.
- Documentação técnica (README, arquitetura) beneficia de prosa mais clara e estruturada.
- Código Python/shell continua forte em Sonnet para escopo do Laboratório.

**Alternativa se Vitor preferir manter OpenAI para Dev:** subir para `gpt-4o` explícito (nunca mini) — mas evidência operacional favorece **troca de provider**.

---

### Donizete Social — `anthropic` · Claude Sonnet · **DEFINIR** (novo)

| Dimensão | Análise |
|----------|---------|
| **Função** | Garimpo, classificação prestador/demanda, CRM, handoff |
| **Raciocínio** | Classificatório, regras explícitas (`lead_criteria.yaml`) |
| **Contexto** | Deve ser **baixo e escopado** — só post + critérios |
| **Criatividade** | Baixa — seguir taxonomia |
| **Volume** | Repetitivo, many-shot |

**Evidência operacional:** **mistura de contexto** durante garimpo (ex.: LEAD-001 classificado errado antes da v2).

**Causa provável (dupla):**

1. **Modelo/provider indefinido** — herda contexto genérico do runtime
2. **Prompt/contexto poluído** — briefing inclui mais do que o post + critérios

**Por que Anthropic Sonnet (e não Haiku):**

- Task pede maximizar desempenho, não economia
- Classificação errada gera custo operacional alto (Caio aborda lead errado)
- Sonnet segue instruções rígidas melhor que modelos genéricos quando briefing é curto

**Complemento obrigatório (não só modelo):** briefing Donizete deve conter **apenas** snippet do post + `lead_criteria.yaml` + formato CRM — nunca dump de memória completa.

**Fase 2 (após validação):** testar `claude-3-5-haiku` para Donizete se classificação ≥95% acurácia em 20 posts — só então considerar down-tier.

---

## 3. Ganhos esperados

### Melhoria de qualidade

| Área | Ganho esperado |
|------|----------------|
| **Dev** | Landing pages, CSS e README com nível visual/documental alinhado ao site institucional |
| **Ronaldo** | Consolidações mais coerentes com entregas Anthropic de Caio/Juarez |
| **Donizete** | Menos leads misclassificados; menos retrabalho de reclassificação |
| **Caio/Juarez** | Estabilidade — sem regressão |

### Melhoria de produtividade

- Menos rodadas de retrabalho visual (Dev)
- Menos correções pós-garimpo (Donizete → Caio)
- Ciclos `orquestrar` com menos divergência de tom entre agentes

### Redução de erros

| Erro observado | Mitigação |
|----------------|-----------|
| LEAD classificado errado | Donizete: Sonnet + briefing escopado |
| HTML funcional mas feio | Dev: Anthropic Sonnet |
| Consolidação genérica | Ronaldo: Anthropic Sonnet |

### Aproveitamento de recursos

- Duas API keys já disponíveis (OpenAI + Anthropic) — passa a usar Anthropic de forma **intencional** por agente
- OpenAI fica como reserva/fallback, não como default cego
- Variáveis `*_PROVIDER` deixam de ser decorativas após implementação no backend

---

## 4. Plano de migração

### 4.1 Pré-requisito — Dev implementa roteamento (TASK-005 E6)

**Problema detectado:** `backend/src/laboratorio/agents/builder.py` **não lê** `MAESTRO_PROVIDER`, `DEV_PROVIDER`, etc. Todos os agentes CrewAI usam o LLM default do CrewAI.

**O que alterar:**

| Arquivo | Mudança |
|---------|---------|
| `backend/src/laboratorio/agents/builder.py` | Ler `{AGENT}_PROVIDER` e `{AGENT}_MODEL` do `.env`; instanciar LLM correto por agente |
| `backend/.env.example` | Documentar todas as variáveis `*_PROVIDER` e `*_MODEL` |
| `backend/README.md` | Tabela provider/modelo por agente |

**Pseudocódigo:**

```python
def _llm_for_agent(agent_id: str):
    key = agent_id.upper().replace("_MAESTRO", "").replace("_MANTEIGA", "")
    # mapear ronaldo_maestro → MAESTRO, caio_manteiga → CAIO, etc.
    provider = os.getenv(f"{ENV_KEY}_PROVIDER", "anthropic")
    model = os.getenv(f"{ENV_KEY}_MODEL", default_model(provider))
    return build_llm(provider, model)
```

### 4.2 Fase 1 — Alterar `.env` (após aprovação Vitor)

```env
MAESTRO_PROVIDER=anthropic
DEV_PROVIDER=anthropic
DONIZETE_PROVIDER=anthropic
# CAIO e JUAREZ — sem mudança
```

Adicionar bloco `*_MODEL` conforme seção 1.

### 4.3 Fase 2 — Validar por agente

| Agente | Teste | Critério de sucesso |
|--------|-------|---------------------|
| **Ronaldo** | `./run.sh orquestrar "objetivo teste"` | CONSOLIDAÇÃO FINAL com decisões explícitas; zero frases proibidas |
| **Caio** | Revisar msg TASK-006 (Ramon) | Tom natural; sem tom robótico |
| **Juarez** | Auditar entrega TASK-003 | Checklist critério a critério |
| **Dev** | Refatorar 1 componente CSS institucional | Visual ≥ baseline Loide; README claro |
| **Donizete** | `./run.sh crm` com 5 posts mix | ≥4/5 classificação correta; zero handoff demanda→Caio |

### 4.4 Fase 3 — Briefing Donizete (independente de modelo)

Atualizar `social_executor` / skill Donizete:

- Input máximo: post + critérios + template CRM
- Proibir: contexto global, memória estratégica, outras TASKs

### 4.5 Rollback

Se regressão em qualquer agente após 3 testes:

1. Reverter apenas `{AGENT}_PROVIDER` no `.env`
2. Registrar em `memoria/aprendizados.md`
3. Não reverter agentes que passaram validação

### 4.6 Cronograma sugerido

| Dia | Ação |
|-----|------|
| D0 | Vitor aprova relatório |
| D1 | Dev implementa roteamento `builder.py` + `.env.example` |
| D2 | Aplicar `.env`; testes Ronaldo + Dev |
| D3 | Testes Donizete + Caio + Juarez |
| D4 | Registrar decisão E5; fechar TASK-005 |

---

## 5. Matriz de decisão (referência rápida)

```
                    Raciocínio estratégico ████████████ Ronaldo  → anthropic/sonnet
                    Relacionamento humano  ████████████ Caio     → anthropic/sonnet ✓
                    Auditoria crítica      ████████████ Juarez   → anthropic/sonnet ✓
                    Código + visual + docs ████████████ Dev      → anthropic/sonnet ↑
                    Classificação escopada ████████████ Donizete → anthropic/sonnet (novo)
```

---

## 6. O que NÃO fazer

- ❌ Alterar `.env` antes da implementação em `builder.py`
- ❌ Usar modelo mini/haiku na migração inicial (validar qualidade primeiro)
- ❌ Mudar Caio ou Juarez sem evidência de regressão
- ❌ Decidir por economia de tokens
- ❌ Aplicar mesmo briefing longo para Donizete e Ronaldo

---

## 7. Próximo passo (Vitor)

1. Revisar este relatório
2. Aprovar ou contestar item a item (especialmente Dev e Ronaldo)
3. Autorizar Dev → E6 (implementação + `.env`)
4. Ronaldo registra decisão em `memoria/decisoes.md` (E5)

---

**Versão:** 1.0 · **TASK:** TASK-005 · **Entregáveis:** E1 ✅ · E2 ✅ · E3 ✅ · E4 ✅ · E5 ⬜ · E6 ⬜
