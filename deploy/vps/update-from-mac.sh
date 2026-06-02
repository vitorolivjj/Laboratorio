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
# Patrulha Ronaldo (timer 30 min)
cp /opt/laboratorio/Laboratorio/deploy/vps/ronaldo-patrol.service /etc/systemd/system/
cp /opt/laboratorio/Laboratorio/deploy/vps/ronaldo-patrol.timer /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now ronaldo-patrol.timer
cp /opt/laboratorio/Laboratorio/deploy/vps/vitor-schedule.service /etc/systemd/system/
cp /opt/laboratorio/Laboratorio/deploy/vps/vitor-schedule.timer /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now vitor-schedule.timer
# Auditoria pós-conclusão Ronaldo (timer 10 min)
cp /opt/laboratorio/Laboratorio/deploy/vps/ronaldo-audit.service /etc/systemd/system/
cp /opt/laboratorio/Laboratorio/deploy/vps/ronaldo-audit.timer /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now ronaldo-audit.timer
# Resumo diário autoevolução (09:00 BRT)
cp /opt/laboratorio/Laboratorio/deploy/vps/evolution-digest.service /etc/systemd/system/
cp /opt/laboratorio/Laboratorio/deploy/vps/evolution-digest.timer /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now evolution-digest.timer
# Garantir VITOR_WHATSAPP_WA_ID no .env (idempotente)
grep -q '^VITOR_WHATSAPP_WA_ID=' "$BACKEND/.env" 2>/dev/null || echo 'VITOR_WHATSAPP_WA_ID=5533999353242' >> "$BACKEND/.env"
sleep 25
curl -sf http://127.0.0.1:8000/health
echo ""
echo "✅ Deploy ok"
REMOTE
