"""Audit the current expanded gold file without promoting or rewriting it.

The project has two distinct artifacts:

* a 600-row query/portal contract; and
* a validated candidate gold with values and API claims.

This audit checks whether the second artifact is allowed to be treated as the
first. It is deliberately read-only and fail-closed. In particular, a value
for a discovery or semantic question is not accepted merely because an API
returned HTTP 200, and a URL without a row-level evidence hash is not enough
to call a target reproducible.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "benchmark" / "gold_standards_expanded.json"
DEFAULT_OUT = ROOT / "benchmark" / "results" / "gold_audit_20260822.json"
DEFAULT_FINDINGS = ROOT / "benchmark" / "results" / "gold_audit_20260822.jsonl"
PORTALS = {"worldbank", "who", "cepalstat", "undata", "sdg"}
HOST_SUFFIXES = {
    "worldbank": ("worldbank.org",),
    "who": ("who.int", "azureedge.net"),
    "cepalstat": ("cepal.org",),
    "undata": ("unstats.un.org",),
    "sdg": ("unstats.un.org",),
}
COUNTRY_CODES = {"ARG", "BOL", "BRA", "CHL", "COL", "CRI", "ECU", "MEX", "PER", "URY"}


def normalize(value: str) -> str:
    text = unicodedata.normalize("NFKD", value or "")
    return "".join(char for char in text if not unicodedata.combining(char)).lower()


def is_numeric_target_requested(item: dict[str, Any]) -> bool:
    """Conservative target policy derived from query intent."""
    text = normalize(item.get("query", ""))
    # These prompts discuss a series, source, definition or dimension; they do
    # not establish a unique numeric target even if a year appears.
    non_numeric_phrases = (
        "encuentra la fuente", "donde puedo consultar", "localiza el indicador",
        "encuentra una pagina", "que indicador usarias", "que indicador usar",
        "debo usar", "distingue correctamente", "que serie corresponde",
        "que medida evitaria", "que significa exactamente", "quien produce",
        "es anual o trimestral", "esta expresado en moneda",
    )
    if any(phrase in text for phrase in non_numeric_phrases):
        return False
    if item.get("stratum") in {"exact_indicator", "comparison", "citation", "temporal"}:
        return any(token in text for token in ("cual fue", "dame el valor", "devuelve el dato", "compara", "responde con", "que economia es mayor"))
    return False


def explicit_measure(item: dict[str, Any]) -> bool:
    text = normalize(item.get("query", ""))
    return any(phrase in text for phrase in ("precios corrientes", "dolares corrientes", "usd corrientes", "crecimiento", "por habitante", "per capita", "precios constantes", "pib real"))


def target_payload_present(item: dict[str, Any]) -> bool:
    value = item.get("target_value")
    values = item.get("target_values")
    return value is not None or (isinstance(values, dict) and any(v not in (None, {}, []) for v in values.values()))


def evidence_pointer_present(item: dict[str, Any]) -> bool:
    """Require a row-level trace, not only an acceptable URL."""
    keys = {"evidence_sha256", "evidence_hash", "evidence_path", "evidence_file", "retrieved_at", "captured_at"}
    return any(item.get(key) for key in keys)


def url_is_official(item: dict[str, Any]) -> bool:
    urls = item.get("acceptable_urls") or []
    if not urls:
        return False
    suffixes = HOST_SUFFIXES.get(item.get("portal_id"), ())
    for url in urls:
        host = (urlparse(str(url)).hostname or "").lower()
        if not host or not any(host == suffix or host.endswith("." + suffix) for suffix in suffixes):
            return False
    return True


def contract_shape(items: list[dict[str, Any]]) -> dict[str, Any]:
    pair_keys = {(item.get("template_id"), item.get("portal_id")) for item in items}
    missing_family_ids = sum(not item.get("template_family_id") for item in items)
    return {
        "n": len(items),
        "unique_pairs": len(pair_keys),
        "n_templates": len({item.get("template_id") for item in items}),
        "n_families": len({item.get("template_family_id") for item in items}),
        "missing_template_family_ids": missing_family_ids,
        "portal_counts": dict(sorted(Counter(item.get("portal_id") for item in items).items())),
        "stratum_counts": dict(sorted(Counter(item.get("stratum") for item in items).items())),
        "country_code_invalid": sum(item.get("expected_country_code") not in COUNTRY_CODES for item in items),
        "status": "PASS" if len(items) == 600 and len(pair_keys) == 600 and missing_family_ids == 0 and set(item.get("portal_id") for item in items) == PORTALS else "HOLD",
    }


def audit(source: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    data = json.loads(source.read_text(encoding="utf-8"))
    items = data.get("items") if isinstance(data, dict) else None
    if not isinstance(items, list):
        raise SystemExit("source has no items list")
    findings: list[dict[str, Any]] = []

    def add(code: str, item: dict[str, Any] | None, reason: str, severity: str = "HOLD") -> None:
        findings.append({"code": code, "severity": severity, "reason": reason, "template_id": item.get("template_id") if item else None, "portal_id": item.get("portal_id") if item else None})

    shape = contract_shape(items)
    if shape["status"] != "PASS":
        add("CONTRACT_SHAPE_INVALID", None, "Expected 600 unique query/portal pairs over the five official portals.")
    if shape["missing_template_family_ids"]:
        add("MISSING_TEMPLATE_FAMILY_ID", None, f"{shape['missing_template_family_ids']} rows do not preserve the 24-family provenance key from the canonical bank.")
    status_counts = Counter(item.get("gold_status") for item in items)
    if status_counts.get("validated", 0) == len(items):
        add("GLOBAL_STATUS_OVERCLAIM", None, "Every row is marked validated; unresolved, not-required and missing targets must remain distinguishable.")
    for item in items:
        target = target_payload_present(item)
        required = is_numeric_target_requested(item)
        if target and not required:
            add("UNEXPECTED_TARGET", item, "A numeric target was populated for a discovery, semantic, metadata or dimension-oriented query.")
        if target and required and not explicit_measure(item):
            add("AMBIGUOUS_MEASURE", item, "Target value exists but the query does not specify price basis, unit, or growth-vs-level measure.")
        if target and not evidence_pointer_present(item):
            add("MISSING_ROW_EVIDENCE_POINTER", item, "URL is not a row-level raw-response hash/path; reproducible promotion is impossible from the gold row alone.")
        if target and not url_is_official(item):
            add("NON_OFFICIAL_OR_MISSING_URL", item, "Target value lacks a URL that passes the portal host allowlist.")
        if item.get("target_available") == "validated_missing" and not required:
            add("MISSING_TARGET_ON_NON_NUMERIC", item, "A non-numeric contract is labelled missing target instead of not_applicable/contract_only.", severity="WARN")
        if item.get("gold_status") == "validated" and item.get("validation_status") in {"validated_missing_target", "pending", "validated_contract"}:
            add("STATUS_COLLAPSES_UNRESOLVED", item, "gold_status=validated hides a contract-only or missing target state.")
    # Detect duplicate family/query combinations and query-bank expansion.
    family_queries: dict[str, set[str]] = defaultdict(set)
    for item in items:
        family_queries[str(item.get("template_family_id"))].add(str(item.get("query")))
    for family, queries in family_queries.items():
        if len(queries) != 1:
            add("FAMILY_QUERY_DRIFT", None, f"template_family_id={family} has {len(queries)} different query strings.")
    findings_by_code = Counter(finding["code"] for finding in findings)
    report = {
        "source": str(source),
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "declared_metadata": {key: data.get(key) for key in ("source", "validated_at", "n", "n_query_ids", "n_query_families", "query_family_note")},
        "shape": shape,
        "gold_status_counts": dict(status_counts),
        "target_available_counts": dict(Counter(item.get("target_available") for item in items)),
        "validation_status_counts": dict(Counter(item.get("validation_status") for item in items)),
        "target_payload_rows": sum(target_payload_present(item) for item in items),
        "numeric_target_expected_rows": sum(is_numeric_target_requested(item) for item in items),
        "row_evidence_pointer_rows": sum(evidence_pointer_present(item) for item in items),
        "findings_by_code": dict(findings_by_code),
        "findings": len(findings),
        "decision": "HOLD" if findings else "PASS",
        "policy": "No numeric target is promoted unless query intent is numeric, measure is explicit, official URL passes allowlist, and row-level raw evidence hash/path is present.",
    }
    return report, findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--findings", type=Path, default=DEFAULT_FINDINGS)
    args = parser.parse_args()
    report, findings = audit(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    with args.findings.open("w", encoding="utf-8") as fh:
        for finding in findings:
            fh.write(json.dumps(finding, ensure_ascii=False, sort_keys=True) + "\n")
    print(json.dumps({"decision": report["decision"], "source": str(args.source), "shape": report["shape"], "target_payload_rows": report["target_payload_rows"], "numeric_target_expected_rows": report["numeric_target_expected_rows"], "findings": report["findings"], "findings_by_code": report["findings_by_code"], "report": str(args.output), "findings_file": str(args.findings)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
