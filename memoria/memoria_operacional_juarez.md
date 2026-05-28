# Memória operacional — Juarez

**Escopo:** médio (semanas / projetos em curso)  
**Dono:** Juarez (Ronaldo audita e pode consolidar em memória compartilhada)

---

## Função

Processos, rotinas, gargalos, KPIs operacionais e padrões de execução — o que mantém a operação rodando no prazo.

---

## O que registrar aqui

- Fluxos operacionais por projeto (ex.: entrega pós-venda TASK-001)
- Gargalos recorrentes e correções aplicadas
- KPIs operacionais e metas
- Checklists e rotinas aprovadas
- Desperdícios detectados e eliminados

---

## Template — processo operacional

```markdown
### [PROJ/TASK] — [Nome do processo]
- **Entrada:**
- **Passos:** (numerados)
- **Dono:**
- **SLA:**
- **KPI:**
- **Última revisão:**
```

---

## Projetos / TASKs ativos

### TASK-001 — Atendimento WhatsApp v0 (pré-fechamento)

- **Entrada:** lead clicou CTA na landing e mandou mensagem no WhatsApp
- **Passos:**
  1. **Responder em até 2h** (Caio) — usar script de primeira resposta
  2. **Qualificar** (Caio) — confirmar interesse, explicar o que inclui (página + publicação + 1 ajuste)
  3. **Fechar manualmente** (Caio) — enviar PIX/chave; aguardar comprovante
  4. **Registrar venda** (Juarez) — nome, WhatsApp, data pagamento, valor em planilha/nota TASK-001
  5. **Handoff operação** (Juarez → Dev) — acionar checklist de entrega abaixo
- **Dono:** Caio (conversa + fechamento) · Juarez (registro + handoff)
- **SLA:** primeira resposta ≤ 2h · fechamento ≤ 24h após interesse qualificado
- **KPI:** % leads respondidos no prazo · % conversas → pagamento
- **Última revisão:** 2026-05-28 (Rodada 3 — v0 WhatsApp only)

---

### TASK-001 — Entrega pós-fechamento (pós-pagamento)

- **Entrada:** pagamento confirmado (PIX manual v0)
- **Passos:**
  1. **Coletar dados** (Juarez) — nome, serviços, cidade, WhatsApp, 3–5 fotos de obra
  2. **Aplicar template** (Dev) — personalizar copy e imagens no HTML
  3. **Publicar URL** (Dev) — deploy cliente (subpasta ou domínio simples)
  4. **Entregar ao cliente** (Juarez) — enviar link + instruções de divulgação por WhatsApp
  5. **Ajuste** (Dev + Juarez) — 1 rodada em até 48h após entrega do link
- **Dono:** Juarez (fluxo + cliente) · Dev (template + publicação)
- **SLA:** 5 dias úteis (pagamento → página no ar)
- **KPI:** % entregas no prazo · NPS informal pós-entrega (sim/não satisfeito)
- **Última revisão:** 2026-05-28 (Rodada 3 — E4)

---

## Gargalos conhecidos

| Gargalo | Impacto | Mitigação |
|---------|---------|-----------|
| Escopo da página indefinido | Atraso entrega | Template fixo 1 página (TASK-001) |
| Fechamento manual v0 | Lead esfria | SLA resposta 2h + follow-up Caio D+1 |
| Falta número WA real na landing | CTA quebrado | Vitor configura antes do deploy |
| Falta gateway pagamento | Sem checkout automático | PIX manual v0; MP na v1 |

---

## Registro

### 2026-05-28 — TASK-003 snapshot dashboard (Juarez E4)

- **Validação:** métricas claras; seção 0 auto não interfere CRM/TASK manual
- **Recomendação:** Ronaldo mantém gargalos/bloqueios manual (seções 7–8)
- **Veredito:** aprovado para operação

### 2026-05-28 — E4 TASK-001 entregue (Rodada 3)

Dois fluxos separados: **pré-fechamento** (WhatsApp) e **pós-pagamento** (entrega). v0 não depende de Mercado Pago.
