# VPS — WhatsApp Caio (produção)

Backend FastAPI em VPS com URL fixa `https://api.laboratorioagentes.com.br`.

**Tempo estimado:** ~45–60 min (primeira vez).

---

## O que você vai ter no final

```
WhatsApp Meta
    → https://api.laboratorioagentes.com.br/webhook/whatsapp
    → nginx (SSL)
    → uvicorn (systemd, 24/7)
    → Caio → resposta WhatsApp
```

Webhook configurado **uma vez** no Meta — sem ngrok.

---

## Parte 1 — Contratar VPS

### Recomendado: Hetzner CX22

1. [hetzner.com/cloud](https://www.hetzner.com/cloud/) → criar conta
2. **New Project** → **Add Server**
3. **Location:** Falkenstein ou Nuremberg (EU, ok para BR)
4. **Image:** Ubuntu 24.04
5. **Type:** CX22 (2 vCPU, 4 GB RAM) — ~€4–5/mês
6. **SSH key:** adicione a sua chave pública (`cat ~/.ssh/id_ed25519.pub`)
7. Crie o servidor e anote o **IP público**

Alternativa: DigitalOcean Droplet Basic $6/mo, Ubuntu 24.04.

---

## Parte 2 — DNS (domínio)

No painel onde está `laboratorioagentes.com.br` (Cloudflare, Registro.br, etc.):

| Tipo | Nome | Valor | TTL |
|------|------|-------|-----|
| **A** | `api` | `IP_DA_VPS` | 300 (ou Auto) |

Resultado: `api.laboratorioagentes.com.br` → sua VPS.

**Cloudflare:** se usar proxy laranja, pode funcionar, mas para o primeiro deploy prefira **DNS only** (nuvem cinza) até o certificado SSL estar ok.

Aguarde 5–15 min e teste:

```bash
dig +short api.laboratorioagentes.com.br
# deve retornar o IP da VPS
```

---

## Parte 3 — Preparar o servidor (uma vez)

SSH na VPS:

```bash
ssh root@IP_DA_VPS
```

Clone o repo (ou envie os scripts). Se o repo for **privado**, configure deploy key ou clone via HTTPS com token.

```bash
apt update && apt upgrade -y
git clone https://github.com/vitorolivjj/Laboratorio.git /opt/laboratorio-src
# ou seu fork/URL real
cd /opt/laboratorio-src/deploy/vps
chmod +x setup-server.sh deploy-app.sh
./setup-server.sh
```

O script instala: Python 3.12, nginx, certbot, firewall (22/80/443), usuário `laboratorio`.

---

## Parte 4 — Variáveis de ambiente

No **seu Mac**, copie o `.env` para a VPS (nunca commite):

```bash
scp backend/.env laboratorio@IP_DA_VPS:/opt/laboratorio/Laboratorio/backend/.env
```

Ou crie manualmente na VPS:

```bash
ssh laboratorio@IP_DA_VPS
nano /opt/laboratorio/Laboratorio/backend/.env
```

Confirme que tem tudo:

```env
ANTHROPIC_API_KEY=...
WHATSAPP_VERIFY_TOKEN=...
WHATSAPP_ACCESS_TOKEN=...
WHATSAPP_PHONE_NUMBER_ID=...
META_APP_SECRET=...
WHATSAPP_HOST=127.0.0.1
WHATSAPP_PORT=8000
```

Produção: uvicorn só escuta localhost; nginx expõe HTTPS.

---

## Parte 5 — Deploy da aplicação

Como root ou com sudo:

```bash
cd /opt/laboratorio-src/deploy/vps
./deploy-app.sh
```

Isso:
- Clona/atualiza repo em `/opt/laboratorio`
- Cria `.venv` e instala dependências
- Instala systemd + nginx
- Reinicia o serviço

Validar:

```bash
systemctl status laboratorio-api
curl -s http://127.0.0.1:8000/health
```

---

## Parte 6 — SSL (HTTPS)

Ainda como root, com DNS já apontando:

```bash
certbot --nginx -d api.laboratorioagentes.com.br
```

Siga o assistente (e-mail, aceitar termos). Renovação automática já vem configurada.

Teste público:

```bash
curl -s https://api.laboratorioagentes.com.br/health
# {"status":"ok","service":"whatsapp-caio"}
```

---

## Parte 7 — Webhook Meta (última vez)

Meta Developers → seu app → WhatsApp → **Configuration**:

| Campo | Valor |
|-------|-------|
| **Callback URL** | `https://api.laboratorioagentes.com.br/webhook/whatsapp` |
| **Verify token** | mesmo `WHATSAPP_VERIFY_TOKEN` do `.env` |

Verificar e salvar → assinar campo **`messages`**.

---

## Parte 8 — Teste real

Do celular, envie **Olá** para o número Business.

Logs na VPS:

```bash
journalctl -u laboratorio-api -f
```

Log de mensagens (no repo):

```bash
tail -f /opt/laboratorio/Laboratorio/logs/whatsapp_mensagens.md
```

---

## Atualizar depois (novo código)

```bash
ssh root@IP_DA_VPS
cd /opt/laboratorio-src/deploy/vps
git -C /opt/laboratorio-src pull
./deploy-app.sh
```

---

## Comandos úteis

```bash
systemctl status laboratorio-api    # status
systemctl restart laboratorio-api   # reiniciar
journalctl -u laboratorio-api -f      # logs ao vivo
nginx -t && systemctl reload nginx    # testar nginx
```

---

## Troubleshooting

| Problema | Solução |
|----------|---------|
| Webhook não verifica | `curl https://api.../health` · DNS · nginx · token igual |
| 502 Bad Gateway | `systemctl status laboratorio-api` · uvicorn caiu |
| Caio não responde | `journalctl -u laboratorio-api` · `ANTHROPIC_API_KEY` |
| Assinatura 403 | `META_APP_SECRET` correto no `.env` |
| Agent não encontrado | Deploy precisa do **repo inteiro** (pastas `agentes/`, `memoria/`) |

---

**Ref:** TASK-007 · `deploy/vps/`
