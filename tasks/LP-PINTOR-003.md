# LP-PINTOR-003 — CRM pintores (funil invertido) + handoff Donizete→Loide

## Metadados

| Campo | Valor |
|-------|-------|
| **ID** | LP-PINTOR-003 |
| **Projeto** | PROJ-LP |
| **Status** | backlog |
| **Kanban** | tasks/backlog.md |
| **Dependências** | LP-PINTOR-007 |
| **Prioridade** | media |
| **Agente responsável** | donizete_social |
| **Agentes auxiliares** | ronaldo_maestro |
| **Criada em** | 2026-05-31 |

## Objetivo

Operacionalizar o CRM `crm_landing_pintor` com o funil invertido e o pacote de handoff Donizete → produção, garantindo que todo lead siga `prospectado → pronto_pra_pagina → previa_no_ar → abordado → ativo/recusou`.

**Gate:** Donizete só opera CRM/captação após LP-PINTOR-007 (página oficial Webflow).

## Critérios de aceite

- [ ] Campos do lead preenchidos (nome, WhatsApp, cidade, serviço, fotos, link origem, quem indicou, tag)
- [ ] Pipeline movido por Donizete conforme o estágio real
- [ ] Pacote de handoff padronizado entregue à Loide (nome, cidade, serviço, melhores fotos, WhatsApp)
- [ ] Tag de origem registrada (indicacao/autopromocao) para medir conversão por canal

## Ref

Manual §5, §6 — `memoria/ronaldo_maestro/operacao_landing_pintor.md`

### Briefing — Donizete — LP-PINTOR-003 — 2026-05-31
- **Objetivo desta rodada:** Manter o CRM atualizado e entregar pacotes de handoff limpos pra Loide
- **Entregável esperado:** leads com pipeline e tags corretos; pacotes de handoff
- **Restrições:** só dados públicos coletados; nada solicitado ao lead
- **Critério de pronto:** Loide recebe pacote completo sem precisar pedir nada de volta
