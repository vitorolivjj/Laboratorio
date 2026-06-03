# Fase 2 — Velocidade LP (fora do escopo sprint 2026-06-03)

Documento de escopo para a **segunda onda** de aceleração, após o pacote sprint (patrulha 30 min, WIP 4, tasks fatiadas, `lp_publish_lead.py`, modo sprint Donizete).

---

## 1. Painel Maestro — card Captação LP

**Problema:** KPI de captação só via WhatsApp `captura` ou CLI; overview já expõe `lp_capture` no JSON mas o frontend não renderiza.

**Entregáveis:**

- Card no [frontend/painel-maestro/app.js](../../frontend/painel-maestro/app.js): `pronto/meta`, `prospectado`, pastas, minutos desde start, alertas ativos
- Sparkline opcional em `logs/maestro_metrics.jsonl` (leads pronto/dia)
- Cor de alerta se `capture_zero_30m` ativo no último snapshot

**Dependências:** deploy API com `overview.lp_capture` populado (já em `maestro.py`).

---

## 2. Autopilot orientado a PROJ-LP

**Problema:** [autopilot.py](../../backend/src/laboratorio/ops/autopilot.py) — `AUTOPILOT_MAX_TASKS=1`, cooldown 30 min — lento para fila de LP-PINTOR-009.

**Entregáveis:**

- Perfil `AUTOPILOT_PROFILE=lp_sprint`: max 2 tasks/ciclo, cooldown 10 min, só tasks `LP-PINTOR-*` + agentes loide/dev/donizete
- Não promover backlog→executando automaticamente (só sugerir no trace) — evita conflito com cadência humana
- Flag `AUTOPILOT_ENABLED` explícita na VPS (hoje default ligado — revisar custo)

**Risco:** custo LLM · ações incorretas — manter Fase 0 WA para mensagens cliente.

---

## 3. LP-PINTOR-008 completo — publish + takedown

**Problema:** [lp_publish_lead.py](../../scripts/lp_publish_lead.py) só build local; falta rsync VPS, CRM hook e expiração prévia.

**Entregáveis:**

- CLI `python -m laboratorio lp-publish <slug>`: build + rsync + healthcheck URL
- Job diário: prévias `previa_no_ar` + 3–5 dias sem PIX → takedown + CRM `recusou`
- Webhook ou arquivo fila `logs/lp_publish_queue.json` alimentado quando CRM muda para `pronto_pra_pagina`
- Integração Juarez: checklist automático (links 200, tarja prévia, WhatsApp no HTML)

---

## 4. CRM → fila de produção automática

**Problema:** Donizete atualiza CRM manualmente; Ronaldo cria LP-PINTOR-009 à mão.

**Entregáveis:**

- Watcher em `crm/crm_landing_pintor.md` ou API interna: status `pronto_pra_pagina` → cria `LP-PINTOR-009-{slug}` no backlog com briefing pré-preenchido
- `record_lead_pronto_event()` já existe — estender para `tasks_store.create_task`
- Notificar Loide no trace / WhatsApp operacional (não cliente)

---

## 5. Caio proativo (LP-PINTOR-006)

**Problema:** Template Meta `abertura_pintor_contato` — erro 132001; só inbound/janela 24h.

**Entregáveis:**

- Vitor aprova template no Business Manager
- Caio: ao `previa_no_ar`, envio template + link prévia (playbook)
- Métrica: tempo abordado → ativo

**Bloqueio externo:** Meta — não automatizável pelo Lab até aprovação.

---

## 6. Memória / Donizete assistido

**Entregáveis opcionais:**

- Agente Donizete com tool `register_lead_crm` + upload manifest schema
- Resumo diário automático em `logs/donizete_captura.md` com posts/grupos (input manual ou planilha)
- A/B de copy post-isca (tags CRM)

---

## 7. Priorização sugerida Fase 2

| # | Item | Impacto | Esforço |
|---|------|---------|---------|
| 1 | LP-PINTOR-008 publish VPS + fila | Alto | Médio |
| 2 | Painel card captação | Médio | Baixo |
| 3 | CRM → task 009 auto | Alto | Médio |
| 4 | LP-PINTOR-006 template Meta | Alto | Baixo (Vitor) |
| 5 | Autopilot perfil LP | Médio | Médio |
| 6 | Donizete tools | Médio | Alto |

---

## Critérios de “Fase 2 concluída”

- Lead `pronto_pra_pagina` → prévia no ar em **< 4h** média sem intervenção manual Dev
- 10 leads sprint com visibilidade no painel e zero alerta `capture_zero_30m` após 2h do 1º post
- Taxa ativação LP medida em dashboard (funil CRM → ativo)

**Ref sprint atual:** [plano_atuacao_donizete_lp.md](plano_atuacao_donizete_lp.md) · [operacao_landing_pintor.md](operacao_landing_pintor.md)
