#!/usr/bin/env bash
# Sempre usa o Python do .venv deste projeto (não o python3 global).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
PY="$ROOT/.venv/bin/python"

if [[ ! -x "$PY" ]]; then
  echo "Erro: .venv não encontrado. Rode: cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"
  exit 1
fi

export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

if [[ "${1:-}" == "orquestrar" ]]; then
  shift
  if [[ $# -eq 0 ]]; then
    exec "$PY" "$ROOT/orquestrador.py"
  else
    exec "$PY" "$ROOT/orquestrador.py" "$@"
  fi
fi

exec "$PY" -m laboratorio "$@"
