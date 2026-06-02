# Operação Landing Page Pintor — Manual (Ronaldo)

**Projeto:** PROJ-LP · **Prefixo tasks:** `LP-PINTOR-` · **CRM:** crm_landing_pintor
**Status:** ativo (2026-05-31) · **Ticket:** R$ 69, pagamento único, PIX
**Papel do Ronaldo:** alinhar o plano, **delegar execuções**, **auditar** KPIs e saúde da conta.

## 1. Lógica — funil invertido

Produz **primeiro**, entrega a prévia, cobra a ativação depois. O pintor vê a página com nome e fotos dele → trata como dele → não ativar vira **perda**, não gasto. Custo de produção ~zero (template + host grátis) → R$ 69 é quase margem. **Nada é pedido ao lead** — todos os dados são coletados no Facebook; o lead só recebe o link pronto e decide ativar.

## 2. Equipe e delegação (regra de separação inquebrável)

| Frente | Agente | Responsabilidade |
|--------|--------|------------------|
| Captação | **Donizete Social** | Post-isca + garimpo no Facebook, qualificação, registro no CRM |
| Produção | **Loide (UX) + Dev** | Template Webflow + automação CRM→API · Juarez confere prévia |
| Venda | **Caio Manteiga** | Aborda no WhatsApp com a página pronta, fecha ativação R$ 69 |
| Orquestração/Auditoria | **Ronaldo** | Alinha plano, delega, audita taxa de ativação e saúde da conta FB |

**Separação:** Facebook = só captação. Venda só no WhatsApp (Caio), sem vínculo com o perfil de prospecção.

## 3. Captação (Donizete) — 2 canais

> **Gate (2026-06-02):** Donizete **só inicia captação após LP-PINTOR-007** — página oficial Webflow publicada. Até lá: zero posts.

- **Canal A — Post-isca (principal):** posta em grupos genéricos da cidade fingindo procurar pintor; a comunidade indica → lead já vem com selo de qualidade. Só monitora comentários e coleta dados.
- **Canal B — Garimpo passivo:** monitora pintores que postam os próprios trabalhos (demanda + sem presença digital).

**Regras anti-ban (NÃO tomar ban):**
- 1× por dia por grupo, **nunca** o mesmo grupo todo dia (rodízio de vários dias).
- Texto **sempre variado** (frase repetida = assinatura de bot).
- Intervalo aleatório entre posts: **40–120 min**, nunca de hora em hora.
- 3–5 posts/dia no início, grupos diferentes, janela humana (manhã/almoço/fim de tarde/noite). **Nada de madrugada.**
- Agir como humano entre posts (scrollar, curtir, comentar). **Sem burst.**

## 4. Qualificação — quem vira página

- ✅ Indicado por terceiros (Canal A) — prioridade máxima.
- ✅ Posta trabalhos com fotos boas e responde clientes (Canal B).
- ✅ Tem WhatsApp/telefone capturável.
- ❌ Descarta: nunca mostrou trabalho, perfil inativo, amador, sem contato.

## 5. CRM (crm_landing_pintor) — campos e pipeline

**Campos por lead:** nome, WhatsApp, cidade, bairros, serviços, fotos, quem indicou/grupo, link origem, slug Webflow, data prévia.
**Tag de origem:** `indicacao` (Canal A) ou `autopromocao` (Canal B).
**Pipeline:** `prospectado` → `pronto_pra_pagina` → `previa_no_ar` → `abordado` → `ativo` (ou `recusou`).

## 6. Tecnologia — Webflow (decisão final)

**Alugar a máquina pronta**, não construir em casa. Detalhes: [webflow_lp_pintor.md](webflow_lp_pintor.md)

- Premium ~US$ 25/mês · 20k páginas · subpath `dominio/slug-pintor`
- 1 template + coleção **Pintores** · 4 variantes de cor
- Publicar/despublicar item via API CMS (prévia/takedown sem rebuild)
- Vitrine fase 1 usou template in-house (`frontend/lp-pintor/`) — legado até migrar

