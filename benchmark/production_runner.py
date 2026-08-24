"""Single production runner for the AEO/agent-visibility experiment.

The runner is deliberately fail-closed.  It materialises the 120-row canonical
template bank against the five portals (600 query/portal pairs), executes three
repeated measurements for each pair in five portal passes (1,800 rows), and
keeps the following layers separate:

* frozen HTTP evidence and raw response files;
* free-form model responses;
* JSON responses and schema validation;
* deterministic semantic/URL checks;
* judge dimensions and a recomputed overall score;
* adversarial review and transport/NA states.

No historical ``benchmark/results`` files are overwritten.  A run gets its own
directory under ``benchmark/results/production`` and can be resumed from its
checkpoint.  The default invocation is a read-only preflight; model execution
requires the explicit ``--execute`` flag.
"""
from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import math
import os
import re
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote_plus, urlparse
from urllib.request import Request, urlopen
from concurrent.futures import ThreadPoolExecutor, as_completed

import yaml

try:
    from .model_policy import allowed_models, assert_allowed_model, parameter_size_b
except ImportError:  # direct invocation: python benchmark/production_runner.py
    from model_policy import allowed_models, assert_allowed_model, parameter_size_b


ROOT = Path(__file__).resolve().parents[1]
CFG_PATH = ROOT / "benchmark" / "config.yaml"
BANK_PATH = ROOT / "benchmark" / "query-bank-120.csv"
MATRIX_PATH = ROOT / "execution" / "expanded-audit-matrix-2026-08-22.csv"
# Production consumes the conservative, versioned snapshot produced by
# ``benchmark/finalize_gold.py``.  The pending contract and broad exploratory
# candidate remain audit inputs only.
GOLD_PATH = ROOT / "benchmark" / "gold_standards_final_2026-08-23.json"
PRODUCTION_ROOT = ROOT / "benchmark" / "results" / "production"
EVIDENCE_WRITE_LOCK = threading.Lock()

PORTALS: dict[str, dict[str, Any]] = {
    "worldbank": {"name": "World Bank Open Data", "home": "https://data.worldbank.org/", "roots": {"worldbank.org"}},
    "who": {"name": "WHO Data", "home": "https://data.who.int/", "roots": {"who.int", "azureedge.net"}},
    "cepalstat": {"name": "CEPALSTAT", "home": "https://statistics.cepal.org/portal/cepalstat/", "roots": {"cepal.org"}},
    "undata": {"name": "UN Data Commons", "home": "https://unstats.un.org/UNSDWebsite/undatacommons/", "roots": {"unstats.un.org"}},
    "sdg": {"name": "UN SDG Indicators", "home": "https://unstats.un.org/sdgs/dataportal/", "roots": {"unstats.un.org"}},
}
PORTAL_ORDER = list(PORTALS)
STRATA_TARGETS = {
    "discovery": 20,
    "exact_indicator": 20,
    "semantic_disambiguation": 25,
    "dimensions": 15,
    "comparison": 15,
    "temporal": 10,
    "metadata": 10,
    "citation": 5,
}
EXPECTED_COLUMNS = ["query_id", "portal_id", "stratum", "query", "country", "country_code"]
ROLES = ["discovery", "semantic", "retrieval", "metadata", "citation", "judge", "adversarial"]
DIMENSION_KEYS = [
    "discovery_success",
    "retrieval_success",
    "temporal_geographic_correctness",
    "semantic_correctness",
    "metadata_correctness",
    "citation_correctness",
]
# AIRSC is deliberately independent of the technical AEO weights.  These
# equal weights are the declared outcome aggregation for the agent task.
OUTCOME_WEIGHTS = {key: 1.0 for key in DIMENSION_KEYS}

ROLE_REQUIRED: dict[str, set[str]] = {
    "discovery": {"discovered", "best_url", "confidence", "reason"},
    "semantic": {"selected_indicator_description", "correct", "confidence", "reason", "ambiguity_flags"},
    "retrieval": {"retrievable", "value_found", "period_correct", "geography_correct", "unit_correct", "confidence", "reason"},
    "metadata": {"metadata_complete", "fields_missing", "confidence", "reason"},
    "citation": {"citable", "citation_url", "source_named", "evidence_specific", "confidence", "reason"},
    "judge": set(DIMENSION_KEYS + ["overall_0_100", "decisive_reason"]),
    "adversarial": {"attack_found", "severity", "alternative_interpretation", "verdict", "reason"},
}

ROLE_PROMPTS = {
    "discovery": """Using only the frozen evidence, identify the official resource relevant to the query. A single specific official URL is valid when it is the only supported resource; do not invent alternatives. Return a concise natural answer.""",
    "semantic": """Using only the frozen evidence, identify the statistically correct series. Check concept, unit, price basis, frequency, geography, period and interpretation. State uncertainty explicitly. Return a concise natural answer.""",
    "retrieval": """Using only the frozen evidence, determine whether the requested value or series is actually retrievable without guessing. A homepage is discovery, not retrieval. State missing fields explicitly. Return a concise natural answer.""",
    "metadata": """Using only the frozen evidence, validate definition, source, unit, frequency, reference period, dimensions and methodology. Do not infer metadata that is absent. Return a concise natural answer.""",
    "citation": """Using only the frozen evidence, determine whether the requested result can be cited precisely and reproducibly. A generic homepage cannot cite an unobserved value. Return a concise natural answer.""",
    "judge": """Act as an independent statistical judge. Use only frozen evidence and structured candidate outputs; never use the technical AEO score. Return only the seven requested keys, with no extra keys, no URLs, and a short decisive_reason. Score each applicable dimension from 0 to 1; your supplied overall score is audited and recomputed by Python.""",
    "adversarial": """Try to falsify the candidate result using only frozen evidence and the candidate role outputs, without relying on a judge score. Look for wrong indicator, unit, price basis, period, geography, unsupported citation, URL outside the official portal, or conflation of discovery with retrieval. Return a concise natural answer.""",
}
ROLE_JSON_INSTRUCTIONS = {
    role: f"Return exactly one JSON object with these keys: {', '.join(sorted(keys))}. Do not add markdown or commentary. Use JSON booleans, arrays and null where appropriate."
    for role, keys in ROLE_REQUIRED.items()
}

# Independent model replicas can service independent role calls without
# changing the declared model identity.  The pool is optional; a scalar
# endpoint remains the default for reproducibility.
ROLE_ENDPOINT_SLOT = {"discovery": 0, "semantic": 1, "retrieval": 0, "metadata": 1, "citation": 0}


