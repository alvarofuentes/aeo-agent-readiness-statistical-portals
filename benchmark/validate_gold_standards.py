"""Validate the 600 query/portal gold contracts against official APIs.

This is a fail-closed *candidate* validator. It never treats a homepage, an
HTTP 200, or a guessed indicator mapping as a target value. A row is
promotable only when the portal adapter, series mapping, geography, period,
unit and value are all explicit and the raw official response is archived with
a SHA-256 hash.

The executable adapter is World Bank Open Data. The other four portals are
represented in the registry as ``ADAPTER_PENDING``; this is intentional. It
makes missing coverage visible instead of silently copying World Bank values
into another portal's gold standard.

Examples::

    python benchmark/validate_gold_standards.py --dry-run
    python benchmark/validate_gold_standards.py --execute --run-id wb-20260822
    python benchmark/validate_gold_standards.py --execute --apply \\
      --output benchmark/gold_standards_validated_wb-20260822.json

The source ``gold_standards_expanded.json`` is never overwritten.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "benchmark" / "gold_standards_expanded.json"
EVIDENCE_ROOT = ROOT / "benchmark" / "results" / "gold_validation"
PORTALS = ("worldbank", "who", "cepalstat", "undata", "sdg")

# This registry is the authority for what this validator may call. The
# non-World-Bank entries are deliberately not guessed from their homepages.
PORTAL_REGISTRY: dict[str, dict[str, Any]] = {
    "worldbank": {
        "adapter": "world_bank_v2",
        "official_api_root": "https://api.worldbank.org/v2",
        "allowed_hosts": ["api.worldbank.org"],
        "status": "IMPLEMENTED",
    },
    "who": {
        "adapter": None,
        "official_api_root": "https://data.who.int/",
        "allowed_hosts": ["who.int"],
        "status": "ADAPTER_PENDING",
        "next_step": "Freeze an exact WHO series/dimension contract before requesting values.",
    },
    "cepalstat": {
        "adapter": None,
        "official_api_root": "https://statistics.cepal.org/portal/cepalstat/",
        "allowed_hosts": ["cepal.org"],
        "status": "ADAPTER_PENDING",
        "next_step": "Freeze a CEPALSTAT series/API contract and dimension mapping.",
    },
    "undata": {
        "adapter": None,
        "official_api_root": "https://unstats.un.org/UNSDWebsite/undatacommons/",
        "allowed_hosts": ["unstats.un.org"],
        "status": "ADAPTER_PENDING",
        "next_step": "Freeze an UN Data Commons series/API contract and dimension mapping.",
    },
    "sdg": {
        "adapter": None,
        "official_api_root": "https://unstats.un.org/sdgs/dataportal/",
        "allowed_hosts": ["unstats.un.org"],
        "status": "ADAPTER_PENDING",
        "next_step": "Freeze an SDG indicator/series contract; GDP is not assumed to be an SDG indicator.",
    },
}

WORLD_BANK_SERIES = {
    "current_total": {"id": "NY.GDP.MKTP.CD", "label": "GDP (current US$)", "unit": "current US$"},
    "constant_total": {"id": "NY.GDP.MKTP.KD", "label": "GDP (constant 2015 US$)", "unit": "constant 2015 US$"},
    "per_capita_current": {"id": "NY.GDP.PCAP.CD", "label": "GDP per capita (current US$)", "unit": "current US$ per capita"},
    "growth": {"id": "NY.GDP.MKTP.KD.ZG", "label": "GDP growth (annual %)", "unit": "annual %"},
}

COUNTRY_CODES = {
    "argentina": "ARG", "bolivia": "BOL", "brazil": "BRA", "brasil": "BRA",
    "chile": "CHL", "colombia": "COL", "costa rica": "CRI", "ecuador": "ECU",
    "mexico": "MEX", "méxico": "MEX", "peru": "PER", "perú": "PER", "uruguay": "URY",
}

# Only these phrases make a series mapping explicit. “PIB total” alone is not
# enough: current-price GDP is defensible, but is still a choice not stated by
# the query and remains review-required.
EXPLICIT_PHRASES = (
    (("crecimiento", "crecio", "growth"), "growth"),
    (("precios corrientes", "dolares corrientes", "usd corrientes"), "current_total"),
    (("por habitante", "per capita"), "per_capita_current"),
    (("precios constantes", "pib real", "constant 2015"), "constant_total"),
)


def now_utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def make_run_id() -> str:
    return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_")[:180]


def normalized(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    return "".join(char for char in value if not unicodedata.combining(char)).lower()


def years(query: str) -> list[str]:
    return sorted(set(re.findall(r"\b(?:19|20)\d{2}\b", query)))


def country_codes(item: dict[str, Any]) -> list[str]:
    """Return codes in query order with the contract country first."""
    text = normalized(item.get("query", ""))
    found: list[str] = []
    for name, code in sorted(COUNTRY_CODES.items(), key=lambda pair: -len(pair[0])):
        if name in text and code not in found:
            found.append(code)
    primary = str(item.get("expected_country_code", "")).upper()
    if primary in found:
        found.remove(primary)
    if primary:
        found.insert(0, primary)
    return found


def needs_numeric_target(item: dict[str, Any]) -> bool:
    """Require an explicit request for an observation, not just a year.

    A question such as Q008 names a year and a valid series concept but asks
    which indicator should be used.  It is contract evidence, not a numeric
    target; assigning its observation would overstate the gold standard.
    """
    text = normalized(item.get("query", ""))
    if "que indicador usarias" in text or "que indicador usar" in text:
        return False
    return any(token in text for token in ("cual fue", "dame el valor", "devuelve el dato", "compara", "que economia es mayor", "responde con"))


def target_periods(item: dict[str, Any]) -> list[str]:
    if item.get("stratum") in {"exact_indicator", "comparison", "citation"} and needs_numeric_target(item):
        return years(item.get("query", ""))
    return []


def mapping(item: dict[str, Any]) -> dict[str, Any]:
    """Resolve only explicit query language; never infer generic ``PIB``."""
    text = normalized(item.get("query", ""))
    matches = [key for phrases, key in EXPLICIT_PHRASES if any(phrase in text for phrase in phrases)]
    keys = list(dict.fromkeys(matches))
    if len(keys) == 1:
        series = WORLD_BANK_SERIES[keys[0]]
        return {"status": "EXPLICIT", "series_ids": [series["id"]], "series_labels": [series["label"]], "units": [series["unit"]], "mapping_rule": keys[0]}
    if len(keys) > 1:
        return {"status": "REVIEW_REQUIRED", "reason": "query_contains_multiple_candidate_concepts", "candidate_series_ids": [WORLD_BANK_SERIES[key]["id"] for key in keys]}
    return {
        "status": "REVIEW_REQUIRED",
        "reason": "generic_or_underspecified_PIB_measure",
        "candidate_series_ids": [series["id"] for series in WORLD_BANK_SERIES.values()],
    }


def read_contract(source: Path = SOURCE) -> dict[str, Any]:
    if not source.exists():
        raise SystemExit(f"Missing gold contract: {source}")
    data = json.loads(source.read_text(encoding="utf-8"))
    items = data.get("items") if isinstance(data, dict) else None
    if not isinstance(items, list) or len(items) != 600:
        raise SystemExit("Gold contract must contain exactly 600 items")
    keys = [(item.get("template_id"), item.get("portal_id")) for item in items]
    if len(set(keys)) != 600 or any(portal not in PORTALS for _, portal in keys):
        raise SystemExit("Gold contract has duplicate or unknown template/portal keys")
    for item in items:
        if not re.fullmatch(r"[A-Z]{3}", str(item.get("expected_country_code", ""))):
            raise SystemExit(f"Invalid country code in {item.get('template_id')} / {item.get('portal_id')}")
        if item.get("target_available") not in {"to_validate", "not_applicable"} or item.get("target_value") is not None:
            raise SystemExit(f"Gold source already contains a target at {item.get('template_id')} / {item.get('portal_id')}; use a pending contract snapshot")
    return data


def contract_audit(contract: dict[str, Any]) -> dict[str, Any]:
    items = contract["items"]
    return {
        "n_items": len(items),
        "unique_template_portal_pairs": len({(x["template_id"], x["portal_id"]) for x in items}),
        "n_templates": len({x["template_id"] for x in items}),
        "n_template_families": len({x.get("template_family_id") for x in items}),
        "by_portal": dict(sorted(Counter(x["portal_id"] for x in items).items())),
        "by_stratum": dict(sorted(Counter(x["stratum"] for x in items).items())),
        "target_available_counts": dict(Counter(x.get("target_available") for x in items)),
        "target_value_present": sum(x.get("target_value") is not None for x in items),
        "acceptable_url_present": sum(bool(x.get("acceptable_urls")) for x in items),
        "expected_periods_missing": sum(not x.get("expected_periods") for x in items),
        "status": "PASS" if len(items) == 600 and len({(x["template_id"], x["portal_id"]) for x in items}) == 600 else "HOLD",
    }


class EvidenceStore:
    def __init__(self, root: Path, timeout: float = 30.0, offline: bool = False) -> None:
        self.root = root
        self.timeout = timeout
        self.offline = offline
        self.root.mkdir(parents=True, exist_ok=True)
        self.cache: dict[str, dict[str, Any]] = {}

    def request(self, url: str, allowed_hosts: set[str]) -> dict[str, Any]:
        if url in self.cache:
            return self.cache[url]
        host = (urlparse(url).hostname or "").lower()
        if host not in allowed_hosts:
            result = {"url": url, "status": 0, "error": "HOST_NOT_ALLOWLISTED", "captured_at": now_utc()}
            self.cache[url] = result
            return result
        key = safe_name(hashlib.sha256(url.encode()).hexdigest()[:16] + "_" + url.split("/")[-1])
        body_path = self.root / f"{key}.body"
        headers_path = self.root / f"{key}.headers.json"
        started = time.perf_counter()
        body = b""
        result: dict[str, Any] = {"url": url, "captured_at": now_utc()}
        if self.offline:
            result.update({"status": 0, "error": "OFFLINE_NOT_RUN", "elapsed_seconds": 0.0, "byte_length": 0, "body_sha256": sha256_bytes(b"")})
        else:
            try:
                req = Request(url, headers={"User-Agent": "AEO-Gold-Validator/2.0", "Accept": "application/json"})
                with urlopen(req, timeout=self.timeout) as response:
                    body = response.read()
                    result.update({"status": int(response.status), "final_url": response.geturl(), "headers": {k.lower(): v for k, v in response.headers.items()}})
            except HTTPError as exc:
                body = exc.read()
                result.update({"status": int(exc.code), "final_url": getattr(exc, "url", url), "headers": {k.lower(): v for k, v in exc.headers.items()} if exc.headers else {}, "error": "HTTPError"})
            except (URLError, TimeoutError, OSError) as exc:
                result.update({"status": 0, "final_url": url, "headers": {}, "error": f"{type(exc).__name__}: {exc}"})
            final_host = (urlparse(result.get("final_url", url)).hostname or "").lower()
            if result.get("status") == 200 and final_host not in allowed_hosts:
                result.update({"status": 0, "error": "FINAL_HOST_NOT_ALLOWLISTED", "final_host": final_host})
            result.update({"elapsed_seconds": round(time.perf_counter() - started, 3), "byte_length": len(body), "body_sha256": sha256_bytes(body)})
        body_path.write_bytes(body)
        headers_path.write_text(json.dumps(result.get("headers", {}), ensure_ascii=False, indent=2), encoding="utf-8")
        result.update({"body_path": str(body_path), "headers_path": str(headers_path), "body_json": None})
        if body:
            try:
                result["body_json"] = json.loads(body.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                pass
        self.cache[url] = result
        return result


def world_bank_url(country: str, indicator: str) -> str:
    params = {"format": "json", "per_page": "100"}
    return f"{PORTAL_REGISTRY['worldbank']['official_api_root']}/country/{country}/indicator/{indicator}?{urlencode(params)}"


def parse_world_bank(response: dict[str, Any], country: str, indicator: str) -> dict[str, Any]:
    payload = response.get("body_json")
    if response.get("status") != 200:
        return {"status": "TRANSPORT_OR_HTTP_ERROR", "reason": response.get("error", f"HTTP {response.get('status')}"), "records": []}
    if not isinstance(payload, list) or len(payload) < 2 or not isinstance(payload[1], list):
        return {"status": "API_PAYLOAD_INVALID", "reason": "expected_World_Bank_two_element_JSON_payload", "records": []}
    records = []
    for record in payload[1]:
        if not isinstance(record, dict):
            continue
        if record.get("countryiso3code") != country or record.get("indicator", {}).get("id") != indicator:
            continue
        records.append({"period": str(record.get("date")), "value": record.get("value"), "unit": record.get("unit"), "indicator": record.get("indicator", {}).get("value"), "indicator_id": indicator, "country_code": record.get("countryiso3code")})
    if not records:
        return {"status": "NOT_OBSERVED", "reason": "country_or_series_not_present", "records": []}
    return {"status": "API_VERIFIED", "records": records}


def validate_world_bank(item: dict[str, Any], store: EvidenceStore) -> dict[str, Any]:
    map_result = mapping(item)
    periods = target_periods(item)
    countries = country_codes(item)
    base: dict[str, Any] = {"adapter": "world_bank_v2", "mapping": map_result, "countries": countries, "periods": periods, "requests": []}
    if map_result["status"] != "EXPLICIT":
        return {**base, "status": "REVIEW_REQUIRED", "reason": map_result["reason"]}
    indicator = map_result["series_ids"][0]
    parsed: dict[str, list[dict[str, Any]]] = {}
    for country in countries:
        url = world_bank_url(country, indicator)
        response = store.request(url, set(PORTAL_REGISTRY["worldbank"]["allowed_hosts"]))
        parsed_result = parse_world_bank(response, country, indicator)
        base["requests"].append({"url": url, "country_code": country, "indicator_id": indicator, "http": {key: response.get(key) for key in ("status", "final_url", "body_sha256", "body_path", "headers_path", "byte_length", "elapsed_seconds", "error")}, "parsed": parsed_result})
        if parsed_result["status"] == "API_VERIFIED":
            parsed[country] = parsed_result["records"]
    if not periods:
        request_statuses = {request["parsed"]["status"] for request in base["requests"]}
        if store.offline:
            return {**base, "status": "OFFLINE_NOT_RUN", "reason": "dry_run_did_not_call_official_api", "target_available": "not_applicable"}
        if request_statuses == {"API_VERIFIED"}:
            return {**base, "status": "API_VERIFIED", "reason": "official_series_payload_verified_without_numeric_target", "target_available": "not_applicable"}
        if "TRANSPORT_OR_HTTP_ERROR" in request_statuses:
            return {**base, "status": "TRANSPORT_OR_HTTP_ERROR", "reason": "official_series_request_failed", "target_available": "not_applicable"}
        return {**base, "status": "NOT_OBSERVED", "reason": "official_series_payload_not_observed", "target_available": "not_applicable"}
    observations: list[dict[str, Any]] = []
    missing: list[dict[str, str]] = []
    if store.offline:
        return {**base, "status": "OFFLINE_NOT_RUN", "reason": "dry_run_did_not_call_official_api", "target_available": "not_verified"}
    for country in countries:
        by_period = {record["period"]: record for record in parsed.get(country, [])}
        for period in periods:
            record = by_period.get(period)
            if not record or record.get("value") is None:
                missing.append({"country_code": country, "period": period})
            else:
                observations.append(record)
    if missing:
        statuses = {request["parsed"]["status"] for request in base["requests"]}
        status = "TRANSPORT_OR_HTTP_ERROR" if "TRANSPORT_OR_HTTP_ERROR" in statuses else "NOT_OBSERVED"
        return {**base, "status": status, "reason": "one_or_more_required_country_period_values_missing", "missing": missing, "target_available": "not_verified"}
    values: dict[str, dict[str, Any]] = defaultdict(dict)
    for record in observations:
        values[record["country_code"]][record["period"]] = record["value"]
    if len(countries) == 1 and len(periods) == 1:
        target_value: Any = observations[0]["value"]
    elif len(countries) == 1:
        target_value = dict(values[countries[0]])
    else:
        target_value = {country: dict(values[country]) for country in countries}
    return {**base, "status": "VERIFIED_VALUE", "reason": "exact_official_series_country_period_unit_contract_satisfied", "target_available": True, "target_value": target_value, "target_observations": observations, "unit": map_result["units"][0]}


def validate_item(item: dict[str, Any], store: EvidenceStore) -> dict[str, Any]:
    registry = PORTAL_REGISTRY[item["portal_id"]]
    if registry["status"] != "IMPLEMENTED":
        return {"status": "ADAPTER_PENDING", "adapter": registry["adapter"], "official_api_root": registry["official_api_root"], "reason": registry["next_step"], "requests": []}
    return validate_world_bank(item, store)


def apply_item(item: dict[str, Any], validation: dict[str, Any]) -> dict[str, Any]:
    updated = dict(item)
    updated["validation"] = validation
    status = validation.get("status")
    if status not in {"API_VERIFIED", "VERIFIED_VALUE"}:
        return updated
    updated["acceptable_urls"] = sorted({request["url"] for request in validation.get("requests", [])})
    series_ids = validation.get("mapping", {}).get("series_ids", [])
    updated["target_series_id"] = series_ids[0] if len(series_ids) == 1 else None
    updated["expected_series_ids"] = series_ids
    if status == "VERIFIED_VALUE":
        updated["gold_status"] = "verified_official_api"
        updated["target_value"] = validation["target_value"]
        updated["target_available"] = True
    elif item.get("stratum") not in {"exact_indicator", "comparison", "citation"}:
        updated["gold_status"] = "verified_official_api_contract_only"
        updated["target_available"] = "not_applicable"
    else:
        # The official series was reached, but the query did not provide a
        # sufficiently explicit observation target (for example Q008). Keep
        # the pending target marker and do not promote this row to gold.
        updated["gold_status"] = "contract_verified_target_pending"
    return updated


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--portal", choices=["all", *PORTALS], default="all")
    parser.add_argument("--source", type=Path, default=SOURCE, help="pending-only gold contract snapshot; never overwritten")
    parser.add_argument("--execute", action="store_true", help="perform official API requests; default is dry-run")
    parser.add_argument("--dry-run", action="store_true", help="do not perform API requests")
    parser.add_argument("--apply", action="store_true", help="write a versioned candidate gold file; source remains untouched")
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--evidence-dir", type=Path, default=None)
    parser.add_argument("--timeout", type=float, default=30)
    parser.add_argument("--limit", type=int, default=None, help="bounded diagnostic limit per selected portal")
    parser.add_argument("--run-id", default=None)
    args = parser.parse_args()
    source = args.source
    contract = read_contract(source)
    audit = contract_audit(contract)
    current_run = args.run_id or make_run_id()
    evidence_dir = args.evidence_dir or (EVIDENCE_ROOT / current_run)
    offline = args.dry_run or not args.execute
    store = EvidenceStore(evidence_dir, timeout=args.timeout, offline=offline)
    selected_portals = list(PORTALS) if args.portal == "all" else [args.portal]
    selected = [item for item in contract["items"] if item["portal_id"] in selected_portals]
    if args.limit is not None:
        selected = [item for portal in selected_portals for item in selected if item["portal_id"] == portal][: max(0, args.limit * len(selected_portals))]
    selected_keys = {(item["template_id"], item["portal_id"]) for item in selected}
    validated: list[dict[str, Any]] = []
    candidate_rows: list[dict[str, Any]] = []
    summary: Counter[str] = Counter()
    by_portal: dict[str, Counter[str]] = defaultdict(Counter)
    by_stratum: dict[str, Counter[str]] = defaultdict(Counter)
    for item in contract["items"]:
        key = (item["template_id"], item["portal_id"])
        if key in selected_keys:
            validation = validate_item(item, store)
            summary[validation["status"]] += 1
            by_portal[item["portal_id"]][validation["status"]] += 1
            by_stratum[item["stratum"]][validation["status"]] += 1
            candidate = apply_item(item, validation)
        else:
            validation = {"status": "NOT_SELECTED", "reason": f"validator_run_scoped_to_{args.portal}", "requests": []}
            candidate = dict(item)
        candidate_rows.append({"template_id": item["template_id"], "portal_id": item["portal_id"], "stratum": item["stratum"], "validation": validation})
        validated.append(candidate)
    promotable = sum(row["validation"].get("status") == "VERIFIED_VALUE" for row in candidate_rows)
    manifest = {
        "source": "auditoría AEO.pdf", "source_contract": str(source), "source_contract_sha256": sha256_bytes(source.read_bytes()), "generated_at": now_utc(), "run_id": current_run,
        "validator": "benchmark/validate_gold_standards.py", "mode": "offline_dry_run" if offline else "official_api_execution",
        "scope_portals": selected_portals, "n_selected": len(selected), "n_contract_items": len(contract["items"]),
        "contract_audit": audit, "portal_registry": PORTAL_REGISTRY, "summary": dict(sorted(summary.items())),
        "summary_by_portal": {portal: dict(sorted(counter.items())) for portal, counter in sorted(by_portal.items())},
        "summary_by_stratum": {stratum: dict(sorted(counter.items())) for stratum, counter in sorted(by_stratum.items())},
        "promotable_verified_value_rows": promotable,
        "promotion_policy": "Only VERIFIED_VALUE rows with explicit mapping and complete official country/period observations may be promoted; all other statuses remain pending/review.",
        "evidence_dir": str(evidence_dir),
    }
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "gold_validation_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    with (evidence_dir / "gold_validation_candidates.jsonl").open("w", encoding="utf-8") as fh:
        for row in candidate_rows:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    output = args.output or (ROOT / "benchmark" / f"gold_standards_validated_{current_run}.json")
    if args.apply:
        output.write_text(json.dumps({"source": "auditoría AEO.pdf", "source_contract": str(source), "source_contract_sha256": sha256_bytes(source.read_bytes()), "generated_at": now_utc(), "validator": "benchmark/validate_gold_standards.py", "run_id": current_run, "n": len(validated), "summary": dict(sorted(summary.items())), "evidence_dir": str(evidence_dir), "items": validated}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": "PASS_CONTRACT_ONLY" if audit["status"] == "PASS" else "HOLD_CONTRACT", "mode": manifest["mode"], "n_contract_items": len(contract["items"]), "n_selected": len(selected), "summary": manifest["summary"], "promotable_verified_value_rows": promotable, "manifest": str(evidence_dir / "gold_validation_manifest.json"), "candidates": str(evidence_dir / "gold_validation_candidates.jsonl"), "output": str(output) if args.apply else None}, ensure_ascii=False, indent=2))
    # Unresolved API coverage is expected HOLD, not a process crash. A
    # malformed contract exits above.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
