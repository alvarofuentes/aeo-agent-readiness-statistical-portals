"""Reproducible analysis for a production-run JSONL checkpoint.

Only ``score.overall_0_100_recomputed`` is used as the agent outcome.  Rows
with transport failures or no applicable judge dimensions remain NA and are
reported as coverage, not converted to zero.  Portal-level association uses
the five portal means; repeats and query templates are clustered in the
descriptive summaries and are not treated as independent portals.
"""
from __future__ import annotations

import argparse
import csv
import itertools
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
import sys
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from benchmark.production_runner import PORTAL_ORDER, ROLES, load_templates, materialize_pairs, safe_name, stable_hash, portal_url_allowed
MATRIX = ROOT / "execution" / "expanded-audit-matrix-2026-08-22.csv"
PORTAL_NAMES = {
    "World Bank Open Data": "worldbank",
    "WHO Data": "who",
    "CEPALSTAT": "cepalstat",
    "UN Data Commons (UNSD)": "undata",
    "UN SDG Indicators": "sdg",
}


def numeric(value: Any) -> float | None:
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (TypeError, ValueError):
        return None


def mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def median(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2


def rank(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda index: values[index])
    output = [0.0] * len(values)
    cursor = 0
    while cursor < len(order):
        end = cursor
        while end + 1 < len(order) and values[order[end + 1]] == values[order[cursor]]:
            end += 1
        value = (cursor + end + 2) / 2
        for index in range(cursor, end + 1):
            output[order[index]] = value
        cursor = end + 1
    return output


def spearman(x: list[float], y: list[float]) -> float | None:
    if len(x) < 2:
        return None
    rx, ry = rank(x), rank(y)
    mx, my = mean(rx), mean(ry)
    assert mx is not None and my is not None
    numerator = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    denominator = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    return numerator / denominator if denominator else None


def kendall(x: list[float], y: list[float]) -> float | None:
    concordant = discordant = 0
    for i in range(len(x)):
        for j in range(i + 1, len(x)):
            dx, dy = x[i] - x[j], y[i] - y[j]
            if dx == 0 or dy == 0:
                continue
            if dx * dy > 0:
                concordant += 1
            else:
                discordant += 1
    total = concordant + discordant
    return (concordant - discordant) / total if total else None


def exact_permutation_p(x: list[float], y: list[float]) -> float | None:
    observed = spearman(x, y)
    if observed is None:
        return None
    extreme = 0
    total = 0
    for permutation in itertools.permutations(y):
        value = spearman(x, list(permutation))
        if value is not None and abs(value) >= abs(observed) - 1e-12:
            extreme += 1
        total += 1
    return extreme / total if total else None


def load_matrix() -> dict[str, float]:
    with MATRIX.open(encoding="utf-8", newline="") as fh:
        result: dict[str, float] = {}
        for row in csv.DictReader(fh):
            portal_id = PORTAL_NAMES.get(row.get("portal", ""))
            if portal_id and numeric(row.get("score")) is not None:
                result[portal_id] = float(row["score"])
    return result


def validate_complete_run(path: Path, rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Fail closed before calculating any portal association."""
    manifest_path = path.parent / "run_manifest.json"
    if not manifest_path.exists():
        raise RuntimeError(f"complete-run gate: missing manifest {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("status") != "COMPLETE" or manifest.get("completed_executions") != 1800:
        raise RuntimeError("complete-run gate: manifest is not COMPLETE with 1,800 executions")
    if manifest.get("gold_status", {}).get("status") != "PASS":
        raise RuntimeError("complete-run gate: gold status is not PASS")
    for key, current in (
        ("gold_sha256", __import__("hashlib").sha256((ROOT / manifest.get("gold_file", "")).read_bytes()).hexdigest() if manifest.get("gold_file") else None),
        ("aeo_matrix_sha256", __import__("hashlib").sha256(MATRIX.read_bytes()).hexdigest()),
    ):
        if current is not None and manifest.get(key) != current:
            raise RuntimeError(f"complete-run gate: manifest {key} does not match current source")
    templates = load_templates()
    pairs = materialize_pairs(templates)
    expected = {
        f"pass{pass_id}__{pair['case_id']}__repeat{repeat}"
        for pass_id, portal in enumerate(PORTAL_ORDER, start=1)
        for pair in pairs if pair["portal_id"] == portal
        for repeat in range(1, 4)
    }
    observed = [row.get("execution_key") for row in rows]
    observed_set = {key for key in observed if isinstance(key, str)}
    if len(rows) != 1800 or len(observed_set) != 1800 or observed_set != expected:
        raise RuntimeError("complete-run gate: rows/keys do not match the exact 1,800 execution contract")
    portal_counts = defaultdict(int)
    for row in rows:
        portal_counts[(row.get("case") or {}).get("portal_id")] += 1
        if row.get("status") != "OK":
            raise RuntimeError(f"complete-run gate: non-OK execution {row.get('execution_key')}")
        for role in ROLES:
            agent = (row.get("agents") or {}).get(role, {})
            if agent.get("schema_valid") is not True:
                raise RuntimeError(f"complete-run gate: invalid {role} schema in {row.get('execution_key')}")
            if (row.get("natural_signals") or {}).get(role, {}).get("available") is not True:
                raise RuntimeError(f"complete-run gate: missing natural RAW output for {role} in {row.get('execution_key')}")
        evidence_hash = row.get("evidence_sha256")
        if not evidence_hash:
            raise RuntimeError(f"complete-run gate: missing evidence hash in {row.get('execution_key')}")
        case = row.get("case") or {}
        evidence_path = path.parent / "evidence" / f"{safe_name(str(case.get('case_id', '')))}.json"
        if not evidence_path.exists():
            raise RuntimeError(f"complete-run gate: missing evidence file for {row.get('execution_key')}")
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        if evidence.get("sha256") != evidence_hash or stable_hash({k: v for k, v in evidence.items() if k != "sha256"}) != evidence_hash:
            raise RuntimeError(f"complete-run gate: evidence hash mismatch in {row.get('execution_key')}")
        portal_id = case.get("portal_id")
        for page in evidence.get("pages", []):
            final_url = page.get("final_url", page.get("requested_url", ""))
            allowlisted = page.get("allowlist_valid") is True and portal_url_allowed(portal_id, final_url)
            if not allowlisted and (page.get("evidence_use") is True or page.get("text_excerpt")):
                raise RuntimeError(f"complete-run gate: rejected redirect body used in {row.get('execution_key')}")
    if dict(portal_counts) != {portal: 360 for portal in PORTAL_ORDER}:
        raise RuntimeError(f"complete-run gate: portal counts are {dict(portal_counts)}")
    return {"manifest": str(manifest_path), "rows": len(rows), "portal_counts": dict(portal_counts), "gold": manifest.get("gold_status")}


def run(path: Path, output_dir: Path) -> dict[str, Any]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    completeness = validate_complete_run(path, rows)
    by_portal: dict[str, list[float]] = defaultdict(list)
    by_template: dict[tuple[str, str], list[float]] = defaultdict(list)
    by_family: dict[tuple[str, str], list[float]] = defaultdict(list)
    by_stratum: dict[tuple[str, str], list[float]] = defaultdict(list)
    by_repeat: dict[tuple[str, int], list[float]] = defaultdict(list)
    by_model: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    schema_failures: dict[str, int] = defaultdict(int)
    na_by_reason: dict[str, int] = defaultdict(int)
    adversarial: dict[tuple[str, str], int] = defaultdict(int)
    for row in rows:
        case = row.get("case", {})
        portal_id = case.get("portal_id")
        template_id = case.get("template_id")
        stratum = case.get("stratum")
        score = numeric((row.get("score") or {}).get("overall_0_100_recomputed"))
        if score is not None and portal_id:
            by_portal[portal_id].append(score)
            if template_id:
                by_template[(portal_id, template_id)].append(score)
            family_id = case.get("template_family_id")
            if family_id:
                by_family[(portal_id, family_id)].append(score)
            if stratum:
                by_stratum[(portal_id, stratum)].append(score)
            if row.get("repeat") is not None:
                by_repeat[(portal_id, int(row["repeat"]))].append(score)
            for role, agent in (row.get("agents") or {}).items():
                model = agent.get("model")
                if model:
                    by_model[(portal_id, role, model)].append(score)
        else:
            na_by_reason[(row.get("status") or "unknown")] += 1
        for role, agent in (row.get("agents") or {}).items():
            if agent.get("schema_valid") is not True:
                schema_failures[portal_id] += 1
        adv = row.get("adversarial", {})
        adversarial[(portal_id, adv.get("verdict") or "NA")] += 1
    matrix = load_matrix()
    portals = [portal for portal in matrix if portal in by_portal]
    outcome = [mean(by_portal[portal]) for portal in portals]
    aeo = [matrix[portal] for portal in portals]
    assert all(value is not None for value in outcome)
    portal_summary = []
    for portal in portals:
        values = by_portal[portal]
        portal_summary.append({
            "portal_id": portal,
            "aeo_score": matrix[portal],
            "mean_airsc": mean(values),
            "median_airsc": median(values),
            "n_valid": len(values),
            "n_total": sum(1 for row in rows if (row.get("case") or {}).get("portal_id") == portal),
            "coverage": len(values) / max(1, sum(1 for row in rows if (row.get("case") or {}).get("portal_id") == portal)),
            "schema_failures": schema_failures[portal],
        })
    strata = [{"portal_id": portal, "stratum": stratum, "mean_airsc": mean(values), "n_valid": len(values)} for (portal, stratum), values in sorted(by_stratum.items())]
    families = [{"portal_id": portal, "template_family_id": family, "mean_airsc": mean(values), "median_airsc": median(values), "n_valid": len(values)} for (portal, family), values in sorted(by_family.items())]
    repeats = [{"portal_id": portal, "repeat": repeat, "mean_airsc": mean(values), "n_valid": len(values)} for (portal, repeat), values in sorted(by_repeat.items())]
    models = [{"portal_id": portal, "role": role, "model": model, "mean_airsc": mean(values), "n_valid": len(values)} for (portal, role, model), values in sorted(by_model.items())]
    result = {
        "source": str(path),
        "n_rows": len(rows),
        "n_portals": len(portals),
        "portal_summary": portal_summary,
        "stratum_summary": strata,
        "family_summary": families,
        "repeat_summary": repeats,
        "model_summary": models,
        "spearman_rho": spearman(aeo, [float(value) for value in outcome]),
        "kendall_tau": kendall(aeo, [float(value) for value in outcome]),
        "spearman_exact_p": exact_permutation_p(aeo, [float(value) for value in outcome]) if len(portals) <= 8 else None,
        "na_by_status": dict(sorted(na_by_reason.items())),
        "adversarial_verdicts": {f"{portal}:{verdict}": count for (portal, verdict), count in sorted(adversarial.items())},
        "warning": "Descriptive association only; repeated executions are clustered by template family and portal, and n=5 is the number of portals. The 24-family sensitivity tables are not independent observations.",
        "completeness": completeness,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "production_analysis.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    with (output_dir / "production_portal_summary.csv").open("w", newline="", encoding="utf-8") as fh:
        fields = list(portal_summary[0]) if portal_summary else ["portal_id"]
        writer = csv.DictWriter(fh, fieldnames=fields); writer.writeheader(); writer.writerows(portal_summary)
    with (output_dir / "production_stratum_summary.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["portal_id", "stratum", "mean_airsc", "n_valid"]); writer.writeheader(); writer.writerows(strata)
    with (output_dir / "production_family_summary.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["portal_id", "template_family_id", "mean_airsc", "median_airsc", "n_valid"]); writer.writeheader(); writer.writerows(families)
    with (output_dir / "production_repeat_summary.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["portal_id", "repeat", "mean_airsc", "n_valid"]); writer.writeheader(); writer.writerows(repeats)
    with (output_dir / "production_model_summary.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["portal_id", "role", "model", "mean_airsc", "n_valid"]); writer.writeheader(); writer.writerows(models)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("jsonl", type=Path)
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args()
    output_dir = args.output_dir or args.jsonl.parent
    print(json.dumps(run(args.jsonl, output_dir), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
