#!/usr/bin/env bash
# Donizete — executor de captação no Mac (Chrome CDP + busca contínua).
# Mac ligado · Facebook logado no perfil Laboratório · WhatsApp Play/Stop na VPS.
#
# Uso:
#   ./scripts/donizete-mac-executor.sh          # inicia busca agora
#   ./scripts/donizete-mac-executor.sh --watch  # aguarda PlayDonizete na VPS e inicia sozinho
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$ROOT/backend"
API_BASE="${LAB_API_URL:-https://api.laboratorioagentes.com.br}"
WATCH="${1:-}"

echo "=== Donizete Mac Executor ==="
echo "Captação Facebook só roda AQUI (não na VPS)."
echo ""

if [[ ! -x "$ROOT/scripts/facebook-cdp-mac.sh" ]]; then
  chmod +x "$ROOT/scripts/facebook-cdp-mac.sh"
fi

echo "[1/2] Chrome CDP (perfil ~/.laboratorio-chrome-fb)…"
if curl -sf "http://127.0.0.1:${FACEBOOK_CDP_PORT:-9222}/json/version" >/dev/null 2>&1; then
  echo "      CDP já online."
else
  "$ROOT/scripts/facebook-cdp-mac.sh"
fi

cd "$BACKEND"

if [[ "$WATCH" == "--watch" ]]; then
  echo ""
  echo "[2/2] Modo watch — aguardando PlayDonizete na VPS ($API_BASE)…"
  echo "      (Ctrl+C para sair; busca para com StopDonizete no WhatsApp)"
  echo ""
  while true; do
    json="$(curl -sf "${API_BASE}/api/donizete/busca-status" 2>/dev/null || true)"
    armed=false
    if [[ -n "$json" ]]; then
      if command -v jq >/dev/null 2>&1; then
        armed="$(echo "$json" | jq -r '.armed_vps // false')"
      elif echo "$json" | grep -q '"armed_vps"[[:space:]]*:[[:space:]]*true'; then
        armed=true
      fi
    fi
    if pgrep -f "laboratorio donizete-busca-local" >/dev/null 2>&1; then
      # Se VPS mudou a TASK armada, reinicia busca no grupo certo
      if [[ "$armed" == "true" ]] && command -v jq >/dev/null 2>&1; then
        remote_tid="$(echo "$json" | jq -r '.active_task_id // empty')"
        if [[ -n "$remote_tid" ]]; then
          local_tid="$(PYTHONPATH=src .venv/bin/python -c "
from laboratorio.ops.donizete_runner import _load_busca_state
print((_load_busca_state().get('active_task_id') or '').upper())
" 2>/dev/null || true)"
          if [[ -n "$local_tid" && "$local_tid" != "$(echo "$remote_tid" | tr '[:lower:]' '[:upper:]')" ]]; then
            echo "$(date '+%H:%M:%S') TASK VPS ($remote_tid) ≠ Mac ($local_tid) — reiniciando…"
            pkill -f "laboratorio donizete-busca-local" 2>/dev/null || true
            sleep 3
          else
            sleep 25
            continue
          fi
        else
          sleep 25
          continue
        fi
      else
        sleep 25
        continue
      fi
    fi
    if [[ "$armed" == "true" ]]; then
      echo "$(date '+%H:%M:%S') VPS armada — sync + busca local…"
      ./run.sh donizete-mac-prepare 2>/dev/null || true
      exec ./run.sh donizete-busca-local
    fi
    sleep 20
  done
fi

echo ""
echo "[2/2] Busca intermitente (Ctrl+C para parar; ou StopDonizete no WhatsApp)…"
echo ""

./run.sh donizete-mac-prepare 2>/dev/null || true
exec ./run.sh donizete-busca-local
