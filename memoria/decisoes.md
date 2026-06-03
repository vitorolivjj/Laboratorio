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

### Produção LP in-house (Webflow revogado) — 2026-06-03

- **Contexto:** Após avaliar Webflow por dentro, fricção operacional sem ganho proporcional. Template `/previas/exemplo-pintor/` aprovado (3 dobras, R$ 69).
- **Decisão:**
  - **Produção oficial:** HTML/CSS + `config.json` + build estático · URL `api.laboratorioagentes.com.br/previas/{slug}/`
  - **Webflow revogado** — não contratar Premium; `webflow_lp_pintor.md` = legado
  - **Captação Donizete liberada** — meta **10 leads** `pronto_pra_pagina`; grupos **genéricos** FB (não só pintores); **sem cidade fixa** (cidade = dado do lead)
  - Ativar = `ativo: true` + rebuild · takedown = remove dist ou expira prévia
- **Responsável:** Loide + Dev (produção) · Donizete (captação)
- **Ref:** [producao_lp_pintor.md](ronaldo_maestro/producao_lp_pintor.md) · [plano_atuacao_donizete_lp.md](ronaldo_maestro/plano_atuacao_donizete_lp.md)

### Webflow como plataforma LP — 2026-06-02 — **REVOGADA**

- **Substituída por:** decisão 2026-06-03 in-house acima. Não executar LP-PINTOR-007 Webflow nem VITOR-001.

### Templates Meta WhatsApp — abertura proativa LP — 2026-06-02

- **Contexto:** Abordagem LEAD-001 com texto livre proativo; Meta exige template aprovado fora da janela 24h (gargalo operacional).
- **Decisão:**
  - Fluxo 2 etapas: (1) template `abertura_pintor_contato` + APROVAR Vitor · (2) link inbound após resposta
  - Código: `send_client_template` · doc `memoria/caio_manteiga/templates_meta_wa.md`
  - Vitor cadastra template no Meta Business Manager antes da próxima abordagem
- **Responsável:** Vitor (Meta) · Dev (código) · Caio (script)
- **Ref:** LP-PINTOR-006 · operacao_landing_pintor §9

### KPI vitrine comercial + plano 4 ondas — 2026-06-02

- **Contexto:** Fases 0–4 concluídas; vitrine = Lab prova entrega + venda low-ticket.
- **Decisão:**
  - **KPI único:** 1 lead `ativo` (R$ 69 PIX) em `crm/crm_landing_pintor.md`
  - Produto piloto: **PROJ-LP** (funil invertido); VitorOS pausado até vitrine
  - Execução: Ondas 1–4 (consolidar → LP mínimo → LAB-006 grafo → narrativa)
  - Lead manual válido antes de escalar Donizete/Facebook
- **Responsável:** Vitor (estratégia) · Ronaldo · Dev · Loide · Caio
- **Ref:** plano vitrine jun/2026 · `contexto/contexto_global.md`

### Fase 4 — Autoevolução supervisionada (resumo 1×/dia) — 2026-06-02

- **Contexto:** Fases 0–3 no ar; Vitor quer evolução proposta, nunca automática em memória/processos.
- **Decisão:**
  - Resumo diário via WhatsApp (timer 09:00 BRT) · propostas append-only
  - `APROVAR XXXX` aplica lote · `RECUSAR XXXX` descarta
  - CLI `./run.sh evolution-digest` · dedup 1 execução/dia
- **Ref:** `memoria/autoevolucao_fase4.md`

### Fase 3 — Autonomia graduada (LAB-004) — 2026-06-02

- **Contexto:** Fases 0–2 estáveis; agentes precisam executar ferramentas com tier auto vs aprovação.
- **Decisão:**
  - Catálogo em `laboratorio/autonomy/` · porta única `run_action()`
  - CLI `./run.sh agent-action` · aprovação WhatsApp tipo `agent_action`
  - Ações auto: log, recall, patrulha dry-run, alerta Vitor, nota em task
  - Ações com OK: mensagem proativa a cliente, piloto LangGraph
