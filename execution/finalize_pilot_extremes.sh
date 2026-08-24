#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RUN_DIR="$(cd "${1:?run directory required}" && pwd)"
PYTHON="$ROOT/.venv/bin/python"
while true; do
  status="$($PYTHON -c 'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8")).get("status", "MISSING"))' "$RUN_DIR/run_manifest.json")"
  if [[ "$status" == "COMPLETE" ]]; then break; fi
  if [[ "$status" != "RUNNING" ]]; then echo "PILOT HOLD: $status" >&2; exit 2; fi
  sleep 60
done
$PYTHON benchmark/pilot_analysis.py "$RUN_DIR"
