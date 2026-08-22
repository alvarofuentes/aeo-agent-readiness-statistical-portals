import csv
import math
from pathlib import Path

base = Path(__file__).parent
rows = list(csv.DictReader((base / "aeo-referral-pilot-2026-08-22.csv").open(encoding="utf-8")))
portals = {
    "World Bank": ("worldbank", 90.9),
    "WHO Data": ("who", 83.6),
    "Statista": ("statista", 65.5),
    "CEPALSTAT": ("cepalstat", 58.2),
}

def mean(values):
    return sum(values) / len(values)

def rank(values):
    ordered = sorted(enumerate(values), key=lambda item: item[1])
    result = [0.0] * len(values)
    i = 0
    while i < len(ordered):
        j = i
        while j + 1 < len(ordered) and ordered[j + 1][1] == ordered[i][1]:
            j += 1
        avg = (i + j + 2) / 2
        for k in range(i, j + 1):
            result[ordered[k][0]] = avg
        i = j + 1
    return result

scores = [value[1] for value in portals.values()]
exposure = [mean([int(row[key]) for row in rows]) for key, _ in portals.values()]
score_rank = rank(scores)
exposure_rank = rank(exposure)
score_mean = mean(score_rank)
exposure_mean = mean(exposure_rank)
numerator = sum((a - score_mean) * (b - exposure_mean) for a, b in zip(score_rank, exposure_rank))
denom = math.sqrt(
    sum((a - score_mean) ** 2 for a in score_rank)
    * sum((b - exposure_mean) ** 2 for b in exposure_rank)
)
rho = numerator / denom

print("portal,common_core_score,exposure")
for (portal, (_, score)), value in zip(portals.items(), exposure):
    print(f"{portal},{score:.1f},{value:.3f}")
print(f"spearman_rho,{rho:.3f}")
print("n_sites,4")
print("n_queries,8")