- **Ref:** `memoria/autonomia_graduada_fase3.md`

### Fase 2 — Piloto LangGraph (LAB-003) — 2026-06-02

- **Contexto:** Fase 0–1 estáveis; validar motor paralelo ao CrewAI numa task real.
- **Decisão:**
  - Task piloto **LAB-003** em `executando.md` · grafo `load→plan→work→cost_gate→finalize`
  - Checkpoints em `logs/langgraph_pilot.sqlite` · CLI `./run.sh graph-pilot TASK_ID`
  - Memória semântica no nó `load` · gasto alto notifica Vitor no `cost_gate`
  - CrewAI mantido para Caio inbound e orquestrador clássico
- **Responsável:** Dev · Ronaldo
- **Ref:** `memoria/langgraph_piloto_fase2.md` · `tasks/LAB-003.md`

### Fase 1 — Memória semântica Supabase — 2026-06-01

- **Contexto:** Agentes precisam lembrar por significado; projeto Supabase `pwlpdpwxxhbsmkclrpoa` já existe (VitorOS).
- **Decisão:**
  - Tabela `lab_semantic_memories` + pgvector (1536, `text-embedding-3-small`)
  - Backend Lab conecta via `SUPABASE_DB_URL` (Postgres); publishable key só para frontend
  - Sync de `memoria/`, `contexto/` e arquivos estratégicos Ronaldo
  - Injeção automática no orquestrador e no LLM WhatsApp Vitor quando memória ativa
- **Responsável:** Vitor (credenciais) · Dev (implementação)
- **Ref:** `memoria/memoria_semantica_fase1.md` · `supabase/README.md`

### Fase 0 — Reset kanban + aprovação WhatsApp — 2026-06-01

- **Contexto:** Roadmap em fases (memória semântica, LangGraph, skills, autoevolução) exige trava de segurança antes de mais autonomia.
- **Decisão:**
  - Kanban ativo **arquivado** (reversível em `tasks/arquivado.md`); filas `executando` / `planejando` / `backlog` vazias até nova task
  - **Mensagem proativa a cliente** → pede OK no WhatsApp do Vitor (`APROVAR XXXX` / `RECUSAR XXXX`)
  - **Gasto alto** → limiar `APPROVAL_COST_THRESHOLD_USD` (padrão US$ 1); infra pronta, gatilhos LLM plugados nas fases seguintes
  - **Inbound Caio** (quem escreveu primeiro) e **canal Vitor operacional** continuam sem trava
- **Responsável:** Vitor (definição) · Dev (implementação)
- **Agentes impactados:** caio_manteiga, ronaldo_maestro, todos com envio proativo
- **Validade / revisar em:** Permanente até Fase 3 (autonomia graduada) revisar escopo
- **Ref:** `memoria/aprovacao_whatsapp_fase0.md`

### Auditoria pós-conclusão do Ronaldo — auditar, delegar e criar follow-ups — 2026-06-01

- **Contexto:** o ciclo terminava ao concluir a task; faltava um passo automático de conferência que gerasse os próximos passos sem depender do Vitor.
- **Decisão:**
  - Toda task que entra em `concluidas.md` é **auditada automaticamente** (`ronaldo-audit.timer`, 10 min, alinhado à cadência).
  - Ronaldo registra veredito (`aprovado` / `aprovado_com_ressalvas` / `ajustes_necessarios`) + gaps + aprendizados em `logs/auditorias.md`.
  - Se houver gap/próximo passo, **cria até 2 follow-ups** no `backlog` já com briefing (delegação escrita), usando o **prefixo do projeto** da task-mãe.
  - Follow-ups nascem em `backlog` (nunca direto em execução); promoção a `executando` respeita a cadência de 10 min.
  - Escala ao Vitor via Caio **só** quando precisa de decisão dele; senão opera em autonomia.
  - **Idempotente:** estado em `logs/ronaldo_audit_state.json`; histórico anterior marcado como já auditado.
  - Sem `OPENAI_API_KEY` → fallback heurístico (auditoria mínima, sem inventar follow-ups).
