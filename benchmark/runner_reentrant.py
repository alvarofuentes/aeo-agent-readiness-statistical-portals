"""Re-entrant local runner for the 1,800-execution AEO benchmark.

The runner is deliberately a control-plane orchestrator: it owns the
query/portal/repeat contract, frozen-evidence cache, checkpoints and fail-closed
manifest.  The scored model roles remain discovery, semantic, retrieval,
metadata, citation and judge; adversarial is mandatory and is always executed
after the judge.  No cloud model or model over 24B is permitted.

Run one portal pass with ``--portal-id`` and repeat it for all five portals, or
run all passes in one process.  Existing execution keys are skipped, so an
interrupted process can be resumed without deleting prior evidence/results.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import time
from pathlib import Path
from typing import Any

try:
    from .materialize_query_bank import EXPANDED, EXPANDED_COLUMNS, PORTALS, materialize
    from .model_policy import allowed_models, assert_allowed_model
    from .ollama_multiagent import (
        OUT as LEGACY_OUT,
        PORTALS as PORTAL_DEFINITIONS,
        evidence_for,
        flatten,
        load_config,
        ollama_tags,
        choose_models,
        repeat_model_map,
        run_one,
    )
except ImportError:  # direct invocation: python benchmark/runner_reentrant.py
    from materialize_query_bank import EXPANDED, EXPANDED_COLUMNS, PORTALS, materialize
    from model_policy import allowed_models, assert_allowed_model
    from ollama_multiagent import (
        OUT as LEGACY_OUT,
        PORTALS as PORTAL_DEFINITIONS,
        evidence_for,
        flatten,
        load_config,
        ollama_tags,
        choose_models,
        repeat_model_map,
        run_one,
    )

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "benchmark" / "results" / "reentrant"
JSONL = OUT / "results.jsonl"
CSV_PATH = OUT / "results.csv"
MANIFEST = OUT / "run_manifest.json"
REPEATS_DEFAULT = 3
PORTAL_ORDER = list(PORTALS)

CSV_FIELDS = [
    "query_id", "portal_id", "source_portal_id", "stratum", "query", "country", "country_code",
    "repeat", "judge_model", "semantic_model", "evidence_sha256", "overall_0_100",
    "discovery_success", "retrieval_success", "temporal_geographic_correctness",
    "semantic_correctness", "metadata_correctness", "citation_correctness",
    "adversarial_verdict", "adversarial_severity", "schema_failures",
    "orchestrator", "execution_key",
]


def read_expanded() -> list[dict[str, str]]:
    rows = list(csv.DictReader(EXPANDED.open(encoding="utf-8", newline="")))
    if list(rows[0]) != EXPANDED_COLUMNS:
        raise RuntimeError(f"Expanded bank columns mismatch: {list(rows[0])}")
    if len(rows) != 600:
        raise RuntimeError(f"Expanded bank must contain 600 rows; found {len(rows)}")
    query_ids = {r["query_id"] for r in rows}
    portals = {r["portal_id"] for r in rows}
    pairs = {(r["query_id"], r["portal_id"]) for r in rows}
    if query_ids != {f"Q{i:03d}" for i in range(1, 121)}:
        raise RuntimeError("Expanded bank query IDs must be Q001-Q120")
    if portals != set(PORTAL_ORDER):
        raise RuntimeError(f"Expanded bank portal set mismatch: {sorted(portals)}")
    if len(pairs) != 600:
        raise RuntimeError("Expanded bank contains duplicate query/portal pairs")
    return rows


def key(row: dict[str, Any], repeat: int) -> str:
    return f"{row['query_id']}|{row['portal_id']}|{repeat}"


def load_existing() -> tuple[dict[str, dict[str, Any]], int]:
    existing: dict[str, dict[str, Any]] = {}
    malformed = 0
    if not JSONL.exists():
        return existing, malformed
    with JSONL.open(encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, 1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
                k = item.get("execution_key")
                if not k or k in existing:
                    malformed += 1
                    continue
                existing[k] = item
            except json.JSONDecodeError:
                malformed += 1
    return existing, malformed


def write_manifest(payload: dict[str, Any]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = MANIFEST.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(MANIFEST)


def write_csv(existing: dict[str, dict[str, Any]]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = CSV_PATH.with_suffix(".csv.tmp")
    with tmp.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for k in sorted(existing):
            row = existing[k].get("flat", {})
            writer.writerow({field: row.get(field) for field in CSV_FIELDS})
    tmp.replace(CSV_PATH)


def make_flat(result: dict[str, Any], row: dict[str, str], repeat: int, models: dict[str, str]) -> dict[str, Any]:
    flat = flatten(result, repeat, models)
    flat["source_portal_id"] = row.get("source_portal_id", "")
    flat["orchestrator"] = "deterministic-python"
    flat["execution_key"] = key(row, repeat)
    return flat


def contract() -> dict[str, int]:
    return {
        "query_instances": 120,
        "portals": 5,
        "query_portal_pairs": 600,
        "repeats": 3,
        "expected_executions": 1800,
        "executions_per_portal_pass": 360,
    }


def run(args: argparse.Namespace) -> int:
    rows = read_expanded()
    cfg = load_config()
    repeats = args.repeats or int(cfg["ollama"].get("repeat_runs", REPEATS_DEFAULT))
    if repeats != REPEATS_DEFAULT:
        raise RuntimeError("The PDF contract requires exactly three repeats")
    selected = PORTAL_ORDER if not args.portal_id else [args.portal_id]
    unknown = set(selected) - set(PORTAL_ORDER)
    if unknown:
        raise RuntimeError(f"Unknown portal(s): {sorted(unknown)}")
    rows = [r for r in rows if r["portal_id"] in selected]
    if args.limit is not None:
        if args.limit < 1:
            raise ValueError("--limit must be positive")
        rows = [r for p in selected for r in rows if r["portal_id"] == p][:args.limit]

    existing, malformed = load_existing()
    if malformed:
        raise RuntimeError(f"Checkpoint contains {malformed} malformed/duplicate JSONL lines")

    if args.dry_run:
        print(json.dumps({
            "status": "DRY_RUN_PASS",
            "contract": contract(),
            "selected_portals": selected,
            "selected_rows": len(rows),
            "selected_executions": len(rows) * repeats,
            "checkpoint": str(JSONL),
        }, ensure_ascii=False, indent=2))
        return 0

    tags = ollama_tags(args.base)
    disallowed = sorted(set(tags) - set(allowed_models(tags)))
    if disallowed:
        # They may be installed locally, but never enter this experiment.
        print("excluded_models=" + json.dumps(disallowed, ensure_ascii=False), flush=True)
    primary_models = choose_models(tags, cfg)
    for model in primary_models.values():
        assert_allowed_model(model)

    expected_total = contract()["expected_executions"]
    manifest = {
        "runner": "runner_reentrant",
        "orchestrator": "deterministic-python",
        "adversarial_required": True,
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ollama": args.base,
        "models_available": tags,
        "excluded_models": disallowed,
        "role_models": primary_models,
        "contract": contract(),
        "selected_portals": selected,
        "selected_rows": len(rows),
        "selected_executions": len(rows) * repeats,
        "evidence_policy": "frozen_per_query_portal_reused_across_repeats",
        "status": "running",
    }
    write_manifest(manifest)

    try:
        for i, row in enumerate(rows, 1):
            ev = evidence_for(row, args.refresh_evidence)
            for repeat in range(1, repeats + 1):
                execution_key = key(row, repeat)
                if execution_key in existing:
                    continue
                models = repeat_model_map(tags, primary_models, repeat)
                result = run_one(args.base, row, ev, models, cfg)
                result["repeat"] = repeat
                result["models"] = models
                result["orchestrator"] = {
                    "name": "deterministic-python",
                    "stages": ["evidence", "discovery", "semantic", "retrieval", "metadata", "citation", "judge", "adversarial"],
                    "adversarial_required": True,
                }
                flat = make_flat(result, row, repeat, models)
                record = {
                    "execution_key": execution_key,
                    "result": result,
                    "flat": flat,
                }
                with JSONL.open("a", encoding="utf-8") as fh:
                    fh.write(json.dumps(record, ensure_ascii=False) + "\n")
                existing[execution_key] = record
                write_csv(existing)
                manifest["completed_executions"] = len(existing)
                manifest["last_execution_key"] = execution_key
                write_manifest(manifest)
                print(f"[{i}/{len(rows)}] {execution_key} completed={len(existing)}/{expected_total}", flush=True)
    except KeyboardInterrupt:
        manifest["status"] = "hold"
        manifest["stop_reason"] = "interrupted_by_operator"
        manifest["completed_executions"] = len(existing)
        write_manifest(manifest)
        raise
    except Exception as exc:
        manifest["status"] = "hold"
        manifest["stop_reason"] = f"{type(exc).__name__}: {exc}"
        manifest["completed_executions"] = len(existing)
        write_manifest(manifest)
        raise

    manifest["completed_executions"] = len(existing)
    manifest["status"] = "complete" if len(existing) == expected_total else "partial"
    manifest["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    write_csv(existing)
    write_manifest(manifest)
    print(json.dumps({
        "status": manifest["status"],
        "completed_executions": len(existing),
        "expected_executions": expected_total,
        "results": str(JSONL),
        "manifest": str(MANIFEST),
    }, ensure_ascii=False, indent=2))
    return 0 if manifest["status"] == "complete" else 2


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default=os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434"))
    parser.add_argument("--portal-id", choices=PORTAL_ORDER)
    parser.add_argument("--repeats", type=int, default=REPEATS_DEFAULT)
    parser.add_argument("--limit", type=int, help="limit source rows for a controlled smoke")
    parser.add_argument("--refresh-evidence", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return run(parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
