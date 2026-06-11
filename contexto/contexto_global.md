# Contexto global

**Fonte única de verdade** do momento: o que o ecossistema precisa saber agora para agir alinhado.

## Posicionamento (plano de negócio v1 — 2026-06-11)

O Laboratório atende **negócios locais que perdem clientes por bagunça em captação,
atendimento e comercial**. Escada: **Dossiê de Vazamentos (grátis) → Plano de Ataque
(R$450) → Sprint (R$1.5–4k+) → Acompanhamento Mensal**. IA no bastidor, processo na
frente. **Rosto público: Vitor** (fim do anonimato). Resumo operacional:
[memoria/plano_negocio.md](../memoria/plano_negocio.md).

O piloto pintor (PROJ-LP) foi teste, está encerrado e arquivado em
`memoria/arquivo/pintor-legado/`. **Pintor não é foco de nenhum agente.**

## Foco atual

1. **Fase de VALIDAÇÃO do novo negócio** — poucos leads bons; sem metas numéricas fixas.
   Gates: 3–5 Dossiês reais · 5 conversas · 2 Planos de Ataque vendidos · 1 entregue ·
   modelo do Dossiê travado. Donizete caça por score (6+), Caio aborda só com template
   aprovado (`abordar_lead`), Vitor faz as calls.
2. **Esteira de Conteúdo (vitrine)** — validada e **em produção**: gera 1 peça/dia (~07:00),
   aprovação do Vitor via WhatsApp, publica nos slots 08:00/12:30/19:00.
   Pendência: migrar publicação para o perfil do Vitor (Postproxy) — anonimato encerrado.

## Prioridades

| # | Prioridade | Dono | Status |
|---|------------|------|--------|
| **P0** | Validação do novo negócio (Dossiês → Planos de Ataque) | Donizete · Caio · Vitor | **em andamento** |
| P1 | Esteira de Conteúdo — operação diária + aprovações | Donizete · Ronaldo | em produção |
| P2 | Modelo da página do Dossiê (P00-01) — travar após 3-5 reais | Ronaldo · Dev | a iniciar |
| — | VitorOS (PROJ-002) | Dev + Loide | pausado |

## Stack Lab (operacional)

| Fase | Capacidade |
|------|------------|
| 0 | Aprovação WhatsApp (mensagem cliente, gasto alto) |
| 1 | Memória semântica Supabase |
| 2 | LangGraph piloto + comercial (`graph-pilot` / `graph-run`) |
| 3 | Autonomia graduada (`agent-action`) |
| 4 | Autoevolução 1×/dia + sync pós-APROVAR |

## Restrições

- **Orçamento:** baixo — MVP, free tier
- **Caio proativo:** sempre trava WA — inbound continua instantâneo
- **Captação FB:** liberada em modo validação (leads bons, score 6+) · anti-ban inalterado · **não vender no FB**
- **Separação:** Laboratório (fábrica) ≠ `centralvitor` (VitorOS deploy)
- **Escalacao Vitor:** credencial, custo, prod Lab, estrutural — WA +5533999353242

## Projetos em destaque

- **PROJ-LAB** — fábrica multiagente · `api.laboratorioagentes.com.br`
- **PROJ-003** — Vitrine/Esteira de Conteúdo · em produção (1 peça/dia + aprovação)
- **PROJ-LP** — ~~Landing Pintor R$69~~ · **encerrado (teste validado)** · arquivo: [memoria/arquivo/pintor-legado/](../memoria/arquivo/pintor-legado/)
- **PROJ-002** — VitorOS · pausado

## Última atualização

| Campo | Valor |
|-------|-------|
| Data | 2026-06-11 |
| Atualizado por | Vitor · Claude |
| Resumo | Plano de negócio v1 implantado: escada Dossiê→Plano de Ataque→Sprint→Acompanhamento · funil novo no CRM · templates de abordagem aprovados (Caio) · fase de validação iniciada |