- **Responsável:** Vitor (mandato) · Ronaldo (execução)
- **Agentes impactados:** Ronaldo (orquestração); Dev/Loide/Caio/Donizete (recebem follow-ups)
- **Validade / revisar em:** revisar quando o volume de follow-ups exigir ajuste do teto (hoje 2/task)
- **Ref:** `memoria/ronaldo_maestro/rotina_pos_task.md` · `backend/src/laboratorio/ops/ronaldo_audit.py`

### Sprint velocidade LP — patrulha 30 min + WIP 4 — 2026-06-03

- **Contexto:** Meta 10 leads/dia; fluxo lento; patrulha tardia (24h/72h).
- **Decisão:**
  - Captação: crítico **30 min** sem pronto/prospectado/pasta captura; warn **15 min**
  - `WIP_SOFT_MAX=4`, `TASK_CADENCE_MIN=2`, patrulha timer **10 min**
  - Tasks fatiadas: LP-PINTOR-001 (5) + 001B (5); produção **LP-PINTOR-009** por lead
  - Donizete modo sprint 48h (6–8 posts, 25–60 min, 2 leads/h)
  - Script [`lp_publish_lead.py`](../../scripts/lp_publish_lead.py); Fase 2 em [fase2_velocidade_lp.md](ronaldo_maestro/fase2_velocidade_lp.md)
- **Ref:** `donizete_capture.py` · `config.py`

### Cadência de tasks — ajuste ritmo (menos tempo parado) — 2026-06-03

- **Contexto:** Tasks ficando muito tempo em `executando` sem fechar frente.
- **Decisão:**
  - `TASK_CADENCE_MIN` padrão **5 min** (antes 10) entre starts
  - `WIP_SOFT_MAX` padrão **2** tasks simultâneas
  - Alerta patrulha/painel se task em executando **>24h** (crítico **>48h**) — fatiar, concluir parcial ou backlog
  - Timers VPS: patrulha **15 min**, auditoria **5 min**
- **Ref:** `config.py` · `ronaldo_patrol.py` · `tasks/executando.md`

### Cadência de tasks substitui teto de WIP — 2026-06-01

- **Contexto:** WIP rígido (máx. 3 simultâneas) limitava o volume; com múltiplos projetos/agentes, faz mais sentido controlar o **ritmo de início** que o total simultâneo.
- **Decisão:**
  - **Sem teto rígido.** O limite passa a ser **cadência**: intervalo mínimo entre iniciar uma task e a próxima (`TASK_CADENCE_MIN`, padrão ~~10~~ **5 min** desde 2026-06-03).
  - Ronaldo pode ter várias frentes abertas, mas **não dispara várias de uma vez** — espaça os starts.
  - Teto opcional `WIP_SOFT_MAX` (0 = sem teto) para quem quiser um limite duro.
  - Painel mostra "Em execução: N" + "Cadência Xmin (livre / aguarda Ymin)". Patrulha alerta só se cadência for violada (2 starts em < intervalo) ou teto opcional excedido.
  - Timestamp real de cada start em `logs/task_cadence_state.json`.
- **Responsável:** Vitor (definição) · Ronaldo (execução)
- **Agentes impactados:** Ronaldo (orquestração)
- **Validade / revisar em:** Ajustar `TASK_CADENCE_MIN` conforme ritmo da operação

### Operação Landing Page Pintor — funil invertido R$ 69 — 2026-05-31

