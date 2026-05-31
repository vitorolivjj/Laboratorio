#!/usr/bin/env bash
# Rodar na VPS depois que DNS api.laboratorioagentes.com.br → IP estiver ok.
set -euo pipefail

DOMAIN="api.laboratorioagentes.com.br"
EMAIL="${CERTBOT_EMAIL:-contato@laboratorioagentes.com.br}"

echo "==> Verificando DNS..."
IP=$(dig +short "$DOMAIN" A @8.8.8.8 | head -1)
SERVER=$(curl -s ifconfig.me || curl -s icanhazip.com)
echo "    DNS $DOMAIN → ${IP:-NÃO CONFIGURADO}"
echo "    IP servidor → $SERVER"

if [[ -z "$IP" ]]; then
  echo "❌ Crie registro A: api → $SERVER no Registro.br"
  exit 1
fi

if [[ "$IP" != "$SERVER" ]]; then
  echo "⚠️  DNS aponta para $IP mas servidor é $SERVER — aguarde propagação"
fi

echo "==> Certbot..."
certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos -m "$EMAIL" --redirect

echo "==> Teste HTTPS..."
curl -sf "https://$DOMAIN/health"
echo ""
echo "✅ SSL ok. Webhook Meta:"
echo "   https://$DOMAIN/webhook/whatsapp"
