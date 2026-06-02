# Webflow — PROJ-LP (produção e escala)

**Decisão:** alugar a máquina pronta (Webflow), não construir em casa. Construir página não é o diferencial (o **funil** é); mensalidade irrisória no volume.

**Vitrine fase 1 (concluída):** template in-house `frontend/lp-pintor/` + API `/previas/` — LEAD-001 Stephanie ativo. **Migrar novos leads para Webflow.**

---

## Plano e capacidade

| Item | Valor |
|------|-------|
| **Plano** | Premium (~US$ 25/mês anual) + assento workspace |
| **Capacidade** | ~20.000 páginas de pintor num site só |
| **URL** | Subpath: `seudominio.com.br/joao-pintor` (não domínio próprio do pintor — aceitável) |
| **In-house fase 2** | Só se volume justificar matar mensalidade — **não agora** |

## Replicação

1. **1 template-matriz** desenhado uma vez, amarrado à coleção **Pintores**
2. Cada pintor = **1 item CMS** → 1 página gerada automaticamente
3. Criar/publicar/despublicar via **API do CMS** (item a item, sem republicar o site)
4. **4 variantes de cor:** Azul · Verde · Grafite-Laranja · Neutro
5. Roadmap: 2º modelo visual numa fase seguinte

## Qualidade Webflow

- Design padrão de mercado · animações nativas (scroll, hover, parallax)
- Otimiza/recorta foto na proporção travada
- Esconde seções/cards vazios (fallback automático)

---

## Schema coleção "Pintores"

### Sistema

| Campo | Tipo | Uso |
|-------|------|-----|
| Nome | texto | — |
| Slug | slug | URL subpath |
| ID do CRM | texto | link LEAD-XXX |
| Variante de cor | seleção | Azul / Verde / Grafite-Laranja / Neutro |
| Ativo | boolean | `sim` = sem tarja prévia · `não` = prévia |
| Data da prévia | data | job expiração 3–5 dias |

### Herói

Headline · Subtítulo · Cidade · Foto de capa

### Serviços (3 cards) — campos fixos

Serviço 1/2/3 — título + descrição (card vazio some). **Sem coleções referenciadas** — schema plano no item Pintores.

### Sobre + números

Sobre (texto) · Anos de experiência · Obras entregues · Bairros/área

### Galeria

Multi-imagem — grid 3–12+ fotos

### Depoimentos (2–3) — campos fixos

Depoimento 1/2/3 — texto + autor (seção some se vazia). **Sem coleções referenciadas.**

### Contato

WhatsApp (→ wa.me) · Mensagem pré-preenchida (opcional)

---

## Decisões fechadas (Vitor — 2026-06-02)

1. **Serviços e depoimentos:** **campos fixos** no item Pintores (não coleções referenciadas)
2. **Ativar:** só **tira a tarja de prévia** (`Ativo = sim` no CMS + CRM `ativo`). Mesmo layout, mesma URL — nada mais muda
3. **Handoff:**
   - **Donizete** — nome, cidade, bairros, fotos, WhatsApp, grupo, serviços brutos
   - **IA** — headline, subtítulo, sobre, cards, depoimentos (se faltar)
   - **Loide+Dev** — script CRM → Webflow API (criar/publicar item)
   - **Juarez** — confere antes de `previa_no_ar`
   - **Caio** — abordagem WhatsApp · **Vitor** — confirma PIX → ativa

---

## Ativo in-house (Loide + Dev)

Loide constrói **coleção + template** (uma vez) + **script-ponte** (CRM → API Webflow → status) + **job takedown** prévias vencidas. Essa automação é o diferencial em casa — não o HTML.

**Ref:** [operacao_landing_pintor.md](operacao_landing_pintor.md) · tasks `LP-PINTOR-007` · `LP-PINTOR-008`
