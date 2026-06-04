# ADR 0001 — Orquestração: CrewAI e LangGraph

- **Status:** Aceito
- **Data:** 2026-06-04
- **Contexto da Fase 7.1** (plano de refatoração): "escolher um framework de orquestração".

## Contexto

Hoje convivem **dois** frameworks de orquestração de agentes:

**CrewAI — a fundação embutida.** Usado por:
`crews/orchestrator.py` (orquestrador hierárquico Ronaldo + especialistas),
`agents/builder.py` (`build_agent`), `agents/llm_config.py` (patch do LLM),
`tools/base.py` (a **classe base das ferramentas** é a `BaseTool` do CrewAI),
`ops/autopilot.py` (`_advance_task` roda uma crew por task),
`whatsapp/caio_handler.py` e `owner.py` (respostas). Toda a camada de
agentes/ferramentas/LLM é CrewAI.

**LangGraph — caminho isolado e controlado.** `graph/` (`pilot.py`,
`commercial.py`, `runner.py`) — `StateGraph` com **`cost_gate`** (trava de custo
com aprovação) e **checkpoint SQLite** (resumível). Chamado por dois pontos:
CLI (`graph-pilot`, `graph-run`) e `autonomy/executor.py` (ação `run_graph_pilot`).

**A sobreposição real é estreita:** ambos sabem "rodar um agente numa task"
(autopilot = CrewAI; graph-pilot = LangGraph). Fora isso, fazem coisas diferentes.

## Decisão

**Não unificar à força em um só framework. Manter os dois, com fronteira clara —
e impedir a sobreposição de crescer.**

| Use **CrewAI** quando… | Use **LangGraph** quando… |
|---|---|
| Raciocínio **multi-agente** com delegação (Ronaldo coordena Juarez/Dev/Caio/Donizete) | Pipeline **determinístico** de uma task (passos fixos) |
| Resposta conversacional de um agente (Caio no WhatsApp) | Precisa de **trava de custo** (`cost_gate`) antes de gastar |
| Uso de **ferramentas** (registry atual) | Precisa **resumir** de onde parou (checkpoint) |

Regra: **execução de task com controle de custo/resumível → LangGraph.**
**Coordenação/raciocínio de vários agentes → CrewAI.**

## Por que não arrancar um

- **Arrancar CrewAI** = reescrever agents, tools, builder, autopilot, orquestrador e
  os handlers de WhatsApp. Semanas de trabalho, muda comportamento dos agentes
  (saída do LLM), **não verificável** sem rodadas reais. Risco alto, valor incerto.
- **Arrancar LangGraph** = perder `cost_gate` + checkpoint, que são justamente o que
  falta no caminho CrewAI. Andar para trás.

Para um piloto pequeno, o custo de unificar supera o ganho. O problema real não é
"ter dois frameworks" — é **não ter fronteira**, deixando a sobreposição crescer.

## Caminho incremental (quando fizer sentido)

1. **Documentar a fronteira** (esta tabela) no README do backend — feito aqui.
2. **Resolver a única sobreposição:** o `autopilot._advance_task` roda uma crew
   CrewAI por task **sem trava de custo**. Migrá-lo para chamar o
   `graph.runner.run_pilot` (que já tem `cost_gate`) dá controle de custo ao
   piloto automático — **mudança localizada e de alto valor**, sem tocar no resto.
3. **Padronizar novas execuções de task em LangGraph** (cost_gate + checkpoint
   viram o default de qualquer fluxo novo "rode esta task").
4. **CrewAI fica congelado** no que faz bem (orquestração multi-agente e Caio);
   não cresce para novos tipos de execução de task.

## Consequências

- **Positivas:** decisão explícita; para de crescer "dois de tudo"; o ganho do
  LangGraph (custo/resumo) fica disponível onde importa; zero risco agora.
- **Negativas:** ainda há duas dependências de orquestração no `requirements`.
  Aceitável — elas cobrem necessidades distintas.

## Alternativas consideradas

- **Tudo em CrewAI:** perde cost_gate/checkpoint. Rejeitado.
- **Tudo em LangGraph:** reescrever toda a base de agentes/ferramentas. Rejeitado
  (custo/risco desproporcional para um piloto).
- **Status quo sem fronteira:** o que gerou a dívida. Rejeitado.
