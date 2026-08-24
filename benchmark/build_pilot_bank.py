"""Materialize the deterministic 60-template extreme-portal pilot bank."""
from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "benchmark" / "query-bank-120.csv"
TARGET = ROOT / "benchmark" / "query-bank-pilot-60.csv"
GOLD_SOURCE = ROOT / "benchmark" / "gold_standards_final_2026-08-23.json"
GOLD_TARGET = ROOT / "benchmark" / "gold_pilot_cepalstat_sdg_60.json"

# Five source-portal copies are retained for provenance.  Each copy contributes
# the same balanced 12-template stratum slice, totalling 60 template IDs.
PER_SOURCE = {
    "discovery": 2,
    "exact_indicator": 2,
    "semantic_disambiguation": 3,
    "dimensions": 1,
    "comparison": 1,
    "temporal": 1,
    "metadata": 1,
    "citation": 1,
}

with SOURCE.open(encoding="utf-8", newline="") as fh:
    rows = list(csv.DictReader(fh))
selected: list[dict[str, str]] = []
for source_portal in sorted({row["portal_id"] for row in rows}):
    by_stratum: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        if row["portal_id"] == source_portal:
            by_stratum[row["stratum"]].append(row)
    for stratum, count in PER_SOURCE.items():
        selected.extend(by_stratum[stratum][:count])
selected.sort(key=lambda row: int(row["query_id"][1:]))
if len(selected) != 60 or len({row["query_id"] for row in selected}) != 60:
    raise SystemExit(f"pilot bank cardinality error: {len(selected)}")
gold_source = json.loads(GOLD_SOURCE.read_text(encoding="utf-8"))
gold_items = gold_source.get("items", [])
for index, row in enumerate(selected, start=1):
    row["query_id"] = f"PILOT-Q{index:03d}"
with TARGET.open("w", encoding="utf-8", newline="") as fh:
    writer = csv.DictWriter(fh, fieldnames=["query_id", "portal_id", "stratum", "query", "country", "country_code"])
    writer.writeheader(); writer.writerows(selected)
pilot_items = []
for row in selected:
    for portal_id in ("cepalstat", "sdg"):
        matches = [item for item in gold_items if item.get("query") == row["query"] and item.get("portal_id") == portal_id and item.get("stratum") == row["stratum"] and item.get("expected_country_code") == row["country_code"]]
        if not matches:
            raise SystemExit(f"missing gold match for {row['query_id']} {portal_id}")
        item = dict(matches[0]); item["template_id"] = row["query_id"]; pilot_items.append(item)
gold_payload = {"source": "gold_standards_final_2026-08-23.json", "source_sha256": hashlib.sha256(GOLD_SOURCE.read_bytes()).hexdigest(), "scope": "pilot_extremes", "template_count": 60, "portals": ["cepalstat", "sdg"], "n": len(pilot_items), "items": pilot_items}
GOLD_TARGET.write_text(json.dumps(gold_payload, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"wrote {TARGET} ({len(selected)} templates)")
print(f"wrote {GOLD_TARGET} ({len(pilot_items)} pair contracts)")
