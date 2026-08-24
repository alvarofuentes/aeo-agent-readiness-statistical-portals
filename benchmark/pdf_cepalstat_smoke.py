"""Run the five CEPALSTAT cases named explicitly by the source PDF.

The frozen homepage evidence is reused only as a diagnostic control; this does
not claim that a series or value was discovered.
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

from natural_schema_smoke import call

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "benchmark" / "results"
CASES = [
    ("Q-CEPAL-01", "PIB total de Chile en 2024"),
    ("Q-CEPAL-02", "PIB de Chile en 2024 a precios constantes"),
    ("Q-CEPAL-03", "PIB por habitante de Chile en 2024"),
    ("Q-CEPAL-04", "tasa de crecimiento del PIB de Chile en 2024"),
    ("Q-CEPAL-05", "comparar PIB total de Chile y Argentina en 2024"),
]


def main() -> int:
    evidence = json.loads((RESULTS / "smoke_evidence_Q049_cepalstat.json").read_text(encoding="utf-8"))
    evidence_text = "\n\n---\n\n".join(f"URL: {p['url']}\nSTATUS: {p['status']}\nTEXT:\n{p['text']}" for p in evidence["pages"])
    output = {"generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "model": "gemma4:latest", "evidence_sha256": evidence["sha256"], "items": []}
    for case_id, query in CASES:
        prompt = f"QUERY: {query}\n\nFROZEN EVIDENCE:\n{evidence_text}\n\nUse only the evidence. Say whether the exact value/series is available, give the most specific official URL if present, and state missing unit, period, geography, metadata and source."
        free = call(prompt, structured=False)
        structured = call(prompt + "\nReturn one JSON object with keys: available, best_url, indicator, value, unit, period, geography, source, missing_fields, reason.", structured=True)
        text = free.get("text", "")
        output["items"].append({"case_id": case_id, "query": query, "free_form": free, "structured": structured, "diagnostic_signals": {"free_form_contains_url": bool(re.search(r"https?://", text)), "free_form_is_json": free.get("parse_error") is None and free.get("json") is not None, "structured_key_count": len(structured.get("json") or {}) if isinstance(structured.get("json"), dict) else 0}})
        print(case_id, flush=True)
    path = RESULTS / "pdf_cepalstat_natural_vs_structured_2026-08-22.json"
    path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

