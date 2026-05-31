# TASK-007 — Conectar Caio ao WhatsApp

**ID:** TASK-007  
**Projeto:** PROJ-001  
**Status:** `concluido`  
**Prioridade:** alta  
**Criada em:** 2026-05-28  
**Concluída em:** 2026-05-31  
**Responsável:** dev · caio_manteiga  

---

## Objetivo

Permitir que mensagens recebidas no WhatsApp Business sejam processadas pelo backend e respondidas pelo agente Caio.

**Fluxo:** WhatsApp → Backend → Caio → WhatsApp

## Fluxo implementado

1. Usuário envia mensagem no WhatsApp.
2. Meta chama `POST /webhook/whatsapp`.
3. Backend extrai remetente (`from`) e texto.
4. Caio (CrewAI) gera resposta curta para WhatsApp.
5. Backend envia resposta via Graph API.
6. Troca registrada em `logs/whatsapp_mensagens.md`.

## Entregáveis

| ID | Entregável | Status |
|----|------------|--------|
| E1 | Webhook GET/POST (`/webhook/whatsapp`) | ✅ |
| E2 | Recepção e parse de mensagens texto | ✅ |
| E3 | Integração Caio ↔ WhatsApp (CrewAI + Graph API) | ✅ |
| E4 | Log de mensagens (`logs/whatsapp_mensagens.md`) | ✅ |
| E5 | Dedup de `message_id` (retries Meta) | ✅ |
| E6 | CLI `./run.sh serve` + `whatsapp-check` | ✅ |
| E7 | Teste real documentado (abaixo) | ✅ |

## Arquivos

```
backend/src/laboratorio/
├── api/app.py                 # FastAPI — webhook + health
└── whatsapp/
    ├── parser.py              # payload Meta → InboundMessage
    ├── handler.py             # orquestra inbound → Caio → outbound
    ├── caio_handler.py        # CrewAI Caio
    ├── client.py              # envio Graph API
    ├── logger.py              # log markdown
    └── dedup.py               # message_id processados
```

## Setup Meta (WhatsApp Cloud API)

1. [Meta for Developers](https://developers.facebook.com/) → criar app → adicionar produto **WhatsApp**.
2. Em **API Setup**, anotar:
   - **Phone number ID** → `WHATSAPP_PHONE_NUMBER_ID`
   - **Temporary access token** (ou token permanente) → `WHATSAPP_ACCESS_TOKEN`
3. Definir `WHATSAPP_VERIFY_TOKEN` (string aleatória sua) no `.env`.
4. Expor o backend publicamente (dev local):

```bash
# Terminal 1 — backend
cd backend
./run.sh serve

# Terminal 2 — túnel (ex.: ngrok)
ngrok http 8000
```

5. No Meta → **Configuration** → **Webhook**:
   - **Callback URL:** `https://<seu-tunel>/webhook/whatsapp`
   - **Verify token:** mesmo valor de `WHATSAPP_VERIFY_TOKEN`
   - Assinar campo **messages**

6. Validar config local:

```bash
./run.sh whatsapp-check
curl http://localhost:8000/health
```

## Produção (VPS — URL fixa)

Guia completo: [deploy/vps/README.md](../deploy/vps/README.md)

- DNS: `api.laboratorioagentes.com.br` → IP da VPS
- Webhook Meta: `https://api.laboratorioagentes.com.br/webhook/whatsapp`
- Scripts: `deploy/vps/setup-server.sh` + `deploy-app.sh`

## Critério de aceite (teste manual)

| Passo | Ação | Resultado esperado |
|-------|------|-------------------|
| 1 | Enviar `"Olá"` do celular para o número Business | Webhook recebe POST 200 |
| 2 | Aguardar resposta (5–30 s) | Caio responde no WhatsApp |
| 3 | Conferir log | Entrada em `logs/whatsapp_mensagens.md` |

**Resposta esperada (exemplo):**

> Olá! Sou o Caio, assistente do Laboratório de Agentes IA. Como posso ajudar?

> Variações naturais do LLM são aceitáveis desde que apresente o Caio e o Laboratório.

## Registro do teste real

| Campo | Valor |
|-------|-------|
| **Data** | 2026-05-31 |
| **Testador** | Vitor |
| **Número remetente** | 553399353242 |
| **Mensagem enviada** | Olá / Oi |
| **Resposta Caio** | Apresentação como assistente do Laboratório de Agentes IA ✅ |
| **Infra** | VPS Hetzner CPX21 · `api.laboratorioagentes.com.br` · HTTPS |
| **Modelo** | `claude-sonnet-4-6` (migrado de `claude-sonnet-4-20250514`, descontinuado) |
| **Status** | ✅ ok — primeira conversa real com humano |

Conversas subsequentes validadas no log (ex.: consulta sobre página institucional / marca de café).

## Variáveis de ambiente

Ver `backend/.env.example` — seção WhatsApp.

## Comandos

```bash
cd backend
./run.sh whatsapp-check    # valida .env
./run.sh serve             # uvicorn :8000
./run.sh check             # ambiente geral
```

## Notas

- Processamento assíncrono no webhook (Meta exige resposta rápida; Caio roda em background).
- `META_APP_SECRET` opcional em dev; recomendado em produção (valida `X-Hub-Signature-256`).
- IDs processados em `backend/data/wa_processed_ids.json` (gitignored).

---

**Relacionada:** TASK-001 (funil pintores · WA real), TASK-002 (Donizete → Caio)
