# Delegação Ronaldo — VitorOS + Negão (PROJ-002)

**Data:** 2026-05-31  
**Orquestrador:** Ronaldo Maestro  
**Origem:** [contexto/escopo-vitoros.md](../contexto/escopo-vitoros.md) v4  
**Autonomia:** Vitor concedeu mandato (2026-05-31) — Ronaldo inicia tasks quando quiser, sem OK por ciclo.

---

## DECISÃO DE HOJE

Iniciar **Track A (Cockpit VitorOS)** na VPS dedicada `vitoroliv.com`. Negão (Track B) só depois que Supabase + A0 estiverem prontos. **Não misturar** com PROJ-001 / VPS Laboratório.

**Ronaldo:** pode mover TASK-010 para `executando` e acionar Dev + Loide **autonomamente** — registrar em `logs/eventos.md`.

**Skills:** briefings devem referenciar `.cursor/skills/` — ver [memoria/agentes/skills-biblioteca.md](../memoria/agentes/skills-biblioteca.md)

**Protocolo obrigatório:** [protocolo_delegacao_conferencia.md](../memoria/ronaldo_maestro/protocolo_delegacao_conferencia.md) — delegar → conferir → aprender

## Fronteiras (obrigatório)

| | VitorOS (PROJ-002) | Laboratório (PROJ-001) |
|--|-------------------|------------------------|
| **Domínio** | `vitoroliv.com` · `ia.vitoroliv.com` | `api.laboratorioagentes.com.br` |
| **VPS** | `5.78.215.136` | `5.78.232.71` |
| **Repo código** | `github.com/vitorolivjj/centralvitor` | `github.com/vitorolivjj/Laboratorio` |
| **Path VPS** | `/opt/centralvitor` | `/opt/laboratorio` |
| **Orquestração/tasks** | Registradas aqui (Laboratório) | — |

O Laboratório **coordena** (tasks, Ronaldo, agentes). O **código e deploy** do VitorOS ficam **só** no repo `centralvitor` e na VPS `vitoroliv.com`.

---

## Mapa de tasks (12)

| ID | Fase | Título | Responsável | Auxiliar | Depende de |
|----|------|--------|-------------|----------|------------|
| TASK-010 | A0 | Esqueleto VitorOS (Supabase, Auth, shell PWA, deploy VPS) | dev | loide | — |
| TASK-011 | A1 | Rabiscos + Projetos + Tasks kanban | dev | loide | TASK-010 |
| TASK-012 | A1 | Home cockpit + KPIs derivados | dev | loide | TASK-011 |
| TASK-013 | A2 | Finanças (caixas, movimentos, metas) | dev | loide | TASK-012 |
| TASK-014 | A2 | Objetivos macro | dev | loide | TASK-013 |
| TASK-015 | A3 | Motor de alertas + feed eventos | dev | juarez | TASK-014 |
| TASK-016 | A3 | Atalhos + Mapa frentes + Busca | dev | loide | TASK-015 |
| TASK-017 | B0 | Import + limpeza conversations.json | dev | — | TASK-010 |
| TASK-018 | B1 | Destilação perfil-semente Negão | dev | — | TASK-017 |
| TASK-019 | B2 | Memória episódica pgvector | dev | — | TASK-018 |
| TASK-020 | B3+B4 | Chat Negão + sugestões + snapshot | dev | — | TASK-019, TASK-012 |
| TASK-021 | INT | Integração cockpit ↔ Negão + seed + DNS ia. | dev | juarez | TASK-016, TASK-020 |

---

## PRIORIZAÇÃO EXECUTIVA

| Prioridade | Ação | Dono | Prazo |
|------------|------|------|-------|
| **Hoje** | TASK-010 — Supabase projeto VitorOS + shell PWA no `centralvitor` + deploy VPS | Dev + Loide | esta semana |
| **Esta semana** | Juarez levantar lista seed (projetos, caixas, frentes) para TASK-021 | Juarez | antes de A2 |
| **Depois A1** | TASK-017 B0 em paralelo (export ChatGPT) | Dev | após Supabase |
| **Marco** | TASK-021 integração quando A3 + B3 prontos | Dev | fase 2 |

## DECISÃO DE HOJE (imperativa)

**Dev + Loide:** abrir workspace `centralvitor`, criar projeto Supabase **separado** do Lab, entregar shell PWA com 3 camadas em `vitoroliv.com` — sem tocar na VPS ou API do Laboratório.

## PRÓXIMO PASSO (24h)

Dev configura Supabase PROJ-002, Loide desenha shell/navegação das 3 camadas, push no `centralvitor`, deploy via `./deploy/deploy.sh` na VPS `5.78.215.136`.

---

## Briefings emitidos

### Briefing — Dev — TASK-010

- **Objetivo:** Esqueleto técnico VitorOS na VPS `vitoroliv.com` apenas.
- **Repo:** `/Users/vitor/00-Projetos/02-CentralVitor/centralvitor` (GitHub `centralvitor`).
- **VPS:** `ssh root@5.78.215.136` · path `/opt/centralvitor` · nginx já aponta para `public/`.
- **Entregável:**
  1. Projeto Supabase novo (não reutilizar credenciais do Lab)
  2. Migrations iniciais: schema cockpit + `sugestoes` + stub `snapshot_estado()`
  3. PWA vanilla JS: shell 3 camadas (macro / operacional / mapa), dark mode, paleta Controle de Rotas
  4. Supabase Auth login único (Vitor)
  5. Deploy: substituir `public/index.html` "em breve" pelo app shell
- **Restrições:** NÃO deployar no Laboratório · NÃO usar `api.laboratorioagentes.com.br` · NÃO Netlify (VPS já pronta)
- **Critério de pronto:** `https://vitoroliv.com` abre shell autenticado com navegação entre camadas (conteúdo placeholder ok)
- **Não fazer:** Negão, pgvector, import memória, integração WhatsApp Lab

### Briefing — Loide — TASK-010

- **Objetivo:** UX do shell VitorOS (3 camadas) antes do Dev codar módulos.
- **Entregável:** fluxo mobile-first + desktop, hierarquia Camada 1/2/3, nav principal, estados vazios, microcopy Home.
- **Referência visual:** Controle de Rotas (navy/slate, verde `#22C55E`, amarelo `#FACC15`, Inter).
- **Trabalhar junto com Dev:** Loide define → Dev implementa no `centralvitor/public/`.
- **Critério de pronto:** wireframe/descrição implementável em 1 sessão de Dev.
- **Não fazer:** Kanban detalhado, finanças, mapa completo (isso é A1–A3).

### Briefing — Juarez — TASK-021 (preparação antecipada)

- **Objetivo:** Inventário para seed inicial (entre A1 e A2).
- **Entregável:** lista em markdown: frentes/projetos ativos, caixas (PF/PJ/VS/Lab) com valores aproximados, objetivos macro, 5 atalhos essenciais.
- **Formato:** tabela simples pronta para Dev importar no Supabase.
- **Prazo:** entregar antes de TASK-013 (finanças).
- **Não fazer:** implementar código · misturar com operação do Laboratório multiagente.

---

## KPI DE SUCESSO (V1 cockpit)

Vitor abre `vitoroliv.com`, em ~10s entende situação macro, cria rabisco, cria task, vê projetos e finanças básicas — **sem** depender do Painel Maestro do Lab.

---

## Registro

- **Evento:** `logs/eventos.md` — delegação VitorOS 2026-05-31
- **Histórico:** `memoria/ronaldo_maestro/historico_de_orquestracao.md`
