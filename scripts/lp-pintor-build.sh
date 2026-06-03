#!/usr/bin/env bash
# Gera dist/<slug>/ a partir de frontend/lp-pintor/leads/<lead>/config.json
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LEAD="${1:?Uso: lp-pintor-build.sh leads/exemplo}"
LEAD_DIR="$ROOT/frontend/lp-pintor/$LEAD"
CONFIG="$LEAD_DIR/config.json"
TEMPLATE="$ROOT/frontend/lp-pintor/template"

if [[ ! -f "$CONFIG" ]]; then
  echo "Erro: $CONFIG não encontrado"
  exit 1
fi

python3 "$ROOT/scripts/build_lp_pintor.py" "$CONFIG" "$TEMPLATE"
echo "✓ Build concluído — veja frontend/lp-pintor/dist/"
