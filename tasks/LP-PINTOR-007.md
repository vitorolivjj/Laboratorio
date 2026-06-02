# LP-PINTOR-007 — Webflow: template + coleção Pintores

| Campo | Valor |
|-------|-------|
| **ID** | LP-PINTOR-007 |
| **Projeto** | PROJ-LP |
| **Status** | executando |
| **Kanban** | tasks/executando.md |
| **Prioridade** | P0 |
| **Agente** | loide · dev |
| **Iniciada em** | 2026-06-02 |

## Objetivo

Montar no Webflow a **página oficial** do produto: 1 template-matriz + 4 variantes de cor (Azul, Verde, Grafite-Laranja, Neutro) amarrado à coleção **Pintores** conforme schema. Desbloqueia captação (Donizete) e automação (008).

## Critérios de aceite

- [ ] Conta Webflow Premium + workspace configurado
- [ ] Coleção Pintores com campos do schema ([webflow_lp_pintor.md](../memoria/ronaldo_maestro/webflow_lp_pintor.md))
- [ ] 1 página de exemplo publicada em subpath de teste (domínio oficial definido)
- [ ] Tarja prévia controlada por campo `Ativo` (ativar = só tira tarja)
- [x] Decisões schema fechadas com Vitor (2026-06-02)

## Ref

Decisão Webflow 2026-06-02 · `memoria/decisoes.md`

---

## Briefings (Ronaldo → agentes) — 2026-06-02

### Briefing — Loide — LP-PINTOR-007 — 2026-06-02

- **Objetivo desta rodada:** Desenhar template-matriz Webflow + 4 variantes de cor + coleção Pintores (campos fixos serviços/depoimentos)
- **Entregável esperado:** template publicável · 1 item CMS de exemplo · tarja prévia ligada ao campo `Ativo`
- **Restrições:** schema em `webflow_lp_pintor.md` · subpath URL · sem domínio próprio por pintor
- **Critério de pronto:** Juarez consegue revisar página exemplo no ar antes de qualquer captação
- **Não fazer:** automação API (LP-PINTOR-008) · captação Donizete

### Briefing — Dev — LP-PINTOR-007 — 2026-06-02

- **Objetivo desta rodada:** Configurar conta/site Webflow · amarrar coleção ao template · publicar subpath de teste
- **Entregável esperado:** site no ar · coleção Pintores operacional · credenciais API anotadas para 008
- **Restrições:** seguir handoff Loide · Premium plan · skill `dev-laboratorio`
- **Critério de pronto:** URL oficial de exemplo acessível · item CMS editável
- **Não fazer:** script CRM→API ainda · migrar Stephanie (fase posterior)
