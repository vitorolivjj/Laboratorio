#!/usr/bin/env bash
# Deploy / atualização da app. Rodar como root (ou sudo).
set -euo pipefail

APP_USER="laboratorio"
APP_DIR="/opt/laboratorio/Laboratorio"
BACKEND_DIR="$APP_DIR/backend"
REPO_URL="${LAB_REPO_URL:-https://github.com/vitorolivjj/Laboratorio.git}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "==> Código em $APP_DIR..."
if [[ ! -d "$APP_DIR/.git" ]]; then
  sudo -u "$APP_USER" git clone "$REPO_URL" "$APP_DIR"
else
  sudo -u "$APP_USER" git -C "$APP_DIR" pull --ff-only
fi

echo "==> Python venv + dependências..."
sudo -u "$APP_USER" bash -c "
  cd '$BACKEND_DIR'
  python3.12 -m venv .venv
  .venv/bin/pip install --upgrade pip
  .venv/bin/pip install -r requirements.txt
"

if [[ ! -f "$BACKEND_DIR/.env" ]]; then
  echo ""
  echo "⚠️  Crie $BACKEND_DIR/.env antes de iniciar (scp do Mac ou nano)."
  echo "    cp .env.example .env && nano .env"
  exit 1
fi

echo "==> systemd..."
install -m 644 "$SCRIPT_DIR/laboratorio-api.service" /etc/systemd/system/laboratorio-api.service
systemctl daemon-reload
systemctl enable laboratorio-api
systemctl restart laboratorio-api

echo "==> nginx..."
install -m 644 "$SCRIPT_DIR/nginx-laboratorio-api.conf" \
  /etc/nginx/sites-available/laboratorio-api
ln -sf /etc/nginx/sites-available/laboratorio-api /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx

echo ""
echo "==> Status:"
systemctl --no-pager status laboratorio-api || true
curl -sf http://127.0.0.1:8000/health && echo "" || echo "health check falhou — veja journalctl -u laboratorio-api"

echo ""
echo "✅ Deploy concluído."
echo "   SSL: certbot --nginx -d api.laboratorioagentes.com.br"
echo "   Webhook: https://api.laboratorioagentes.com.br/webhook/whatsapp"
