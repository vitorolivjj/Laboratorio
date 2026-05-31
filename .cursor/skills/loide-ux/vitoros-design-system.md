# VitorOS — Design System (Loide)

Referência visual para mockups e specs. Implementação: `centralvitor/public/css/app.css`.

## Cores

| Token | Hex | Uso |
|-------|-----|-----|
| `--bg` | `#0a0f1c` | Fundo app |
| `--bg-card` | `#0f1830` | Cards, login |
| `--bg-elevated` | `#141e38` | Hover, elevado |
| `--border` | `#1e2c4f` | Bordas |
| `--text` | `#e8eefc` | Texto principal |
| `--muted` | `#a9b6d4` | Secundário |
| `--dim` | `#5f6f93` | Placeholder, hints |
| `--accent` | `#22c55e` | Sucesso, CTA primário, KPI ok |
| `--warn` | `#facc15` | Alertas, atenção |
| `--blue` | `#7aa2ff` | Links, info |

## Tipografia

- **Fonte:** Inter (400, 600, 700, 800)
- **Títulos painel:** 1.25–1.5rem, weight 700
- **KPI valor:** 1.75–2rem, weight 800
- **Corpo:** 0.95rem
- **Hint/caption:** 0.78–0.85rem, `--muted`

## Espaçamento & forma

- `--radius`: 12px
- Padding card: 16–24px
- Gap grid KPI: 12px
- Topbar + bottom nav: `--nav-h` 64px

## 3 camadas (shell)

| Camada | Nome | Foco |
|--------|------|------|
| 1 | Macro | KPIs, alertas, sugestões Negão — leitura 10s |
| 2 | Operacional | Rabiscos, projetos, kanban, finanças |
| 3 | Mapa | Frentes, atalhos, busca global |

Navegação: tabs top + bottom nav mobile (mesmos 3 botões).

## Componentes base

- **`.kpi`** — valor grande + label pequena
- **`.card`** — bloco conteúdo com título h3
- **`.btn-primary`** — verde, CTA
- **`.btn-ghost`** — transparente, secundário
- **`.placeholder-item`** — módulo futuro (TASK-011+)

## Kanban (TASK-011)

Colunas tasks: Backlog → Planejando → Executando → Revisão → Concluído → Arquivado

Rabiscos: Solto → Vinculado → Arquivado

## A11y

- Contraste mínimo 4.5:1 texto/fundo
- Touch targets ≥ 44px
- Focus visible em botões
- `aria-label` em nav por camadas

## Frentes iniciais (mapa)

Negão · Laboratório · VS Rota · AppVS · Consultoria · Saúde Familiar · Finanças · Sítio
