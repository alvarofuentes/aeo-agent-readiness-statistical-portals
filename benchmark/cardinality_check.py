"""Fail-closed cardinality audit for the PDF benchmark contract.

This gate materializes and validates the deterministic 120 x 5 cross-product.
It does not execute models or web requests.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_BANK = ROOT / "benchmark" / "query-bank-120.csv"
EXPANDED_BANK = ROOT / "benchmark" / "query-bank-expanded-600.csv"
PORTALS = {"worldbank", "who", "cepalstat", "undata", "sdg"}
REPEATS = 3
PASSES = 5


def main() -> int:
    from materialize_query_bank import EXPANDED_COLUMNS, materialize

    source_rows = list(csv.DictReader(SOURCE_BANK.open(encoding="utf-8", newline="")))
    rows = materialize()
    query_ids = {row["query_id"] for row in source_rows}
    query_texts = {row["query"] for row in source_rows}
    portals = {row["portal_id"] for row in rows}
    observed_pairs = {(row["query_id"], row["portal_id"]) for row in rows}
    expected_pairs = len(query_ids) * len(PORTALS)
    expected_executions = expected_pairs * REPEATS
    observed_executions = len(rows) * REPEATS
    duplicate_pairs = len(rows) - len(observed_pairs)
    columns_ok = list(rows[0]) == EXPANDED_COLUMNS
    report = {
        "source_bank": str(SOURCE_BANK),
        "expanded_bank": str(EXPANDED_BANK),
        "source_bank_rows": len(source_rows),
        "expanded_bank_rows": len(rows),
        "query_ids": len(query_ids),
        "unique_query_texts": len(query_texts),
        "portals": len(portals),
        "observed_query_portal_pairs": len(observed_pairs),
        "expected_query_portal_pairs": expected_pairs,
        "repeats": REPEATS,
        "passes": PASSES,
        "executions_per_pass": len(query_ids) * REPEATS,
        "expected_executions_pdf": expected_executions,
        "observed_executions": observed_executions,
        "duplicate_query_portal_pairs": duplicate_pairs,
        "expanded_columns_ok": columns_ok,
        "status": "PASS" if (
            len(source_rows) == 120
            and query_ids == {f"Q{i:03d}" for i in range(1, 121)}
            and portals == PORTALS
            and len(rows) == expected_pairs
            and duplicate_pairs == 0
            and columns_ok
            and observed_executions == expected_executions
        ) else "HOLD",
        "reason": "Materialized bank matches 120 queries x 5 portals x 3 repeats."
        if observed_executions == expected_executions and duplicate_pairs == 0
        else "Expanded bank does not satisfy the PDF cardinality contract.",
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
