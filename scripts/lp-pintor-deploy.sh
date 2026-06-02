#!/usr/bin/env bash
# Publica dist/<slug> — API /previas, Surge.sh ou instruções manuais.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LEAD="${1:?Uso: lp-pintor-deploy.sh leads/exemplo}"

"$ROOT/scripts/lp-pintor-build.sh" "$LEAD"

SLUG=$(python3 -c "import json; print(json.load(open('$ROOT/frontend/lp-pintor/$LEAD/config.json'))['slug'])")
DIST="$ROOT/frontend/lp-pintor/dist/$SLUG"
DOMAIN="${LP_PINTOR_DOMAIN:-$SLUG.surge.sh}"
API_BASE="${LAB_API_PUBLIC_URL:-https://api.laboratorioagentes.com.br}"

echo "✓ Build pronto: $DIST"
echo "  Prévia via API (após deploy VPS): ${API_BASE}/previas/${SLUG}/"

if command -v surge >/dev/null 2>&1; then
  cd "$DIST"
  surge . "$DOMAIN"
  echo "✓ Surge: https://$DOMAIN"
else
  echo "Surge CLI não instalado. Opções:"
  echo "  1. ${API_BASE}/previas/${SLUG}/ (rsync VPS + restart API)"
  echo "  2. npm i -g surge && surge $DIST $DOMAIN"
  echo "  3. Netlify/Cloudflare: upload pasta $DIST"
fi
