#!/usr/bin/env bash
# Chrome dedicado ao Donizete — remote debugging para Playwright CDP.
# No macOS use `open` para a janela aparecer (exec direto no terminal do IDE às vezes não mostra GUI).
set -euo pipefail

PORT="${FACEBOOK_CDP_PORT:-9222}"
PROFILE="${LAB_FB_PROFILE:-$HOME/.laboratorio-chrome-fb}"
URL="${LAB_FB_START_URL:-https://www.facebook.com/}"

CHROME_APP="/Applications/Google Chrome.app"
CHROME_BIN="$CHROME_APP/Contents/MacOS/Google Chrome"

if [[ ! -d "$CHROME_APP" ]]; then
  echo "Google Chrome não encontrado em $CHROME_APP"
  echo "Instale o Chrome ou ajuste CHROME_APP no script."
  exit 1
fi

mkdir -p "$PROFILE"

# Se outra instância travou o perfil, avisa (não apaga automaticamente).
if [[ -e "$PROFILE/SingletonLock" || -e "$PROFILE/SingletonSocket" ]]; then
  echo "Aviso: perfil pode estar em uso ($PROFILE)."
  echo "Feche a janela 'Laboratório FB' do Chrome ou rode: pkill -f 'laboratorio-chrome-fb'"
  echo ""
fi

echo "Perfil: $PROFILE"
echo "CDP:    http://127.0.0.1:${PORT}"
echo "URL:    $URL"
echo ""
echo "Abrindo Chrome (janela nova)…"
echo ""

CHROME_ARGS=(
  --remote-debugging-port="$PORT"
  --user-data-dir="$PROFILE"
  --new-window
  --no-first-run
  --no-default-browser-check
  "$URL"
)

# Preferir `open` no macOS — traz a janela para frente.
if [[ "$(uname -s)" == "Darwin" ]]; then
  open -na "$CHROME_APP" --args "${CHROME_ARGS[@]}"
  sleep 1
  osascript -e 'tell application "Google Chrome" to activate' 2>/dev/null || true
else
  nohup "$CHROME_BIN" "${CHROME_ARGS[@]}" >/dev/null 2>&1 &
fi

# Espera CDP ficar online (até ~15s).
for i in $(seq 1 15); do
  if curl -sf "http://127.0.0.1:${PORT}/json/version" >/dev/null 2>&1; then
    echo "OK — Chrome CDP online em http://127.0.0.1:${PORT}"
    echo "Mantenha esta janela do Chrome aberta (perfil Laboratório FB)."
    echo "Teste: cd backend && ./run.sh donizete-fb status"
    exit 0
  fi
  sleep 1
done

echo ""
echo "Chrome foi iniciado, mas CDP ainda não respondeu em ${PORT}s."
echo "Verifique se a janela do Chrome abriu (Dock / Mission Control)."
echo "Se abriu só o Chrome normal, feche-o e rode este script de novo no Terminal.app (fora do Cursor)."
echo "Ou tente porta livre: FACEBOOK_CDP_PORT=9223 ./scripts/facebook-cdp-mac.sh"
exit 1
