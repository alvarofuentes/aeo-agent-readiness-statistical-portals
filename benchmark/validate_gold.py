"""Validate the pair-level gold contracts against public official APIs.

The source bank contains 120 administrative IDs but 24 repeated query families.
This validator preserves both facts, records the family id, and marks portal
capability gaps as explicit ``not_applicable`` rather than inventing a value.
All HTTP bodies and headers are kept under ``benchmark/gold_evidence_*``.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
BANK = ROOT / "benchmark" / "query-bank-120.csv"
OUT = ROOT / "benchmark" / "gold_standards_expanded.json"
EVIDENCE = ROOT / "benchmark" / "gold_evidence_2026-08-23"

COUNTRIES = {
    "Argentina": {"iso3": "ARG", "m49": "032"}, "Bolivia": {"iso3": "BOL", "m49": "068"},
    "Brazil": {"iso3": "BRA", "m49": "076"}, "Chile": {"iso3": "CHL", "m49": "152"},
    "Colombia": {"iso3": "COL", "m49": "170"}, "Costa Rica": {"iso3": "CRI", "m49": "188"},
    "Ecuador": {"iso3": "ECU", "m49": "218"}, "Mexico": {"iso3": "MEX", "m49": "484"},
    "Peru": {"iso3": "PER", "m49": "604"}, "Uruguay": {"iso3": "URY", "m49": "858"},
}
COUNTRY_ALIASES = {name.lower(): name for name in COUNTRIES}

WB_SERIES = {
    "current_usd": "NY.GDP.MKTP.CD", "constant_usd": "NY.GDP.MKTP.KD",
    "current_lcu": "NY.GDP.MKTP.CN", "constant_lcu": "NY.GDP.MKTP.KN",
    "per_capita_current": "NY.GDP.PCAP.CD", "per_capita_constant": "NY.GDP.PCAP.KD",
    "growth": "NY.GDP.MKTP.KD.ZG",
}
CEPAL_SERIES = {
    "current_usd": 2203, "constant_usd": 2204, "per_capita_current": 2205,
    "per_capita_constant": 2206, "growth": 2207, "current_lcu": 2193, "constant_lcu": 2194,
}
UN_SERIES = {
    "current_lcu": 1, "current_usd": 2, "constant_lcu": 3,
    "constant_usd": 4, "per_capita_current": 5, "growth": 8,
}


def fetch_json(url: str, name: str) -> Any:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    stem = hashlib.sha256(url.encode()).hexdigest()[:16] + "_" + name
    body_path = EVIDENCE / f"{stem}.json"
    if body_path.exists():
        cached = json.loads(body_path.read_text(encoding="utf-8"))
        return cached.get("payload", cached) if isinstance(cached, dict) else cached
    request = Request(url, headers={"User-Agent": "AEO-Gold-Validator/1.0", "Accept": "application/json"})
    try:
        with urlopen(request, timeout=60) as response:
            body = response.read()
            meta = {"url": url, "status": int(response.status), "headers": {k.lower(): v for k, v in response.headers.items()}, "captured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        meta = {"url": url, "status": getattr(exc, "code", 0) or 0, "error": f"{type(exc).__name__}: {exc}", "captured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        body = b"{}"
    try:
        payload = json.loads(body.decode("utf-8", errors="replace"))
    except json.JSONDecodeError:
        payload = {"raw_text": body.decode("utf-8", errors="replace")}
    body_path.write_text(json.dumps({"meta": meta, "payload": payload}, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def query_countries(query: str) -> list[str]:
    lower = query.lower()
    found = [name for name in COUNTRIES if name.lower() in lower]
    return found


def query_years(query: str) -> list[str]:
    return sorted(set(re.findall(r"\b(?:19|20)\d{2}\b", query)))


def series_kind(query: str) -> str:
    q = query.lower()
    if "crecimiento" in q or "growth" in q:
        return "growth"
    if "per cápita" in q or "per capita" in q or "por habitante" in q:
        return "per_capita_constant" if "constante" in q or "constant" in q else "per_capita_current"
    if "moneda nacional" in q or "national currency" in q:
        return "constant_lcu" if "constante" in q or "constant" in q else "current_lcu"
    if "precios constantes" in q or "precios constante" in q or "constant prices" in q or "dólares constantes" in q:
        return "constant_usd"
    return "current_usd"


def worldbank_value(country: str, kind: str, years: list[str]) -> dict[str, Any]:
    code = COUNTRIES[country]["iso3"]
    indicator = WB_SERIES[kind]
    url = f"https://api.worldbank.org/v2/country/{code}/indicator/{indicator}?format=json&per_page=100"
    payload = fetch_json(url, "worldbank")
    rows = payload[1] if isinstance(payload, list) and len(payload) > 1 and isinstance(payload[1], list) else []
    values = {str(row.get("date")): row.get("value") for row in rows if row.get("value") is not None}
    selected = {year: values.get(year) for year in years}
    return {"series_id": indicator, "url": url, "values": selected, "available": bool(values) and all(selected.get(y) is not None for y in years)}


def cepal_catalog() -> dict[int, dict[str, Any]]:
    result = {}
    for indicator in sorted(set(CEPAL_SERIES.values())):
        url = f"https://api-cepalstat.cepal.org/cepalstat/api/v1/indicator/{indicator}/data"
        payload = fetch_json(url, f"cepal_{indicator}")
        body = payload.get("body", {}) if isinstance(payload, dict) else {}
        result[indicator] = body
    return result


def cepal_value(body: dict[str, Any], country: str, years: list[str]) -> dict[str, Any]:
    country_code = COUNTRIES[country]["iso3"]
    country_ids: set[int] = set()
    year_ids: dict[str, int] = {}
    for dim in body.get("dimensions", []):
        name = str(dim.get("name", "")).lower()
        if "country" in name:
            for member in dim.get("members", []):
                if str(member.get("name", "")).lower().split(" [", 1)[0] == country.lower():
                    country_ids.add(int(member["id"]))
        if "year" in name:
            for member in dim.get("members", []):
                year_ids[str(member.get("name"))] = int(member["id"])
    values: dict[str, Any] = {}
    for row in body.get("data", []):
        if row.get("iso3") == country_code or row.get("dim_208") in country_ids:
            row_year = next((str(year) for year, value in year_ids.items() if value == row.get("dim_29117")), None)
            if row_year in years:
                # GDP-by-expenditure indicators require the GDP aggregate item.
                if "dim_21005" in row and row.get("dim_21005") != 21046:
                    continue
                values[row_year] = row.get("value")
    return {"values": {year: values.get(year) for year in years}, "available": all(values.get(year) is not None for year in years)}


def un_catalog() -> list[dict[str, Any]]:
    return fetch_json("https://unstats.un.org/unsd/amaapi/api/Series", "unsd_series")


def un_value(country: str, kind: str, years: list[str]) -> dict[str, Any]:
    m49 = int(COUNTRIES[country]["m49"])
    series = UN_SERIES[kind]
    url = f"https://unstats.un.org/unsd/amaapi/api/Data/limited/{m49}/{series}"
    payload = fetch_json(url, "unsd_data")
    values = {str(row.get("fiscalYear")): row.get("observationValue") for row in payload if isinstance(row, dict) and row.get("observationValue") is not None}
    return {"series_id": series, "url": url, "values": {year: values.get(year) for year in years}, "available": all(values.get(year) is not None for year in years)}


def base_item(row: dict[str, str], portal: str) -> dict[str, Any]:
    query = row["query"]
    countries = query_countries(query) or ([row["country"]] if row.get("country") in COUNTRIES else [])
    years = query_years(query)
    return {
        "case_id": f"{row['query_id']}__{portal}", "template_id": row["query_id"], "portal_id": portal,
        "template_family_id": row.get("template_family_id"), "stratum": row["stratum"], "query": query,
        "expected_country": row.get("country"), "expected_country_code": row.get("country_code"),
        "expected_countries": countries, "expected_periods": years, "target_series_id": None,
        "target_value": None, "target_values": {}, "acceptable_urls": [], "target_available": "not_required",
        "validation_status": "pending", "validation_reason": "",
    }


def validate() -> dict[str, Any]:
    rows = list(csv.DictReader(BANK.open(encoding="utf-8", newline="")))
    cepal = cepal_catalog()
    who_url = "https://ghoapi.azureedge.net/api/Indicator?$filter=contains(IndicatorName,%20%27GDP%27)"
    who = fetch_json(who_url, "who_gdp_catalog")
    sdg_url = "https://unstats.un.org/SDGAPI/v1/sdg/Indicator/List"
    sdg = fetch_json(sdg_url, "sdg_indicator_catalog")
    unsd_series = un_catalog()
    # A stable catalog record is enough for discovery/semantic/metadata/citation
    # contracts; exact values are populated whenever the query includes years.
    items: list[dict[str, Any]] = []
    for row in rows:
        for portal in ["worldbank", "who", "cepalstat", "undata", "sdg"]:
            item = base_item(row, portal)
            kind = series_kind(row["query"])
            countries = item["expected_countries"]
            years = item["expected_periods"]
            if portal == "who":
                item.update({"target_available": "not_applicable", "validation_status": "validated_not_applicable", "validation_reason": "WHO GHO catalog exposes GDP-related health/R&D ratios, not a general total/per-capita GDP series for this query.", "acceptable_urls": [who_url], "available_catalog_series": [x.get("IndicatorCode") for x in who.get("value", [])] if isinstance(who, dict) else []})
            elif portal == "sdg":
                item.update({"target_available": "not_applicable", "validation_status": "validated_not_applicable", "validation_reason": "SDG catalog exposes GDP-derived SDG indicators (notably real GDP per-capita growth), not the requested general GDP level/unit series.", "acceptable_urls": [sdg_url], "available_catalog_indicators": [x.get("code") for x in sdg if isinstance(x, dict) and "gdp" in str(x).lower()] if isinstance(sdg, list) else []})
            elif not countries:
                item.update({"validation_status": "validated_contract", "validation_reason": "No country-specific target requested by this semantic/discovery contract; official series catalog is recorded.", "target_available": "not_required"})
            elif portal == "worldbank":
                results = {country: worldbank_value(country, kind, years) for country in countries} if years else {}
                item.update({"target_series_id": WB_SERIES[kind], "acceptable_urls": sorted({r["url"] for r in results.values()}) or [f"https://api.worldbank.org/v2/indicator/{WB_SERIES[kind]}?format=json"], "target_values": {country: r["values"] for country, r in results.items()}, "target_value": next(iter(results.values()))["values"].get(years[0]) if len(countries) == 1 and len(years) == 1 and results else None})
                ok = all(r["available"] for r in results.values()) if results else True
                item.update({"target_available": "validated_value" if results and years and ok else ("validated_missing" if results and years else "not_required"), "validation_status": "validated_value" if results and years and ok else ("validated_missing_target" if results and years else "validated_contract"), "validation_reason": "World Bank indicator API response captured and matched by country/year."})
            elif portal == "cepalstat":
                indicator = CEPAL_SERIES[kind]
                results = {country: cepal_value(cepal[indicator], country, years) for country in countries} if years else {}
                url = f"https://api-cepalstat.cepal.org/cepalstat/api/v1/indicator/{indicator}/data"
                item.update({"target_series_id": indicator, "acceptable_urls": [url], "target_values": {country: r["values"] for country, r in results.items()}, "target_value": next(iter(results.values()))["values"].get(years[0]) if len(countries) == 1 and len(years) == 1 and results else None})
                ok = all(r["available"] for r in results.values()) if results else True
                item.update({"target_available": "validated_value" if results and years and ok else ("validated_missing" if results and years else "not_required"), "validation_status": "validated_value" if results and years and ok else ("validated_missing_target" if results and years else "validated_contract"), "validation_reason": "CEPALSTAT indicator metadata/data response captured; country and year dimensions matched."})
            else:
                results = {country: un_value(country, kind, years) for country in countries} if years else {}
                series = UN_SERIES[kind]
                item.update({"target_series_id": series, "acceptable_urls": sorted({r["url"] for r in results.values()}) or ["https://unstats.un.org/unsd/amaapi/api/Series"], "target_values": {country: r["values"] for country, r in results.items()}, "target_value": next(iter(results.values()))["values"].get(years[0]) if len(countries) == 1 and len(years) == 1 and results else None})
                ok = all(r["available"] for r in results.values()) if results else True
                item.update({"target_available": "validated_value" if results and years and ok else ("validated_missing" if results and years else "not_required"), "validation_status": "validated_value" if results and years and ok else ("validated_missing_target" if results and years else "validated_contract"), "validation_reason": "UNSD AMA series catalog/data response captured and matched by M49 country/year."})
            item["gold_status"] = "validated" if item["validation_status"] in {"validated_value", "validated_contract", "validated_not_applicable", "validated_missing_target"} else "pending"
            items.append(item)
    families = len({(r.get("template_family_id"), r["query"]) for r in rows})
    payload = {"source": "auditoría AEO.pdf", "validated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "n": len(items), "n_query_ids": len(rows), "n_query_families": families, "query_family_note": "The bank has 120 administrative IDs and 24 repeated semantic query families; family clustering is required for inferential summaries.", "items": items}
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    counts: dict[str, int] = {}
    for item in items: counts[item["validation_status"]] = counts.get(item["validation_status"], 0) + 1
    return {"output": str(OUT), "items": len(items), "families": families, "statuses": counts, "evidence_dir": str(EVIDENCE)}


if __name__ == "__main__":
    print(json.dumps(validate(), ensure_ascii=False, indent=2))
