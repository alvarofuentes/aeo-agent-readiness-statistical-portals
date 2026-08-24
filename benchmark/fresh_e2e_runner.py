#!/usr/bin/env python3
"""Fresh portal-directed E2E benchmark for the statistical-portal universe.

This runner intentionally does not read any previous capture, evidence bundle,
gold file, or pilot result.  Each repeat refreshes the official portal
catalogue, performs a model-mediated candidate selection, retrieves current
data, and writes the raw response under the new run directory.

The default pilot contract is 30 query templates x 2 portals x 3 repeats = 180
rows.  ``--portals`` expands the same clean runner to the remaining statistical
portals without reading a prior result or evidence bundle.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import threading
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlencode
from urllib.error import HTTPError
from urllib.request import Request, urlopen

try:
    from benchmark.review_cepalstat_exports import run_review as run_cepalstat_export_review
except ImportError:  # pragma: no cover - direct script fallback
    try:
        from review_cepalstat_exports import run_review as run_cepalstat_export_review
    except ImportError:
        run_cepalstat_export_review = None


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BANK = ROOT / "benchmark" / "query-bank-120.csv"
DEFAULT_MODEL = "qwen3.5:9b-mlx"
DEFAULT_ENDPOINTS = ["http://127.0.0.1:11434", "http://127.0.0.1:11435"]
DEFAULT_PORTALS = ("cepalstat", "worldbank")
PORTALS = DEFAULT_PORTALS
CEPAL_TREE = "https://api-cepalstat.cepal.org/cepalstat/api/v1/thematic-tree?lang=es&format=json"
CEPAL_DATA = "https://api-cepalstat.cepal.org/cepalstat/api/v1/indicator/{indicator}/data"
CEPAL_TECHNICAL = "https://statistics.cepal.org/portal/cepalstat/technical-sheet.html?indicator_id={indicator}&lang=es"
CEPAL_ROOT = "https://statistics.cepal.org/portal/cepalstat/index.html?lang=es"
WB_INDICATORS = "https://api.worldbank.org/v2/indicator?format=json&per_page=30000"
WB_DATA = "https://api.worldbank.org/v2/country/{country}/indicator/{indicator}?date=1960:2026&format=json&per_page=100"
WB_ROOT = "https://data.worldbank.org/"
WHO_ROOT = "https://data.who.int/"
WHO_INDICATORS = "https://ghoapi.azureedge.net/api/Indicator?$filter=contains(IndicatorName,%20%27GDP%27)"
WHO_DATA = "https://ghoapi.azureedge.net/api/{indicator}"
UNDATA_ROOT = "https://unstats.un.org/UNSDWebsite/undatacommons/"
UNDATA_SEARCH = "https://unstats.un.org/UNSDWebsite/undatacommons/search"
UNDATA_SERIES = "https://unstats.un.org/unsd/amaapi/api/Series"
UNDATA_DATA = "https://unstats.un.org/unsd/amaapi/api/Data/limited/{country}/{series}"
SDG_ROOT = "https://unstats.un.org/sdgs/dataportal/"
SDG_DATABASE = "https://unstats.un.org/sdgs/dataportal/database"
SDG_INDICATORS = "https://unstats.un.org/SDGAPI/v1/sdg/Indicator/List"
SDG_DATA = "https://unstats.un.org/SDGAPI/v1/sdg/Series/Data"

COUNTRIES = {
    "argentina": ("Argentina", "ARG"), "bolivia": ("Bolivia", "BOL"),
    "brasil": ("Brazil", "BRA"), "brazil": ("Brazil", "BRA"),
    "chile": ("Chile", "CHL"), "colombia": ("Colombia", "COL"),
    "costa rica": ("Costa Rica", "CRI"), "ecuador": ("Ecuador", "ECU"),
    "mexico": ("Mexico", "MEX"), "méxico": ("Mexico", "MEX"),
    "peru": ("Peru", "PER"), "perú": ("Peru", "PER"),
    "uruguay": ("Uruguay", "URY"),
}
UN_M49 = {
    "ARG": "032", "BOL": "068", "BRA": "076", "CHL": "152", "COL": "170",
    "CRI": "188", "ECU": "218", "MEX": "484", "PER": "604", "URY": "858",
}
CEPAL_COUNTRY_NAMES = {
    "Argentina": "Argentina", "Bolivia": "Bolivia (Estado Plurinacional de)",
    "Brazil": "Brasil", "Chile": "Chile", "Colombia": "Colombia",
    "Costa Rica": "Costa Rica", "Ecuador": "Ecuador", "Mexico": "México",
    "Peru": "Perú", "Uruguay": "Uruguay",
}


class ReviewRequired(RuntimeError):
    """Fail-closed pause raised when the run needs human/agent review."""


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def norm(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", text).strip()


def slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value)[:150]


def http_json(url: str, timeout: float = 45.0) -> dict[str, Any]:
    started = time.perf_counter(); last: dict[str, Any] | None = None
    request = Request(url, headers={"User-Agent": "AEO-Portal-E2E-Fresh/2.0", "Accept": "application/json,text/plain,*/*"})
    for attempt in range(1, 3):
        try:
            with urlopen(request, timeout=timeout) as response:
                raw = response.read(); payload = json.loads(raw.decode("utf-8", errors="replace"))
                return {"url": url, "status": int(response.status), "headers": dict(response.headers.items()),
                        "payload": payload, "attempts": attempt, "elapsed_seconds": round(time.perf_counter() - started, 3), "error": None}
        except HTTPError as exc:
            raw = exc.read() if hasattr(exc, "read") else b""
            last = {"url": url, "status": int(exc.code), "headers": dict(getattr(exc, "headers", {}) or {}), "payload": None,
                    "attempts": attempt, "elapsed_seconds": round(time.perf_counter() - started, 3), "error": f"HTTPError: HTTP Error {exc.code}: {exc.reason}"}
            if int(exc.code) >= 500 and attempt < 2:
                time.sleep(0.5); continue
            return last
        except Exception as exc:
            last = {"url": url, "status": 0, "headers": {}, "payload": None, "attempts": attempt,
                    "elapsed_seconds": round(time.perf_counter() - started, 3), "error": f"{type(exc).__name__}: {exc}"}
            # A transient peer reset is transport noise, not an observation.
            # Retry it once, then preserve NOT_VERIFIED and let the fail-closed
            # gate stop the run if the isolated route still cannot be observed.
            if attempt < 2 and any(token in str(exc).lower() for token in ("timed out", "timeout", "handshake", "temporarily", "connection reset", "reset by peer", "connection aborted", "broken pipe", "eof")):
                time.sleep(0.5); continue
            return last
    return last or {"url": url, "status": 0, "headers": {}, "payload": None, "attempts": 2, "elapsed_seconds": round(time.perf_counter() - started, 3), "error": "request_exhausted"}


def http_text(url: str, timeout: float = 30.0) -> dict[str, Any]:
    started = time.perf_counter()
    request = Request(url, headers={"User-Agent": "AEO-Portal-E2E-Fresh/2.0", "Accept": "text/html,application/xhtml+xml,*/*"})
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read()
            return {"url": url, "status": int(response.status), "headers": dict(response.headers.items()),
                    "text": raw.decode("utf-8", errors="replace"), "bytes": len(raw),
                    "elapsed_seconds": round(time.perf_counter() - started, 3), "error": None}
    except HTTPError as exc:
        raw = exc.read() if hasattr(exc, "read") else b""
        return {"url": url, "status": int(exc.code), "headers": dict(getattr(exc, "headers", {}) or {}),
                "text": raw.decode("utf-8", errors="replace"), "bytes": len(raw),
                "elapsed_seconds": round(time.perf_counter() - started, 3),
                "error": f"HTTPError: HTTP Error {exc.code}: {exc.reason}"}
    except Exception as exc:
        return {"url": url, "status": 0, "headers": {}, "text": "", "bytes": 0,
                "elapsed_seconds": round(time.perf_counter() - started, 3),
                "error": f"{type(exc).__name__}: {exc}"}


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def walk(node: Any):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from walk(value)
    elif isinstance(node, list):
        for value in node:
            yield from walk(value)


def select_templates(bank: Path, limit: int = 30) -> list[dict[str, str]]:
    with bank.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    # The historical pilot had 60 portal-labelled rows.  Half of that contract
    # is 30 templates.  Keep all 24 World Bank strata rows and six live CEPAL
    # rows so the new run preserves the original question families without
    # reading any old result or evidence.
    selected = (rows[:24] + rows[48:54])[:limit]
    if len(selected) != limit:
        raise RuntimeError(f"Expected {limit} fresh templates, got {len(selected)}")
    out = []
    for i, row in enumerate(selected, 1):
        item = dict(row)
        item["fresh_template_id"] = f"FRESH-Q{i:03d}"
        out.append(item)
    return out


def parse_query(query: str) -> dict[str, Any]:
    nq = norm(query)
    countries = []
    for key, value in sorted(COUNTRIES.items(), key=lambda kv: -len(kv[0])):
        if key in nq and value not in countries:
            countries.append(value)
    years = [int(y) for y in re.findall(r"\b(?:19|20)\d{2}\b", query)]
    if not years:
        years = [2024]
    if "per capita" in nq or "habitante" in nq:
        concept = "gdp_per_capita"
    elif "crecimiento" in nq or "crecimiento economico" in nq:
        concept = "gdp_growth"
    elif "constantes" in nq:
        concept = "gdp_constant"
    else:
        concept = "gdp_total"
    subnational_terms = ("subnacional", "sub nacional", "provincia", "municipio", "comuna", "departamento", "estado subnacional")
    requested_scope = "subnational" if any(term in nq for term in subnational_terms) else "country_aggregate"
    verification_question = any(term in nq for term in ("verifica", "verificar", "es anual o trimestral", "usd o usd por habitante", "moneda nacional, usd"))
    if verification_question and ("moneda nacional" in nq or "usd por habitante" in nq):
        # The question asks the agent to verify the unit among alternatives;
        # mentioning "habitante" is not a request for the per-capita series.
        concept = "gdp_total"
    requested_frequency = "unspecified" if verification_question and "trimestral" in nq and "anual" in nq else "quarterly" if any(term in nq for term in ("trimestral", "trimestre")) else "annual" if "anual" in nq else "unspecified"
    requested_unit = "unspecified" if verification_question and ("moneda nacional" in nq or "usd por habitante" in nq) else "percent" if "porcentaje" in nq or "tasa" in nq or "crecimiento" in nq else "per_capita" if "per capita" in nq or "habitante" in nq else "unspecified"
    requested_price_base = "constant" if "constante" in nq else "current" if "corriente" in nq else "unspecified"
    excluded_measures = []
    if concept == "gdp_total" and "por actividad" in nq and ("distingue" in nq or "diferencia" in nq or "total" in nq):
        excluded_measures.append("activity_breakdown")
    return {"countries": countries, "years": sorted(set(years)), "concept": concept,
            "requested_scope": requested_scope, "requested_frequency": requested_frequency,
            "requested_unit": requested_unit, "requested_price_base": requested_price_base,
            "excluded_measures": excluded_measures,
            "dimension_to_verify": "frequency_or_unit" if verification_question else None}


def infer_candidate_metadata(candidate: dict[str, Any], portal: str) -> dict[str, Any]:
    """Derive explicit, inspectable metadata for model disambiguation.

    These fields are diagnostic aids for the selector.  They never overwrite
    the candidate chosen by the model and never trigger a deterministic
    re-selection.
    """
    text = norm(" ".join(str(candidate.get(k, "")) for k in ("name", "sourceNote", "unit")))
    scope = "subnational" if "sub nacional" in text or "subnacional" in text else "country_aggregate"
    frequency = "quarterly" if "trimestral" in text or "quarter" in text else "annual" if "anual" in text or "annual" in text else "unspecified"
    if "per capita" in text or "habitante" in text:
        unit_class = "per_capita"
    elif "porcentaje" in text or "percent" in text or "growth" in text or "crecimiento" in text:
        unit_class = "percent"
    elif "dolar" in text or "dollar" in text or "usd" in text:
        unit_class = "currency_usd"
    elif "moneda nacional" in text or "national currency" in text:
        unit_class = "currency_national"
    else:
        unit_class = "unspecified"
    price_base = "constant" if "constante" in text or "constant" in text else "current" if "corriente" in text or "current" in text else "unspecified"
    country_tokens = set(COUNTRIES.keys()) | set(CEPAL_COUNTRY_NAMES.keys()) | set(CEPAL_COUNTRY_NAMES.values())
    country_scope = "country_specific" if any(norm(name) and norm(name) in text for name in country_tokens) else "all_countries"
    return {"scope": scope, "country_scope": country_scope, "frequency": frequency,
            "unit_class": unit_class, "price_base": price_base,
            "source_catalog": {
                "cepalstat": "CEPALSTAT", "worldbank": "World Bank", "who": "WHO GHO",
                "undata": "UNSD AMA", "sdg": "UN SDG Indicators",
            }.get(portal, portal)}


def semantic_selection_mismatches(candidate: dict[str, Any], decomposition: dict[str, Any]) -> list[str]:
    mismatches = []
    metadata = candidate.get("selection_metadata") or {}
    expected_scope = decomposition.get("requested_scope")
    if expected_scope and expected_scope != "unspecified" and metadata.get("scope") != expected_scope:
        mismatches.append(f"scope_expected:{expected_scope};observed:{metadata.get('scope')}")
    if decomposition.get("requested_frequency") not in (None, "unspecified") and metadata.get("frequency") not in (decomposition.get("requested_frequency"), "unspecified"):
        mismatches.append(f"frequency_expected:{decomposition.get('requested_frequency')};observed:{metadata.get('frequency')}")
    requested_unit = decomposition.get("requested_unit")
    if requested_unit not in (None, "unspecified") and metadata.get("unit_class") not in (requested_unit, "unspecified"):
        mismatches.append(f"unit_expected:{requested_unit};observed:{metadata.get('unit_class')}")
    requested_price = decomposition.get("requested_price_base")
    if requested_price not in (None, "unspecified") and metadata.get("price_base") not in (requested_price, "unspecified"):
        mismatches.append(f"price_base_expected:{requested_price};observed:{metadata.get('price_base')}")
    text = norm(candidate.get("name"))
    if decomposition.get("concept") == "gdp_total" and ("por actividad economica" in text or "by economic activity" in text):
        mismatches.append("measure_expected:gdp_total;observed:activity_breakdown")
    if decomposition.get("concept") == "gdp_total" and any(term in text for term in ("per capita", "per cápita", "percentage", "proportion", "growth", "crecimiento", "rate of")):
        mismatches.append("measure_expected:gdp_total;observed:derived_or_rate_measure")
    if decomposition.get("concept") == "gdp_growth" and not ("growth" in text or "crecimiento" in text or metadata.get("unit_class") == "percent"):
        mismatches.append("measure_expected:gdp_growth;observed:level_or_other")
    if decomposition.get("concept") == "gdp_per_capita" and metadata.get("unit_class") not in ("per_capita", "unspecified"):
        mismatches.append("measure_expected:gdp_per_capita;observed:not_per_capita")
    if "activity_breakdown" in decomposition.get("excluded_measures", []) and ("por actividad economica" in text or "by economic activity" in text):
        mismatches.append("measure_excluded:activity_breakdown")
    return mismatches


def candidate_rank(candidates: list[dict[str, Any]], decomposition: dict[str, Any], portal: str) -> list[dict[str, Any]]:
    concept = decomposition["concept"]
    ranked = []
    for candidate in candidates:
        text = norm(candidate.get("name") or candidate.get("text") or candidate.get("description"))
        score = 0
        if "gdp_growth" == concept and ("growth" in text or "crecimiento" in text): score += 10
        if "gdp_per_capita" == concept and ("per capita" in text or "habitante" in text): score += 10
        if concept == "gdp_constant" and ("constant" in text or "constante" in text): score += 7
        if concept == "gdp_total" and "gdp" in text or "producto interno bruto" in text: score += 3
        if "total" in text: score += 2
        if "current" in text or "corriente" in text: score += 1
        if "dollar" in text or "dolar" in text: score += 1
        # Rank only for candidate presentation.  This score never rewrites the
        # model's selected candidate; a semantic mismatch is evidence about
        # model discrimination and must remain visible in the run.
        if "sub national" in text or "subnacional" in text:
            score -= 25
        if portal == "cepalstat" and concept == "gdp_total" and str(candidate.get("id")) == "2203":
            score += 12
        if portal == "worldbank" and candidate.get("id") in {"NY.GDP.MKTP.CD", "NY.GDP.MKTP.KD.ZG", "NY.GDP.PCAP.CD", "NY.GDP.MKTP.KD"}: score += 4
        ranked.append((score, candidate))
    return [candidate for _, candidate in sorted(ranked, key=lambda pair: (-pair[0], str(pair[1].get("id"))))]


def model_select(prompt: str, model: str, endpoint: str, timeout: float = 120.0) -> dict[str, Any]:
    body = {"model": model, "prompt": prompt, "stream": False,
            "think": False, "options": {"temperature": 0, "num_predict": 220}}
    request = Request(endpoint.rstrip("/") + "/api/generate", data=json.dumps(body).encode(),
                      headers={"Content-Type": "application/json"})
    last_error = "model_selection_failed"
    for attempt in range(1, 3):
        try:
            with urlopen(request, timeout=timeout) as response:
                payload = json.loads(response.read().decode("utf-8", errors="replace"))
            text = str(payload.get("response", "")); match = re.search(r"\{.*\}", text, re.S)
            if not match: raise ValueError("model_response_has_no_json_object")
            parsed = json.loads(match.group(0)); parsed["model_raw"] = text; parsed["model_attempts"] = attempt
            return {"ok": True, "data": parsed}
        except HTTPError as exc:
            last_error = f"HTTPError: HTTP Error {exc.code}: {exc.reason}"
            if int(exc.code) >= 500 and attempt < 2:
                time.sleep(0.5); continue
            break
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            if attempt < 2 and any(token in str(exc).lower() for token in ("timed out", "timeout", "handshake", "temporarily")):
                time.sleep(0.5); continue
            break
    return {"ok": False, "data": {}, "error": last_error, "attempts": 2}


def search_worldbank(catalog: dict[str, Any], decomposition: dict[str, Any]) -> list[dict[str, Any]]:
    payload = catalog.get("payload") or []
    rows = payload[1] if isinstance(payload, list) and len(payload) > 1 else []
    candidates = []
    for item in rows:
        text = " ".join(str(item.get(k, "")) for k in ("id", "name", "sourceNote", "unit"))
        if "gdp" in norm(text) or "gross domestic product" in norm(text):
            candidate = {"id": item.get("id"), "name": item.get("name"), "unit": item.get("unit"),
                         "sourceNote": item.get("sourceNote"), "sourceOrganization": item.get("sourceOrganization")}
            candidate["selection_metadata"] = infer_candidate_metadata(candidate, "worldbank")
            candidates.append(candidate)
    return candidate_rank(candidates, decomposition, "worldbank")[:12]


def search_cepalstat(tree: dict[str, Any], decomposition: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = []
    for item in walk(tree.get("payload")):
        indicator = item.get("indicator_id")
        name = item.get("name")
        if indicator and name and ("pib" in norm(name) or "producto interno bruto" in norm(name)):
            candidate = {"id": str(indicator), "name": name, "indicator_id": indicator}
            candidate["selection_metadata"] = infer_candidate_metadata(candidate, "cepalstat")
            candidates.append(candidate)
    # Deduplicate indicator IDs while preserving the highest-ranked wording.
    unique = {}
    for c in candidate_rank(candidates, decomposition, "cepalstat"):
        unique.setdefault(c["id"], c)
    return list(unique.values())[:12]


def search_who(catalog: dict[str, Any], decomposition: dict[str, Any]) -> list[dict[str, Any]]:
    """Return live WHO/GHO indicators mentioning GDP.

    WHO does not publish a generic national-accounts GDP level in this
    catalogue; GDP-related indicators are retained as near-matches so a
    model's domain/metadata discrimination remains observable rather than
    being silently replaced by another portal's series.
    """
    candidates = []
    for item in (catalog.get("payload") or {}).get("value", []) if isinstance(catalog.get("payload"), dict) else []:
        code = item.get("IndicatorCode")
        name = item.get("IndicatorName")
        if code and name and "gdp" in norm(name):
            candidate = {"id": code, "name": name, "unit": "percent" if any(x in norm(name) for x in ("proportion", "percentage", "%")) else None,
                         "sourceNote": "WHO Global Health Observatory indicator catalogue", "sourceOrganization": "WHO"}
            candidate["selection_metadata"] = infer_candidate_metadata(candidate, "who")
            candidates.append(candidate)
    return candidate_rank(candidates, decomposition, "who")[:12]


def search_undata(catalog: dict[str, Any], decomposition: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = []
    payload = catalog.get("payload") or []
    for item in payload if isinstance(payload, list) else []:
        name = item.get("serieName")
        code = item.get("serieCode")
        if code is not None and name and "gdp" in norm(name):
            candidate = {"id": str(int(code)), "name": name, "unit": item.get("unitMeasureType"),
                         "sourceNote": "UNSD AMA / Data Commons series catalogue", "sourceOrganization": "United Nations Statistics Division"}
            candidate["selection_metadata"] = infer_candidate_metadata(candidate, "undata")
            candidates.append(candidate)
    return candidate_rank(candidates, decomposition, "undata")[:12]


def search_sdg(catalog: dict[str, Any], decomposition: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = []
    payload = catalog.get("payload") or []
    for indicator in payload if isinstance(payload, list) else []:
        for series in indicator.get("series") or []:
            name = series.get("description") or indicator.get("description")
            code = series.get("code")
            if code and name and "gdp" in norm(name):
                candidate = {"id": code, "name": name, "unit": "percent" if any(x in norm(name) for x in ("percentage", "rate", "%")) else None,
                             "sourceNote": indicator.get("description"), "sourceOrganization": "United Nations Statistics Division", "indicator_code": indicator.get("code")}
                candidate["selection_metadata"] = infer_candidate_metadata(candidate, "sdg")
                candidates.append(candidate)
    return candidate_rank(candidates, decomposition, "sdg")[:12]


def choose_candidate(portal: str, query: str, decomposition: dict[str, Any], candidates: list[dict[str, Any]], model: str, endpoint: str) -> dict[str, Any]:
    compact = [{k: c.get(k) for k in ("id", "name", "unit", "sourceNote", "selection_metadata") if c.get(k) is not None} for c in candidates]
    hard_constraints = ""
    if "activity_breakdown" in decomposition.get("excluded_measures", []):
        hard_constraints = "La mención de 'PIB por actividad económica' es un near-match que la consulta pide distinguir y excluir; NO es la medida solicitada. Debes elegir el PIB total agregado, no una tabla por actividad ni subnacional. "
    prompt = ("Eres el selector de una prueba E2E. La consulta del usuario debe resolverse buscando dentro del portal oficial. "
              "Elige únicamente un id de la lista de candidatos, sin inventarlo. Usa explícitamente scope, geography, frequency, unit_class y price_base. "
              "No elijas scope=subnational para una consulta country_aggregate. Devuelve solo JSON con candidate_id, "
              "query_rewrite y reason. Si no hay candidato válido usa candidate_id null. La prueba conserva exactamente tu primera selección: "
              "no la sustituyas por otra serie si detectas una incompatibilidad. " + hard_constraints + "\n"
              f"portal={portal}\nconsulta={query}\ndescomposicion={json.dumps(decomposition, ensure_ascii=False)}\n"
              f"candidatos={json.dumps(compact, ensure_ascii=False)}")
    selected = model_select(prompt, model, endpoint)
    if selected["ok"]:
        data = selected["data"]
        wanted = str(data.get("candidate_id")) if data.get("candidate_id") is not None else None
        match = next((c for c in candidates if str(c.get("id")) == wanted), None)
        if match:
            mismatches = semantic_selection_mismatches(match, decomposition)
            if mismatches:
                error = {"failure_class": "MODEL_SELECTION_ERROR",
                         "selected_candidate": match,
                         "expected": {"scope": decomposition.get("requested_scope"), "frequency": decomposition.get("requested_frequency"), "unit_class": decomposition.get("requested_unit"), "price_base": decomposition.get("requested_price_base"), "concept": decomposition.get("concept")},
                         "mismatches": mismatches,
                         "note": "The model's original candidate is retained and tested; no deterministic re-selection was applied."}
                return {"candidate": match, "model": selected, "selection_mode": "model", "selection_status": "FAIL", "selection_failure_class": "MODEL_SELECTION_ERROR", "selection_error": error, "model_candidate_rejected": None}
            return {"candidate": match, "model": selected, "selection_mode": "model", "selection_status": "PASS", "selection_failure_class": None, "selection_error": None, "model_candidate_rejected": None}
    # A deterministic, evidence-bound fallback keeps a transport/model error
    # visible instead of turning the row into a fabricated answer.
    fallback = candidates[0] if candidates else None
    return {"candidate": fallback, "model": selected, "selection_mode": "ranked_fallback", "selection_status": "FAIL" if fallback else "NOT_VERIFIED", "selection_failure_class": "MODEL_RESPONSE_ERROR" if fallback else "MODEL_NO_CANDIDATE", "selection_error": {"failure_class": "MODEL_RESPONSE_ERROR", "note": "The model did not return a usable candidate; ranked fallback is preserved for diagnosis."} if fallback else None, "model_candidate_rejected": None}


def portal_endpoints(portal: str) -> dict[str, Any]:
    configs = {
        "worldbank": {"root": WB_ROOT, "catalog": WB_INDICATORS, "sample": "https://data.worldbank.org/indicator/NY.GDP.MKTP.CD", "direct": "https://api.worldbank.org/v2/country/CHL/indicator/NY.GDP.MKTP.CD?date=2024:2024&format=json&per_page=100"},
        "cepalstat": {"root": CEPAL_ROOT, "catalog": CEPAL_TREE, "sample": CEPAL_TECHNICAL.format(indicator=2203), "direct": "https://api-cepalstat.cepal.org/cepalstat/api/v1/indicator/2203/data?lang=es&format=json&in=1&path=1&members=224%2C29194"},
        "who": {"root": WHO_ROOT, "catalog": WHO_INDICATORS, "sample": "https://data.who.int/indicators", "direct": WHO_DATA.format(indicator="GHED_GGHE-DGDP_SHA2011") + "?$top=1"},
        "undata": {"root": UNDATA_ROOT, "catalog": UNDATA_SERIES, "sample": UNDATA_SEARCH, "direct": UNDATA_DATA.format(country="152", series="2")},
        "sdg": {"root": SDG_ROOT, "catalog": SDG_INDICATORS, "sample": SDG_DATABASE, "direct": SDG_DATA + "?seriesCode=NY_GDP_PCAP&areaCode=152&timePeriod=2024"},
    }
    if portal not in configs:
        raise ValueError(f"unknown portal: {portal}")
    root = configs[portal]["root"]
    host = root.split("//", 1)[-1].split("/", 1)[0]
    configs[portal]["extra"] = [f"https://{host}/robots.txt", f"https://{host}/sitemap.xml", f"https://{host}/llms.txt"]
    return configs[portal]


def technical_probe(portal: str, run_dir: Path, repeat: int, catalog_response: dict[str, Any], rendered_evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = portal_endpoints(portal)
    root_url, api_url, sample, extra = cfg["root"], cfg["catalog"], cfg["sample"], cfg["extra"]
    root = http_text(root_url)
    sample_page = http_text(sample)
    extras = {url: http_text(url) for url in extra}
    root_text = root.get("text", "")
    initial_jsonld = len(re.findall(r"<script[^>]+application/ld\+json", root_text, flags=re.I))
    unresolved = []
    rendered_items = (rendered_evidence or {}).get(portal, [])
    rendered = next((item for item in rendered_items if int(item.get("repeat", 0)) == repeat), None)
    if rendered:
        write_json(run_dir / "evidence" / "rendered" / f"{portal}__repeat-{repeat}.json", rendered)
        rendered_status = "PASS" if rendered.get("readyState") == "complete" and rendered.get("htmlChars", 0) > 0 else "NOT_VERIFIED"
        rendered_jsonld_status = "PASS" if rendered_status == "PASS" and rendered.get("jsonld", 0) > 0 else "ABSENT" if rendered_status == "PASS" else "NOT_VERIFIED"
    else:
        rendered_status = "NOT_VERIFIED"
        rendered_jsonld_status = "NOT_VERIFIED"
        unresolved.append({
            "check_id": "jsonld_rendered_dom",
            "status": "NOT_VERIFIED",
            "evidence_state": "rendered_dom_not_captured",
            "observed_evidence": "No live settled DOM probe was supplied for this portal/repeat.",
            "verification_gap": "The DOM after JavaScript hydration was not captured.",
            "next_verification_action": "Open the same representative page in an instrumented browser and save the settled DOM before classifying JSON-LD/microdata as absent."
        })

    direct_url = cfg["direct"]
    direct = http_json(direct_url, timeout=120)
    direct_raw = run_dir / "evidence" / "raw" / f"technical__{portal}__repeat-{repeat}__direct.json"
    write_json(direct_raw, direct)
    payload = direct.get("payload")
    if portal == "worldbank":
        direct_records = payload[1] if isinstance(payload, list) and len(payload) > 1 and isinstance(payload[1], list) else []
    elif portal == "cepalstat":
        body = payload.get("body") if isinstance(payload, dict) else None
        direct_records = body if isinstance(body, (list, dict)) else payload
    elif portal == "who":
        direct_records = payload.get("value", []) if isinstance(payload, dict) else []
    elif portal == "sdg":
        direct_records = payload.get("data", []) if isinstance(payload, dict) else []
    else:
        direct_records = payload if isinstance(payload, list) else []
    direct_ok = direct.get("status") == 200 and bool(direct_records)
    if not direct_ok:
        unresolved.append({
            "check_id": "api_direct_representative_record",
            "status": "NOT_VERIFIED",
            "evidence_state": "isolated_request_failed_or_empty",
            "observed_evidence": f"The isolated live request returned HTTP {direct.get('status')} with {len(json.dumps(payload, ensure_ascii=False)) if payload is not None else 0} payload characters.",
            "verification_gap": "The representative indicator/record did not yield a validated record.",
            "next_verification_action": "Inspect the isolated request, dimensions and provenance; resolve before relaunching the evaluation."
        })
    probe = {
        "portal_id": portal, "repeat": repeat, "captured_at": now_iso(), "catalog_url": api_url,
        "catalog_status": catalog_response.get("status"),
        "root": {k: root.get(k) for k in ("url", "status", "bytes", "elapsed_seconds", "error")},
        "sample_page": {k: sample_page.get(k) for k in ("url", "status", "bytes", "elapsed_seconds", "error")},
        "well_known": {url: {k: value.get(k) for k in ("status", "bytes", "elapsed_seconds", "error")} for url, value in extras.items()},
        "json_ld_count": initial_jsonld,
        "jsonld_initial_status": "PASS" if initial_jsonld else "ABSENT",
        "jsonld_rendered_status": rendered_jsonld_status,
        "structured_markup_scope": "embedded_html_initial_and_rendered",
        "api_route_declared": api_url,
        "api_direct_http_status": direct.get("status"),
        "api_direct_verified": "PASS" if direct_ok else "NOT_VERIFIED",
        "api_direct_url": direct_url,
        "api_direct_raw_path": str(direct_raw.relative_to(run_dir)),
        "unverified_checks": unresolved,
        "dimensions": {
            "discovery": "PASS" if catalog_response.get("status") == 200 else "NOT_VERIFIED",
            "retrieval": "PENDING_E2E",
            "rendering": "PASS" if root.get("status") == 200 and root.get("bytes", 0) > 500 else "NOT_VERIFIED",
            "structured_data": "PASS" if initial_jsonld else rendered_jsonld_status,
            "authority_citation": "PASS" if sample_page.get("status") == 200 else "NOT_VERIFIED",
            "accessibility": "PASS" if any(v.get("status") == 200 for v in extras.values()) else "ABSENT" if extras and all(v.get("status") in (404, 410) for v in extras.values()) else "NOT_VERIFIED",
        },
    }
    write_json(run_dir / "evidence" / "technical" / f"{portal}__repeat-{repeat}.json", probe)
    return probe


def cepal_dimension_maps(full_payload: dict[str, Any]) -> tuple[dict[str, int], dict[str, int]]:
    body = (full_payload.get("payload") or {}).get("body", {})
    country, year = {}, {}
    for dim in body.get("dimensions") or []:
        name = norm(dim.get("name"))
        target = country if "pais" in name else year if "ano" in name or "year" in name else None
        if target is not None:
            for member in dim.get("members") or []:
                target[norm(member.get("name"))] = int(member["id"])
    return country, year


def retrieve_worldbank(candidate: dict[str, Any], decomposition: dict[str, Any], run_dir: Path, exec_id: str) -> dict[str, Any]:
    indicator = candidate.get("id")
    countries = decomposition["countries"] or [("Chile", "CHL")]
    calls, rows = [], []
    for _, code in countries:
        response = http_json(WB_DATA.format(country=code, indicator=quote(str(indicator))))
        raw_path = run_dir / "evidence" / "raw" / f"{exec_id}__worldbank__{code}.json"
        write_json(raw_path, response)
        calls.append({"url": response.get("url"), "status": response.get("status"), "raw_path": str(raw_path.relative_to(run_dir)), "elapsed_seconds": response.get("elapsed_seconds"), "error": response.get("error")})
        payload = response.get("payload") or []
        data = payload[1] if isinstance(payload, list) and len(payload) > 1 else []
        wanted = set(str(y) for y in decomposition["years"])
        rows.extend([r for r in data if str(r.get("date")) in wanted])
    values = [{"country": r.get("country", {}).get("value"), "country_code": r.get("countryiso3code"), "date": r.get("date"), "value": r.get("value"), "unit": candidate.get("unit"), "indicator": indicator} for r in rows]
    ok = bool(values) and all(c["status"] == 200 for c in calls)
    return {"status": "PASS" if ok else "FAIL" if all(c["status"] == 200 for c in calls) else "NOT_VERIFIED",
            "value_found": bool(values), "values": values, "rows_returned": len(rows), "calls": calls,
            "metadata": {"indicator_name": candidate.get("name"), "unit": candidate.get("unit"), "definition": candidate.get("sourceNote"), "source": candidate.get("sourceOrganization")},
            "citation_url": calls[0]["url"] if calls else None}


def retrieve_cepal(candidate: dict[str, Any], decomposition: dict[str, Any], run_dir: Path, exec_id: str, dimension_cache: dict[str, tuple[dict[str, int], dict[str, int]]]) -> dict[str, Any]:
    indicator = str(candidate.get("id"))
    if indicator not in dimension_cache:
        full_url = CEPAL_DATA.format(indicator=indicator) + "?lang=es&format=json&in=1&path=1"
        full = http_json(full_url, timeout=60)
        write_json(run_dir / "evidence" / "raw" / f"catalog__cepalstat__indicator-{indicator}.json", full)
        dimension_cache[indicator] = cepal_dimension_maps(full)
        dimension_cache[indicator + "__meta"] = full  # type: ignore[assignment]
    countries_map, years_map = dimension_cache[indicator]
    full_meta = dimension_cache.get(indicator + "__meta", {})
    body = (full_meta.get("payload") or {}).get("body", {}) if isinstance(full_meta, dict) else {}
    metadata = body.get("metadata") or {}
    sources = body.get("sources") or []
    countries = decomposition["countries"] or [("Chile", "CHL")]
    calls, values = [], []
    for country, code in countries:
        cepal_name = CEPAL_COUNTRY_NAMES.get(country, country)
        cid = countries_map.get(norm(cepal_name)) or countries_map.get(norm(country))
        if not cid:
            calls.append({"status": 0, "error": f"country_not_in_live_dimensions:{country}"})
            continue
        for year in decomposition["years"]:
            yid = years_map.get(str(year))
            if not yid:
                calls.append({"status": 0, "error": f"year_not_in_live_dimensions:{year}"})
                continue
            url = CEPAL_DATA.format(indicator=indicator) + "?" + urlencode({"lang": "es", "format": "json", "in": 1, "path": 1, "members": f"{cid},{yid}"})
            response = http_json(url, timeout=60)
            raw_path = run_dir / "evidence" / "raw" / f"{exec_id}__cepalstat__{code}__{year}.json"
            write_json(raw_path, response)
            calls.append({"url": response.get("url"), "status": response.get("status"), "raw_path": str(raw_path.relative_to(run_dir)), "elapsed_seconds": response.get("elapsed_seconds"), "error": response.get("error")})
            rbody = (response.get("payload") or {}).get("body", {}) if isinstance(response.get("payload"), dict) else {}
            for row in rbody.get("data") or []:
                if row.get("iso3") == code or not code:
                    values.append({"country": country, "country_code": code, "date": year, "value": row.get("value"), "unit": metadata.get("unit"), "indicator": indicator})
    ok = bool(values) and all(c.get("status") == 200 for c in calls)
    missing = [k for k in ("indicator_name", "unit", "definition", "calculation_methodology", "last_update") if not metadata.get(k)]
    if not sources: missing.append("source")
    return {"status": "PASS" if ok else "FAIL" if calls and all(c.get("status") == 200 for c in calls) else "NOT_VERIFIED",
            "value_found": bool(values), "values": values, "rows_returned": len(values), "calls": calls,
            "metadata": {"indicator_name": metadata.get("indicator_name"), "unit": metadata.get("unit"), "definition": metadata.get("definition"), "methodology": metadata.get("calculation_methodology"), "last_update": metadata.get("last_update"), "source": sources[0] if sources else None, "missing": missing},
            "citation_url": CEPAL_DATA.format(indicator=indicator)}


def retrieve_who(candidate: dict[str, Any], decomposition: dict[str, Any], run_dir: Path, exec_id: str) -> dict[str, Any]:
    indicator = str(candidate.get("id")); countries = decomposition["countries"] or [("Chile", "CHL")]
    calls, values = [], []
    for country, code in countries:
        url = WHO_DATA.format(indicator=quote(indicator)) + "?" + urlencode({"$filter": f"SpatialDim eq '{code}'", "$top": "1000"})
        response = http_json(url, timeout=90)
        raw_path = run_dir / "evidence" / "raw" / f"{exec_id}__who__{code}.json"; write_json(raw_path, response)
        calls.append({"url": response.get("url"), "status": response.get("status"), "raw_path": str(raw_path.relative_to(run_dir)), "elapsed_seconds": response.get("elapsed_seconds"), "error": response.get("error")})
        payload = response.get("payload") or {}; data = payload.get("value", []) if isinstance(payload, dict) else []
        wanted = set(decomposition["years"]); selected = [r for r in data if int(r.get("TimeDim", 0) or 0) in wanted]
        if not selected and data:
            selected = data[-3:]
        for row in selected:
            values.append({"country": country, "country_code": code, "date": row.get("TimeDim"), "value": row.get("NumericValue", row.get("Value")), "unit": candidate.get("unit"), "indicator": indicator, "period_match": int(row.get("TimeDim", 0) or 0) in wanted})
    ok = bool(values) and all(c["status"] == 200 for c in calls)
    return {"status": "PASS" if ok else "FAIL" if calls and all(c["status"] == 200 for c in calls) else "NOT_VERIFIED", "value_found": bool(values), "values": values, "rows_returned": len(values), "calls": calls, "metadata": {"indicator_name": candidate.get("name"), "unit": candidate.get("unit"), "definition": candidate.get("sourceNote"), "source": "WHO Global Health Observatory", "missing": []}, "citation_url": WHO_DATA.format(indicator=quote(indicator))}


def retrieve_undata(candidate: dict[str, Any], decomposition: dict[str, Any], run_dir: Path, exec_id: str) -> dict[str, Any]:
    series = str(candidate.get("id")); countries = decomposition["countries"] or [("Chile", "CHL")]
    calls, values = [], []
    for country, code in countries:
        m49 = UN_M49.get(code)
        url = UNDATA_DATA.format(country=m49 or code, series=quote(series))
        response = http_json(url, timeout=90)
        raw_path = run_dir / "evidence" / "raw" / f"{exec_id}__undata__{code}.json"; write_json(raw_path, response)
        calls.append({"url": response.get("url"), "status": response.get("status"), "raw_path": str(raw_path.relative_to(run_dir)), "elapsed_seconds": response.get("elapsed_seconds"), "error": response.get("error")})
        data = response.get("payload") or []; data = data if isinstance(data, list) else []
        wanted = set(decomposition["years"]); selected = [r for r in data if int(r.get("fiscalYear", 0) or 0) in wanted]
        if not selected and data: selected = data[-3:]
        for row in selected:
            values.append({"country": row.get("countryName", country), "country_code": code, "date": row.get("fiscalYear"), "value": row.get("observationValue"), "unit": row.get("unit") or candidate.get("unit"), "indicator": series, "period_match": int(row.get("fiscalYear", 0) or 0) in wanted})
    ok = bool(values) and all(c["status"] == 200 for c in calls)
    return {"status": "PASS" if ok else "FAIL" if calls and all(c["status"] == 200 for c in calls) else "NOT_VERIFIED", "value_found": bool(values), "values": values, "rows_returned": len(values), "calls": calls, "metadata": {"indicator_name": candidate.get("name"), "unit": candidate.get("unit"), "definition": candidate.get("sourceNote"), "source": "United Nations Statistics Division AMA", "missing": []}, "citation_url": UNDATA_DATA.format(country="{M49}", series=quote(series))}


def retrieve_sdg(candidate: dict[str, Any], decomposition: dict[str, Any], run_dir: Path, exec_id: str) -> dict[str, Any]:
    series = str(candidate.get("id")); countries = decomposition["countries"] or [("Chile", "CHL")]
    calls, values = [], []
    for country, code in countries:
        m49 = UN_M49.get(code) or code
        url = SDG_DATA + "?" + urlencode({"seriesCode": series, "areaCode": m49})
        response = http_json(url, timeout=120)
        raw_path = run_dir / "evidence" / "raw" / f"{exec_id}__sdg__{code}.json"; write_json(raw_path, response)
        calls.append({"url": response.get("url"), "status": response.get("status"), "raw_path": str(raw_path.relative_to(run_dir)), "elapsed_seconds": response.get("elapsed_seconds"), "error": response.get("error")})
        payload = response.get("payload") or {}; data = payload.get("data", []) if isinstance(payload, dict) else []
        wanted = set(decomposition["years"]); selected = [r for r in data if int(float(r.get("timePeriodStart", 0) or 0)) in wanted]
        if not selected and data: selected = data[-3:]
        for row in selected:
            year = int(float(row.get("timePeriodStart", 0) or 0))
            values.append({"country": row.get("geoAreaName", country), "country_code": code, "date": year, "value": row.get("value"), "unit": (row.get("attributes") or {}).get("Units") or candidate.get("unit"), "indicator": series, "period_match": year in wanted, "source": row.get("source")})
    ok = bool(values) and all(c["status"] == 200 for c in calls)
    return {"status": "PASS" if ok else "FAIL" if calls and all(c["status"] == 200 for c in calls) else "NOT_VERIFIED", "value_found": bool(values), "values": values, "rows_returned": len(values), "calls": calls, "metadata": {"indicator_name": candidate.get("name"), "unit": candidate.get("unit"), "definition": candidate.get("sourceNote"), "source": "United Nations Statistics Division SDG API", "missing": []}, "citation_url": SDG_DATA + "?seriesCode=" + quote(series)}


def execute_one(template: dict[str, str], portal: str, repeat: int, catalog: dict[str, Any], run_dir: Path, model: str, endpoint: str, dimension_cache: dict[str, tuple[dict[str, int], dict[str, int]]]) -> dict[str, Any]:
    started = time.perf_counter()
    exec_id = f"{template['fresh_template_id']}__{portal}__r{repeat}"
    query = template["query"]
    decomposition = parse_query(query)
    searchers = {"worldbank": search_worldbank, "cepalstat": search_cepalstat, "who": search_who, "undata": search_undata, "sdg": search_sdg}
    candidates = searchers[portal](catalog, decomposition)
    selection = choose_candidate(portal, query, decomposition, candidates, model, endpoint)
    write_json(run_dir / "evidence" / "models" / f"{exec_id}.json", {"query": query, "portal": portal, "repeat": repeat, "endpoint": endpoint, "selection": selection.get("model"), "selection_mode": selection.get("selection_mode"), "selection_status": selection.get("selection_status"), "selection_failure_class": selection.get("selection_failure_class"), "selection_error": selection.get("selection_error"), "model_candidate_rejected": selection.get("model_candidate_rejected"), "candidate_count": len(candidates), "candidates": candidates})
    candidate = selection.get("candidate")
    if not candidate:
        retrieval = {"status": "FAIL", "value_found": False, "values": [], "rows_returned": 0, "calls": [], "metadata": {}, "citation_url": None}
    elif portal == "worldbank":
        retrieval = retrieve_worldbank(candidate, decomposition, run_dir, exec_id)
    elif portal == "cepalstat":
        retrieval = retrieve_cepal(candidate, decomposition, run_dir, exec_id, dimension_cache)
    elif portal == "who":
        retrieval = retrieve_who(candidate, decomposition, run_dir, exec_id)
    elif portal == "undata":
        retrieval = retrieve_undata(candidate, decomposition, run_dir, exec_id)
    else:
        retrieval = retrieve_sdg(candidate, decomposition, run_dir, exec_id)
    retrieval_status = retrieval.get("status")
    selection_status = selection.get("selection_status", "NOT_VERIFIED")
    e2e_status = "PASS" if selection_status == "PASS" and retrieval_status == "PASS" else "FAIL" if selection_status == "FAIL" or retrieval_status == "FAIL" else "NOT_VERIFIED"
    row = {"execution_id": exec_id, "fresh_template_id": template["fresh_template_id"], "source_template_id": template.get("query_id"), "portal_id": portal, "repeat": repeat, "stratum": template.get("stratum"), "query": query, "decomposition": decomposition, "candidate": candidate, "candidate_count": len(candidates), "near_matches": candidates[1:6], "selection_mode": selection.get("selection_mode"), "selection_status": selection_status, "selection_failure_class": selection.get("selection_failure_class"), "selection_error": selection.get("selection_error"), "model_candidate_rejected": selection.get("model_candidate_rejected"), "e2e_status": e2e_status, "model": model, "model_endpoint": endpoint, "model_ok": bool(selection.get("model", {}).get("ok")), "retrieval_status": retrieval_status, "value_found": retrieval.get("value_found"), "values": retrieval.get("values"), "rows_returned": retrieval.get("rows_returned"), "metadata": retrieval.get("metadata"), "citation_url": retrieval.get("citation_url"), "calls": retrieval.get("calls"), "elapsed_seconds": round(time.perf_counter() - started, 3), "evidence_policy": "live_portal_fetch_per_repeat_no_cache"}
    return row


def finalize_technical_probes(run_dir: Path) -> list[dict[str, Any]]:
    """Close technical retrieval only from completed live E2E rows."""
    results_path = run_dir / "results.jsonl"
    rows = [json.loads(line) for line in results_path.read_text(encoding="utf-8").splitlines() if line.strip()] if results_path.exists() else []
    by_portal = {portal: [row for row in rows if row.get("portal_id") == portal] for portal in PORTALS}
    unresolved = []
    for path in sorted((run_dir / "evidence" / "technical").glob("*.json")):
        probe = json.loads(path.read_text(encoding="utf-8"))
        portal = probe.get("portal_id")
        portal_rows = by_portal.get(portal, [])
        direct_rows = [
            row for row in portal_rows
            if row.get("retrieval_status") == "PASS"
            and row.get("rows_returned", 0) > 0
            and any(call.get("status") == 200 for call in row.get("calls", []))
        ]
        probe.setdefault("dimensions", {})["retrieval"] = "PASS" if direct_rows else "NOT_VERIFIED"
        probe["e2e_representative_execution_id"] = direct_rows[0].get("execution_id") if direct_rows else None
        probe["e2e_representative_raw_paths"] = [call.get("raw_path") for call in (direct_rows[0].get("calls", []) if direct_rows else [])]
        probe["e2e_representative_verified"] = bool(direct_rows)
        if not direct_rows:
            probe.setdefault("unverified_checks", []).append({
                "check_id": "e2e_representative_retrieval",
                "status": "NOT_VERIFIED",
                "evidence_state": "no_completed_direct_record",
                "observed_evidence": "No completed live E2E row had a non-empty 200 direct indicator response.",
                "verification_gap": "The representative retrieval could not be closed.",
                "next_verification_action": "Inspect the portal route and model-selected dimensions, then relaunch from a clean run."
            })
        remaining = [check for check in probe.get("unverified_checks", []) if check.get("status") == "NOT_VERIFIED"]
        if remaining or any(value == "NOT_VERIFIED" for value in probe.get("dimensions", {}).values()):
            unresolved.extend({"portal_id": portal, **item} for item in remaining)
        write_json(path, probe)
    return unresolved


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bank", type=Path, default=DEFAULT_BANK)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--endpoints", default=",".join(DEFAULT_ENDPOINTS))
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--templates", type=int, default=30)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--rendered-evidence", type=Path, help="Fresh in-app-browser settled-DOM probe JSON, one entry per portal/repeat")
    parser.add_argument("--portals", default=",".join(DEFAULT_PORTALS), help="Comma-separated portal ids: worldbank,cepalstat,who,undata,sdg")
    args = parser.parse_args()
    global PORTALS
    PORTALS = tuple(p.strip() for p in args.portals.split(",") if p.strip())
    invalid = [p for p in PORTALS if p not in {"worldbank", "cepalstat", "who", "undata", "sdg"}]
    if invalid or not PORTALS:
        raise SystemExit(f"unknown or empty --portals: {invalid or args.portals}")
    endpoints = [e.strip().rstrip("/") for e in args.endpoints.split(",") if e.strip()]
    if args.templates < 1 or args.templates > 30:
        raise SystemExit("--templates must be between 1 and 30")
    templates = select_templates(args.bank, args.templates)
    rendered_evidence = {}
    if args.rendered_evidence:
        rendered_evidence = json.loads(args.rendered_evidence.read_text(encoding="utf-8"))
    run_dir = args.run_dir or (ROOT / "benchmark" / "results" / "fresh" / f"e2e_{'-'.join(PORTALS)}-{args.templates}x{len(PORTALS)}x{args.repeats}-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
    run_dir.mkdir(parents=True, exist_ok=False)
    manifest = {"run_id": run_dir.name, "created_at": now_iso(), "status": "RUNNING", "portals": list(PORTALS), "template_count": len(templates), "repeat_count": args.repeats, "expected_executions": len(templates) * len(PORTALS) * args.repeats, "completed_executions": 0, "evidence_policy": "live_portal_fetch_per_repeat_no_cache", "model": args.model, "model_endpoints": endpoints, "source_bank": str(args.bank.relative_to(ROOT)), "editorial_status": "pending", "selection_policy": "preserve_model_selection_and_continue; classify semantic mismatch as MODEL_SELECTION_ERROR", "diagnostic_classes": ["MODEL_SELECTION_ERROR"], "stop_conditions": ["any_e2e_retrieval_status_not_verified", "zero_observations_after_two_attempts"], "stop_action": "write_review_alert_pause_and_relaunch_from_clean_run"}
    write_json(run_dir / "run_manifest.json", manifest)
    with (run_dir / "query_bank_used.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(templates[0]))
        writer.writeheader(); writer.writerows(templates)
    write_json(run_dir / "config.json", {"model": args.model, "endpoints": endpoints, "workers": args.workers, "repeats": args.repeats, "templates": len(templates), "portals": list(PORTALS), "expected_rows": manifest["expected_executions"]})
    results_path = run_dir / "results.jsonl"
    lock = threading.Lock()
    completed = 0
    attempt_history: dict[tuple[str, str], list[dict[str, Any]]] = {}
    dimension_cache_by_repeat = {(portal, repeat): {} for portal in PORTALS for repeat in range(1, args.repeats + 1)}
    try:
        for repeat in range(1, args.repeats + 1):
            pass_catalogs = {}
            for portal in PORTALS:
                response = http_json(portal_endpoints(portal)["catalog"], timeout=120)
                pass_catalogs[portal] = response
                write_json(run_dir / "evidence" / "catalog" / f"{portal}__repeat-{repeat}.json", response)
                probe = technical_probe(portal, run_dir, repeat, response, rendered_evidence)
                technical_gaps = list(probe.get("unverified_checks", []))
                technical_gaps.extend({"check_id": dimension, "status": value} for dimension, value in probe.get("dimensions", {}).items() if value == "NOT_VERIFIED")
                if technical_gaps:
                    alert = {
                        "alert_type": "technical_not_verified",
                        "portal_id": portal,
                        "repeat": repeat,
                        "message": "A technical probe is NOT_VERIFIED; stop, inspect the live evidence, resolve it, and relaunch from a clean run.",
                        "created_at": now_iso(),
                        "checks": technical_gaps,
                    }
                    write_json(run_dir / "review_alert.json", alert)
                    manifest["status"] = "PAUSED_FOR_REVIEW"
                    manifest["pause_reason"] = "technical_not_verified"
                    manifest["review_alert"] = "review_alert.json"
                    write_json(run_dir / "run_manifest.json", manifest)
                    raise ReviewRequired(alert["message"])
            tasks = []
            with ThreadPoolExecutor(max_workers=args.workers) as pool:
                for index, template in enumerate(templates):
                    for portal_index, portal in enumerate(PORTALS):
                        # Keep the two portal calls for one template on
                        # different Ollama endpoints whenever two endpoints
                        # are configured.  This avoids serializing the pair
                        # on one local model server while preserving the
                        # endpoint in row-level evidence.
                        endpoint = endpoints[(index * len(PORTALS) + portal_index) % len(endpoints)]
                        tasks.append(pool.submit(execute_one, template, portal, repeat, pass_catalogs[portal], run_dir, args.model, endpoint, dimension_cache_by_repeat[(portal, repeat)]))
                for future in as_completed(tasks):
                    row = future.result()
                    with lock:
                        with results_path.open("a", encoding="utf-8") as handle:
                            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
                        completed += 1
                        manifest["completed_executions"] = completed
                        manifest["last_update"] = now_iso()
                        manifest["last_execution_id"] = row["execution_id"]
                        write_json(run_dir / "run_manifest.json", manifest)
                    key = (row["fresh_template_id"], row["portal_id"])
                    history = attempt_history.setdefault(key, [])
                    history.append(row)
                    # A model semantic mismatch is an outcome, not a transport
                    # interruption.  Preserve the selected candidate, retrieve
                    # it, and continue so the run measures the visibility cost
                    # of bad metadata discrimination instead of hiding it.
                    # A query that produces no observation in two consecutive
                    # attempts is a diagnostic signal, not a score. Pause the
                    # run so the adapter/model/portal route can be reviewed
                    # and the run can be relaunched from a clean directory.
                    # A semantic model-selection error may make the selected
                    # series unable to answer the requested geography.  That
                    # is still valuable evidence and must not be reclassified
                    # as a portal/transport NOT_VERIFIED stop.  Preserve the
                    # raw retrieval status in the row and continue.  A clean
                    # selection that remains NOT_VERIFIED still pauses.
                    if row.get("retrieval_status") == "NOT_VERIFIED" and row.get("selection_failure_class") != "MODEL_SELECTION_ERROR":
                        alert = {
                            "alert_type": "not_verified_query",
                            "execution_id": row["execution_id"],
                            "message": "A query remained NOT_VERIFIED; stop, inspect the live request/model route, resolve it, and relaunch.",
                            "created_at": now_iso(),
                            "row": row,
                        }
                        write_json(run_dir / "review_alert.json", alert)
                        manifest["status"] = "PAUSED_FOR_REVIEW"
                        manifest["pause_reason"] = "not_verified_query"
                        manifest["review_alert"] = "review_alert.json"
                        write_json(run_dir / "run_manifest.json", manifest)
                        raise ReviewRequired(alert["message"])
                    if len(history) >= 2 and not any(bool(item.get("value_found")) for item in history):
                        alert = {
                            "alert_type": "zero_observations_after_attempts",
                            "execution_id": row["execution_id"],
                            "attempts": len(history),
                            "message": "Zero observations after two attempts; stop, inspect the route/selection/dimensions, resolve it, and relaunch.",
                            "created_at": now_iso(),
                            "attempt_rows": history,
                        }
                        write_json(run_dir / "review_alert.json", alert)
                        manifest["status"] = "PAUSED_FOR_REVIEW"
                        manifest["pause_reason"] = "zero_observations_after_attempts"
                        manifest["review_alert"] = "review_alert.json"
                        write_json(run_dir / "run_manifest.json", manifest)
                        raise ReviewRequired(alert["message"])
    except ReviewRequired:
        # The alert and paused manifest are already durable.  Returning a
        # distinct code lets an orchestration layer review and relaunch rather
        # than silently continuing a compromised run.
        return 3
    except KeyboardInterrupt:
        manifest["status"] = "INTERRUPTED"
        manifest["completed_executions"] = completed
        manifest["last_update"] = now_iso()
        write_json(run_dir / "run_manifest.json", manifest)
        raise
    unresolved_technical = finalize_technical_probes(run_dir)
    if unresolved_technical:
        alert = {
            "alert_type": "technical_not_verified",
            "message": "A technical probe remains NOT_VERIFIED after the live E2E pass; stop, resolve it, and relaunch from a clean run.",
            "created_at": now_iso(),
            "checks": unresolved_technical,
        }
        write_json(run_dir / "review_alert.json", alert)
        manifest["status"] = "PAUSED_FOR_REVIEW"
        manifest["completed_executions"] = completed
        manifest["pause_reason"] = "technical_not_verified"
        manifest["review_alert"] = "review_alert.json"
        manifest["last_update"] = now_iso()
        write_json(run_dir / "run_manifest.json", manifest)
        return 3
    if "cepalstat" in PORTALS and run_cepalstat_export_review is not None:
        try:
            export_review = run_cepalstat_export_review(run_dir)
        except Exception as exc:
            export_review = {"status": "NOT_VERIFIED", "error": f"{type(exc).__name__}: {exc}"}
        if export_review.get("status") != "PASS":
            alert = {
                "alert_type": "data_export_not_verified",
                "portal_id": "cepalstat",
                "message": "The advertised CEPALSTAT machine-readable export did not close; inspect the artifact and relaunch from a clean run.",
                "created_at": now_iso(),
                "review": export_review,
            }
            write_json(run_dir / "review_alert.json", alert)
            manifest["status"] = "PAUSED_FOR_REVIEW"
            manifest["completed_executions"] = completed
            manifest["pause_reason"] = "data_export_not_verified"
            manifest["review_alert"] = "review_alert.json"
            manifest["last_update"] = now_iso()
            write_json(run_dir / "run_manifest.json", manifest)
            return 3
    manifest["completed_executions"] = completed
    manifest["status"] = "COMPLETE" if completed == manifest["expected_executions"] else "INCOMPLETE"
    manifest["completed_at"] = now_iso()
    manifest["editorial_status"] = "pending"
    write_json(run_dir / "run_manifest.json", manifest)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0 if manifest["status"] == "COMPLETE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
