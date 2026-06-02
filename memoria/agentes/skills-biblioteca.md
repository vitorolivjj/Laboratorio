# Biblioteca de Skills — Dev & Loide

Cursor Agent Skills do ecossistema Laboratório/VitorOS. Ronaldo aciona agentes **com** estas skills quando o escopo envolver código ou UX.

**Local:** `.cursor/skills/` (project skills — versionadas no repo Laboratorio)

## Índice

| Skill | Agente | Escopo | Arquivo |
|-------|--------|--------|---------|
| **loide-ux** | Loide | UX, wireframes, mockups visuais, design system VitorOS, geração de imagens | `.cursor/skills/loide-ux/SKILL.md` |
| **dev-vitoros** | Dev | PWA centralvitor, Supabase, deploy VPS vitoroliv.com | `.cursor/skills/dev-vitoros/SKILL.md` |
| **dev-laboratorio** | Dev | Backend Lab, Maestro, orquestrador, VPS api.laboratorio | `.cursor/skills/dev-laboratorio/SKILL.md` |

## Quando acionar

| Situação | Skills |
|----------|--------|
| Nova tela VitorOS | Loide: `loide-ux` → Dev: `dev-vitoros` |
| Bug/deploy vitoroliv.com | Dev: `dev-vitoros` |
| Painel Maestro / WhatsApp / backend Lab | Dev: `dev-laboratorio` |
| Revisão usabilidade | Loide: `loide-ux` |

## Loide — capacidade visual

A skill `loide-ux` instrui o agente a usar **GenerateImage** para mockups. Artefatos salvos **somente no Laboratório**:

- VitorOS: `docs/ux/vitoros/`
- Lab: `docs/ux/laboratorio/`

Design tokens: `.cursor/skills/loide-ux/vitoros-design-system.md`

**Nunca** versionar mockups/specs de agente no repo `centralvitor`.

## Autonomia graduada (Fase 3)

Agentes no **backend** usam `run_action()` — não confundir com Cursor skills.

| Tier | Exemplos |
|------|----------|
| auto | `log_event`, `memory_recall`, `patrol_check` |
| approval | `send_client_message`, `run_graph_pilot` |

Ver `memoria/autonomia_graduada_fase3.md` · CLI: `./run.sh agent-action`

## Manutenção

Task oficial: **TASK-022** · Expandir skills conforme novos padrões (Negão, finanças, etc.)

## Skills Cursor globais (referência)

Em `~/.cursor/skills-cursor/` — built-in Cursor (canvas, create-skill, sdk…). **Não editar.** Skills do ecossistema ficam só em `.cursor/skills/`.
