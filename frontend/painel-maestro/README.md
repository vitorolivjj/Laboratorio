# Painel Maestro — uso rápido

Dashboard operacional do Laboratório de Agentes IA (TASK-008).

## Acesso

**Produção:** https://maestro.laboratorioagentes.com.br/painel/

**Alternativa:** https://api.laboratorioagentes.com.br/painel/

## O que você vê

| Seção | Responde |
|-------|----------|
| Visão Geral | Sistema, VPS, WhatsApp online? Mensagens/leads hoje? Custo? Último erro? |
| Agentes | Status de Ronaldo, Caio, Donizete, Dev, Juarez, Loide |
| Delegações | Quem delegou o quê e próximo passo |
| WhatsApp | Conversas reais do Caio |
| Leads | CRM markdown |
| Logs | Eventos, erros, decisões |

## Atualização

- Automática a cada **30 segundos**
- Manual: botão **Atualizar**

## Deploy / atualizar

```bash
./deploy/vps/update-from-mac.sh
```

## DNS + SSL (primeira vez)

1. Registro.br → A `maestro` → IP VPS
2. Na VPS:

```bash
sudo cp /opt/laboratorio/Laboratorio/deploy/vps/nginx-maestro.conf /etc/nginx/sites-available/maestro
sudo ln -sf /etc/nginx/sites-available/maestro /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d maestro.laboratorioagentes.com.br
```

## Desenvolvimento local

```bash
cd backend
./run.sh serve
open http://127.0.0.1:8000/painel/
```

API JSON: http://127.0.0.1:8000/api/maestro/snapshot
