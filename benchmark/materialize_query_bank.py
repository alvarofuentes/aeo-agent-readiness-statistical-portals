"""Materialize the PDF benchmark contract.

The committed ``query-bank-120.csv`` is the canonical set of query instances
used by the project.  The source PDF requires every instance to be evaluated
against every one of the five active portals.  This module creates the
deterministic 600-row query/portal cross-product without changing the source
bank, so the re-entrant runner can checkpoint 600 * 3 = 1,800 executions.
"""
from __future__ import annotations

import csv
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "benchmark" / "query-bank-120.csv"
EXPANDED = ROOT / "benchmark" / "query-bank-expanded-600.csv"

PORTALS = ["worldbank", "who", "cepalstat", "undata", "sdg"]
SOURCE_COLUMNS = [
    "query_id", "portal_id", "stratum", "query", "country", "country_code",
]
EXPANDED_COLUMNS = SOURCE_COLUMNS + ["source_portal_id"]


def load_source() -> list[dict[str, str]]:
    with SOURCE.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    if len(rows) != 120:
        raise ValueError(f"Expected 120 source rows, found {len(rows)}")
    if list(rows[0]) != SOURCE_COLUMNS:
        raise ValueError(f"Unexpected source columns: {list(rows[0])}")
    if [r["query_id"] for r in rows] != [f"Q{i:03d}" for i in range(1, 121)]:
        raise ValueError("Source query IDs must be contiguous Q001-Q120")
    if {r["portal_id"] for r in rows} != set(PORTALS):
        raise ValueError("Source bank does not cover the five active portals")
    return rows


def build(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    expanded: list[dict[str, str]] = []
    for row in rows:
        for portal_id in PORTALS:
            expanded.append({
                "query_id": row["query_id"],
                "portal_id": portal_id,
                "stratum": row["stratum"],
                "query": row["query"],
                "country": row["country"],
                "country_code": row["country_code"],
                "source_portal_id": row["portal_id"],
            })
    return expanded


def materialize(path: Path = EXPANDED) -> list[dict[str, str]]:
    rows = build(load_source())
    path.parent.mkdir(parents=True, exist_ok=True)
    # Include the PID so concurrent read-only gate invocations cannot consume
    # each other's temporary file before ``replace``.
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=EXPANDED_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)
    return rows


def main() -> int:
    rows = materialize()
    print(f"materialized={EXPANDED}")
    print(f"rows={len(rows)}")
    print(f"query_ids={len({r['query_id'] for r in rows})}")
    print(f"portals={len({r['portal_id'] for r in rows})}")
    print("expected_executions=1800")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
