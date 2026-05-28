# Aprendizados (memória compartilhada)

O que funcionou, o que falhou e o que **não repetir**. Todos podem contribuir; **Ronaldo audita** após cada entrega e registra aqui.

> Arquitetura: [docs/arquitetura-agentes.md](../docs/arquitetura-agentes.md)  
> Hipóteses formalizadas: `hipoteses_testadas.md`  
> Aprendizado de domínio persistente: memória do agente (`memoria_*_<agente>.md`)

## Como usar

- Frases curtas e acionáveis.
- Tag opcional: `#operacao` `#dev` `#comercial` `#orquestracao`
- Aprendizado estratégico de longo prazo pode ir também para `memoria/ronaldo_maestro/` se orientar coordenação.

## Template

```markdown
### YYYY-MM-DD — [Título curto]
- **Situação:**
- **Aprendizado:**
- **Ação daqui pra frente:**
- **Tags:**
```

---

## Aprendizados

### 2026-05-28 — Funil v0 em dois checklists #operacao #orquestracao

- **Situação:** v0 sem Mercado Pago — fechamento manual via PIX.
- **Aprendizado:** Separar checklist **pré-fechamento** (Caio/Juarez) de **pós-pagamento** (Juarez/Dev) evita confusão operacional.
- **Ação daqui pra frente:** Todo funil manual começa com fluxo de conversa antes do fluxo de entrega.
- **Tags:** `#operacao` `#orquestracao`

### 2026-05-28 — HTML estático v0 antes da copy final #dev #orquestracao

- **Situação:** E3 (Caio) pendente; Vitor pediu velocidade na landing.
- **Aprendizado:** Dev pode entregar HTML com placeholder alinhado ao wireframe; Caio refina copy depois sem bloquear estrutura.
- **Ação daqui pra frente:** Manter copy em blocos nomeados no HTML ou TASK-001 para troca rápida.
- **Tags:** `#dev` `#orquestracao`

### 2026-05-28 — Memória separada evita ruído

- **Situação:** Misturar contexto tático e estratégico confunde agentes.
- **Aprendizado:** Memória compartilhada (`memoria/*.md`) para fatos do dia a dia; memória do Ronaldo para orquestração.
- **Ação daqui pra frente:** Consultar `contexto/contexto_global.md` antes de executar tarefa nova.
- **Tags:** `#orquestracao`

---

<!-- Novas entradas acima desta linha -->
