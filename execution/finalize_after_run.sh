#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RUN_DIR="$(cd "${1:?run directory required}" && pwd)"
DATE_TAG="${2:-2026-08-23}"
PYTHON="/Users/alvarofuentes/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"
NODE="/Users/alvarofuentes/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node"
TMP_DIR="/private/tmp/aeo-ppt-build"
PPT_SKILL="/Users/alvarofuentes/.codex/plugins/cache/openai-primary-runtime/presentations/26.819.11345/skills/presentations"

cd "$ROOT"
while true; do
  STATUS="$($PYTHON -c 'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8")).get("status", "MISSING"))' "$RUN_DIR/run_manifest.json")"
  if [[ "$STATUS" == "COMPLETE" ]]; then
    break
  fi
  if [[ "$STATUS" != "RUNNING" ]]; then
    echo "FINALIZATION HOLD: run status is $STATUS" >&2
    exit 2
  fi
  sleep 60
done

# First pass materializes all tables/reports and the provisional deck.
$PYTHON execution/build_deliverables.py "$RUN_DIR" --date-tag "$DATE_TAG"

# Replace only the provisional deck with the required artifact-tool implementation.
mkdir -p "$TMP_DIR/node_modules"
ln -sfn "/Users/alvarofuentes/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai" "$TMP_DIR/node_modules/@oai"
cp execution/build_ppt_artifact.mjs "$TMP_DIR/build_ppt_artifact.mjs"
cd "$TMP_DIR"
"$NODE" "$TMP_DIR/build_ppt_artifact.mjs" "$ROOT" "$RUN_DIR" "$DATE_TAG"
RUNTIME_NODE="$NODE" RUNTIME_NODE_MODULES="/Users/alvarofuentes/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules" RUNTIME_BIN_DIR="/Users/alvarofuentes/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/override" "$PYTHON" "$PPT_SKILL/container_tools/slides_test.py" "$ROOT/outputs/aeo-comparative-deck-$DATE_TAG.pptx"

# Documents are deliberately the final mutation and cannot overwrite the QA'd deck.
cd "$ROOT"
$PYTHON execution/build_deliverables.py "$RUN_DIR" --date-tag "$DATE_TAG" --update-docs --skip-ppt
echo "FINALIZATION COMPLETE: $ROOT/outputs/aeo-comparative-deck-$DATE_TAG.pptx"
