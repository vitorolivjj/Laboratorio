#!/usr/bin/env bash
# Monitora captura LP-PINTOR-011 por N minutos (amostra a cada INTERVAL s).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
API="${LAB_API_URL:-https://api.laboratorioagentes.com.br}"
TASK_ID="${1:-LP-PINTOR-011}"
MINUTES="${2:-20}"
INTERVAL="${3:-120}"
OUT="$ROOT/logs/monitor_captura_20260604.md"
ISSUES="$ROOT/logs/monitor_captura_issues.txt"
: > "$ISSUES"

SAMPLES=$(( (MINUTES * 60) / INTERVAL ))
if [ "$SAMPLES" -lt 1 ]; then SAMPLES=1; fi

append_row() {
  local ts="$1" json="$2"
  python3 - "$ts" "$json" "$OUT" "$ISSUES" "$TASK_ID" <<'PY'
import sys, json
from datetime import datetime, timezone
ts, raw, out_path, issues_path, task_id = sys.argv[1:6]
try:
    d = json.loads(raw)
except json.JSONDecodeError:
    with open(out_path, "a") as f:
        f.write(f"| {ts} | API_ERR | - | - | - | - | - | parse fail |\n")
    sys.exit(0)

cycles = d.get("cycles", 0)
last = (d.get("last_cycle_at") or "-")[:19]
active = d.get("active_task_id") or "-"
armed = d.get("armed_vps")
stale = d.get("stale_warning")
source = d.get("source", "-")
note = (d.get("last_error") or d.get("last_summary") or d.get("summary") or "")[:60]

with open(out_path, "a") as f:
    f.write(f"| {ts} | {cycles} | {last} | {active} | {armed} | {stale} | {source} | {note} |\n")

issues = []
if armed and stale:
    issues.append("stale_armed_vps_sem_ciclo_mac")
if active and active != task_id:
    issues.append(f"task_id_divergente:{active}")
if d.get("modo") == "rotativo" and active == task_id:
    issues.append("modo_rotativo_com_task_fixa")
if cycles == 0 and armed and ts > "01:28":
    issues.append("zero_ciclos_armado_prolongado")

if issues:
    with open(issues_path, "a") as f:
        for i in issues:
            f.write(f"{ts} {i}\n")
print(f"[{ts}] cycles={cycles} active={active} armed={armed} stale={stale}")
PY
}

echo "Monitor $TASK_ID — ${MINUTES}min / ${INTERVAL}s → $OUT"
for i in $(seq 1 "$SAMPLES"); do
  TS=$(date -u +"%H:%M:%S")
  JSON=$(curl -sf "${API}/api/donizete/busca-status" 2>/dev/null || echo "{}")
  append_row "$TS" "$JSON" || true
  MAC=$(pgrep -fc "donizete-busca-local" 2>/dev/null || echo 0)
  echo "  mac_processes=$MAC sample=$i/$SAMPLES"
  [ "$i" -lt "$SAMPLES" ] && sleep "$INTERVAL"
done
echo "Done. Issues: $(sort -u "$ISSUES" 2>/dev/null | wc -l | tr -d ' ')"
