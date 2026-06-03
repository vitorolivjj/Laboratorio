# Plano de atuação — Donizete Social · PROJ-LP

**Task:** LP-PINTOR-001 (+ CRM LP-PINTOR-003) · **Gate liberado:** 2026-06-03 — página modelo [exemplo-pintor](https://api.laboratorioagentes.com.br/previas/exemplo-pintor/) aprovada pelo Vitor  
**Produto:** Landing pintor R$ 69 · funil invertido · **CRM:** `crm/crm_landing_pintor.md`  
**Meta sprint (2026-06-03):** **10 leads** em `pronto_pra_pagina`

---

## 1. Missão (uma frase)

Captar pintores qualificados no Facebook **sem vender**, com stalk completo do perfil e mídia salva para Loide — entregar leads em `pronto_pra_pagina` com pacote completo.

---

## 2. O que NÃO fazer

| Proibido |
|----------|
| Mencionar preço, PIX ou “página por R$ 69” no Facebook |
| DM comercial em massa · burst de posts · mesmo texto em vários grupos |
| Pedir foto/dados ao pintor (tudo é coleta pública) |
| Filtrar “só as melhores” fotos — Loide curadoria depois |
| Automatizar follow/unfollow ou flood |
| Limitar-se a grupos “de pintores” ou a uma cidade fixa de operação |

---

## 3. Dois canais

### Canal A — Post-isca (prioridade)

Post em **qualquer grupo genérico** com atividade (classificados, bairro, compra/venda, serviços gerais, vizinhança) — **não** precisa ser grupo de pintores. Ajustar **[CIDADE]** no texto para a **cidade/região do grupo** onde está postando (ou bairro do grupo). A comunidade indica → lead com selo social.

**Rotina:** publicar → monitorar comentários 24–48h → extrair nome, perfil, WhatsApp, contexto.

**Tag CRM:** `indicacao`

### Canal B — Garimpo passivo

Monitorar pintores que **postam próprios trabalhos** (fotos de obra, antes/depois, “faço orçamento”) — em qualquer grupo ou feed público.

**Tag CRM:** `autopromocao`

### Região e cidade

- **Sem cidade piloto fixa** — Donizete pode atuar em vários grupos/regiões em paralelo (respeitando anti-ban).
- **Cidade do lead** = dado capturado no stalk (bio, posts, comentário) — registrar no CRM; não inventar.

---

## 4. Anti-ban (obrigatório)

| Regra | Valor |
|-------|--------|
| Posts por dia | 3–5 (fase inicial; pode subir com cuidado se meta 10 exigir) |
| Mesmo grupo | **1× por dia**, rodízio ≥3 dias antes de repetir |
| Intervalo entre posts | **40–120 min** aleatório |
| Horário | Manhã · almoço · fim de tarde/noite — **sem madrugada** |
| Entre posts | Scroll, curtir, 1 comentário humano ocasional |
| Texto | **Sempre variado** — banco §5 |

**Limite qualificação:** até **1 lead qualificado/hora** (fase inicial) — priorizar completar stalk/CRM de leads já indicados antes de acelerar posts.

---

## 5. Banco de posts-isca (8 variações)

Usar **uma variação por grupo**. **[CIDADE]** = cidade ou região **do grupo onde você posta** (ler nome/descrição do grupo).

1. *Pessoal:* «Oi pessoal! Estou precisando de um **pintor de confiança** aqui em **[CIDADE]** pra pintura interna. Alguém indica?»
2. *Urgência leve:* «Reforma em casa em **[CIDADE]** — preciso de pintor que capriche e não deixe sujeira. Indicações?»
3. *Fachada:* «Quem indicam pra **pintura de fachada** na região de **[CIDADE]**? Orçamento justo e serviço limpo.»
4. *Apartamento:* «Mudei pro apê em **[CIDADE]** e preciso pintar antes de mobiliar. Pintor bom que vocês conhecem?»
5. *Comercial:* «Preciso pintar um **ponto comercial** pequeno em **[CIDADE]**. Quem já usou e recomenda?»
6. *Indireto:* «Alguém sabe de pintor que atenda **[CIDADE]** e região? Trabalho residencial, sem enrolação.»
7. *Recomendação:* «Vale a pena indicar pintor que faz **massa corrida e acabamento** em **[CIDADE]**? Preciso de orçamento.»
8. *Curto:* «**Pintor** em **[CIDADE]** — indicação de quem já contratou? Obrigado!»

---

## 6. Qualificação — checklist

Marcar `pronto_pra_pagina` só se **todos** forem sim:

| # | Critério |
|---|----------|
| 1 | Pintor real (não loja de tinta, não spam) |
| 2 | **WhatsApp ou telefone público** capturável |
| 3 | Cidade/região identificável (do perfil ou indicação) |
| 4 | Há **fotos de trabalho** no perfil ou no comentário (Canal A) ou no feed (Canal B) |
| 5 | Perfil ativo (postou nos últimos ~6 meses) |
| 6 | Stalk + mídia concluídos (§7) |

**Descartar:** sem obra, perfil fake, sem contato, só revenda de serviço genérico.

**Prioridade:** indicação de terceiro (Canal A) > autopromoção (Canal B).

---

## 7. Stalk de perfil + mídia (obrigatório por lead)

### 7.1 Varrer (público)

- Facebook: foto perfil, capa, bio, últimos posts com obra, comentários do thread de indicação
- Instagram (se linkado): bio, grid, destaques públicos

### 7.2 Salvar no repo

```
frontend/lp-pintor/leads/{slug}/
  captura/
    raw/           ← imagens baixadas: {slug}-001.jpg, 002…
    manifest.json  ← inventário (ver template leads/_template/captura/)
  (Loide depois preenche assets/ — Donizete não escolhe layout)
```

**manifest.json** por imagem: origem (FB/IG), URL do post, tipo sugerido (`trabalho`, `fachada`, `interna`, `antes`, `depois`, `logo`, `outro`), nota de contexto.

### 7.3 Texto para CRM

Bio literal · serviços que menciona · bairros · link do post/grupo · quem indicou (Canal A).

**Loide** aprova/rejeita fotos — se ruins, usa stock/IA; Donizete não bloqueia lead por foto feia.

---

## 8. CRM — registro

**Arquivo:** `crm/crm_landing_pintor.md`  
**Template:** ver seção «Template — novo lead» no CRM.

| Campo obrigatório | Exemplo |
|-------------------|---------|
| ID | LEAD-002 |
| Nome | João Silva Pinturas |
| Cidade | (do lead — ex. Viçosa — MG) |
| Contato | 5533… (só números) |
| Origem | `indicacao` ou `autopromocao` |
| Grupo / quem indicou | Grupo Classificados XYZ — comentário Maria |
| Perfil social | URL FB ou @ Instagram |
| Slug | `joao-silva` (minúsculo, hífen) |
| Pasta captura | `frontend/lp-pintor/leads/joao-silva/captura/` |
| Status | `prospectado` → `pronto_pra_pagina` |

**Status `pronto_pra_pagina`:** pacote §7 completo + checklist §6 OK → notificar Ronaldo (handoff produção).

---

## 9. Fluxo após Donizete

```
Donizete → pronto_pra_pagina
    → Loide (curadoria mídia → assets/)
    → Dev (config + build /previas/{slug}/)
    → Juarez (QA)
    → previa_no_ar
    → Caio (WhatsApp · R$ 69)
```

Donizete **não** fala com pintor sobre venda.

---

## 10. Rotina diária (cola)

| Horário | Ação |
|---------|------|
| Manhã | 1 post-isca (grupo A) + garimpo 15 min |
| +40–120 min | Comportamento humano no FB |
| Almoço | 1 post (grupo B) + responder comentários de ontem |
| Tarde | Stalk de leads qualificados + salvar mídia + CRM |
| Noite | 1–2 posts (grupos C/D) + atualizar status leads |

**Meta sprint:** **10 leads** `pronto_pra_pagina` (qualidade mantida; stalk completo obrigatório).

---

## 11. Grupos (mapeamento)

Donizete entrega **lista de 10–15 grupos** mapeados (nome + link + cidade/região do grupo para posts) — **qualquer nicho genérico**, várias regiões permitidas.

---

## 12. Entregáveis LP-PINTOR-001

- [ ] Lista 10+ grupos mapeados (genéricos, rodízio, multi-região OK)
- [ ] Banco 8 posts em uso (CIDADE alinhada ao grupo de cada post)
- [ ] Rotina anti-ban documentada (log: posts/dia, grupos, intervalos)
- [ ] **10 leads** `pronto_pra_pagina` com captura/raw + manifest
- [ ] Zero restrição/ban na conta

---

## 13. Referências

- Manual: [operacao_landing_pintor.md](operacao_landing_pintor.md)
- Produção: [producao_lp_pintor.md](producao_lp_pintor.md)
- Página modelo: https://api.laboratorioagentes.com.br/previas/exemplo-pintor/
- Agente: [donizete_social.md](../../agentes/donizete_social.md)
- Task: [LP-PINTOR-001.md](../../tasks/LP-PINTOR-001.md)
