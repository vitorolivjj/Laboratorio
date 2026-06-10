# Playbook — produto low-ticket (vitrine)

**Escopo:** PROJ-LP e futuros produtos ≤ R$ 100 · **Princípio:** entregar antes de cobrar.

## 1. Definir oferta fechada

- Preço único (PIX), sem mensalidade oculta
- Escopo incluso vs upsell explícito (§10 operacao_landing_pintor)
- KPI único por produto (LP: 1 `ativo` no CRM)

## 2. Produção mínima vendável

- Template parametrizado (`config.json` + build em minutos)
- Prévia pública removível (API `/previas/` ou Surge)
- 1 lead manual antes de escalar captação (Donizete/FB)

## 3. Funil invertido

1. Qualificar e cadastrar CRM com origem
2. Loide + Dev montam prévia
3. Caio aborda com **link pronto** (preço só no fechamento)
4. Não ativou em 3–5 dias → despublicar

## 4. Travas de autonomia

| Ação | Tier |
|------|------|
| append_task_note, notify_vitor | auto |
| send_client_message | **APROVAR WA** |
| deploy produção / PIX | humano |

CLI: `./run.sh agent-action` · grafo: `./run.sh graph-run <TASK-LP>`

**Playbook Caio:** [playbook_comercial_lp_pintor.md](caio_manteiga/playbook_comercial_lp_pintor.md)

## 5. Auditoria Ronaldo

- Taxa ativação = ativos ÷ prévias entregues
- CRM atualizado · patrulha + audit pós-task
- KPI vitrine em `crm/arquivo/crm_landing_pintor.md` (piloto encerrado)

## 6. Repetir

Documentar case em `docs/vitrine/` · memória semântica sync · próximo produto copia pipeline.