- **Contexto:** Produto/teste PROJ-LP reativado com playbook completo (Vitor). Modelo "entrega antes de vender".
- **Decisão:**
  - **Funil invertido:** produz a página primeiro, sobe prévia grátis, cobra ativação **R$ 69 PIX**. Prévia sai do ar em 3–5 dias se não ativar.
  - **Separação inquebrável:** Facebook = só captação (Donizete). Venda só no WhatsApp (Caio), sem vínculo com perfil de prospecção.
  - **Delegação:** Donizete (captação/qualificação/CRM), Loide+Dev (template 2×4 + host grátis), Caio (venda), Ronaldo (alinha/delega/audita).
  - **KPI-chave:** taxa de ativação (vendas ÷ páginas entregues). Conversão caiu → revisar qualificação, não preço.
  - **CRM próprio** `crm_landing_pintor`, funil: prospectado → enviado_loide → previa_no_ar → abordado → ativo/recusou. Tag origem indicacao/autopromocao.
- **Responsável:** Vitor (modelo) · Ronaldo (orquestração)
- **Agentes impactados:** Donizete, Loide, Dev, Caio, Ronaldo
- **Validade / revisar em:** Após primeiras ativações (medir taxa) · Manual: `memoria/ronaldo_maestro/operacao_landing_pintor.md`

### Organização por projeto — hierarquia fábrica/projeto/CRM — 2026-05-31

- **Contexto:** Painel misturava 3 naturezas (Laboratório-fábrica, projetos internos/contratados, produtos/leads comerciais).
- **Decisão:**
  - **Laboratório = fábrica** (operação principal), não "um projeto".
  - **Projetos** com prefixo padronizado: `LAB-` (Core), `VITOROS-` (cliente interno), `LP-PINTOR-` (produto/teste), `VIOLA-` (consultoria), `APPVS-` (futuro), `NEGAO-` (sub-VitorOS). Registry: `projetos/projetos.md`.
  - **Toda task pertence a um projeto** (campo `Projeto:` / prefixo / mapa legado). Nenhuma task solta.
  - **CRM segmentado por finalidade:** `crm_laboratorio` (leads da empresa — Dr. Viola, clínicas, consultorias) e `crm_landing_pintor` (produto). VitorOS/Negão/interno **não entram em CRM**.
  - Painel: sidebar com submenu por projeto · seção **Projetos** master-detail (cada projeto mostra suas tasks e **o CRM dentro do próprio projeto**) · seção **Tasks** com filtro por projeto. Sem aba de CRM solta.
- **Responsável:** Vitor (definição) · Dev/Ronaldo (execução — LAB-002)
- **Agentes impactados:** Todos (Ronaldo classifica tasks; Donizete/Caio usam CRM correto)
- **Validade / revisar em:** Permanente — novos projetos entram no registry

### Fluxo total de tasks liberado — 2026-05-31

- **Contexto:** Patrulha operacional + WhatsApp Vitor ativos. Vitor autoriza Ronaldo conduzir o ciclo completo sem gates intermediários.
- **Decisão:**
  - Ronaldo opera **backlog → planejando → executando → concluído → próxima TASK** de forma autônoma e contínua
  - **Sem** aguardar OK do Vitor entre transições de status
  - **Auditoria Ronaldo** = gate para `concluído` (não aceite manual prévio)
  - Aceite Vitor = **informação** (WhatsApp/painel), não bloqueio — salvo escalacao explícita (credencial, custo, prod Lab)
  - Ao liberar slot WIP: priorizar fila PROJ-002 (TASK-013+) automaticamente
  - Patrulha 30 min + alerta WhatsApp só para exceções
- **Responsável:** Vitor (autorização) · Ronaldo Maestro (execução)
- **Agentes impactados:** Todos
- **Validade / revisar em:** Permanente até revogação

### Canal WhatsApp Vitor — operacional + alertas — 2026-05-31

