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

### 2026-05-31 — Fábrica Lab vs produto centralvitor #orquestracao #dev
- **TASK:** TASK-010, TASK-011, TASK-022
- **Situação:** Risco de misturar agentes/skills/UX no repo deployável.
- **Aprendizado:** Laboratório concentra orquestração; `centralvitor` só código. Loide mockups em `docs/ux/vitoros/`.
- **Muda no próximo briefing:** Sempre citar separação + skill correta (`dev-vitoros`, `loide-ux`).
- **Tags:** `#orquestracao` `#dev` `#ux`

### 2026-05-31 — Delegação Ronaldo antes de executar #orquestracao
- **TASK:** transversal
- **Situação:** Dev/Loide executaram direto na sessão Cursor sem briefing formal.
- **Aprendizado:** Toda TASK exige delegação + conferência Ronaldo — mesmo com autonomia operacional.
- **Muda no próximo briefing:** Protocolo em `protocolo_delegacao_conferencia.md`; backfill auditoria retroativa.
- **Tags:** `#orquestracao`

### 2026-05-31 — Supabase Site URL = domínio prod #dev
- **TASK:** TASK-010
- **Situação:** Links de e-mail auth quebravam (redirect localhost).
- **Aprendizado:** Configurar Site URL e Redirect URLs no Supabase antes de validar auth com Vitor.
- **Muda no próximo briefing:** Checklist deploy auth inclui URL config.
- **Tags:** `#dev`

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
