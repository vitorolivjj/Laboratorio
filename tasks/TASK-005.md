# TASK-005 — Revisão Estratégica dos Modelos dos Agentes

**ID:** TASK-005  
**Projeto:** PROJ-001 (Laboratório multiagente)  
**Status:** `concluido` (E6 ✅ · validação operacional §4.3 pendente)  
**Prioridade:** alta  
**Criada em:** 2026-05-30  
**Atualizada em:** 2026-05-30  

> Task persistente · Modelo: [docs/modelo-task.md](../docs/modelo-task.md)  
> **Agente responsável:** ronaldo_maestro  
> **Bloqueio de execução:** alterações em `backend/.env` só após Vitor analisar o relatório junto com Dev

---

## Objetivo

Revisar a arquitetura de IA do Laboratório e garantir que cada agente utilize o **modelo mais adequado à sua função operacional**.

> O objetivo **NÃO** é economizar tokens.  
> O objetivo é **maximizar desempenho, qualidade das entregas e aderência ao papel de cada agente**.

---

## Contexto

### Configuração atual (`backend/.env`)

```env
MAESTRO_PROVIDER=openai
JUAREZ_PROVIDER=anthropic
DEV_PROVIDER=openai
CAIO_PROVIDER=anthropic
```

> **Nota:** `DONIZETE_PROVIDER` ainda não está definido no `.env` — incluir na análise.

### Observações dos testes (Vitor)

| Agente | Observação |
|--------|------------|
| **Caio** | Excelente desempenho em comunicação |
| **Juarez** | Boa capacidade analítica |
| **Dev** | Resultados funcionais, porém inferiores em qualidade visual e documentação |
| **Donizete** | Alguma mistura de contexto durante o garimpo |

### Regra principal

A decisão deve ser baseada em **desempenho operacional** do Laboratório.

- Não priorizar preferência pessoal  
- Não priorizar economia  
- **Priorizar resultado**

---

## Missão do Ronaldo

Realizar uma **análise crítica** da arquitetura atual.

Avaliar por agente:

- Função operacional
- Tipo de raciocínio exigido
- Volume de contexto necessário
- Necessidade de criatividade
- Necessidade de execução técnica
- Necessidade de relacionamento humano

---

## Critérios de avaliação por agente

### Ronaldo Maestro

Responsável por: coordenação, planejamento estratégico, priorização, gestão de TASKs, distribuição de trabalho.

**Avaliar:** qual modelo oferece melhor raciocínio estratégico e coordenação.

### Caio Manteiga

Responsável por: conversas, relacionamento, qualificação, conversão, atendimento.

**Avaliar:** qual modelo possui maior naturalidade e retenção de contexto para interação humana.

### Donizete Social

Responsável por: garimpo, pesquisa, captura, classificação de leads, descoberta de oportunidades.

**Avaliar:** qual modelo apresenta melhor custo-benefício para operações repetitivas e de classificação.

### Juarez

Responsável por: auditoria, revisão, controle de qualidade, identificação de falhas, conferência de processos.

**Avaliar:** qual modelo apresenta maior capacidade crítica.

### Dev

Responsável por: código, arquitetura, landing pages, integrações, documentação técnica, automações.

**Avaliar:** qual modelo apresenta melhor qualidade técnica para construção e manutenção de sistemas.

---

## Entregáveis

| ID | Entregável | Dono | Status |
|----|------------|------|--------|
| E1 | Relatório — configuração recomendada | Ronaldo | ✅ |
| E2 | Relatório — justificativa individual por agente | Ronaldo | ✅ |
| E3 | Relatório — ganhos esperados | Ronaldo | ✅ |
| E4 | Relatório — plano de migração | Ronaldo | ✅ |
| E5 | Decisão registrada em `memoria/decisoes.md` | Ronaldo | ✅ |
| E6 | Roteamento `.env` + `builder.py` + `llm-config` | Dev | ✅ |

**Relatório:** [TASK-005-relatorio-modelos.md](TASK-005-relatorio-modelos.md)

Status: ⬜ pendente · 🔄 em progresso · ✅ concluído · ❌ cancelado

---

## Critérios de aceite

- [x] Relatório cobre os 5 agentes (Ronaldo, Caio, Donizete, Juarez, Dev)
- [x] Cada recomendação tem justificativa ligada à **função operacional**, não a preferência ou custo
- [x] Plano de migração inclui critérios de validação pós-mudança
- [x] `.env` atualizado após implementação E6 (Vitor aprovou)
- [x] Ganhos esperados são mensuráveis ou observáveis

---

## Formato do relatório (E1–E4)

Salvar em: `tasks/TASK-005-relatorio-modelos.md` (ou seção dedicada neste arquivo)

### 1. Configuração recomendada

```env
MAESTRO_PROVIDER=...
CAIO_PROVIDER=...
DONIZETE_PROVIDER=...
JUAREZ_PROVIDER=...
DEV_PROVIDER=...
```

### 2. Justificativa individual

Por agente — por que aquele provider/modelo.

### 3. Ganhos esperados

- Melhoria de qualidade  
- Melhoria de produtividade  
- Redução de erros  
- Melhor aproveitamento dos recursos disponíveis  

### 4. Plano de migração

Se houver alteração recomendada:

- O que alterar  
- Como alterar  
- Como validar após a mudança  

---

## Registros por agente

### Ronaldo Maestro
- **Última ação:** Relatório E1–E4 entregue — [TASK-005-relatorio-modelos.md](TASK-005-relatorio-modelos.md)
- **Briefings emitidos:** —
- **Data:** 2026-05-30

### Dev
- **Última ação:** E6 — `llm_config.py`, `builder.py`, `.env.example`, comando `llm-config`
- **Entrega:** Roteamento LLM por agente implementado
- **Data:** 2026-05-30

---

## Auditoria

| Campo | Valor |
|-------|-------|
| **Veredito** | E6 implementado — validação §4.3 pendente |
| **Data** | 2026-05-30 |
| **Observações** | `./run.sh llm-config` confirma anthropic/sonnet nos 5 agentes |

---

## Histórico

| Data | Evento |
|------|--------|
| 2026-05-30 | E6 implementado — llm_config + builder + llm-config CLI |
| 2026-05-30 | Relatório E1–E4 entregue — recomendação anthropic/sonnet |
| 2026-05-30 | TASK criada — pedido Vitor: revisão estratégica modelos por agente |
