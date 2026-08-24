"""Analyze Ollama benchmark results against technical AEO scores.

The benchmark outcome is independent of the AEO score. Repeated query runs are
summarized at portal level, while permutation inference uses only the five
portal-level observations.
"""
from __future__ import annotations

import csv
import itertools
import math
import sys
from collections import defaultdict

AEO = {
    "worldbank": 77.0,
    "who": 77.0,
    "cepalstat": 48.0,
    "undata": 78.0,
    "sdg": 88.0,
}
REQUIRED = [
    "discovery_success", "retrieval_success", "temporal_geographic_correctness",
    "semantic_correctness", "metadata_correctness", "citation_correctness",
]


def mean(values):
    return sum(values) / len(values) if values else float("nan")


def rank(values):
    order = sorted(range(len(values)), key=lambda i: values[i])
    out = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        r = (i + j + 2) / 2
        for k in range(i, j + 1):
            out[order[k]] = r
        i = j + 1
    return out


def corr(x, y):
    mx, my = mean(x), mean(y)
    den = math.sqrt(sum((a - mx) ** 2 for a in x) * sum((b - my) ** 2 for b in y))
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / den if den else float("nan")


def spearman(x, y):
    return corr(rank(x), rank(y))


def kendall(x, y):
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
    return (concordant - discordant) / total if total else float("nan")


def exact_permutation_p(x, y, statistic):
    observed = abs(statistic(x, y))
    extreme = 0
    total = 0
    for perm in itertools.permutations(y):
        extreme += abs(statistic(x, list(perm))) >= observed - 1e-12
        total += 1
    return extreme / total if total else float("nan")


def numeric(value):
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def main(path):
    with open(path, encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        raise SystemExit("No benchmark rows found")
    required = {"portal_id", "query_id", "repeat", "overall_0_100", *REQUIRED}
    missing = required - set(rows[0].keys())
    if missing:
        raise SystemExit("Missing benchmark columns: " + ", ".join(sorted(missing)))

    by_portal = defaultdict(list)
    by_stratum = defaultdict(list)
    for row in rows:
        vals = [numeric(row.get(col)) for col in REQUIRED]
        vals = [v for v in vals if v is not None]
        overall = numeric(row.get("overall_0_100"))
        if overall is None and vals:
            overall = 100 * mean(vals)
        if overall is not None:
            by_portal[row["portal_id"]].append(overall)
            by_stratum[(row["portal_id"], row["stratum"])].append(overall)

    portals = [p for p in AEO if p in by_portal and by_portal[p]]
    outcome = [mean(by_portal[p]) for p in portals]
    x = [AEO[p] for p in portals]
    print("portal_id,aeo_score,mean_airsc,n_runs")
    for p, a, o in zip(portals, x, outcome):
        print(f"{p},{a:.1f},{o:.4f},{len(by_portal[p])}")
    if len(portals) >= 3:
        rho = spearman(x, outcome); tau = kendall(x, outcome)
        print(f"spearman_rho,{rho:.4f}")
        print(f"kendall_tau,{tau:.4f}")
        if len(portals) <= 8:
            print(f"spearman_exact_p,{exact_permutation_p(x, outcome, spearman):.4f}")
    else:
        print("insufficient_portals_for_rank_test,1")
    print("note,Repeated executions are clustered by query; portal-level n is number of portals.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: analyze_agent_benchmark.py benchmark/results/results.csv")
    main(sys.argv[1])
