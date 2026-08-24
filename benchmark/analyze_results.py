"""Analyze completed benchmark results and association with technical AEO score.

Portal-level rank tests are intentionally based on five portals. Repeated query
runs are summarized, and the script also reports stratum-level means and model
coverage without treating repeated executions as independent portals.
"""
from __future__ import annotations

import csv
import itertools
import json
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "benchmark/results/results.csv"
MATRIX = ROOT / "execution/expanded-audit-matrix-2026-08-22.csv"
OUT = ROOT / "benchmark/results"
AEO = {"worldbank": 77.0, "who": 77.0, "cepalstat": 48.0, "undata": 78.0, "sdg": 88.0}
DIMENSIONS = ["discovery_success", "retrieval_success", "temporal_geographic_correctness", "semantic_correctness", "metadata_correctness", "citation_correctness"]


def mean(values): return sum(values) / len(values) if values else float("nan")

def rank(values):
    order = sorted(range(len(values)), key=lambda i: values[i]); out = [0.0] * len(values); i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]: j += 1
        r = (i + j + 2) / 2
        for k in range(i, j + 1): out[order[k]] = r
        i = j + 1
    return out

def spearman(x, y):
    if len(x) < 2: return float("nan")
    rx, ry = rank(x), rank(y); mx, my = mean(rx), mean(ry)
    den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    return sum((a - mx) * (b - my) for a, b in zip(rx, ry)) / den if den else float("nan")

def kendall(x, y):
    c = d = 0
    for i in range(len(x)):
        for j in range(i + 1, len(x)):
            dx, dy = x[i] - x[j], y[i] - y[j]
            if dx == 0 or dy == 0: continue
            if dx * dy > 0: c += 1
            else: d += 1
    return (c - d) / (c + d) if c + d else float("nan")

def exact_perm_p(x, y, statistic):
    observed = abs(statistic(x, y)); extreme = 0; total = 0
    for perm in itertools.permutations(y):
        extreme += abs(statistic(x, list(perm))) >= observed - 1e-12; total += 1
    return extreme / total if total else float("nan")

def numeric(v):
    try:
        x = float(v); return x if math.isfinite(x) else None
    except (TypeError, ValueError):
        return None


def main():
    if not RESULTS.exists(): raise SystemExit(f"Missing {RESULTS}; run the Ollama benchmark first")
    with RESULTS.open(encoding="utf-8", newline="") as fh: rows = list(csv.DictReader(fh))
    with MATRIX.open(encoding="utf-8", newline="") as fh: mat = {r["portal_id"]: float(r["score"]) for r in csv.DictReader(fh)}
    if not rows: raise SystemExit("No benchmark rows")
    required = {"portal_id", "stratum", "repeat", "overall_0_100", *DIMENSIONS}
    missing = required - set(rows[0].keys())
    if missing: raise SystemExit("Missing benchmark columns: " + ", ".join(sorted(missing)))

    by_portal = defaultdict(list); by_stratum = defaultdict(list); models = defaultdict(set); schema_failures = defaultdict(int)
    for row in rows:
        score = numeric(row.get("overall_0_100"))
        if score is not None:
            by_portal[row["portal_id"]].append(score); by_stratum[(row["portal_id"], row["stratum"])].append(score)
        for key in ["judge_model", "semantic_model"]: 
            if row.get(key): models[row["portal_id"]].add(row[key])
        sf = numeric(row.get("schema_failures")); schema_failures[row["portal_id"]] += int(sf or 0)

    portals = [p for p in AEO if p in by_portal and p in mat]
    x = [mat[p] for p in portals]; y = [mean(by_portal[p]) for p in portals]
    summary = [{"portal_id": p, "aeo_score": mat[p], "mean_airsc": mean(by_portal[p]), "median_airsc": sorted(by_portal[p])[len(by_portal[p]) // 2], "n_runs": len(by_portal[p]), "models": sorted(models[p]), "schema_failures": schema_failures[p]} for p in portals]
    strata = [{"portal_id": p, "stratum": s, "mean_airsc": mean(v), "n": len(v)} for (p, s), v in sorted(by_stratum.items())]
    result = {
        "n_rows": len(rows), "n_portals": len(portals), "portal_summary": summary, "stratum_summary": strata,
        "spearman_rho": spearman(x, y), "kendall_tau": kendall(x, y),
        "spearman_exact_p": exact_perm_p(x, y, spearman) if len(portals) <= 8 else None,
        "warning": "Repeated executions are clustered by query; portal-level n is the number of portals, not execution count.",
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "analysis_summary.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    with (OUT / "portal_summary.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=summary[0].keys() if summary else ["portal_id"]); w.writeheader(); w.writerows(summary)
    with (OUT / "stratum_summary.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["portal_id", "stratum", "mean_airsc", "n"]); w.writeheader(); w.writerows(strata)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__": main()
