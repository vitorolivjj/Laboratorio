# Plano de Negócio — resumo operacional (v1 · 2026-06-11)

Fonte da verdade completa: vault Obsidian do Vitor (`Laboratorio/` — Matriz, Estratégia
Comercial, Produtos P00/P01). Este resumo existe para os agentes operarem alinhados.

## Posicionamento

O Laboratório de Agentes ajuda **negócios locais a parar de perder clientes por bagunça
em captação, atendimento e comercial**. Encontramos vazamentos no caminho entre o
cliente interessado e a venda — e transformamos em processo.

- **Não vendemos IA nem hype.** IA no bastidor, processo na frente.
- **Rosto público: Vitor** (fim do anonimato desde 2026-06-11). O Laboratório é a
  estrutura; perfil único do Vitor compartilha o conteúdo do Laboratório.
- Frases-guia: "A IA gera. O processo vende." · "Primeiro processo. Depois automação."

## Escada comercial (preços fase de validação)

1. **Dossiê de Vazamentos** — GRÁTIS. Página visual com sinais públicos de vazamento.
   Abre conversa; nunca vira diagnóstico completo gratuito.
2. **Plano de Ataque Comercial/Operacional** — **R$450, pagamento antecipado**
   ("pagou, agenda; não pagou, não agenda"). Análise + prioridade + Sprint recomendada.
   Não inclui implantação.
3. **Sprint de Implantação** — R$1.500–4.000+ (mín. R$1.500). 50% entrada / 50% antes
   da entrega final. Tipos: Presença Local · Atendimento e CRM · Comercial Ativo ·
   Automação Interna.
4. **Acompanhamento Mensal** — R$297–1.500/mês, antecipado (inadimplência pausa).
5. **Projetos Especiais** — sob orçamento (40/30/30), só com escopo e contrato.

## ICP prioritário

1. clínicas, consultórios e veterinárias · 2. advocacia/perícia/serviços profissionais ·
3. imobiliárias pequenas · 4. oficinas/serviços técnicos · 5. reforma/obra com orçamento ·
6. estética e negócios locais com agenda · 7. prestadores estruturados com equipe.

Lead bom: WhatsApp ativo, recebe contatos, perde follow-up, ticket relevante, capacidade
de pagar, aceita processo. **Score 0–10** (dor, pagamento, vazamento, canal, potencial —
0–2 cada): <6 arquiva/nutre · 6+ coleta profunda/Dossiê · 8+ prioridade.

## Funil oficial (CRM `crm_laboratorio.md`)

`novo → pesquisado → vazamento_provavel → dossie_enviado → aguardando_resposta →
respondeu → qualificando → pronto_plano_ataque → plano_ataque_enviado →
plano_ataque_pago → call_agendada → plano_em_producao → plano_entregue →
sprint_proposta → sprint_fechada → acompanhamento_proposto → cliente_ativo`
(saídas: `pausado`/`perdido` com motivo/`arquivado`)

## Papéis (esteira do Dossiê — implantada 2026-06-11)

```
Ronaldo sugere célula (segmento×área) → VITOR aprova
  → Donizete varre o Google Maps (Places API) e pontua → 6+ entram no CRM
    → Juarez audita o atendimento (passiva sempre; ativa por template, se ligada)
      → Ronaldo monta o DIAGNÓSTICO do Dossiê (cérebro da análise)
        → página HTML gerada (design Loide, build Dev) em /d/{slug}.html
          → VITOR aprova o Dossiê → Caio aborda (template) e conduz até o pagamento
```

- **Donizete** — captação por célula via Places (`ops/captacao.py` · `captacao-celula`).
  Pontua 0–10; só 6+ entra. Áreas/células: `memoria/captacao_celulas.md`.
- **Juarez** — auditor de atendimento: passiva (`ops/juarez_auditoria.py`, sempre) +
  sondagem ativa (`whatsapp/juarez_sondagem.py` · `juarez-sondar`; número dedicado,
  kill-switch JUAREZ_SONDAGEM, 1× por lead, nunca agenda horário real).
- **Ronaldo** — sugere células (`sugerir_celula_captacao`) e é o cérebro do diagnóstico
  do Dossiê (`ops/dossie.py` · `dossie-gerar`). Não desenha página.
- **Loide + Dev** — página do Dossiê (template `assets/dossie_template.html`, servida
  em /d/).
- **Caio** — cérebro em `memoria/caio_manteiga/cerebro_comercial.md`: CRM primeiro
  (mensagem por estágio do funil), fast-track de lead quente, oferta o Plano de Ataque
  e manda **link de pagamento por lead** ([LINK_PAGAMENTO] → Mercado Pago ou PIX);
  pagamento confirmado → Vitor assume (call). Abordagem proativa só por template
  (`abordar_lead`). Follow-up D+1/3/7/15.
- **Vitor** — aprova células e Dossiês (Fila Quente), faz as calls, decide exceções.

## Fase atual: VALIDAÇÃO (sem metas numéricas fixas)

Gates para sair da validação: 3–5 Dossiês reais enviados · 5 conversas reais ·
2 Planos de Ataque vendidos · 1 entregue · objeções mapeadas · modelo do Dossiê travado.
Só depois disso fixar metas com taxas reais.

## Regras inegociáveis (Manifesto)

Processo antes de IA · sem pagamento, sem execução · sem escopo, sem promessa ·
inadimplência pausa · conhecido tem MAIS regra · Vitor não cobra pessoalmente ·
cliente sem compromisso não entra · não automatizar bagunça · o Laboratório diz não.
