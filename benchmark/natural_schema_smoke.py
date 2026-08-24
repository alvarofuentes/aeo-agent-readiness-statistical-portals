"""Compare free-form and JSON-constrained answers on the frozen CEPALSTAT smoke.

The comparison is diagnostic only.  It never turns schema compliance into a
semantic score and preserves both raw responses for manual review.
"""
from __future__ import annotations

import csv
import json
import re
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "benchmark" / "results"
MODEL = "gemma4:latest"
BASE = "http://127.0.0.1:11434"
IDS = ["Q049", "Q050", "Q051", "Q052", "Q053"]


def call(prompt: str, structured: bool) -> dict:
    payload = {
        "model": MODEL,
        "stream": False,
        "options": {"temperature": 0},
        "messages": [
            {"role": "system", "content": "You are a statistical data retrieval assistant. Preserve uncertainty and do not invent values."},
            {"role": "user", "content": prompt},
        ],
    }
    if structured:
        payload["format"] = "json"
    started = time.perf_counter()
    req = Request(BASE + "/api/chat", data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=180) as response:
            data = json.loads(response.read().decode("utf-8"))
        text = data.get("message", {}).get("content", "")
        parsed = None
        parse_error = None
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            parse_error = str(exc)
        return {"ok": True, "text": text, "json": parsed, "parse_error": parse_error, "elapsed_seconds": round(time.perf_counter() - started, 3)}
    except HTTPError as exc:
        return {"ok": False, "http_status": exc.code, "error": exc.read().decode(errors="replace"), "elapsed_seconds": round(time.perf_counter() - started, 3)}
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}", "elapsed_seconds": round(time.perf_counter() - started, 3)}


def main() -> int:
    rows = {r["query_id"]: r for r in csv.DictReader((ROOT / "benchmark/query-bank-120.csv").open(encoding="utf-8"))}
    output = {"generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "model": MODEL, "base": BASE, "items": []}
    for query_id in IDS:
        row = rows[query_id]
        evidence_path = RESULTS / f"smoke_evidence_{query_id}_cepalstat.json"
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        evidence_text = "\n\n---\n\n".join(f"URL: {p['url']}\nSTATUS: {p['status']}\nTEXT:\n{p['text']}" for p in evidence["pages"])
        prompt = (
            f"QUERY: {row['query']}\n\nFROZEN EVIDENCE:\n{evidence_text}\n\n"
            "Answer using only the frozen evidence. State whether the exact indicator/value is available, "
            "include the most specific official URL if present, and identify missing unit, period, geography or metadata."
        )
        free = call(prompt, structured=False)
        structured = call(prompt + "\nReturn one JSON object with keys: available, best_url, indicator, value, unit, period, geography, source, missing_fields, reason.", structured=True)
        free_text = free.get("text", "")
        output["items"].append({
            "query_id": query_id,
            "portal_id": row["portal_id"],
            "query": row["query"],
            "evidence_sha256": evidence["sha256"],
            "free_form": free,
            "structured": structured,
            "diagnostic_signals": {
                "free_form_contains_url": bool(re.search(r"https?://", free_text)),
                "free_form_contains_indicator_language": bool(re.search(r"PIB|producto interno bruto|GDP", free_text, re.I)),
                "free_form_is_json": free.get("parse_error") is None and free.get("json") is not None,
                "structured_schema_key_count": len(structured.get("json") or {}) if isinstance(structured.get("json"), dict) else 0,
            },
        })
        print(query_id, flush=True)
    path = RESULTS / "cepalstat_natural_vs_structured_2026-08-22.json"
    path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

