"""Preflight checks for the AEO benchmark.

Run before any Ollama execution. This validates the benchmark contract without
contacting Ollama or external web services.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BANK = ROOT / "benchmark" / "query-bank-120.csv"
CONFIG = ROOT / "benchmark" / "config.yaml"
EXPECTED = {"discovery": 20, "exact_indicator": 20, "semantic_disambiguation": 25, "dimensions": 15, "comparison": 15, "temporal": 10, "metadata": 10, "citation": 5}
PORTALS = {"worldbank", "who", "cepalstat", "undata", "sdg"}
COLS = ["query_id", "portal_id", "stratum", "query", "country", "country_code"]


def fail(msg: str) -> None:
    raise SystemExit("SELF-CHECK FAILED: " + msg)


def main() -> int:
    if not BANK.exists(): fail(f"missing canonical bank: {BANK}")
    if not CONFIG.exists(): fail(f"missing config: {CONFIG}")
    with BANK.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    if len(rows) != 120: fail(f"expected 120 rows, found {len(rows)}")
    if list(rows[0]) != COLS: fail(f"unexpected bank columns: {list(rows[0])}")
    if {r["portal_id"] for r in rows} != PORTALS: fail("portal set does not match five-portal universe")
    counts = {}
    for r in rows: counts[r["stratum"]] = counts.get(r["stratum"], 0) + 1
    if counts != EXPECTED: fail(f"stratum counts {counts} != {EXPECTED}")
    ids = [r["query_id"] for r in rows]
    if ids != [f"Q{i:03d}" for i in range(1, 121)]: fail("query IDs are not contiguous Q001-Q120")
    if len({(r["portal_id"], r["query"]) for r in rows}) != 120: fail("duplicate portal/query combinations")
    print("SELF-CHECK PASS")
    print("bank_rows=120")
    print("portals=5")
    print("strata=" + repr(counts))
    print("config_present=True")
    print("runner_ready=True")
    return 0


if __name__ == "__main__":
    sys.exit(main())
