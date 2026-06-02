# Projetos — Registry oficial

**Regra de ouro:** O **Laboratório de Agentes IA** é a **fábrica** (empresa-mãe). Projetos são o que a fábrica executa. CRM é onde entram oportunidades comerciais. Task é trabalho executável.

Fonte única para o Painel Maestro (seção **Projetos**) e para classificar tasks e CRM. Toda task pertence a **um** projeto; todo lead pertence a **um** CRM.

## Como usar

- Um bloco por projeto, campos fixos (o parser lê estes campos).
- **Prefixo** define o ID das tasks do projeto (ex.: `VITOROS-003`).
- **CRM** indica o segmento comercial (ou `—` se não comercial).
- **Legado** mapeia IDs antigos `PROJ-XXX` / faixas `TASK-XXX` para o projeto.

## Template

```markdown
### [Nome]
- **ID:** PROJ-XXX
- **Prefixo:** XXX
- **Natureza:** fabrica | cliente-interno | produto-teste | consultoria | produto-futuro
- **Status:** ativo | pausado | futuro | concluido
- **CRM:** crm_laboratorio | crm_landing_pintor | crm_appvs | —
- **Legado:** PROJ-XXX · TASK-faixa (opcional)
- **Repo / deploy:** 
- **Descrição:** 
- **Última atualização:** YYYY-MM-DD
```

---

## Projetos

### Laboratório Core
- **ID:** PROJ-LAB
- **Prefixo:** LAB
- **Natureza:** fabrica
- **Status:** ativo
- **CRM:** crm_laboratorio
- **Legado:** PROJ-001 · TASK-000, TASK-003, TASK-004, TASK-005, TASK-006, TASK-007, TASK-008, TASK-009, TASK-022
- **Repo / deploy:** `Laboratorio` · `api.laboratorioagentes.com.br`
- **Descrição:** A própria fábrica trabalhando nela mesma — painel Maestro, agentes, WhatsApp Caio, CRM, logs, organização. Não é "um projeto cliente"; é a operação principal.
- **Última atualização:** 2026-05-31

### VitorOS
- **ID:** PROJ-002
- **Prefixo:** VITOROS
- **Natureza:** cliente-interno
- **Status:** ativo
- **CRM:** —
- **Legado:** PROJ-002 · TASK-010 a TASK-021
- **Repo / deploy:** `centralvitor` · `vitoroliv.com` · VPS `5.78.215.136`
- **Descrição:** Vitor Oliveira contratou o Laboratório para construir o VitorOS (cockpit + Negão). Cliente interno — **não entra em CRM comercial**.
- **Última atualização:** 2026-05-31

### Negão (sub-VitorOS)
- **ID:** PROJ-002-NEGAO
- **Prefixo:** NEGAO
- **Natureza:** cliente-interno
- **Status:** futuro
- **CRM:** —
- **Legado:** TASK-017 a TASK-020
- **Repo / deploy:** `centralvitor` · `ia.vitoroliv.com`
- **Descrição:** Agente pessoal do Vitor (memória episódica, chat, sugestões). Trilha B do VitorOS.
- **Última atualização:** 2026-05-31

### Landing Page Pintor
- **ID:** PROJ-LP
- **Prefixo:** LP-PINTOR
- **Natureza:** produto-teste
- **Status:** ativo
- **CRM:** crm_landing_pintor
- **Legado:** TASK-001, TASK-002
- **Repo / deploy:** Webflow (Premium) · subpath `dominio/slug` · legado vitrine: `frontend/lp-pintor/` + API `/previas/`
- **Descrição:** Produto comercial funil invertido R$ 69 PIX. **KPI vitrine 1/1** (Stephanie). **P0:** LP-PINTOR-007 Webflow oficial · captação gateada até página no ar.
- **Última atualização:** 2026-06-02

### Consultoria Dr. Viola
- **ID:** PROJ-VIOLA
- **Prefixo:** VIOLA
- **Natureza:** consultoria
- **Status:** futuro
- **CRM:** crm_laboratorio
- **Legado:** —
- **Repo / deploy:** —
- **Descrição:** Lead de consultoria do Laboratório — agentes para consultório de ginecologia e perícias trabalhistas. Vive no CRM Laboratório até virar contrato; então gera tasks `VIOLA-XXX`.
- **Última atualização:** 2026-05-31

### AppVS
- **ID:** PROJ-APPVS
- **Prefixo:** APPVS
- **Natureza:** produto-futuro
- **Status:** futuro
- **CRM:** crm_appvs
- **Legado:** —
- **Repo / deploy:** —
- **Descrição:** Produto futuro para logística (motoristas, transportadoras, rotas). CRM próprio quando existir comercialmente.
- **Última atualização:** 2026-05-31

---

<!-- Novos projetos acima desta linha -->
