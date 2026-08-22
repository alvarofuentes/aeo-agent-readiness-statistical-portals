#!/usr/bin/env python3
"""Analyze independent agent benchmark results against technical AEO scores.

Expected input columns:
portal, query_id, repeat, discovery_success, retrieval_success,
semantic_correctness, metadata_correctness, citation_correctness, final_answer_score

The script deliberately keeps the benchmark outcome independent from the AEO score.
"""
from __future__ import annotations
import csv
import math
import itertools
import sys
from collections import defaultdict

AEO = {
    "World Bank Open Data": 77.0,
    "WHO Data": 77.0,
    "CEPALSTAT": 48.0,
    "UN Data Commons (UNSD)": 78.0,
    "UN SDG Indicators": 88.0,
}

def mean(xs):
    return sum(xs) / len(xs) if xs else float("nan")

def rank(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    out = [0.0] * len(xs)
    i = 0
    while i < len(xs):
        j = i
        while j + 1 < len(xs) and xs[order[j+1]] == xs[order[i]]:
            j += 1
        r = (i + j + 2) / 2
        for k in range(i, j + 1): out[order[k]] = r
        i = j + 1
    return out

def corr(xs, ys):
    mx, my = mean(xs), mean(ys)
    num = sum((x-mx)*(y-my) for x,y in zip(xs,ys))
    den = math.sqrt(sum((x-mx)**2 for x in xs) * sum((y-my)**2 for y in ys))
    return num/den if den else float("nan")

def spearman(xs, ys): return corr(rank(xs), rank(ys))

def kendall(xs, ys):
    c = d = 0
    for i in range(len(xs)):
        for j in range(i+1, len(xs)):
            dx = xs[i] - xs[j]; dy = ys[i] - ys[j]
            if dx == 0 or dy == 0: continue
            if dx * dy > 0: c += 1
            else: d += 1
    return (c-d) / (c+d) if c+d else float("nan")

def exact_permutation_p(xs, ys, statistic):
    observed = abs(statistic(xs, ys))
    idx = list(range(len(ys)))
    extreme = 0
    total = 0
    for perm in itertools.permutations(idx):
        yp = [ys[i] for i in perm]
        val = abs(statistic(xs, yp))
        extreme += val >= observed - 1e-12
        total += 1
    return extreme / total

def main(path):
    with open(path, encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    by_portal = defaultdict(list)
    for r in rows:
        required = ["discovery_success","retrieval_success","semantic_correctness","metadata_correctness","citation_correctness","final_answer_score"]
        vals = []
        for col in required:
            try: vals.append(float(r[col]))
            except Exception: vals.append(float("nan"))
        score = mean([v for v in vals if not math.isnan(v)])
        by_portal[r["portal"]].append(score)
    portals = [p for p in AEO if p in by_portal and by_portal[p]]
    outcome = [mean(by_portal[p]) for p in portals]
    x = [AEO[p] for p in portals]
    print("portal,aeo_score,mean_AIRSC")
    for p,a,o in zip(portals,x,outcome): print(f"{p},{a:.1f},{o:.4f}")
    if len(portals) >= 3:
        print(f"spearman_rho,{spearman(x,outcome):.4f}")
        print(f"kendall_tau,{kendall(x,outcome):.4f}")
        if len(portals) <= 8:
            print(f"spearman_exact_p,{exact_permutation_p(x,outcome,spearman):.4f}")
    else:
        print("insufficient_portals_for_rank_test,1")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: analyze_agent_benchmark.py results.csv")
    main(sys.argv[1])