- **Contexto:** Vitor autoriza conversas do +5533999353242 com Caio como canal do dono (Ronaldo). Patrulha periódica de tasks/estrutura; escalacao WhatsApp quando precisar autorização.
- **Decisão:**
  - `memoria/autorizacao_vitor_whatsapp.md`
  - Backend: número autorizado → Ronaldo; outros → Caio comercial
  - `./run.sh ronaldo-patrol` + timer 30 min VPS
  - Caio envia alerta quando Ronaldo detectar bloqueio crítico (dedup 4 h)
- **Responsável:** Vitor · Ronaldo · Caio · Dev
- **Agentes impactados:** ronaldo_maestro, caio_manteiga
- **Validade / revisar em:** Permanente até revogação

### Protocolo delegação + conferência + evolução — 2026-05-31

- **Contexto:** Vitor exige que **todas** as tasks sejam delegadas pelo Ronaldo, conferidas por ele, e que aprendizados alimentem evolução constante.
- **Decisão:**
  - Protocolo oficial: `memoria/ronaldo_maestro/protocolo_delegacao_conferencia.md`
  - **Gate `executando`:** briefing Ronaldo por agente em `TASK-XXX.md`
  - **Gate `concluído`:** § Auditoria do Ronaldo preenchida + aceite quando aplicável
  - **Pós-aprovação:** entrada em `aprendizados.md` + `evolucao_orquestracao.md`
  - Especialistas **não iniciam** TASK sem delegação; sessões diretas exigem backfill em 24h
  - Laboratório = fábrica (agentes, skills, memória, UX specs); repos produto = código only
- **Responsável:** Vitor · Ronaldo Maestro (execução)
- **Agentes impactados:** Todos
- **Validade / revisar em:** Permanente

### Laboratório = fábrica · centralvitor = produto — 2026-05-31

- **Contexto:** Risco de misturar orquestração (agentes, skills, memória) com código deployável do VitorOS.
- **Decisão:**
  - **Laboratório** concentra: agentes (`agentes/`), skills (`.cursor/skills/`), memória (`memoria/`), tasks, logs, **mockups/specs UX** (`docs/ux/`).
  - **centralvitor** contém **somente** código, migrations e deploy do app em `vitoroliv.com`.
  - Dev implementa no centralvitor lendo specs da fábrica; Loide nunca commita artefatos de agente no repo produto.
- **Responsável:** Vitor
- **Agentes impactados:** Dev, Loide, Ronaldo
- **Validade / revisar em:** Permanente

### TASK-001 / TASK-002 canceladas (teste pintores) — 2026-05-31

- **Contexto:** Landing low ticket pintores (TASK-001) e captação orgânica Donizete→Caio (TASK-002) eram experimentos de validação.
- **Decisão:** Cancelar e arquivar ambas. Não continuar funil pintores nem captação de leads para esse ICP.
- **Responsável:** Vitor
- **Agentes impactados:** Caio, Donizete, Juarez, Dev (escopo encerrado)
- **Validade / revisar em:** Permanente — histórico preservado em `tasks/arquivado.md`

### Ronaldo — autonomia para iniciar tasks — 2026-05-31

- **Contexto:** Vitor concedeu autonomia operacional ao Ronaldo Maestro para iniciar e mover tasks sem aprovação prévia a cada ciclo.
- **Decisão:**
  - Ronaldo **pode** criar `TASK-XXX`, mover `backlog → planejando → executando`, emitir briefings e acionar agentes **quando julgar o momento certo**.
  - **Não precisa** pedir permissão ao Vitor para iniciar execução de tasks já priorizadas no backlog (ex.: PROJ-002 VitorOS TASK-010+).
  - **Deve registrar** toda iniciativa em `logs/eventos.md` + atualizar `tasks/` + briefing no doc da task.
  - **Respeitar WIP máx. 3** em `executando.md`; se iniciar 4ª, mover a de menor impacto para `aguardando` ou `backlog` com nota — não paralisar PROJ-002 por burocracia.
  - **Escalar ao Vitor apenas quando:** credenciais/contas novas, gasto financeiro, alteração em produção do Lab, decisão estrutural irreversível, bloqueio externo >48h.
  - **PROJ-002:** código/deploy **somente** `centralvitor` + VPS `vitoroliv.com` — nunca misturar com Lab.