## 7. A esteira (fluxo completo)

1. **Donizete** capta no Facebook → CRM (nome, cidade, bairros, serviços, fotos, WhatsApp, quem indicou). Status: *prospectado*.
2. Qualificou → *pronto_pra_pagina*.
3. **Automação (Loide+Dev):** CRM → IA copy → item Webflow publicado → **Juarez confere** → *previa_no_ar* (link + data).
4. **Caio** aborda WhatsApp · vende ativação R$ 69 PIX ([playbook](../caio_manteiga/playbook_comercial_lp_pintor.md)).
5. **Pagou** (Vitor confirma PIX) → *ativo* (tarja prévia off). **Não pagou 3–5 dias** → job despublica item → *recusou*.

## 8. Handoff Donizete → produção (fechado)

| Etapa | Quem | Entrega |
|-------|------|---------|
| Captação | **Donizete** | Nome, cidade, bairros, fotos galeria, WhatsApp, grupo, serviços brutos, variante de cor sugerida |
| Copy | **IA** | Headline, subtítulo, sobre, cards de serviço, depoimentos (se faltar) |
| Publicação | **Loide+Dev** | Script CRM → item Webflow publicado |
| QA | **Juarez** | Confere antes de `previa_no_ar` |
| Venda | **Caio** | WhatsApp · R$ 69 PIX |
| Ativação | **Vitor** | Confirma PIX → `Ativo` no CMS + CRM `ativo` |

## 9. Mecânica da ativação (fechado)

Prévia com tarja · **Ativar = só tira a tarja** (`Ativo = sim` no CMS + CRM `ativo`). Mesmo layout, mesma URL. Takedown = despublicar item Webflow.

## 10. Venda (Caio, WhatsApp) — playbook 5 etapas

**Playbook:** [playbook_comercial_lp_pintor.md](../caio_manteiga/playbook_comercial_lp_pintor.md)

1. Abertura sem link · 2. Entrega link · 3. Oferta R$ 69 · 4. PIX `financeiro@vitoroliv.com` · 5. Pós-venda (após Vitor confirmar)

**Código:** `lp_leads.py` + `caio_handler.py` · Webflow API (LP-PINTOR-007/008).

## 11. Escopo de alterações

| Incluso (grátis) | À parte (cobra) |
|------------------|-----------------|
| Trocar/adicionar foto | Nova seção |
| Ajustar texto | Logo / identidade visual |
| Mudar cor | Domínio próprio, várias páginas |
| Corrigir contato | Integração / formulário avançado |

Sem isso fechado, Loide vira refém de pedidos infinitos por R$ 69.

## 12. KPIs (Ronaldo audita)

**Vitrine jun/2026:** progresso em [crm/crm_landing_pintor.md](../../crm/crm_landing_pintor.md) — meta **1 ativo R$ 69** antes de escalar Donizete.

Métrica-chave = **taxa de ativação** (vendas ÷ páginas entregues). Também: leads qualificados/dia por origem, páginas produzidas/dia, receita, saúde da conta FB (posts/dia, restrições/bans). Se a conversão cair, o problema costuma ser **qualificação**, não preço.

**Painel:** case [docs/vitrine/caso-lp-pintor.md](../../docs/vitrine/caso-lp-pintor.md) · playbook [playbook_produto_low_ticket.md](../../memoria/playbook_produto_low_ticket.md)

## 13. Fluxo (cola rápida)

1. Donizete capta → CRM *prospectado* → *pronto_pra_pagina*.
2. Automação Loide: CRM → Webflow item → Juarez confere → *previa_no_ar*.
3. Caio aborda (template Meta ou janela 24h) → link → R$ 69 PIX.
4. Vitor confirma PIX → *ativo* · tarja off. Não pagou 3–5 dias → job takedown → *recusou*.
