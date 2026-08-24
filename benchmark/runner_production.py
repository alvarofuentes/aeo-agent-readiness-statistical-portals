"""Production AEO benchmark runner.

The deterministic orchestrator expands the 120 canonical rows across the five
portals, freezes evidence once per query/portal pair, runs the role chain, and
resumes from an append-only JSONL checkpoint.  Transport, schema, semantic and
adversarial states remain separate; no failed model call is converted to zero.

This runner deliberately keeps the 120 source rows as template IDs even when
their text is repeated across portal-specific source rows.  The repeated-text
family is recorded so clustered sensitivity analyses can account for it.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import time
from pathlib import Path
from typing import Any

from . import ollama_multiagent as core

ROOT = Path(__file__).resolve().parents[1]
BANK = ROOT / "benchmark" / "query-bank-120.csv"
PORTAL_IDS = ["worldbank", "who", "cepalstat", "undata", "sdg"]
DIMENSIONS = [
    "discovery_success", "retrieval_success", "temporal_geographic_correctness",
    "semantic_correctness", "metadata_correctness", "citation_correctness",
]
DIMENSION_WEIGHTS = {name: 1 / len(DIMENSIONS) for name in DIMENSIONS}
ROLE_ORDER = ["discovery", "semantic", "retrieval", "metadata", "citation", "judge", "adversarial"]


def normalize_query(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def template_family_id(text: str) -> str:
    return "F" + hashlib.sha1(normalize_query(text).encode("utf-8")).hexdigest()[:10]


def load_rows() -> list[dict[str, str]]:
    with BANK.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    if len(rows) != 120 or [r["query_id"] for r in rows] != [f"Q{i:03d}" for i in range(1, 121)]:
        raise RuntimeError("Canonical bank must contain contiguous Q001-Q120 template IDs")
    for row in rows:
        row["source_portal_id"] = row["portal_id"]
        row["template_family_id"] = template_family_id(row["query"])
    return rows


def expand_rows(rows: list[dict[str, str]], portal: str | None) -> list[dict[str, str]]:
    portals = [portal] if portal else PORTAL_IDS
    if any(p not in PORTAL_IDS for p in portals):
        raise ValueError(f"Unknown portal: {portal}")
    expanded: list[dict[str, str]] = []
    for row in rows:
        for portal_id in portals:
            item = dict(row)
            item["portal_id"] = portal_id
            item["execution_key"] = f"{row['query_id']}__{portal_id}"
            expanded.append(item)
    return expanded


def score_from_dimensions(judge: dict[str, Any]) -> tuple[float | None, list[str]]:
    values: list[float] = []
    applicable: list[str] = []
    for name in DIMENSIONS:
        value = judge.get(name)
        if isinstance(value, (int, float)) and not isinstance(value, bool) and 0 <= value <= 1:
            values.append(float(value) * DIMENSION_WEIGHTS[name])
            applicable.append(name)
    if not applicable:
        return None, []
    denom = sum(DIMENSION_WEIGHTS[name] for name in applicable)
    return round(100 * sum(values) / denom, 4), applicable


def evidence_hash(ev: core.Evidence) -> str:
    raw = json.dumps(ev.pages, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def call_role(base: str, role: str, model: str, user: str, cfg: dict[str, Any]) -> dict[str, Any]:
    ans = core.ollama_chat(
        base,
        model,
        core.ROLE_PROMPTS[role],
        user,
        float(cfg["ollama"].get("timeout_seconds", 180)),
        float(cfg["ollama"].get("temperature", 0.0)),
    )
    valid, schema_error = core.validate_agent_json(role, ans.get("json"))
    ans["schema_valid"] = valid
    ans["schema_error"] = schema_error
    ans["transport_state"] = "ok" if ans.get("ok") else "model_unavailable"
    return ans


def run_execution(base: str, row: dict[str, str], ev: core.Evidence, models: dict[str, str], cfg: dict[str, Any]) -> dict[str, Any]:
    max_chars = int(cfg["ollama"].get("max_context_chars", 18000))
    result: dict[str, Any] = {
        "query": row,
        "evidence_sha256": ev.sha256,
        "agents": {},
        "orchestrator": {"role_order": ROLE_ORDER, "evidence_policy": "frozen_query_portal", "adversarial_independent_of_judge": True},
    }
    evidence = core.evidence_prompt(ev, row["query"], max_chars)
    prior: dict[str, Any] = {}

    discovery = call_role(base, "discovery", models["discovery"], evidence, cfg)
    result["agents"]["discovery"] = discovery
    discovery_json = discovery.get("json") if discovery.get("schema_valid") else {}
    candidate = discovery_json.get("best_url") if isinstance(discovery_json, dict) else ""
    candidate_rejected = bool(candidate and not core.portal_url_allowed(row["portal_id"], candidate))
    result["orchestrator"]["candidate_url"] = candidate
    result["orchestrator"]["candidate_url_rejected"] = candidate_rejected
    if candidate and not candidate_rejected and candidate not in [p["url"] for p in ev.pages]:
        status, text, headers = core.http_get(candidate)
        ev.pages.append({"url": candidate, "status": status, "content_type": headers.get("content-type", ""), "text": re.sub(r"\s+", " ", text)[:30000], "source": "discovery_candidate"})
        ev.urls.append(candidate)
        ev.sha256 = evidence_hash(ev)
        result["evidence_sha256_after_discovery"] = ev.sha256
        evidence = core.evidence_prompt(ev, row["query"], max_chars)
    prior["discovery"] = discovery_json

    for role in ["semantic", "retrieval", "metadata", "citation"]:
        context = evidence + "\n\nCANDIDATE OUTPUTS:\n" + json.dumps(prior, ensure_ascii=False, indent=2)
        ans = call_role(base, role, models[role], context[:max_chars], cfg)
        result["agents"][role] = ans
        prior[role] = ans.get("json") if ans.get("schema_valid") else {"schema_error": ans.get("schema_error"), "raw": ans.get("text", "")}

    judge_context = evidence + "\n\nCANDIDATE OUTPUTS:\n" + json.dumps(prior, ensure_ascii=False, indent=2)
    judge = call_role(base, "judge", models["judge"], judge_context[:max_chars], cfg)
    result["agents"]["judge"] = judge
    # The adversarial reviewer sees evidence and candidate outputs, not judge score.
    adv_context = evidence + "\n\nCANDIDATE OUTPUTS TO FALSIFY:\n" + json.dumps(prior, ensure_ascii=False, indent=2)
    adversarial = call_role(base, "adversarial", models["adversarial"], adv_context[:max_chars], cfg)
    result["agents"]["adversarial"] = adversarial
    return result


def flatten(result: dict[str, Any], repeat: int, models: dict[str, str]) -> dict[str, Any]:
    q = result["query"]
    judge = result["agents"].get("judge", {})
    judge_json = judge.get("json") if judge.get("schema_valid") else {}
    adv = result["agents"].get("adversarial", {}).get("json") or {}
    score, applicable = score_from_dimensions(judge_json if isinstance(judge_json, dict) else {})
    transport_errors = [role for role, ans in result["agents"].items() if not ans.get("ok")]
    schema_failures = [role for role, ans in result["agents"].items() if not ans.get("schema_valid")]
    run_status = "ok" if not transport_errors and score is not None else ("model_unavailable" if transport_errors else "judge_invalid")
    return {
        "execution_key": f"{q['query_id']}__{q['portal_id']}__r{repeat}",
        "query_id": q["query_id"], "template_family_id": q["template_family_id"], "source_portal_id": q["source_portal_id"],
        "portal_id": q["portal_id"], "stratum": q["stratum"], "query": q["query"], "country": q["country"], "country_code": q["country_code"],
        "repeat": repeat, "run_status": run_status, "transport_errors": ";".join(transport_errors), "schema_failures": ";".join(schema_failures),
        "judge_model": models["judge"], "semantic_model": models["semantic"], "retrieval_model": models["retrieval"],
        "evidence_sha256": result["evidence_sha256"], "overall_0_100": score, "applicable_dimensions": ";".join(applicable),
        **{name: (judge_json.get(name) if isinstance(judge_json, dict) else None) for name in DIMENSIONS},
        "adversarial_verdict": adv.get("verdict"), "adversarial_severity": adv.get("severity"),
        "candidate_url": result.get("orchestrator", {}).get("candidate_url"),
        "candidate_url_rejected": result.get("orchestrator", {}).get("candidate_url_rejected", False),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434"))
    ap.add_argument("--portal", choices=PORTAL_IDS)
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--max-templates", type=int)
    ap.add_argument("--refresh-evidence", action="store_true")
    ap.add_argument("--output-dir", default="benchmark/results/production")
    args = ap.parse_args()
    if args.repeats < 1:
        raise SystemExit("--repeats must be >= 1")
    cfg = core.load_config()
    templates = load_rows()
    if args.max_templates:
        templates = templates[: args.max_templates]
    rows = expand_rows(templates, args.portal)
    tags = core.ollama_tags(args.base)
    models = core.choose_models(tags, cfg)
    out = ROOT / args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    # Keep production evidence isolated from historical smoke caches.
    core.OUT = out / "evidence"
    core.OUT.mkdir(parents=True, exist_ok=True)
    jsonl = out / (f"results_{args.portal or 'all'}.jsonl")
    csv_path = out / (f"results_{args.portal or 'all'}.csv")
    manifest_path = out / (f"manifest_{args.portal or 'all'}.json")
    completed: set[str] = set()
    if jsonl.exists():
        with jsonl.open(encoding="utf-8") as fh:
            for line in fh:
                try:
                    completed.add(json.loads(line)["execution_key"])
                except (json.JSONDecodeError, KeyError):
                    continue
    manifest = {
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source_bank": str(BANK), "portal": args.portal or "all", "n_templates": len(templates),
        "n_portals": len(PORTAL_IDS), "n_query_portal_pairs": len(templates) * len(PORTAL_IDS),
        "repeats": args.repeats, "expected_executions": len(templates) * (1 if args.portal else len(PORTAL_IDS)) * args.repeats,
        "models_available": tags, "selected_role_models": models, "model_policy": cfg.get("model_policy", {"max_parameter_b": 24}),
        "orchestrator": "deterministic-python", "adversarial_role": "required", "resume_existing": len(completed),
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    flat_rows: list[dict[str, Any]] = []
    for index, row in enumerate(rows, 1):
        ev = core.evidence_for(row, refresh=args.refresh_evidence)
        for repeat in range(1, args.repeats + 1):
            key = f"{row['query_id']}__{row['portal_id']}__r{repeat}"
            if key in completed:
                continue
            result = run_execution(args.base, row, ev, models, cfg)
            result["repeat"] = repeat
            result["models"] = models
            result["execution_key"] = key
            with jsonl.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(result, ensure_ascii=False) + "\n")
            flat_rows.append(flatten(result, repeat, models))
            print(f"[{index}/{len(rows)}] {key} status={flat_rows[-1]['run_status']}", flush=True)
    if flat_rows:
        all_flat: list[dict[str, Any]] = []
        if csv_path.exists():
            with csv_path.open(encoding="utf-8", newline="") as fh:
                all_flat.extend(csv.DictReader(fh))
        all_flat.extend(flat_rows)
        fields = list(all_flat[0].keys())
        with csv_path.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=fields); writer.writeheader(); writer.writerows(all_flat)
    print(json.dumps({"completed_new": len(flat_rows), "already_completed": len(completed), "expected": manifest["expected_executions"], "jsonl": str(jsonl), "csv": str(csv_path)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
