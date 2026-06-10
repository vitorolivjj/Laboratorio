# Script Caio — LP Pintor R$ 69 (PROJ-LP)

> **🗄 ARQUIVO / PINTOR — LEGADO** (2026-06-10) · Piloto Landing Page Pintor encerrado — mantido só como histórico/aprendizado. **Não é mais foco** de nenhum agente. Novo posicionamento: negócios locais que perdem clientes por bagunça em captação, atendimento e comercial.

**Playbook completo:** [playbook_comercial_lp_pintor.md](playbook_comercial_lp_pintor.md)  
**Templates Meta:** [templates_meta_wa.md](templates_meta_wa.md) · LP-PINTOR-006

## Funil (5 etapas)

1. **Abertura** — sem link · pedir permissão  
2. **Entrega** — link prévia · "o que achou?"  
3. **Oferta** — R$ 69 PIX único · ancoragem lata de tinta  
4. **Fechamento** — chave `financeiro@vitoroliv.com` · **Vitor confirma PIX antes de ativar**  
5. **Pós-venda** — só após confirmação Vitor

## CLI (abertura proativa — template Meta)

```bash
cd backend
./run.sh agent-action send_client_template --json '{
  "to_wa_id": "5516997559557",
  "template_name": "abertura_pintor_contato",
  "body_params": ["Stephanie", "Jardinópolis"]
}'
```

## Inbound (janela 24h)

Caio responde automaticamente via `lp_leads.py` + playbook — objeções, etapas e LLM com contexto CRM.

## Critérios

- [x] Playbook comercial documentado
- [x] Integração código (`lp_leads` + `caio_handler`)
- [x] Primeira ativação R$ 69 — LEAD-001 Stephanie · KPI 1/1
