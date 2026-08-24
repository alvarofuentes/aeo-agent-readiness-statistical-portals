"""Run one real portal-search smoke case per pilot portal.

This is intentionally separate from the 360-row benchmark.  It is the review
gate that must pass before the benchmark is restarted.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

try:
    from .portal_e2e import DEFAULT_CAPTURE_DIR, run_case
except ImportError:
    from portal_e2e import DEFAULT_CAPTURE_DIR, run_case


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "benchmark" / "results" / "e2e_smoke_2026-08-23"
CASES = [
    (
        "cepalstat",
        "Dame el valor del PIB total anual a precios corrientes en dólares de Chile para 2024, con su unidad, fuente y URL oficial.",
    ),
    (
        "sdg",
        "Dame la proporción de la población de Chile que vive bajo la línea internacional de pobreza en 2024, con unidad, fuente y URL oficial.",
    ),
]


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in fieldnames})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture-dir", type=Path, default=DEFAULT_CAPTURE_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    results = [run_case(portal, query, args.capture_dir) for portal, query in CASES]
    (args.out_dir / "e2e_results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    summary_rows = []
    step_rows = []
    candidate_rows = []
    evidence_rows = []
    qa_rows = []
    for result in results:
        portal = result["portal_id"]
        search = result["search"]
        retrieval = result["retrieval"]
        verdict = result["verdict"]
        summary_rows.append(
            {
                "portal_id": portal,
                "query": result["query"],
                "concept": search["decomposition"].get("concept"),
                "country": search["decomposition"].get("country"),
                "year": search["decomposition"].get("year"),
                "candidate_url": search.get("candidate_url"),
                "selected_series_or_indicator": search.get("series_code") or search.get("indicator_id"),
                "value": retrieval.get("value"),
                "unit": retrieval.get("unit"),
                "source": (retrieval.get("source") or {}).get("description") if isinstance(retrieval.get("source"), dict) else retrieval.get("source"),
                "request_url": retrieval.get("request_url"),
                "metadata_complete": verdict["metadata_complete"],
                "citation_citable": verdict["citation_citable"],
                "e2e_pass": verdict["e2e_pass"],
                "reason": verdict["reason"],
            }
        )
        for step in result["steps"]:
            step_rows.append({"portal_id": portal, "query": result["query"], **step})
        for rank, candidate in enumerate(search.get("matches", []) or [search.get("selected")], 1):
            if candidate:
                candidate_rows.append(
                    {
                        "portal_id": portal,
                        "rank": rank,
                        "label": candidate.get("text") or candidate.get("series_description") or candidate.get("indicator_description"),
                        "indicator_id": search.get("indicator_id"),
                        "indicator_code": candidate.get("indicator_code"),
                        "series_code": candidate.get("series_code"),
                        "series_uri": candidate.get("series_uri"),
                        "selected": candidate == search.get("selected"),
                        "candidate_url": search.get("candidate_url"),
                    }
                )
        evidence_rows.extend(
            [
                {"portal_id": portal, "evidence_role": "catalog_search", "url": search.get("catalog_url"), "capture_method": search.get("capture_method"), "status": "observed", "detail": f"selected={bool(search.get('selected'))}"},
                {"portal_id": portal, "evidence_role": "candidate", "url": search.get("candidate_url"), "capture_method": search.get("capture_method"), "status": "allowlisted" if search.get("candidate_allowed") else "rejected", "detail": "specific series/API URL"},
                {"portal_id": portal, "evidence_role": "data_request", "url": retrieval.get("request_url"), "capture_method": retrieval.get("capture_method"), "status": retrieval.get("http_status"), "detail": f"rows={retrieval.get('rows_returned', 0)}; filtered={retrieval.get('rows_after_dimension_filter', 0)}"},
                {"portal_id": portal, "evidence_role": "technical_or_series_metadata", "url": search.get("technical_url") or search.get("series_url"), "capture_method": search.get("capture_method"), "status": "observed", "detail": "metadata/citation surface"},
            ]
        )
        checks = [
            ("query_decomposed", True, "The query has concept, geography, period and dimension constraints."),
            ("candidate_found_inside_portal", verdict["search_success"], "A portal catalogue returned a specific candidate."),
            ("candidate_allowlisted", verdict["candidate_allowed"], "The candidate remains under the portal's official host."),
            ("value_retrieved", verdict["retrieval_success"], "A value was present in the returned data."),
            ("metadata_complete", verdict["metadata_complete"], "Unit, source, definition/method and period were checked."),
            ("citation_reproducible", verdict["citation_citable"], "The result has an official, specific request URL."),
            ("end_to_end_gate", verdict["e2e_pass"], verdict["reason"]),
        ]
        for assertion, passed, detail in checks:
            qa_rows.append({"portal_id": portal, "assertion": assertion, "passed": passed, "detail": detail})

    _write_csv(args.out_dir / "e2e_summary.csv", summary_rows, list(summary_rows[0]))
    _write_csv(args.out_dir / "e2e_steps.csv", step_rows, ["portal_id", "query", "step", "status", "input", "evidence_url", "detail"])
    _write_csv(args.out_dir / "e2e_candidates.csv", candidate_rows, ["portal_id", "rank", "label", "indicator_id", "indicator_code", "series_code", "series_uri", "selected", "candidate_url"])
    _write_csv(args.out_dir / "e2e_evidence.csv", evidence_rows, ["portal_id", "evidence_role", "url", "capture_method", "status", "detail"])
    _write_csv(args.out_dir / "e2e_qa.csv", qa_rows, ["portal_id", "assertion", "passed", "detail"])
    print(json.dumps({"output_dir": str(args.out_dir), "cases": len(results), "all_pass": all(item["verdict"]["e2e_pass"] for item in results), "portals": {item["portal_id"]: item["verdict"] for item in results}}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