- **Responsável:** Vitor (concessão) · Ronaldo Maestro (execução da política)
- **Agentes impactados:** Todos — especialmente Dev, Loide, Juarez
- **Validade / revisar em:** Permanente até Vitor revogar

### TASK-007 — Migração modelo Anthropic + WhatsApp em produção — 2026-05-31

- **Contexto:** TASK-007 em produção na VPS Hetzner; API Anthropic retornou `not_found` para `claude-sonnet-4-20250514` (snapshot descontinuado).
- **Decisão:**
  - **Especialistas (Caio, Juarez, Dev, Donizete):** migrar para `anthropic` / **`claude-sonnet-4-6`**.
  - **Ronaldo Maestro:** mantém `openai` / `gpt-5`.
  - **WhatsApp produção:** `https://api.laboratorioagentes.com.br/webhook/whatsapp` · VPS CPX21 · systemd `laboratorio-api`.
  - Atualizar `.env`, `.env.example`, `llm_config.py` DEFAULT_MODEL e docs operacionais.
- **Responsável:** Dev · Vitor (validação teste real)
- **Agentes impactados:** Caio (crítico — WhatsApp), demais especialistas
- **Validade / revisar em:** Quando Anthropic deprecar `claude-sonnet-4-6` ou nova evidência por agente

### TASK-006 — Arquitetura oficial de modelos v1 — 2026-05-30

- **Contexto:** TASK-005 implementou roteamento LLM; Vitor aprovou ajuste final antes dos testes operacionais reais.
- **Decisão:**
  - **Princípio:** camada estratégica do Grupo = padrão **Ronaldo** (OpenAI); especialistas = modelos distintos conforme função e evidência.
  - **Ronaldo Maestro:** `openai` / `gpt-5` — estratégia, coordenação, priorização, governança.
  - **Caio, Juarez, Dev, Donizete:** `anthropic` / `claude-sonnet-4-20250514` _(especialistas migrados para `claude-sonnet-4-6` em 2026-05-31 — ver decisão TASK-007 abaixo)_.
  - Fase atual: aprender, validar, medir, acumular histórico — não otimizar custo.
  - Verificação: `./run.sh llm-config`.
- **Responsável:** Vitor (aprovação) · Ronaldo Maestro (consolidação) · Dev (E6 TASK-005)
- **Agentes impactados:** Todos
- **Validade / revisar em:** Após ciclo de testes operacionais reais ou nova evidência por agente

### TASK-005 — Modelos LLM por agente (Anthropic Sonnet) — 2026-05-30

- **Contexto:** Relatório TASK-005 aprovado pelo Vitor; `*_PROVIDER` no `.env` não eram lidos pelo backend.
- **Decisão:**
  - Todos os agentes passam a usar **anthropic / claude-sonnet-4-20250514** _(supersedido parcialmente por TASK-006 — Ronaldo passa a OpenAI gpt-5)_.
  - Implementar roteamento em `backend/src/laboratorio/agents/llm_config.py` + `builder.py`.
  - Fallback: `DEFAULT_PROVIDER` + `DEFAULT_MODEL` quando variável específica ausente.
  - Comando de verificação: `./run.sh llm-config`.
  - Caio e Juarez: mantidos em Anthropic (já performavam bem).
  - Dev e Ronaldo: migrados de OpenAI para Anthropic.
  - Donizete: provider definido pela primeira vez.
- **Responsável:** Vitor (aprovação) · Dev (E6)
- **Agentes impactados:** Todos
- **Validade / revisar em:** Após checklist validação §4.3 TASK-005-relatorio-modelos.md

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
