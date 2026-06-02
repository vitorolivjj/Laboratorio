#!/usr/bin/env bash
# Gera dist/<slug>/ a partir de frontend/lp-pintor/leads/<lead>/config.json
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LEAD="${1:?Uso: lp-pintor-build.sh leads/exemplo ou leads/joao}"
LEAD_DIR="$ROOT/frontend/lp-pintor/$LEAD"
CONFIG="$LEAD_DIR/config.json"
TEMPLATE="$ROOT/frontend/lp-pintor/template"

if [[ ! -f "$CONFIG" ]]; then
  echo "Erro: $CONFIG não encontrado"
  exit 1
fi

SLUG=$(python3 -c "import json; print(json.load(open('$CONFIG'))['slug'])")
OUT="$ROOT/frontend/lp-pintor/dist/$SLUG"
rm -rf "$OUT"
mkdir -p "$OUT"

python3 <<PY
import json, pathlib
config = json.loads(pathlib.Path("$CONFIG").read_text())
html = pathlib.Path("$TEMPLATE/index.html").read_text()
html = html.replace("{{NOME}}", config.get("nome", ""))
html = html.replace("{{CIDADE}}", config.get("cidade", ""))
html = html.replace("{{SERVICO}}", config.get("servico", ""))
html = html.replace("{{THEME}}", config.get("theme", "azul"))
html = html.replace("{{CONFIG_JSON}}", json.dumps(config, ensure_ascii=False))
pathlib.Path("$OUT/index.html").write_text(html, encoding="utf-8")
PY

cp "$TEMPLATE/styles.css" "$OUT/styles.css"
echo "✓ Build: $OUT"
echo "  Preview: cd $OUT && python3 -m http.server 8765"