@dataclass
class ModelCall:
    mode: str
    model: str
    ok: bool
    raw_text: str = ""
    parsed_json: Any = None
    parse_error: str | None = None
    schema_valid: bool | None = None
    schema_error: str | None = None
    http_status: int | None = None
    error: str | None = None
    error_body: str | None = None
    elapsed_seconds: float = 0.0

    def as_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "model": self.model,
            "ok": self.ok,
            "raw_text": self.raw_text,
            "parsed_json": self.parsed_json,
            "parse_error": self.parse_error,
            "schema_valid": self.schema_valid,
            "schema_error": self.schema_error,
            "http_status": self.http_status,
            "error": self.error,
            "error_body": self.error_body,
            "elapsed_seconds": self.elapsed_seconds,
        }


def now_utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def stable_hash(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_")[:180]


def load_config(path: Path = CFG_PATH) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def scope_settings(cfg: dict[str, Any]) -> dict[str, Any]:
    benchmark_cfg = cfg.get("benchmark", {})
    portal_order = list(benchmark_cfg.get("portals", PORTAL_ORDER))
    if not portal_order or any(portal not in PORTALS for portal in portal_order):
        raise RuntimeError(f"invalid benchmark portal scope: {portal_order}")
    bank_path = ROOT / benchmark_cfg.get("template_bank", str(BANK_PATH.relative_to(ROOT)))
    expected_count = int(benchmark_cfg.get("template_count", 120))
    strata_targets = benchmark_cfg.get("strata_targets", STRATA_TARGETS)
    gold_path = ROOT / benchmark_cfg.get("gold_standard", str(GOLD_PATH.relative_to(ROOT)))
    results_root = ROOT / benchmark_cfg.get("results_root", str(PRODUCTION_ROOT.relative_to(ROOT)))
    return {"portal_order": portal_order, "bank_path": bank_path, "template_count": expected_count, "strata_targets": strata_targets, "gold_path": gold_path, "results_root": results_root}


def load_templates(bank_path: Path = BANK_PATH, expected_count: int = 120, expected_strata: dict[str, int] | None = None) -> list[dict[str, str]]:
    expected_strata = expected_strata or STRATA_TARGETS
    with bank_path.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    if len(rows) != expected_count:
        raise RuntimeError(f"template bank must have {expected_count} rows, found {len(rows)}")
    if list(rows[0]) != EXPECTED_COLUMNS:
        raise RuntimeError(f"unexpected bank columns: {list(rows[0])}")
    ids = [row["query_id"] for row in rows]
    if len({row["query_id"] for row in rows}) != expected_count:
        raise RuntimeError("duplicate template IDs")
    if not all(row["query"].strip() and row["country_code"].strip() for row in rows):
        raise RuntimeError("blank query or country code in canonical bank")
    observed = {row["stratum"]: 0 for row in rows}
    for row in rows:
        observed[row["stratum"]] = observed.get(row["stratum"], 0) + 1
    if observed != expected_strata:
        raise RuntimeError(f"template stratum counts {observed} != {expected_strata}")
    return rows


def materialize_pairs(templates: list[dict[str, str]], portal_order: list[str] | None = None) -> list[dict[str, str]]:
    portal_order = portal_order or PORTAL_ORDER
    pairs: list[dict[str, str]] = []
    for template in templates:
        for portal_id in portal_order:
            pairs.append({
                "case_id": f"{template['query_id']}__{portal_id}",
                "template_id": template["query_id"],
                "template_source_portal_id": template["portal_id"],
                "portal_id": portal_id,
                "stratum": template["stratum"],
                "query": template["query"],
                "country": template["country"],
                "country_code": template["country_code"],
            })
    expected_pairs = len(templates) * len(portal_order)
    if len(pairs) != expected_pairs or len({p["case_id"] for p in pairs}) != expected_pairs:
        raise RuntimeError(f"query/portal materialisation is not exactly {expected_pairs} unique pairs")
    return pairs


def portal_url_allowed(portal_id: str, url: str) -> bool:
    if not isinstance(url, str):
        return False
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    host = (parsed.hostname or "").lower().rstrip(".")
    if parsed.scheme not in {"http", "https"} or not host:
        return False
    if host in {"www.w3.org", "w3.org"} or host.endswith(".w3.org"):
        return False
    return any(host == root or host.endswith("." + root) for root in PORTALS[portal_id]["roots"])


def http_fetch(url: str, raw_dir: Path, label: str, timeout: float) -> dict[str, Any]:
    """Fetch and persist the complete response body and headers before parsing."""
    request = Request(url, headers={
        "User-Agent": "AEO-Agent-Readiness-Production/1.0",
        "Accept": "text/html,application/json,text/plain,*/*",
    })
    started = time.perf_counter()
    result: dict[str, Any] = {"requested_url": url, "captured_at": now_utc()}
    body = b""
    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read()
            result.update({
                "status": int(response.status),
                "final_url": response.geturl(),
                "headers": {k.lower(): v for k, v in response.headers.items()},
            })
    except HTTPError as exc:
        body = exc.read()
        result.update({"status": int(exc.code), "final_url": getattr(exc, "url", url), "headers": {k.lower(): v for k, v in exc.headers.items()} if exc.headers else {}, "error": "HTTPError"})
    except (URLError, TimeoutError, OSError) as exc:
        result.update({"status": 0, "final_url": url, "headers": {}, "error": f"{type(exc).__name__}: {exc}"})
    result["elapsed_seconds"] = round(time.perf_counter() - started, 3)
    result["byte_length"] = len(body)
    result["body_sha256"] = hashlib.sha256(body).hexdigest()
    stem = safe_name(label)
    body_path = raw_dir / f"{stem}.body"
    headers_path = raw_dir / f"{stem}.headers.json"
    body_path.parent.mkdir(parents=True, exist_ok=True)
    body_path.write_bytes(body)
    headers_path.write_text(json.dumps(result.get("headers", {}), ensure_ascii=False, indent=2), encoding="utf-8")
    result["body_path"] = str(body_path)
    result["headers_path"] = str(headers_path)
    result["text_excerpt"] = body.decode("utf-8", errors="replace")[:30000]
    return result


def parse_search_urls(text: str, portal_id: str) -> tuple[list[str], list[dict[str, str]]]:
    accepted: list[str] = []
    rejected: list[dict[str, str]] = []
    for match in re.findall(r"https?://[^\s\"'<>]+", text or ""):
        url = match.replace("&amp;", "&").rstrip(".,);'\"")
        if url in accepted or any(item["url"] == url for item in rejected):
            continue
        host = (urlparse(url).hostname or "").lower()
        if host.endswith("google.com") or host.endswith("bing.com") or host.endswith("duckduckgo.com"):
            continue
        if portal_url_allowed(portal_id, url):
            accepted.append(url)
        else:
            rejected.append({"url": url, "reason": "outside_portal_allowlist"})
    return accepted, rejected


def search_web(query: str, portal_id: str, raw_dir: Path, timeout: float, limit: int = 6) -> dict[str, Any]:
    urls: list[str] = []
    rejected: list[dict[str, str]] = []
    captures: list[dict[str, Any]] = []
    encoded = quote_plus(query)
    for engine_name, engine in [("google", f"https://www.google.com/search?q={encoded}"), ("bing", f"https://www.bing.com/search?q={encoded}")]:
        capture = http_fetch(engine, raw_dir, f"serp_{engine_name}", timeout)
        captures.append({k: v for k, v in capture.items() if k not in {"text_excerpt"}})
        accepted, denied = parse_search_urls(capture.get("text_excerpt", ""), portal_id)
        for url in accepted:
            if url not in urls and len(urls) < limit:
                urls.append(url)
        rejected.extend(denied)
    return {"urls": urls, "rejected": rejected, "captures": captures}


def evidence_for(pair: dict[str, str], run_dir: Path, cfg: dict[str, Any], refresh: bool = False) -> dict[str, Any]:
    evidence_path = run_dir / "evidence" / f"{safe_name(pair['case_id'])}.json"
    if evidence_path.exists() and not refresh:
        cached = json.loads(evidence_path.read_text(encoding="utf-8"))
        cached_pages = cached.get("pages", [])
        cache_valid = (
            cached.get("capture_version") == 2
            and cached.get("case_id") == pair["case_id"]
            and cached.get("portal_id") == pair["portal_id"]
            and all(
                page.get("allowlist_valid") is True
                and portal_url_allowed(pair["portal_id"], page.get("final_url", page.get("requested_url", "")))
                for page in cached_pages
            )
        )
        if cache_valid:
            return cached
    timeout = float(cfg.get("ollama", {}).get("http_timeout_seconds", 30))
    raw_dir = run_dir / "raw_http" / safe_name(pair["case_id"])
    portal_id = pair["portal_id"]
    home = PORTALS[portal_id]["home"]
    serp = search_web(f"site:{urlparse(home).netloc} {pair['query']}", portal_id, raw_dir, timeout)
    urls = [home] + [u for u in serp["urls"] if u != home]
    pages: list[dict[str, Any]] = []
    for i, url in enumerate(urls[: int(cfg.get("evidence", {}).get("max_pages", 7))]):
        if not portal_url_allowed(portal_id, url):
            continue
        page = http_fetch(url, raw_dir, f"page_{i:02d}", timeout)
        page["allowlist_valid"] = portal_url_allowed(portal_id, page.get("final_url", url))
        page["evidence_use"] = page["allowlist_valid"]
        if not page["allowlist_valid"]:
            page["rejected_reason"] = "redirected_outside_portal_allowlist"
            page["text_excerpt"] = ""
        pages.append(page)
    index = {
        "capture_version": 2,
        "case_id": pair["case_id"],
        "template_id": pair["template_id"],
        "portal_id": portal_id,
        "query": pair["query"],
        "captured_at": now_utc(),
        "allowlist_roots": sorted(PORTALS[portal_id]["roots"]),
        "serp": serp,
        "pages": pages,
    }
    index["sha256"] = stable_hash(index)
    atomic_json(evidence_path, index)
    return index


def add_candidate(evidence: dict[str, Any], candidate: str, run_dir: Path, cfg: dict[str, Any]) -> dict[str, Any]:
    portal_id = evidence["portal_id"]
    evidence["candidate_url"] = candidate or None
    evidence["candidate_allowed"] = bool(candidate and portal_url_allowed(portal_id, candidate))
    if candidate and evidence["candidate_allowed"] and candidate not in [p.get("requested_url") for p in evidence["pages"]]:
        raw_dir = run_dir / "raw_http" / safe_name(evidence["case_id"])
        page = http_fetch(candidate, raw_dir, f"candidate_{len(evidence['pages']):02d}", float(cfg.get("ollama", {}).get("http_timeout_seconds", 30)))
        page["allowlist_valid"] = portal_url_allowed(portal_id, page.get("final_url", candidate))
        page["evidence_use"] = page["allowlist_valid"]
        if not page["allowlist_valid"]:
            page["rejected_reason"] = "redirected_outside_portal_allowlist"
            page["text_excerpt"] = ""
        evidence["pages"].append(page)
    evidence["sha256"] = stable_hash({k: v for k, v in evidence.items() if k != "sha256"})
    # Repeated measurements may be evaluated in parallel.  Candidate pages
    # are auxiliary evidence for the same query/portal, so serialize only the
    # small read-modify-write section while model calls remain concurrent.
    with EVIDENCE_WRITE_LOCK:
        atomic_json(run_dir / "evidence" / f"{safe_name(evidence['case_id'])}.json", evidence)
    return evidence


def evidence_prompt(evidence: dict[str, Any], query: str, max_chars: int) -> str:
    chunks = []
    for page in evidence.get("pages", []):
        if page.get("allowlist_valid") is not True:
            continue
        chunks.append(f"URL: {page.get('final_url', page.get('requested_url'))}\nSTATUS: {page.get('status')}\nCONTENT-TYPE: {page.get('headers', {}).get('content-type', '')}\nTEXT:\n{page.get('text_excerpt', '')}")
    body = "\n\n---\n\n".join(chunks) if chunks else "NO ALLOWLISTED PORTAL PAGE WAS AVAILABLE. Treat retrieval and citation as unavailable; do not infer from the SERP."
    return (f"QUERY: {query}\n\nFROZEN EVIDENCE (do not browse outside it):\n" + body)[:max_chars]


def validate_schema(role: str, value: Any) -> tuple[bool, str | None]:
    if not isinstance(value, dict):
        return False, "response_not_object"
    missing = sorted(ROLE_REQUIRED[role] - set(value))
    if missing:
        return False, "missing_keys:" + ",".join(missing)
    bool_keys = {
        "discovery": ["discovered"],
        "semantic": ["correct"],
        "retrieval": ["retrievable", "value_found", "period_correct", "geography_correct", "unit_correct"],
        "metadata": ["metadata_complete"],
        "citation": ["citable", "source_named", "evidence_specific"],
        "adversarial": ["attack_found"],
    }.get(role, [])
    for key in bool_keys:
        if isinstance(value.get(key), str) and value[key].strip().lower() in {"true", "false"}:
            value[key] = value[key].strip().lower() == "true"
        elif role == "discovery" and key == "discovered" and isinstance(value.get(key), list):
            value[key] = bool(value[key])
        elif role == "citation" and key == "evidence_specific" and isinstance(value.get(key), list):
            value[key] = bool(value[key])
        if value[key] is not None and not isinstance(value[key], bool):
            return False, f"{key}_not_boolean"
    if role in {"discovery", "semantic", "retrieval", "metadata", "citation"}:
        confidence = value["confidence"]
        if confidence is not None and (not isinstance(confidence, (int, float)) or isinstance(confidence, bool) or not 0 <= confidence <= 1):
            return False, "confidence_out_of_range"
    if role == "judge":
        for key in DIMENSION_KEYS:
            if value[key] is None:
                continue
            if not isinstance(value[key], (int, float)) or isinstance(value[key], bool) or not 0 <= value[key] <= 1:
                return False, f"{key}_out_of_range"
        if value["overall_0_100"] is not None and (not isinstance(value["overall_0_100"], (int, float)) or isinstance(value["overall_0_100"], bool) or not 0 <= value["overall_0_100"] <= 100):
            return False, "overall_out_of_range"
    if role == "adversarial":
        if value["severity"] not in {"none", "low", "medium", "high"}:
            return False, "invalid_severity"
        if value["verdict"] not in {"pass", "fail", "uncertain"}:
            return False, "invalid_verdict"
    for key in ["ambiguity_flags", "fields_missing"]:
        if role == "semantic" and key == "ambiguity_flags" and not isinstance(value[key], list):
            return False, f"{key}_not_array"
        if role == "metadata" and key == "fields_missing" and not isinstance(value[key], list):
            return False, f"{key}_not_array"
    return True, None


def normalize_structured(role: str, value: Any) -> Any:
    """Normalize conservative model variants without inventing missing values."""
    if not isinstance(value, dict):
        return value
    value = dict(value)
    if role in {"discovery", "semantic", "retrieval", "metadata", "citation"} and isinstance(value.get("confidence"), bool):
        # Local Qwen variants use a boolean confidence flag.  Preserve its
        # meaning in the declared [0,1] contract rather than rejecting an
        # otherwise complete response.
        value["confidence"] = 1.0 if value["confidence"] else 0.0
    if role == "judge":
        for key in DIMENSION_KEYS:
            if isinstance(value.get(key), bool):
                value[key] = 1.0 if value[key] else 0.0
    if role == "adversarial":
        verdict = value.get("verdict")
        verdict_key = verdict.strip().lower().replace(" ", "_") if isinstance(verdict, str) else verdict
        if verdict_key in {"insufficient", "insufficient_evidence", "unclear", "not_enough_evidence"}:
            value["verdict"] = "uncertain"
        elif verdict_key in {"valid", "acceptable", "confirmed"}:
            value["verdict"] = "pass"
        elif verdict_key in {"invalid", "rejected"}:
            value["verdict"] = "fail"
        elif isinstance(verdict, str) and verdict.strip():
            # Some local models return a prose verdict despite JSON mode. Keep
            # the raw text in the role output but map the categorical field to
            # the conservative state required by the contract.
            value["verdict"] = "uncertain"
        severity = value.get("severity")
        if isinstance(severity, str):
            severity_key = severity.strip().lower().replace(" ", "_")
            if severity_key in {"none", "low", "medium", "high"}:
                value["severity"] = severity_key
            elif severity_key in {"insufficient", "unclear"}:
                value["severity"] = "medium"
        if value.get("severity") in {"insufficient", "unclear"}:
            value["severity"] = "medium"
    if role == "citation" and isinstance(value.get("source_named"), str):
        # A non-empty source name is affirmative evidence for this boolean
        # field; preserve the original raw response alongside the normalized
        # object for auditability.
        value["source_named"] = bool(value["source_named"].strip())
    return value


def salvage_judge_json(text: str) -> dict[str, Any] | None:
    """Extract only explicitly emitted judge fields from truncated JSON."""
    result: dict[str, Any] = {}
    for key in [*DIMENSION_KEYS, "overall_0_100"]:
        matches = re.findall(rf'"{re.escape(key)}"\s*:\s*(true|false|null|-?\d+(?:\.\d+)?)', text, flags=re.I)
        if not matches:
            return None
        raw = matches[-1].lower()
        result[key] = None if raw == "null" else (raw == "true" if raw in {"true", "false"} else float(raw))
    reasons = re.findall(r'"decisive_reason"\s*:\s*"((?:\\.|[^"\\])*)"', text)
    if not reasons:
        return None
    try:
        result["decisive_reason"] = json.loads('"' + reasons[-1] + '"')
    except json.JSONDecodeError:
        result["decisive_reason"] = reasons[-1]
    return result


def call_model(base: str, model: str, role: str, user: str, timeout: float, temperature: float, structured: bool, num_predict: int = 160) -> ModelCall:
    mode = "structured" if structured else "natural"
    system = ROLE_PROMPTS[role] + ("\n" + ROLE_JSON_INSTRUCTIONS[role] if structured else "")
    payload: dict[str, Any] = {
        "model": model,
        "stream": False,
        # Qwen/Gemma-family local models may spend the entire small token
        # budget in a hidden reasoning channel when thinking is enabled.  The
        # benchmark measures the returned answer, so disable that channel and
        # preserve the natural response verbatim.
        "think": False,
        "options": {"temperature": temperature, "num_predict": num_predict},
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
    }
    if structured:
        payload["format"] = "json"
    started = time.perf_counter()
    try:
        request = Request(base.rstrip("/") + "/api/chat", data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
        with urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
        text = data.get("message", {}).get("content", "")
        parsed: Any = None
        parse_error: str | None = None
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            parse_error = str(exc)
            if structured and role == "judge":
                recovered = salvage_judge_json(text)
                if recovered is not None:
                    parsed = recovered
                    parse_error = None
        call = ModelCall(mode=mode, model=model, ok=True, raw_text=text, parsed_json=parsed, parse_error=parse_error, http_status=200, elapsed_seconds=round(time.perf_counter() - started, 3))
        if structured:
            call.parsed_json = normalize_structured(role, parsed)
            call.schema_valid, call.schema_error = validate_schema(role, call.parsed_json)
        return call
    except HTTPError as exc:
        body = exc.read().decode(errors="replace")
        return ModelCall(mode=mode, model=model, ok=False, http_status=int(exc.code), error="HTTPError", error_body=body, elapsed_seconds=round(time.perf_counter() - started, 3))
    except Exception as exc:
        return ModelCall(mode=mode, model=model, ok=False, error=f"{type(exc).__name__}: {exc}", elapsed_seconds=round(time.perf_counter() - started, 3))


def role_context(evidence: dict[str, Any], pair: dict[str, str], prior: dict[str, Any], cfg: dict[str, Any]) -> str:
    extra = "\n\nSTRUCTURED CANDIDATE OUTPUTS:\n" + json.dumps(prior, ensure_ascii=False, indent=2) if prior else ""
    return evidence_prompt(evidence, pair["query"], int(cfg.get("ollama", {}).get("max_context_chars", 18000))) + extra


def role_call_with_retry(base: str, model: str, role: str, context: str, cfg: dict[str, Any]) -> dict[str, Any]:
    ollama_cfg = cfg.get("ollama", {})
    pool = ollama_cfg.get("model_endpoint_pools", {}).get(model)
    if isinstance(pool, list) and pool:
        endpoint = str(pool[ROLE_ENDPOINT_SLOT.get(role, 0) % len(pool)])
    else:
        endpoint = str(ollama_cfg.get("model_endpoints", {}).get(model, base))
    timeout = float(cfg.get("ollama", {}).get("timeout_seconds", 180))
    temperature = float(cfg.get("ollama", {}).get("temperature", 0.0))
    num_predict = int(ollama_cfg.get("role_num_predict", {}).get(role, ollama_cfg.get("num_predict", 160)))
    if cfg.get("benchmark", {}).get("capture_natural", False):
        natural_num_predict = int(cfg.get("ollama", {}).get("natural_num_predict", min(num_predict, 96)))
        natural = call_model(endpoint, model, role, context, timeout, temperature, structured=False, num_predict=natural_num_predict)
    else:
        natural = ModelCall(mode="natural", model=model, ok=False, error="natural_capture_disabled_for_full_run")
    structured_initial = call_model(endpoint, model, role, context, timeout, temperature, structured=True, num_predict=num_predict)
    structured_retry: ModelCall | None = None
    selected = structured_initial
    if structured_initial.schema_valid is not True:
        retry_context = context[: int(cfg.get("ollama", {}).get("retry_context_chars", 8000))]
        structured_retry = call_model(endpoint, model, role, retry_context, timeout, temperature, structured=True, num_predict=num_predict)
        if structured_retry.schema_valid is True:
            selected = structured_retry
    return {
        "model": model,
        "natural": natural.as_dict(),
        "structured_initial": structured_initial.as_dict(),
        "structured_retry": structured_retry.as_dict() if structured_retry else None,
        "selected_structured": selected.as_dict(),
        "schema_valid": selected.schema_valid,
        "schema_error": selected.schema_error,
    }


def deterministic_semantic_check(pair: dict[str, str], semantic: dict[str, Any] | None) -> dict[str, Any]:
    """A transparent diagnostic, not a substitute for query-specific gold labels."""
    if not isinstance(semantic, dict):
        return {"status": "NA", "value": None, "reason": "semantic_output_unavailable"}
    text = str(semantic.get("selected_indicator_description", "")).lower()
    query = pair["query"].lower()
    expected_tokens: list[str] = []
    if "per cápita" in query or "por habitante" in query:
        expected_tokens = ["per cápita", "por habitante", "per capita"]
    elif "crecimiento" in query or "creció" in query:
        expected_tokens = ["crecimiento", "growth", "variación porcentual", "%"]
    elif "precios constantes" in query or "real" in query:
        expected_tokens = ["constantes", "real", "volumen"]
    elif "precios corrientes" in query or "dólares corrientes" in query:
        expected_tokens = ["corrientes", "nominal", "current"]
    if not expected_tokens:
        return {"status": "NA", "value": None, "reason": "no_rule_without_gold_case"}
    matched = any(token in text for token in expected_tokens)
    return {"status": "rule_check", "value": matched, "reason": "expected_token_match" if matched else "expected_token_absent", "expected_tokens": expected_tokens}


def natural_signals(call: dict[str, Any]) -> dict[str, Any]:
    text = call.get("raw_text", "") if isinstance(call, dict) else ""
    return {
        "available": bool(call.get("ok")) and bool(text.strip()),
        "character_count": len(text),
        "url_count": len(re.findall(r"https?://[^\s)<>\"']+", text)),
        "contains_uncertainty": bool(re.search(r"no se|no está|no disponible|cannot|unable|missing|falt", text, re.I)),
        "natural_schema_parse": call.get("parse_error") is None and call.get("parsed_json") is not None,
    }


def recompute_overall(judge: dict[str, Any] | None) -> dict[str, Any]:
    values = {key: judge.get(key) for key in DIMENSION_KEYS} if isinstance(judge, dict) else {key: None for key in DIMENSION_KEYS}
    applicable = {key: float(value) for key, value in values.items() if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))}
    if not applicable:
        return {"overall_0_100_recomputed": None, "applicable_dimensions": [], "status": "NA", "weights": OUTCOME_WEIGHTS}
    total_weight = sum(OUTCOME_WEIGHTS[key] for key in applicable)
    score = 100.0 * sum(applicable[key] * OUTCOME_WEIGHTS[key] for key in applicable) / total_weight
    return {"overall_0_100_recomputed": round(score, 6), "applicable_dimensions": sorted(applicable), "status": "OK", "weights": OUTCOME_WEIGHTS}


