# Escopo de Desenvolvimento — VitorOS + Negão (v4 · consolidado)

> Cockpit operacional pessoal de Vitor Oliveira.
> Documento definitivo de desenvolvimento. Consolida o Escopo Final de produto com a arquitetura técnica e resolve os pontos em aberto.
> Decisões de engenharia abaixo são reversíveis e estão marcadas onde houver escolha em aberto.

**Infra (decisão 2026-05-31):** VitorOS roda em **vitoroliv.com** na VPS dedicada (`5.78.215.136`), repo `centralvitor`. **Não** usar VPS/API do Laboratório (`api.laboratorioagentes.com.br`).

---

# PARTE I — PRODUTO E FILOSOFIA

## 0. Nomenclatura e domínios

- **VitorOS** — o sistema (cockpit). Domínio: `vitoroliv.com`.
- **Cockpit** — a tela inicial do VitorOS.
- **Negão** — o agente de IA principal, sistema separado. Domínio: `ia.vitoroliv.com`.

São dois sistemas, um só cérebro de dados (mesmo Supabase). Ver seção 4.

## 1. Definição do produto

O **VitorOS** é o cockpit operacional pessoal do Vitor: central visual para organizar e acompanhar as frentes da vida, negócios, finanças, projetos, tasks e movimentações.

Não é site institucional, rede social, base de conhecimento nem histórico de conversas. É um ambiente de comando para enxergar o estado atual e agir com clareza.

## 2. Premissa central

A forma de pensar, conversar e decidir do Vitor não muda. As decisões continuam acontecendo na conversa com o **Negão**, em `ia.vitoroliv.com`.

- O cockpit responde: **"Como estão minhas frentes agora?"**
- O Negão responde: **"O que isso significa e qual movimento faz sentido?"**

**O cockpit mostra. O Negão interpreta. O Vitor decide.**

## 3. O que NÃO entra no VitorOS

Pertence ao domínio do Negão, não ao cockpit:

- Timeline da vida · base de conhecimento separada · histórico de conversas visível
- Biblioteca de decisões antigas · página de revisão de contexto bruto
- Qualquer tentativa de substituir o Negão ou decidir sozinho

O cockpit é visual, operacional e atual. O Negão é contextual, histórico e reflexivo.

---

# PARTE II — ARQUITETURA

## 4. Visão de arquitetura

```
   vitoroliv.com (VitorOS)              ia.vitoroliv.com (Negão)
   ┌───────────────────────┐           ┌───────────────────────┐
   │  Cockpit (PWA, vanilla)│           │  Agente (Laboratório)  │
   │  - lê/escreve estado   │           │  - conversa diária     │
   └───────────┬───────────┘           │  - memória 3 anos      │
               │                       └───────────┬───────────┘
               │        SUPABASE (fonte da verdade)│
               └───────────────┬───────────────────┘
                               ▼
        ┌──────────────────────────────────────────────┐
        │  Estado vivo (cockpit)  │  Memória do Negão     │
        │  projetos, tasks,       │  bruta + episódica     │
        │  caixas, objetivos…     │  (pgvector) + perfil   │
        └──────────────────────────────────────────────┘
```

Os dois sistemas conversam **através do Supabase**, não por chamadas diretas entre si. Isso mantém cada front leve e independente.

## 5. Contrato VitorOS ↔ Negão

**Fonte da verdade:** um único projeto Supabase, compartilhado pelos dois domínios. Usuário único, RLS ligado.

**Negão LÊ o cockpit:** view/função `snapshot_estado()` → JSON compacto do estado atual.

**Negão ESCREVE no cockpit:** tabela `sugestoes` (proposta → aceita/recusada). Vitor confirma no cockpit.

## 6–9. Memória Negão, stack, auth, mobile

Ver seções completas no arquivo original em `~/Downloads/escopo-vitoros.md` — resumo técnico:

- **Front:** PWA vanilla JS, dark mode, visual Controle de Rotas (navy/slate, verde `#22C55E`, amarelo `#FACC15`, Inter)
- **Dados:** Supabase (Postgres + Auth + RLS + pgvector para Negão)
- **Deploy VitorOS:** VPS `vitoroliv.com` (repo `centralvitor`) — **não** Netlify, **não** VPS Laboratório
- **Auth:** usuário único (Vitor), sessão compartilhada entre domínios quando possível

---

# PARTE III–V — Módulos, dados, faseamento

Documento completo: seções 10–28 do escopo v4 (KPIs, alertas, projetos, tasks, rabiscos, finanças, objetivos, tracks A0–A3 e B0–B4, MVP V1, riscos).

**Faseamento (tracks):**

| Track | Fase | Conteúdo |
|-------|------|----------|
| A | A0 | Supabase + Auth, shell 3 camadas, navegação, deploy VPS |
| A | A1 | Rabiscos, Projetos, Tasks kanban, Home KPIs |
| A | A2 | Caixas, movimentos, metas, objetivos |
| A | A3 | Alertas, eventos, atalhos, mapa, busca |
| B | B0 | Import + limpeza conversations.json |
| B | B1 | Destilação perfil-semente |
| B | B2 | Memória episódica pgvector |
| B | B3 | Loop chat (perfil + retrieval + snapshot) |
| B | B4 | Memória incremental + sugestões |

**Marco integração:** A1 + `snapshot_estado()` + B3 → conectar via `sugestoes`.

**Frase:** *O cockpit mostra. O Negão interpreta. O Vitor decide.*

---

**Ref:** PROJ-002 · Tasks TASK-010–TASK-021 · Repo código: `github.com/vitorolivjj/centralvitor`
