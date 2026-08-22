"""Local macOS runner for the multi-agent AEO benchmark.

The runner is deterministic at the orchestration/evidence layer and uses the
user's local Ollama models only for agent judgements. Evidence is frozen per
query/portal and reused across repeats. Invalid JSON or schema failures are
recorded rather than silently repaired.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote_plus, urlparse
from urllib.request import Request, urlopen

try:
    import yaml
except ImportError as exc:
    raise SystemExit("PyYAML is required: python -m pip install pyyaml") from exc

ROOT = Path(__file__).resolve().parents[1]
CFG_PATH = ROOT / "benchmark" / "config.yaml"
BANK = ROOT / "benchmark" / "query-bank-120.csv"
OUT = ROOT / "benchmark" / "results"

PORTALS = {
    "worldbank": ("World Bank Open Data", "https://data.worldbank.org/"),
    "who": ("WHO Data", "https://data.who.int/"),
    "cepalstat": ("CEPALSTAT", "https://statistics.cepal.org/portal/cepalstat/"),
    "undata": ("UN Data Commons", "https://unstats.un.org/UNSDWebsite/undatacommons/"),
    "sdg": ("UN SDG Indicators", "https://unstats.un.org/sdgs/dataportal/"),
}

ROLE_PROMPTS = {
    "discovery": "Determine whether the supplied frozen evidence lets an AI agent discover the official portal/resource relevant to the query. Return only JSON with keys: discovered (boolean), best_url (string), confidence (0..1), reason (string).",
    "semantic": "Identify the statistically correct indicator/series among the evidence. Focus on concept, unit, price basis, frequency, geography, period and meaning. Return only JSON with keys: selected_indicator_description, correct (boolean), confidence (0..1), reason, ambiguity_flags (array).",
    "retrieval": "Check whether the evidence contains enough information to retrieve the requested value/series without guessing. Return only JSON with keys: retrievable, value_found, period_correct, geography_correct, unit_correct (booleans or null when not testable), confidence, reason.",
    "metadata": "Validate the statistical metadata needed for a rigorous answer: definition, source, unit, frequency, reference period, dimensions and methodological notes. Return only JSON with keys: metadata_complete (boolean), fields_missing (array), confidence, reason.",
    "citation": "Check whether a user could cite the evidence precisely and reproducibly. Return only JSON with keys: citable (boolean), citation_url, source_named (boolean), evidence_specific (boolean), confidence, reason.",
    "judge": "Act as an independent statistical judge. Score only from the supplied frozen evidence and agent outputs; do not infer quality from the technical AEO score. Return only JSON with keys: discovery_success, retrieval_success, temporal_geographic_correctness, semantic_correctness, metadata_correctness, citation_correctness (numbers 0..1), overall_0_100 (0..100), decisive_reason.",
    "adversarial": "Try to falsify the candidate answer using only the frozen evidence and candidate outputs. Look for wrong indicator, wrong unit, wrong price basis, wrong period, wrong geography, hidden-JS dependence, non-authoritative source, stale page, or unsupported citation. Return only JSON with keys: attack_found (boolean), severity (none/low/medium/high), alternative_interpretation, verdict (pass/fail/uncertain), reason.",
}

EXPECTED_COLUMNS = [
    "query_id", "portal_id", "stratum", "query", "country", "country_code",
]
STRATA_TARGETS = {
    "discovery": 20, "exact_indicator": 20, "semantic_disambiguation": 25,
    "dimensions": 15, "comparison": 15, "temporal": 10, "metadata": 10, "citation": 5,
}

@dataclass
class Evidence:
    portal_id: str
    query_id: str
    urls: list[str]
    pages: list[dict[str, Any]]
    captured_at: str
    sha256: str


def load_config() -> dict[str, Any]:
    with CFG_PATH.open(encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh) or {}
    return cfg


def validate_bank(rows: list[dict[str, str]]) -> None:
    if len(rows) != 120:
        raise ValueError(f"Query bank must contain 120 rows; found {len(rows)}")
    if list(rows[0].keys()) != EXPECTED_COLUMNS:
        raise ValueError(f"Query bank columns mismatch: {list(rows[0].keys())}")
    totals: dict[str, int] = {}
    portals: set[str] = set()
    for row in rows:
        portals.add(row["portal_id"])
        totals[row["stratum"]] = totals.get(row["stratum"], 0) + 1
        if row["portal_id"] not in PORTALS:
            raise ValueError(f"Unknown portal_id: {row['portal_id']}")
    if portals != set(PORTALS):
        raise ValueError(f"Portal set mismatch: {sorted(portals)}")
    if totals != STRATA_TARGETS:
        raise ValueError(f"Stratum totals mismatch: {totals}; expected {STRATA_TARGETS}")


def http_get(url: str, timeout: float = 25, max_bytes: int = 120000) -> tuple[int, str, dict[str, str]]:
    req = Request(url, headers={
        "User-Agent": "AEO-Agent-Readiness-Benchmark/1.1",
        "Accept": "text/html,application/json,text/plain,*/*",
    })
    try:
        with urlopen(req, timeout=timeout) as r:
            body = r.read(max_bytes)
            headers = {k.lower(): v for k, v in r.headers.items()}
            enc = "utf-8"
            m = re.search(r"charset=([^;]+)", headers.get("content-type", ""), re.I)
            if m:
                enc = m.group(1).strip('"\'')
            return r.status, body.decode(enc, errors="replace"), headers
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        return 0, f"FETCH_ERROR: {type(exc).__name__}: {exc}", {}


def search_web(query: str, limit: int = 5) -> list[str]:
    urls: list[str] = []
    q = quote_plus(query)
    for engine in [f"https://www.google.com/search?q={q}", f"https://www.bing.com/search?q={q}"]:
        _, text, _ = http_get(engine, timeout=20, max_bytes=60000)
        for match in re.findall(r'https?://[^\s"<>]+', text or ""):
            u = match.replace("&amp;", "&").rstrip(".,);'\"")
            host = urlparse(u).netloc.lower()
            if host in {"www.google.com", "google.com", "www.bing.com", "bing.com"}:
                continue
            if u not in urls:
                urls.append(u)
            if len(urls) >= limit:
                return urls
    return urls


def evidence_for(row: dict[str, str], refresh: bool = False) -> Evidence:
    OUT.mkdir(parents=True, exist_ok=True)
    cache = OUT / f"evidence_{row['query_id']}_{row['portal_id']}.json"
    if cache.exists() and not refresh:
        return Evidence(**json.loads(cache.read_text(encoding="utf-8")))
    _, home = PORTALS[row["portal_id"]]
    urls = [home]
    for url in search_web(f"site:{urlparse(home).netloc} {row['query']}", limit=6):
        if url not in urls:
            urls.append(url)
    pages: list[dict[str, Any]] = []
    for url in urls[:7]:
        status, text, headers = http_get(url)
        pages.append({
            "url": url, "status": status, "content_type": headers.get("content-type", ""),
            "text": re.sub(r"\s+", " ", text)[:30000],
        })
    raw = json.dumps(pages, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ev = Evidence(row["portal_id"], row["query_id"], urls, pages,
                  time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                  hashlib.sha256(raw).hexdigest())
    cache.write_text(json.dumps(asdict(ev), ensure_ascii=False, indent=2), encoding="utf-8")
    return ev


def ollama_tags(base: str) -> list[str]:
    status, text, _ = http_get(base.rstrip("/") + "/api/tags", timeout=10, max_bytes=200000)
    if status != 200:
        raise RuntimeError(f"Ollama is not reachable at {base}")
    data = json.loads(text)
    return [m["name"] for m in data.get("models", [])]


def choose_models(tags: list[str], cfg: dict[str, Any]) -> dict[str, str]:
    if not tags:
        raise RuntimeError("No Ollama models installed")
    explicit = (cfg.get("roles") or {})
    env = {role: os.getenv("AEO_MODEL_" + role.upper()) for role in ROLE_PROMPTS}
    fallback: list[str] = []
    for wanted in ["gemma", "qwen", "llama", "mistral", "deepseek"]:
        fallback.extend([t for t in tags if wanted in t.lower()])
    fallback.extend(tags)
    fallback = list(dict.fromkeys(fallback))
    chosen: dict[str, str] = {}
    for role in ROLE_PROMPTS:
        requested = env.get(role) or explicit.get(role)
        if requested and requested != "auto":
            if requested not in tags:
                raise RuntimeError(f"Configured model '{requested}' for role '{role}' is not installed")
            chosen[role] = requested
        elif role in {"semantic", "judge", "adversarial"}:
            chosen[role] = next((x for x in fallback if "gemma" in x.lower()), fallback[0])
        elif role == "retrieval":
            chosen[role] = next((x for x in fallback if "qwen" in x.lower()), fallback[0])
        else:
            chosen[role] = fallback[0]
    return chosen


def repeat_model_map(tags: list[str], primary: dict[str, str], repeat: int) -> dict[str, str]:
    families = list(dict.fromkeys(tags))
    if len(families) < 2:
        return primary
    alt = families[(repeat - 1) % len(families)]
    out = dict(primary)
    if repeat > 1:
        for role in ["semantic", "judge", "adversarial"]:
            out[role] = alt
    return out


def ollama_chat(base: str, model: str, system: str, user: str, timeout: float, temperature: float) -> dict[str, Any]:
    payload = json.dumps({
        "model": model, "stream": False, "format": "json",
        "options": {"temperature": temperature},
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
    }).encode("utf-8")
    req = Request(base.rstrip("/") + "/api/chat", data=payload, headers={"Content-Type": "application/json"})
    started = time.perf_counter()
    try:
        with urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read().decode("utf-8"))
    except Exception as exc:
        return {"model": model, "ok": False, "error": f"{type(exc).__name__}: {exc}", "elapsed_seconds": round(time.perf_counter() - started, 3)}
    text = data.get("message", {}).get("content", "")
    parsed: Any = None
    parse_error = None
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        parse_error = str(exc)
    return {
        "model": model, "ok": True, "text": text, "json": parsed,
        "parse_error": parse_error, "elapsed_seconds": round(time.perf_counter() - started, 3),
    }


def evidence_prompt(ev: Evidence, query: str, max_chars: int) -> str:
    chunks = []
    for page in ev.pages:
        chunks.append(f"URL: {page['url']}\nSTATUS: {page['status']}\nCONTENT-TYPE: {page['content_type']}\nTEXT:\n{page['text']}")
    prompt = f"QUERY: {query}\n\nFROZEN WEB EVIDENCE (do not browse outside it):\n" + "\n\n---\n\n".join(chunks)
    return prompt[:max_chars]


def validate_agent_json(role: str, value: Any) -> tuple[bool, str | None]:
    if not isinstance(value, dict):
        return False, "response_not_object"
    required = {
        "discovery": {"discovered", "best_url", "confidence", "reason"},
        "semantic": {"selected_indicator_description", "correct", "confidence", "reason", "ambiguity_flags"},
        "retrieval": {"retrievable", "value_found", "period_correct", "geography_correct", "unit_correct", "confidence", "reason"},
        "metadata": {"metadata_complete", "fields_missing", "confidence", "reason"},
        "citation": {"citable", "citation_url", "source_named", "evidence_specific", "confidence", "reason"},
        "judge": {"discovery_success", "retrieval_success", "temporal_geographic_correctness", "semantic_correctness", "metadata_correctness", "citation_correctness", "overall_0_100", "decisive_reason"},
        "adversarial": {"attack_found", "severity", "alternative_interpretation", "verdict", "reason"},
    }[role]
    missing = sorted(required - value.keys())
    return (True, None) if not missing else (False, "missing_keys:" + ",".join(missing))


def run_one(base: str, row: dict[str, str], ev: Evidence, models: dict[str, str], cfg: dict[str, Any]) -> dict[str, Any]:
    evidence = evidence_prompt(ev, row["query"], int(cfg["ollama"].get("max_context_chars", 18000)))
    result: dict[str, Any] = {"query": row, "evidence_sha256": ev.sha256, "agents": {}}
    prior: dict[str, Any] = {}
    for role in ["discovery", "semantic", "retrieval", "metadata", "citation"]:
        ans = ollama_chat(base, models[role], ROLE_PROMPTS[role], evidence, float(cfg["ollama"].get("timeout_seconds", 180)), float(cfg["ollama"].get("temperature", 0.0)))
        valid, schema_error = validate_agent_json(role, ans.get("json"))
        ans["schema_valid"] = valid
        ans["schema_error"] = schema_error
        result["agents"][role] = ans
        prior[role] = ans.get("json") if valid else {"schema_error": schema_error, "raw": ans.get("text", "")}
    judge_context = evidence + "\n\nCANDIDATE AGENT OUTPUTS:\n" + json.dumps(prior, ensure_ascii=False, indent=2)
    judge = ollama_chat(base, models["judge"], ROLE_PROMPTS["judge"], judge_context[:int(cfg["ollama"].get("max_context_chars", 18000))], float(cfg["ollama"].get("timeout_seconds", 180)), float(cfg["ollama"].get("temperature", 0.0)))
    valid, schema_error = validate_agent_json("judge", judge.get("json")); judge["schema_valid"] = valid; judge["schema_error"] = schema_error
    result["agents"]["judge"] = judge
    candidate = judge.get("json") if valid else {"schema_error": schema_error, "raw": judge.get("text", "")}
    adversarial_context = evidence + "\n\nCANDIDATE JUDGEMENT:\n" + json.dumps(candidate, ensure_ascii=False, indent=2)
    adversarial = ollama_chat(base, models["adversarial"], ROLE_PROMPTS["adversarial"], adversarial_context[:int(cfg["ollama"].get("max_context_chars", 18000))], float(cfg["ollama"].get("timeout_seconds", 180)), float(cfg["ollama"].get("temperature", 0.0)))
    valid, schema_error = validate_agent_json("adversarial", adversarial.get("json")); adversarial["schema_valid"] = valid; adversarial["schema_error"] = schema_error
    result["agents"]["adversarial"] = adversarial
    return result


def flatten(result: dict[str, Any], repeat: int, models: dict[str, str]) -> dict[str, Any]:
    judge = result["agents"].get("judge", {}).get("json") or {}
    adv = result["agents"].get("adversarial", {}).get("json") or {}
    q = result["query"]
    return {
        "query_id": q["query_id"], "portal_id": q["portal_id"], "stratum": q["stratum"],
        "query": q["query"], "country": q["country"], "country_code": q["country_code"],
        "repeat": repeat, "judge_model": models["judge"], "semantic_model": models["semantic"],
        "evidence_sha256": result["evidence_sha256"], "overall_0_100": judge.get("overall_0_100"),
        "discovery_success": judge.get("discovery_success"), "retrieval_success": judge.get("retrieval_success"),
        "temporal_geographic_correctness": judge.get("temporal_geographic_correctness"),
        "semantic_correctness": judge.get("semantic_correctness"), "metadata_correctness": judge.get("metadata_correctness"),
        "citation_correctness": judge.get("citation_correctness"), "adversarial_verdict": adv.get("verdict"),
        "adversarial_severity": adv.get("severity"),
        "schema_failures": sum(1 for a in result["agents"].values() if not a.get("schema_valid", False)),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434"))
    ap.add_argument("--repeats", type=int)
    ap.add_argument("--refresh-evidence", action="store_true")
    ap.add_argument("--max-queries", type=int)
    args = ap.parse_args()
    cfg = load_config()
    repeats = args.repeats or int(cfg["ollama"].get("repeat_runs", 3))
    if repeats < 1:
        raise ValueError("--repeats must be >= 1")
    if not BANK.exists():
        raise FileNotFoundError(f"Canonical query bank missing: {BANK}")
    rows = list(csv.DictReader(BANK.open(encoding="utf-8")))
    validate_bank(rows)
    if args.max_queries:
        rows = rows[: args.max_queries]
    tags = ollama_tags(args.base)
    primary_models = choose_models(tags, cfg)
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ollama": args.base, "models_available": tags, "primary_role_models": primary_models,
        "repeats": repeats, "n_queries": len(rows), "n_executions": len(rows) * repeats,
        "evidence_policy": "frozen_per_query_portal", "temperature": cfg["ollama"].get("temperature", 0.0),
    }
    (OUT / "run_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    jsonl = OUT / "results.jsonl"; csvp = OUT / "results.csv"
    if jsonl.exists(): jsonl.unlink()
    flat_rows: list[dict[str, Any]] = []
    for i, row in enumerate(rows, 1):
        ev = evidence_for(row, args.refresh_evidence)
        for repeat in range(1, repeats + 1):
            models = repeat_model_map(tags, primary_models, repeat)
            result = run_one(args.base, row, ev, models, cfg)
            result["repeat"] = repeat; result["models"] = models
            with jsonl.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(result, ensure_ascii=False) + "\n")
            flat_rows.append(flatten(result, repeat, models))
            print(f"[{i}/{len(rows)}] {row['query_id']} {row['portal_id']} repeat={repeat}", flush=True)
    fields = list(flat_rows[0].keys()) if flat_rows else []
    with csvp.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields); writer.writeheader(); writer.writerows(flat_rows)
    print(json.dumps({"completed": len(flat_rows), "results": str(csvp), "models": primary_models}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
