#!/usr/bin/env bash
# Bootstrap inicial — Ubuntu 24.04. Rodar como root, uma vez.
set -euo pipefail

APP_USER="laboratorio"
APP_DIR="/opt/laboratorio"

echo "==> Atualizando sistema..."
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get upgrade -y

echo "==> Instalando pacotes..."
apt-get install -y \
  python3.12 python3.12-venv python3-pip \
  git nginx certbot python3-certbot-nginx \
  ufw curl

echo "==> Firewall (SSH + HTTP + HTTPS)..."
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable

echo "==> Usuário $APP_USER..."
if ! id "$APP_USER" &>/dev/null; then
  useradd --system --create-home --shell /bin/bash "$APP_USER"
fi

mkdir -p "$APP_DIR"
chown -R "$APP_USER:$APP_USER" /opt

echo ""
echo "✅ Servidor pronto."
echo "   Próximo: copie backend/.env para a VPS"
echo "   Depois: ./deploy-app.sh"