def run_execution(base: str, pair: dict[str, str], evidence: dict[str, Any], models: dict[str, str], cfg: dict[str, Any], pass_id: int, repeat: int, run_dir: Path) -> dict[str, Any]:
    events = [{"event": "evidence_frozen", "at": now_utc(), "sha256": evidence["sha256"]}]
    discovery = role_call_with_retry(base, models["discovery"], "discovery", role_context(evidence, pair, {}, cfg), cfg)
    d = discovery["selected_structured"].get("parsed_json") if discovery.get("schema_valid") else None
    candidate = d.get("best_url") if isinstance(d, dict) else None
    evidence = add_candidate(evidence, candidate, run_dir, cfg)
    events.append({"event": "discovery_completed", "at": now_utc(), "candidate_url": candidate, "candidate_allowed": evidence.get("candidate_allowed")})
    prior: dict[str, Any] = {"discovery": d if isinstance(d, dict) else {"status": "NA", "schema_error": discovery.get("schema_error")}}
    agents: dict[str, Any] = {"discovery": discovery}
    # These four roles all consume the same frozen evidence and discovery
    # output.  They are intentionally independent and may run concurrently;
    # the judge still receives all four structured outputs below.
    independent_roles = ["semantic", "retrieval", "metadata", "citation"]
    role_workers = max(1, int(cfg.get("ollama", {}).get("parallel_role_workers", 1)))
    with ThreadPoolExecutor(max_workers=min(role_workers, len(independent_roles))) as pool:
        futures = {pool.submit(role_call_with_retry, base, models[role], role, role_context(evidence, pair, prior, cfg), cfg): role for role in independent_roles}
        for future in as_completed(futures):
            role = futures[future]
            answer = future.result()
            agents[role] = answer
    for role in independent_roles:
        answer = agents[role]
        prior[role] = answer["selected_structured"].get("parsed_json") if answer.get("schema_valid") else {"status": "NA", "schema_error": answer.get("schema_error")}
        events.append({"event": role + "_completed", "at": now_utc(), "schema_valid": answer.get("schema_valid")})
    # Judge and adversarial are also independent of one another; both receive
    # the same role bundle and neither is allowed to consume the other's score.
    with ThreadPoolExecutor(max_workers=2) as pool:
        judge_future = pool.submit(role_call_with_retry, base, models["judge"], "judge", role_context(evidence, pair, prior, cfg), cfg)
        adversarial_future = pool.submit(role_call_with_retry, base, models["adversarial"], "adversarial", role_context(evidence, pair, prior, cfg), cfg)
        judge = judge_future.result()
        adversarial = adversarial_future.result()
    agents["judge"] = judge
    judge_json = judge["selected_structured"].get("parsed_json") if judge.get("schema_valid") else None
    events.append({"event": "judge_completed", "at": now_utc(), "schema_valid": judge.get("schema_valid")})
    agents["adversarial"] = adversarial
    events.append({"event": "adversarial_completed", "at": now_utc(), "schema_valid": adversarial.get("schema_valid")})
    semantic_json = agents["semantic"]["selected_structured"].get("parsed_json") if agents["semantic"].get("schema_valid") else None
    dimensions = recompute_overall(judge_json)
    natural_signal_values = {role: natural_signals(agent.get("natural", {})) for role, agent in agents.items()}
    schemas_valid = all(agents.get(role, {}).get("schema_valid") is True for role in ROLES)
    natural_valid = all(natural_signal_values.get(role, {}).get("available") is True for role in ROLES)
    capture_natural = bool(cfg.get("benchmark", {}).get("capture_natural", False))
    return {
        "execution_key": f"pass{pass_id}__{pair['case_id']}__repeat{repeat}",
        "pass_id": pass_id,
        "pass_portal_id": pair["portal_id"],
        "repeat": repeat,
        "case": pair,
        "evidence_sha256": evidence["sha256"],
        "candidate_url": candidate,
        "candidate_allowed": evidence.get("candidate_allowed"),
        "orchestrator": {"role": "deterministic-python", "events": events},
        "agents": agents,
        "natural_signals": natural_signal_values,
        "semantic_check": deterministic_semantic_check(pair, semantic_json),
        "judge_dimensions": judge_json if isinstance(judge_json, dict) else {key: None for key in DIMENSION_KEYS},
        "score": dimensions,
        "adversarial": {
            "schema_valid": adversarial.get("schema_valid"),
            "verdict": (adversarial["selected_structured"].get("parsed_json") or {}).get("verdict") if adversarial.get("schema_valid") else None,
            "severity": (adversarial["selected_structured"].get("parsed_json") or {}).get("severity") if adversarial.get("schema_valid") else None,
        },
        "status": "OK" if schemas_valid and (not capture_natural or natural_valid) else "PARTIAL",
        "generated_at": now_utc(),
    }


