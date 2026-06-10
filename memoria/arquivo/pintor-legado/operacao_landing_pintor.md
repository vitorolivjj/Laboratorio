# Operação Landing Page Pintor — Manual (Ronaldo)

> **🗄 ARQUIVO / PINTOR — LEGADO** (2026-06-10) · Piloto Landing Page Pintor encerrado — mantido só como histórico/aprendizado. **Não é mais foco** de nenhum agente. Novo posicionamento: negócios locais que perdem clientes por bagunça em captação, atendimento e comercial.

**Projeto:** PROJ-LP · **Prefixo tasks:** `LP-PINTOR-` · **CRM:** crm_landing_pintor
**Status:** ativo · **Ticket:** R$ 69 PIX · **Produção:** in-house `/previas/`

## 1. Lógica — funil invertido

Produz **primeiro**, entrega prévia, cobra ativação depois. **Nada é pedido ao lead** no Facebook — Donizete coleta tudo publicamente.

## 2. Equipe

| Frente | Agente | Responsabilidade |
|--------|--------|------------------|
| Captação | **Donizete** | Post-isca + garimpo FB · stalk · CRM |
| Produção | **Loide + Dev** | Curadoria mídia · build `/previas/` · Juarez QA |
| Venda | **Caio** | WhatsApp · R$ 69 PIX |
| Orquestração | **Ronaldo** | Plano · auditoria · KPIs |

**Separação:** Facebook = só captação. Venda = só WhatsApp (Caio).

## 3. Captação (Donizete) — ATIVA

**Plano:** [plano_atuacao_donizete_lp.md](plano_atuacao_donizete_lp.md) · Task **LP-PINTOR-001**

- **Grupos:** qualquer grupo **genérico** (classificados, bairro, compra/venda, serviços) — **não** precisa ser grupo de pintores
- **Região:** vem do **perfil do lead** (cidade que ele atende) — sem cidade fixa de operação
- **Meta sprint:** **10 leads** (001: 5 + 001B: 5) · produção paralela **LP-PINTOR-009**/lead
- Canal A post-isca · Canal B garimpo · anti-ban · stalk → `captura/`

## 4. Qualificação

✅ Indicação (Canal A) · ✅ autopromoção com fotos (Canal B) · ✅ WhatsApp público · ❌ sem obra/contato

## 5. CRM

**Pipeline:** `prospectado` → `pronto_pra_pagina` → `previa_no_ar` → `abordado` → `ativo` | `recusou`  
**Tags:** `indicacao` · `autopromocao`  
**Campos:** nome, WhatsApp, cidade (do lead), serviços, grupo origem, slug, pasta captura, link perfil

## 6. Tecnologia — in-house

[producao_lp_pintor.md](producao_lp_pintor.md) · modelo `/previas/exemplo-pintor/`

## 7. Esteira

1. Donizete → `pronto_pra_pagina` (captura completa)
2. Loide curadoria → Dev build → Juarez → `previa_no_ar`
3. Caio aborda · R$ 69 PIX
4. Vitor confirma PIX → `ativo: true` + rebuild (tarja off)
5. Não pagou 3–5 dias → takedown → `recusou`

## 8. Handoff produção

| Etapa | Quem | Entrega |
|-------|------|---------|
| Captação | Donizete | CRM + `captura/raw` + manifest |
| Mídia | Loide | `assets/` aprovados |
| Build | Dev | `/previas/{slug}/` |
| QA | Juarez | OK prévia |
| Venda | Caio | WhatsApp |

## 9. Ativação

`ativo: true` no JSON + CRM → rebuild → mesma URL, tarja off.

## 10. Venda

[playbook_comercial_lp_pintor.md](../caio_manteiga/playbook_comercial_lp_pintor.md) · `lp_leads.py`

## 11. KPIs

**Vitrine:** 1/1 ✓ Stephanie. **Captação:** meta **10** `pronto_pra_pagina`. Métrica escala = taxa ativação.
