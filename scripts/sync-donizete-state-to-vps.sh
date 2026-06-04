#!/usr/bin/env bash
# Publica logs/donizete_busca_state.json do Mac → VPS (painel alinhado com captura local).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STATE="$ROOT/logs/donizete_busca_state.json"
VPS="${LAB_VPS_IP:-5.78.232.71}"
API="${DONIZETE_STATE_PUSH_URL:-https://api.laboratorioagentes.com.br/api/donizete/busca-state}"
TOKEN="${DONIZETE_STATE_PUSH_TOKEN:-}"

if [[ ! -f "$STATE" ]]; then
  echo "Sem $STATE — busca ainda não rodou no Mac."
  exit 1
fi

if [[ -n "$TOKEN" ]]; then
  # armed_vps=false no Mac para o painel não ficar preso em "0 ciclos armado"
  BODY="$(python3 -c "
import json, sys
d=json.load(open(sys.argv[1]))
d['armed_vps']=False
print(json.dumps(d))
" "$STATE")"
  HTTP="$(curl -s -o /tmp/donizete-push-resp.json -w '%{http_code}' -X POST "$API" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$BODY")"
  if [[ "$HTTP" == "200" ]]; then
    echo "✓ Estado enviado via API (ciclos=$(echo "$BODY" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("cycles",0))' 2>/dev/null || echo ?))"
    exit 0
  fi
  echo "ERRO push HTTP $HTTP: $(cat /tmp/donizete-push-resp.json 2>/dev/null | head -c 200)"
  exit 1
fi

rsync -az -e ssh "$STATE" "root@$VPS:/opt/laboratorio/Laboratorio/logs/"
ssh "root@$VPS" 'chown laboratorio:laboratorio /opt/laboratorio/Laboratorio/logs/donizete_busca_state.json'
echo "✓ Estado copiado para VPS (logs/)"