def model_inventory(base: str) -> dict[str, Any]:
    request = Request(base.rstrip("/") + "/api/tags", headers={"Accept": "application/json"})
    started = time.perf_counter()
    try:
        with urlopen(request, timeout=15) as response:
            payload = json.loads(response.read().decode("utf-8"))
        models = payload.get("models", [])
        inventory = []
        for item in models:
            name = item.get("name", "")
            inventory.append({"name": name, "size_parameter_b": parameter_size_b(name), "size_bytes": item.get("size"), "digest": item.get("digest"), "allowed": name in allowed_models([name])})
        return {"ok": True, "http_status": 200, "elapsed_seconds": round(time.perf_counter() - started, 3), "models": inventory, "raw_sha256": stable_hash(payload)}
    except HTTPError as exc:
        return {"ok": False, "http_status": int(exc.code), "error": "HTTPError", "error_body": exc.read().decode(errors="replace"), "elapsed_seconds": round(time.perf_counter() - started, 3)}
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}", "elapsed_seconds": round(time.perf_counter() - started, 3)}


def select_models(cfg: dict[str, Any], inventory: dict[str, Any]) -> dict[str, str]:
    if not inventory.get("ok"):
        raise RuntimeError("Ollama model inventory unavailable")
    installed = {item["name"] for item in inventory.get("models", [])}
    roles = cfg.get("roles", {})
    selected: dict[str, str] = {}
    for role in ROLES:
        model = roles.get(role, "gemma4:latest")
        if model == "auto":
            model = next((name for name in installed if "gemma" in name.lower()), "")
        if not model or model not in installed:
            raise RuntimeError(f"configured model for {role} is not installed: {model}")
        assert_allowed_model(model)
        selected[role] = model
    return selected


