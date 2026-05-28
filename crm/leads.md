# CRM — Leads

CRM operacional markdown-first. Donizete Social registra captações; Caio Manteiga opera abordagem.

**Workflow oficial:** [docs/workflow-captacao-comercial.md](../docs/workflow-captacao-comercial.md)

**Dono da captura:** Donizete Social · **Dono comercial:** Caio Manteiga · **Auditoria:** Ronaldo Maestro

---

## Como usar

1. Donizete cria entrada `LEAD-XXX` ao identificar potencial.
2. Qualifica → status `qualificado` → handoff Caio.
3. Caio atualiza status após abordagem (`abordado`, `convertido`, `sem_resposta`, `descartado`).
4. Referenciar TASK ativa quando aplicável (ex.: TASK-001).

## Regras

- Só informações **públicas**
- Máximo **1 lead qualificado/hora** (fase inicial — Donizete)
- Sempre preencher **Origem** e **Observações** (contexto de captação)

---

## Template — novo lead

```markdown
## LEAD-XXX — [Nome ou @perfil]

| Campo | Valor |
|-------|-------|
| **ID** | LEAD-XXX |
| **Nome** | |
| **Cidade** | |
| **Serviço** | |
| **Contato** | |
| **Origem** | |
| **Perfil social** | |
| **Status** | novo |
| **Responsável** | donizete_social |
| **TASK** | TASK-XXX |
| **Score** | 0–5 |
| **Temperatura** | frio \| morno \| quente |
| **Prioridade** | P1 \| P2 \| P3 |
| **Tags** | |
| **Observações** | |
| **Data captura** | YYYY-MM-DD |
| **Handoff Caio** | |
| **SLA abordagem** | |
```

**Status:** `novo` · `qualificado` · `entregue_caio` · `abordado` · `convertido` · `sem_resposta` · `descartado`

---

## Índice de leads

| ID | Nome | Score | Temp | Prioridade | Status | TASK | Captura |
|----|------|-------|------|------------|--------|------|---------|
| _—_ | _nenhum lead registrado_ | — | — | — | — |

---

## Leads

<!-- Donizete: adicionar novos leads abaixo, mais recente no topo -->

---

## Estatísticas (opcional)

| Período | Captados | Qualificados | Entregues Caio | Convertidos |
|---------|----------|--------------|----------------|-------------|
| — | 0 | 0 | 0 | 0 |

**Última atualização:** 2026-05-28
