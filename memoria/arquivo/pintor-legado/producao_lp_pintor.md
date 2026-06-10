# Produção LP Pintor — PROJ-LP (in-house)

> **🗄 ARQUIVO / PINTOR — LEGADO** (2026-06-10) · Piloto Landing Page Pintor encerrado — mantido só como histórico/aprendizado. **Não é mais foco** de nenhum agente. Novo posicionamento: negócios locais que perdem clientes por bagunça em captação, atendimento e comercial.

**Decisão (2026-06-02, reforço 2026-06-03):** produção em **HTML/CSS + build estático** — Webflow **revogado**.

**URL:** `https://api.laboratorioagentes.com.br/previas/{slug}/`

**Modelo:** [exemplo-pintor](https://api.laboratorioagentes.com.br/previas/exemplo-pintor/) · matriz **3 dobras** · conversão R$ 69

---

## Stack

| Camada | Onde |
|--------|------|
| Template | `frontend/lp-pintor/template/` |
| Lead | `frontend/lp-pintor/leads/{slug}/config.json` + `assets/` |
| Captura bruta | `leads/{slug}/captura/` (Donizete) |
| Build | `scripts/lp-pintor-build.sh` → `dist/{slug}/` |
| Serve | FastAPI `/previas/` · VPS rsync |

---

## Schema `config.json` (resumo)

Ver campos em `leads/exemplo/config.json`. Principais: `slug`, `nome`, `headline`, `subtitulo`, `cidade`, `whatsapp`, `servicos[]`, `diferenciais[]`, `foto_capa`, `comparacao_antes`/`depois`, `fotos[]`, `theme`, `ativo`, `preview_expires`.

---

## Handoff

Donizete (captura + stalk) → Loide (mídia) → Dev (build) → Juarez (QA) → Caio (venda) → Vitor (PIX → `ativo: true` + rebuild).

**Plano Donizete:** [plano_atuacao_donizete_lp.md](plano_atuacao_donizete_lp.md) · **Publish:** `scripts/lp_publish_lead.py` · **Fase 2:** [fase2_velocidade_lp.md](fase2_velocidade_lp.md)

**Webflow (legado):** [webflow_lp_pintor.md](webflow_lp_pintor.md) — não usar.
