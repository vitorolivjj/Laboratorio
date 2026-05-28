# Decisões (memória compartilhada)

Registro de **decisões** visíveis a **todos os agentes**.

> Arquitetura completa: [docs/arquitetura-agentes.md](../docs/arquitetura-agentes.md)  
> Decisões **estratégicas de longo prazo** (Ronaldo): também `memoria/ronaldo_maestro/decisoes_criticas.md`  
> Memória de domínio por agente: `memoria_*_<agente>.md` — não duplicar aqui salvo impacto global

## Como usar

1. Uma entrada por decisão relevante.
2. Das mais recentes para as mais antigas.
3. Se afetar prioridade global, o Ronaldo deve espelhar ou referenciar em `decisoes_criticas.md`.

## Template

```markdown
### [Título] — YYYY-MM-DD
- **Contexto:**
- **Decisão:**
- **Responsável:** Vitor | agente
- **Agentes impactados:**
- **Validade / revisar em:**
```

---

## Decisões

### TASK-001 — número WA adiado; deploy desacoplado — 2026-05-28

- **Contexto:** Vitor autorizou prosseguir sem configurar WhatsApp agora.
- **Decisão:**
  - Publicar landing **antes** do número real (placeholder mantido).
  - Número WA entra quando Vitor disponibilizar — editar `index.html` e redeploy.
  - E5 fecha com **URL pública**, não com WA configurado.
- **Responsável:** Vitor
- **Agentes impactados:** Dev, Caio Manteiga
- **Validade / revisar em:** Antes de tráfego real (E7)

### TASK-001 Gateway v0 — somente WhatsApp — 2026-05-28

- **Contexto:** Vitor respondeu escalonamento da Rodada 1; objetivo v0 é velocidade, baixa fricção, validar interesse/conversão.
- **Decisão:**
  - **v0:** único CTA ativo = **WhatsApp** (sem checkout na landing).
  - **v1 (futuro):** CTA secundário **Mercado Pago** — Dev reserva estrutura em `frontend/LANDING.md`, oculta na v0.
  - KPI v0: cliques e respostas WhatsApp; pagamentos online ficam para após validação de interesse.
- **Responsável:** Vitor
- **Agentes impactados:** Dev, Caio Manteiga, Juarez
- **Validade / revisar em:** Após 100 visitas ou 20 conversas WhatsApp (H-001)

### TASK-001 Rodada 1 — escopo MVP fechado — 2026-05-28

- **Contexto:** TASK-001 em `executando`; bloqueio parcial (gateway pagamento); necessidade de plano imediato sem código ainda.
- **Decisão:**
  - Preço **R$ 49** na v1 (H-001 permanece `a_testar` com 20 leads).
  - Landing **HTML estático** em `frontend/` — uma página, sem login, sem CMS.
  - **CTA primário:** WhatsApp; **CTA secundário:** adiado — Mercado Pago na v1 (placeholder Dev).
  - Escopo fixo: 5 seções (hero, serviços, prova social leve, preço, CTA).
  - Execução **paralela** 48h: Dev → E2 | Caio → E3 | Juarez → E4.
- **Responsável:** Ronaldo Maestro (coord.) — confirmação gateway: Vitor
- **Agentes impactados:** Dev, Caio Manteiga, Juarez, Vitor
- **Validade / revisar em:** Após entregas E2–E4 ou decisão de gateway (2026-05-30)

### Sistema de memória multiagente — 2026-05-28

- **Contexto:** Necessidade de camadas de memória por agente com auditoria do Ronaldo.
- **Decisão:** Arquivos `memoria_*_<agente>.md` + compartilhados (`decisoes`, `aprendizados`, `hipoteses_testadas`).
- **Responsável:** Dev
- **Agentes impactados:** Todos
- **Validade / revisar em:** Após TASK-001

### Estrutura operacional do ecossistema — 2026-05-28

- **Contexto:** Necessidade de memória, contexto, tarefas e workflows compartilhados.
- **Decisão:** Pastas `memoria/`, `contexto/`, `tasks/`, `logs/`, `workflows/` na raiz do repositório.
- **Responsável:** Dev
- **Agentes impactados:** Todos
- **Validade / revisar em:** Após primeiro ciclo real de orquestração

---

<!-- Novas entradas acima desta linha -->
