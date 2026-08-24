"""Build portal/query gold contracts from the canonical query bank.

The contract is explicit about what is known from the query text and what still
requires portal-specific manual/API validation.  It prevents the LLM judge from
inventing a target value and keeps unavailable targets distinct from model
failures.
"""
from __future__ import annotations

import json
import re
import argparse
from pathlib import Path

from .runner_production import PORTAL_IDS, load_rows

ROOT = Path(__file__).resolve().parents[1]
PORTAL_ROOTS = {
    "worldbank": "worldbank.org", "who": "who.int", "cepalstat": "cepal.org",
    "undata": "unstats.un.org", "sdg": "unstats.un.org",
}


def year_terms(query: str) -> list[str]:
    return sorted(set(re.findall(r"\b(?:19|20)\d{2}\b", query)))


def applicable(stratum: str) -> list[str]:
    base = ["discovery_success", "semantic_correctness", "citation_correctness"]
    if stratum in {"exact_indicator", "dimensions", "comparison", "temporal"}:
        base += ["retrieval_success", "temporal_geographic_correctness"]
    if stratum in {"metadata", "exact_indicator", "dimensions"}:
        base += ["metadata_correctness"]
    return list(dict.fromkeys(base))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "benchmark" / "gold_standards_expanded.json")
    args = parser.parse_args()
    gold: list[dict] = []
    for row in load_rows():
        for portal_id in PORTAL_IDS:
            query = row["query"]
            gold.append({
                "template_id": row["query_id"], "portal_id": portal_id,
                "template_family_id": row["template_family_id"], "stratum": row["stratum"],
                "query": query, "expected_country": row["country"], "expected_country_code": row["country_code"],
                "expected_periods": year_terms(query), "expected_host_root": PORTAL_ROOTS[portal_id],
                "expected_concepts": ["PIB", "GDP", "producto interno bruto"],
                "expected_unit_hints": [term for term in ["precios corrientes", "precios constantes", "por habitante", "crecimiento", "moneda nacional", "USD"] if term.lower() in query.lower()],
                "acceptable_urls": [], "target_series_id": None, "target_value": None,
                "target_available": "to_validate", "applicable_dimensions": applicable(row["stratum"]),
                "gold_status": "contract_only_manual_or_api_validation_required",
            })
    out = args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"source": "auditoría AEO.pdf", "n": len(gold), "items": gold}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(out), "n": len(gold), "status": "CONTRACT_READY_TARGET_VALUES_PENDING"}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
