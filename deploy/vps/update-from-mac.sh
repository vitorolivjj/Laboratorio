#!/usr/bin/env bash
# Atualiza código local → VPS (rodar no Mac).
set -euo pipefail
VPS="${LAB_VPS_IP:-5.78.232.71}"
ROOT="/Users/vitor/00-Projetos/01-Laboratorio/Laboratorio"

rsync -az --delete \
  --exclude '.venv' \
  --exclude '__pycache__' \
  --exclude '.git' \
  --exclude 'social_executor' \
  --exclude 'node_modules' \
  --exclude 'backend/.env' \
  -e "ssh" \
  "$ROOT/" "root@$VPS:/opt/laboratorio/Laboratorio/"

ssh "root@$VPS" bash <<'REMOTE'
set -euo pipefail
chown -R laboratorio:laboratorio /opt/laboratorio/Laboratorio
BACKEND=/opt/laboratorio/Laboratorio/backend
sudo -u laboratorio bash -c "
  cd '$BACKEND'
  .venv/bin/pip install -r requirements.txt -q
"
systemctl restart laboratorio-api
sleep 15
curl -sf http://127.0.0.1:8000/health
echo ""
echo "✅ Deploy ok"
REMOTE
