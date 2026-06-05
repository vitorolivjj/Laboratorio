#!/usr/bin/env bash
# Deploy / atualização da app. Rodar como root (ou sudo).
set -euo pipefail

APP_USER="laboratorio"
APP_DIR="/opt/laboratorio/Laboratorio"
BACKEND_DIR="$APP_DIR/backend"
REPO_URL="${LAB_REPO_URL:-https://github.com/vitorolivjj/Laboratorio.git}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "==> Código em $APP_DIR..."
# Robusto para 3 casos: repo git já existente, pasta criada por rsync (sem .git)
# e diretório novo. Usa reset --hard (não pull), que preserva arquivos não
# versionados como backend/.env e backend/.venv.
if [[ ! -d "$APP_DIR/.git" ]]; then
  echo "    sem repositório git — inicializando (preserva .env/.venv)..."
  sudo -u "$APP_USER" mkdir -p "$APP_DIR"
  sudo -u "$APP_USER" git -C "$APP_DIR" init -q
  sudo -u "$APP_USER" git -C "$APP_DIR" remote add origin "$REPO_URL" 2>/dev/null \
    || sudo -u "$APP_USER" git -C "$APP_DIR" remote set-url origin "$REPO_URL"
fi
sudo -u "$APP_USER" git -C "$APP_DIR" fetch origin main
sudo -u "$APP_USER" git -C "$APP_DIR" reset --hard origin/main
sudo -u "$APP_USER" git -C "$APP_DIR" branch -M main 2>/dev/null || true

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

# Timer de sincronização markdown -> Postgres (espelho, a cada 5 min).
if [[ -f "$SCRIPT_DIR/db-sync.service" && -f "$SCRIPT_DIR/db-sync.timer" ]]; then
  echo "==> db-sync timer..."
  install -m 644 "$SCRIPT_DIR/db-sync.service" /etc/systemd/system/db-sync.service
  install -m 644 "$SCRIPT_DIR/db-sync.timer" /etc/systemd/system/db-sync.timer
  systemctl daemon-reload
  systemctl enable --now db-sync.timer
fi

echo "==> nginx..."
# IMPORTANTE: NÃO sobrescrever a config se ela já existe. O certbot edita este
# arquivo para adicionar o bloco HTTPS (porta 443). Reinstalar a versão HTTP-only
# do repo apagaria o SSL e derrubaria o site (ERR_CONNECTION_REFUSED na 443).
if [[ ! -f /etc/nginx/sites-available/laboratorio-api ]]; then
  install -m 644 "$SCRIPT_DIR/nginx-laboratorio-api.conf" \
    /etc/nginx/sites-available/laboratorio-api
  ln -sf /etc/nginx/sites-available/laboratorio-api /etc/nginx/sites-enabled/
  rm -f /etc/nginx/sites-enabled/default
  echo "    config nginx instalada — rode 'certbot --nginx -d <dominio>' para habilitar HTTPS."
else
  echo "    config nginx já existe — preservada (mantém SSL do certbot intacto)."
fi
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