def probe_selected_models(base: str, models: dict[str, str], cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    """Run one tiny structured probe per distinct selected model.

    This is a transport/contract gate only.  It does not enter the benchmark
    output and it does not claim semantic quality.
    """
    probes: dict[str, Any] = {}
    endpoint_map = (cfg or {}).get("ollama", {}).get("model_endpoints", {})
    for model in sorted(set(models.values())):
        model_base = str(endpoint_map.get(model, base))
        payload = {
            "model": model,
            "stream": False,
            "think": False,
            "format": "json",
            "options": {"temperature": 0, "num_predict": 32},
            "messages": [
                {"role": "system", "content": "Return exactly one JSON object with key ok."},
                {"role": "user", "content": "Respond with {\"ok\":true}."},
            ],
        }
        started = time.perf_counter()
        probe: dict[str, Any] = {"model": model}
        try:
            request = Request(model_base.rstrip("/") + "/api/chat", data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
            with urlopen(request, timeout=90) as response:
                data = json.loads(response.read().decode("utf-8"))
            text = data.get("message", {}).get("content", "")
            probe.update({"ok": True, "http_status": 200, "raw_text": text, "elapsed_seconds": round(time.perf_counter() - started, 3)})
            try:
                probe["parsed_json"] = json.loads(text)
                probe["schema_valid"] = isinstance(probe["parsed_json"], dict) and probe["parsed_json"].get("ok") is True
            except json.JSONDecodeError as exc:
                probe.update({"parsed_json": None, "schema_valid": False, "parse_error": str(exc)})
        except HTTPError as exc:
            probe.update({"ok": False, "http_status": int(exc.code), "error": "HTTPError", "error_body": exc.read().decode(errors="replace"), "elapsed_seconds": round(time.perf_counter() - started, 3)})
        except Exception as exc:
            probe.update({"ok": False, "error": f"{type(exc).__name__}: {exc}", "elapsed_seconds": round(time.perf_counter() - started, 3)})
        probes[model] = probe
    return {"status": "PASS" if all(item.get("ok") and item.get("schema_valid") for item in probes.values()) else "HOLD", "models": probes}


def gold_coverage(pairs: list[dict[str, str]], gold_path: Path = GOLD_PATH) -> dict[str, Any]:
    if not gold_path.exists():
        return {"status": "HOLD", "gold_cases": 0, "expected_pairs": len(pairs), "reason": "gold file missing"}
    data = json.loads(gold_path.read_text(encoding="utf-8"))
    cases = data.get("cases", []) if isinstance(data, dict) else []
    if not cases and isinstance(data, dict):
        cases = data.get("items", [])
    ids = {
        case.get("case_id") or f"{case.get('template_id')}__{case.get('portal_id')}"
        for case in cases if isinstance(case, dict)
    }
    # Existing human cases use semantic IDs and are intentionally not treated
    # as coverage of all portal pairs.  Production requires explicit pair IDs.
    pair_ids = {p["case_id"] for p in pairs}
    covered = len(pair_ids & ids)
    target_pending = any(case.get("target_available") == "to_validate" or case.get("gold_status", "").endswith("validation_required") for case in cases if isinstance(case, dict))
    status = "CONTRACT_ONLY" if covered == len(pair_ids) and target_pending else ("PASS" if covered == len(pair_ids) else "HOLD")
    reason = "pair-level contract present; target values/API validation pending" if status == "CONTRACT_ONLY" else ("complete" if status == "PASS" else "complete pair-level gold required")
    return {"status": status, "gold_cases": len(ids), "covered_pairs": covered, "expected_pairs": len(pair_ids), "reason": reason}


def preflight(base: str, cfg: dict[str, Any], require_models: bool = True, probe_models: bool = False) -> dict[str, Any]:
    scope = scope_settings(cfg)
    templates = load_templates(scope["bank_path"], scope["template_count"], scope["strata_targets"])
    pairs = materialize_pairs(templates, scope["portal_order"])
    inventory = model_inventory(base) if require_models else {"ok": None, "status": "SKIPPED_OFFLINE"}
    models = None
    model_status = "SKIPPED"
    if require_models:
        models = select_models(cfg, inventory)
        model_status = "PASS"
    health = {"status": "SKIPPED"}
    if require_models and probe_models and models:
        health = probe_selected_models(base, models, cfg)
        if health["status"] != "PASS":
            model_status = "HOLD"
    gold = gold_coverage(pairs, scope["gold_path"])
    expected_exec = len(pairs) * int(cfg.get("ollama", {}).get("repeat_runs", 3))
    cardinality_pass = len(templates) == scope["template_count"] and len(pairs) == scope["template_count"] * len(scope["portal_order"]) and expected_exec == len(pairs) * int(cfg.get("ollama", {}).get("repeat_runs", 3))
    report = {
        "status": "PASS" if cardinality_pass and model_status in {"PASS", "SKIPPED"} and gold["status"] == "PASS" else "HOLD",
        "cardinality_status": "PASS" if cardinality_pass else "HOLD",
        "bank_rows": len(templates),
        "portals": len(scope["portal_order"]),
        "portal_scope": scope["portal_order"],
        "query_portal_pairs": len(pairs),
        "repeats": int(cfg.get("ollama", {}).get("repeat_runs", 3)),
        "expected_executions": expected_exec,
        "passes": len(scope["portal_order"]),
        "executions_per_pass": len(templates) * int(cfg.get("ollama", {}).get("repeat_runs", 3)),
        "model_policy": model_status,
        "model_health": health,
        "selected_models": models,
        "inventory": inventory,
        "gold": gold,
        "allowlist_roots": {portal: sorted(info["roots"]) for portal, info in PORTALS.items()},
    }
    return report


def run(args: argparse.Namespace) -> int:
    cfg = load_config(Path(args.config))
    if args.repeats != 3:
        raise RuntimeError("the PDF contract is fixed at three repeats per query/portal pair")
    configured_base = args.base or os.getenv("OLLAMA_HOST") or cfg.get("ollama", {}).get("base_url") or "http://localhost:11434"
    effective_base = configured_base.replace("127.0.0.1", "localhost")
    report = preflight(effective_base, cfg, require_models=args.execute, probe_models=args.execute)
    if args.plan or not args.execute:
        print(json.dumps({"configured_base": configured_base, "effective_base": effective_base, "preflight": report}, ensure_ascii=False, indent=2))
        return 0 if report.get("status") == "PASS" else 2
    if report.get("status") != "PASS":
        only_gold_hold = report.get("cardinality_status") == "PASS" and report.get("model_policy") == "PASS" and report.get("gold", {}).get("status") != "PASS"
        if not (args.allow_incomplete_gold and only_gold_hold):
            raise SystemExit("PRODUCTION PREFLIGHT HOLD: " + json.dumps(report, ensure_ascii=False))
    if report["gold"]["status"] != "PASS" and not args.allow_incomplete_gold:
        raise SystemExit("GOLD COVERAGE HOLD: pass --allow-incomplete-gold only for non-final diagnostics")
    scope = scope_settings(cfg)
    templates = load_templates(scope["bank_path"], scope["template_count"], scope["strata_targets"])
    pairs = materialize_pairs(templates, scope["portal_order"])
    pair_by_portal = {portal: [p for p in pairs if p["portal_id"] == portal] for portal in scope["portal_order"]}
    expected_executions = len(pairs) * int(args.repeats)
    models = report["selected_models"]
    run_id = args.run_id or time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    run_dir = scope["results_root"] / safe_name(run_id)
    run_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = run_dir / "run_manifest.json"
    manifest = {
        "runner": "production_runner.py",
        "run_id": run_id,
        "started_at": now_utc(),
        "configured_base": configured_base,
        "effective_base": effective_base,
        "models": models,
        "model_endpoints": cfg.get("ollama", {}).get("model_endpoints", {}),
        "model_endpoint_pools": cfg.get("ollama", {}).get("model_endpoint_pools", {}),
        "model_inventory": report["inventory"],
        "bank_file": str(scope["bank_path"].relative_to(ROOT)),
        "bank_sha256": hashlib.sha256(scope["bank_path"].read_bytes()).hexdigest(),
        "gold_file": str(scope["gold_path"].relative_to(ROOT)),
        "gold_sha256": hashlib.sha256(scope["gold_path"].read_bytes()).hexdigest(),
        "aeo_matrix_file": str(MATRIX_PATH.relative_to(ROOT)),
        "aeo_matrix_sha256": hashlib.sha256(MATRIX_PATH.read_bytes()).hexdigest(),
        "skill_file": ".agents/skills/aeo-agent-readiness-auditor/SKILL.md",
        "skill_sha256": hashlib.sha256((ROOT / ".agents/skills/aeo-agent-readiness-auditor/SKILL.md").read_bytes()).hexdigest(),
        "report_template_sha256": hashlib.sha256((ROOT / ".agents/skills/aeo-agent-readiness-auditor/references/report-template.md").read_bytes()).hexdigest(),
        "scope": "pilot_extremes" if scope["portal_order"] != PORTAL_ORDER or scope["template_count"] != 120 else "canonical_full",
        "portal_scope": scope["portal_order"],
        "production_benchmark": scope["portal_order"] == PORTAL_ORDER and scope["template_count"] == 120,
        "expected": {"templates": len(templates), "portals": len(scope["portal_order"]), "pairs": len(pairs), "repeats": int(args.repeats), "executions": expected_executions, "passes": len(scope["portal_order"]), "executions_per_pass": len(templates) * int(args.repeats)},
        "evidence_policy": "frozen_once_per_query_portal; candidate fetch appended and rehashed",
        "natural_capture": bool(cfg.get("benchmark", {}).get("capture_natural", False)),
        "parallel_role_workers": int(cfg.get("ollama", {}).get("parallel_role_workers", 1)),
        "gold_status": report["gold"],
        "status": "RUNNING",
    }
    atomic_json(manifest_path, manifest)
    results_path = run_dir / "results.jsonl"
    checkpoint_path = run_dir / "checkpoint.json"
    completed: set[str] = set()
    if args.resume and checkpoint_path.exists():
        completed = set(json.loads(checkpoint_path.read_text(encoding="utf-8")).get("completed", []))
        # A checkpoint may contain transport/schema-partial rows from an
        # earlier model profile.  They are deliberately re-run on resume;
        # only rows that satisfy the full role contract remain completed.
        if results_path.exists():
            retained: list[str] = []
            valid_keys: set[str] = set()
            for line in results_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                key = row.get("execution_key")
                natural_valid = all((row.get("natural_signals") or {}).get(role, {}).get("available") is True for role in ROLES)
                natural_required = bool(cfg.get("benchmark", {}).get("capture_natural", False))
                if row.get("status") == "OK" and key and all((row.get("agents") or {}).get(role, {}).get("schema_valid") is True for role in ROLES) and (not natural_required or natural_valid):
                    retained.append(json.dumps(row, ensure_ascii=False))
                    valid_keys.add(key)
            if len(retained) != len(results_path.read_text(encoding="utf-8").splitlines()):
                tmp_results = results_path.with_suffix(".jsonl.resume-tmp")
                tmp_results.write_text("\n".join(retained) + ("\n" if retained else ""), encoding="utf-8")
                tmp_results.replace(results_path)
            completed &= valid_keys
    max_exec = args.max_executions or expected_executions
    count = len(completed)
    parallel_workers = max(1, int(cfg.get("ollama", {}).get("parallel_workers", 1)))
    try:
        for pass_id, portal_id in enumerate(scope["portal_order"], start=1):
            if args.only_passes and pass_id not in args.only_passes:
                continue
            # Freeze each query/portal evidence once, then submit its repeats
            # as independent tasks while the remaining evidence is captured.
            # A bounded pool exploits separate Ollama endpoints without
            # changing the declared three-repeat design.
            with ThreadPoolExecutor(max_workers=parallel_workers) as pool:
                future_map = {}
                remaining = max(0, max_exec - count)
                for pair in pair_by_portal[portal_id]:
                    evidence = evidence_for(pair, run_dir, cfg, refresh=args.refresh_evidence)
                    for repeat in range(1, int(args.repeats) + 1):
                        key = f"pass{pass_id}__{pair['case_id']}__repeat{repeat}"
                        if key in completed or len(future_map) >= remaining:
                            continue
                        future = pool.submit(run_execution, effective_base, pair, copy.deepcopy(evidence), models, cfg, pass_id, repeat, run_dir)
                        future_map[future] = (key, pair, repeat)
                for future in as_completed(future_map):
                    key, pair, repeat = future_map[future]
                    result = future.result()
                    with results_path.open("a", encoding="utf-8") as fh:
                        fh.write(json.dumps(result, ensure_ascii=False) + "\n")
                        fh.flush()
                    completed.add(key); count += 1
                    atomic_json(checkpoint_path, {"updated_at": now_utc(), "completed": sorted(completed), "count": count, "expected": expected_executions})
                    print(f"[{count}/{max_exec}] pass={pass_id} portal={portal_id} {pair['template_id']} repeat={repeat}", flush=True)
                    if count >= max_exec:
                        break
            if count >= max_exec:
                break
    except KeyboardInterrupt:
        manifest["completed_executions"] = count
        manifest["status"] = "HOLD_INTERRUPTED"
        manifest["stop_reason"] = "interrupted_by_operator"
        manifest["finished_at"] = now_utc()
        atomic_json(manifest_path, manifest)
        print(json.dumps({"run_dir": str(run_dir), "completed": count, "expected": expected_executions, "status": manifest["status"]}, ensure_ascii=False, indent=2), flush=True)
        return 130
    except Exception as exc:
        manifest["completed_executions"] = count
        manifest["status"] = "HOLD"
        manifest["stop_reason"] = f"{type(exc).__name__}: {exc}"
        manifest["finished_at"] = now_utc()
        atomic_json(manifest_path, manifest)
        raise
    manifest["completed_executions"] = count
    manifest["status"] = "COMPLETE" if count == expected_executions else "PARTIAL"
    manifest["finished_at"] = now_utc()
    atomic_json(manifest_path, manifest)
    print(json.dumps({"run_dir": str(run_dir), "completed": count, "expected": expected_executions, "status": manifest["status"]}, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="run model/web workflow; without this flag only preflight runs")
    parser.add_argument("--plan", action="store_true", help="print the offline cardinality/model plan")
    parser.add_argument("--base", default=None, help="Ollama base URL; defaults to OLLAMA_HOST/config")
    parser.add_argument("--config", default=str(CFG_PATH), help="configuration YAML; defaults to benchmark/config.yaml")
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--refresh-evidence", action="store_true")
    parser.add_argument("--max-executions", type=int, default=None, help="bounded diagnostic run; never represents final 1,800 result")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--only-passes", type=int, nargs="*", default=None, help="portal pass numbers 1..5")
    parser.add_argument("--allow-incomplete-gold", action="store_true", help="diagnostic only; never use for final benchmark")
    return parser


if __name__ == "__main__":
    try:
        raise SystemExit(run(build_parser().parse_args()))
    except (RuntimeError, ValueError) as exc:
        raise SystemExit(f"PRODUCTION RUNNER FAILED CLOSED: {exc}") from exc
