# Memória estratégica — Ronaldo Maestro

**Escopo:** longa (meses / trimestre)  
**Dono:** Ronaldo Maestro (escrita prioritária; leitura orientada para orquestração)  
**Complemento operacional:** `memoria/ronaldo_maestro/` (histórico, mapa, regras de fluxo)

---

## Função

Guardar visão de longo prazo do ecossistema: prioridades do Vitor, direção de negócio, padrões de coordenação e decisões que atravessam projetos.

Ronaldo **lê** esta memória antes de orquestrar e **atualiza** após auditar entregas.

---

## O que registrar aqui

- Prioridades estratégicas do trimestre
- Princípios de coordenação que se repetem
- Decisões de direção (espelhar em `decisoes.md` se todos precisarem saber)
- Padrões de delegação que funcionaram
- Riscos sistêmicos do ecossistema

---

## O que NÃO registrar aqui

- Detalhe técnico de implementação → `memoria_tecnica_dev.md`
- Copy de oferta → `memoria_comercial_caio.md`
- Checklist operacional de obra/processo → `memoria_operacional_juarez.md`
- Log de evento pontual → `logs/eventos.md`

---

## Template — entrada estratégica

```markdown
### YYYY-MM-DD — [Título]
- **Horizonte:** trimestre | ano
- **Contexto:**
- **Decisão / princípio:**
- **Impacto em agentes:**
- **Briefing curto para execução:** (2–4 linhas)
- **Revisar em:**
```

---

## Prioridades estratégicas atuais

| # | Prioridade | Status |
|---|------------|--------|
| 1 | Validar fluxo comercial real (TASK-001 — landing pintores) | em_andamento |
| 1b | Validar captação orgânica (TASK-002 — Donizete → Caio) | em_andamento |
| 2 | Manter ecossistema simples: markdown first, sem over-engineering | ativo |
| 3 | Monetização low ticket antes de escalar complexidade | ativo |

---

## Princípios de coordenação (Ronaldo)

1. Memória longa vira **briefing curto** antes de delegar.
2. Um ciclo = uma TASK ativa quando possível.
3. Após entrega: auditar → registrar em `aprendizados.md`, `decisoes.md`, `hipoteses_testadas.md`.
4. Especialista executa; Ronaldo consolida e decide divergências.

---

## Registro

<!-- Entradas estratégicas abaixo, mais recentes primeiro -->

### 2026-05-28 — Dashboard operacional inicial #orquestracao

- **Horizonte:** contínuo
- **Contexto:** TASK-001 e TASK-002 ativas; necessidade de visão sistêmica.
- **Decisão / princípio:** Métricas centralizadas em `dashboard/metricas_operacionais.md` — markdown-first, atualização manual pelo Ronaldo.
- **Impacto em agentes:** Ronaldo consolida; demais agentes alimentam fontes (CRM, TASK, logs).
- **Revisar em:** Fim de cada rodada ou diariamente com TASK ativa

- **Horizonte:** trimestre
- **Contexto:** Ecossistema precisava de camadas de memória por agente.
- **Decisão / princípio:** Memória longa (Ronaldo) → briefing curto → execução → auditoria → memória compartilhada.
- **Impacto em agentes:** Todos consultam `decisoes.md` e `aprendizados.md`; cada um mantém sua memória de domínio.
- **Briefing curto para execução:** "Consulte sua memória de domínio + TASK ativa; não reinvente contexto."
- **Revisar em:** Após conclusão TASK-001
