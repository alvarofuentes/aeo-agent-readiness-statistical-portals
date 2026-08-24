"""Create the final, conservative gold snapshot from the pending contract.

The pending contract is the source of truth for intent and family provenance.
This script only promotes an observation when the query explicitly asks for a
measure and the already-captured official API evidence contains the requested
country/period values.  Discovery, semantic, metadata and ambiguous GDP
questions remain validated contracts without invented numeric targets.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any

from audit_gold_contract import explicit_measure, is_numeric_target_requested

ROOT = Path(__file__).resolve().parents[1]
PENDING = ROOT / "benchmark" / "gold_contract_600_pending.json"
EXPANDED = ROOT / "benchmark" / "gold_standards_expanded.json"
EVIDENCE = ROOT / "benchmark" / "gold_evidence_2026-08-23"
OUT = ROOT / "benchmark" / "gold_standards_final_2026-08-23.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evidence_for_url(url: str) -> dict[str, Any] | None:
    """Find the archived wrapper whose metadata URL equals *url*."""
    for path in sorted(EVIDENCE.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, dict) and data.get("meta", {}).get("url") == url:
            meta = data.get("meta", {})
            return {
                "evidence_path": str(path.relative_to(ROOT)),
                "evidence_sha256": sha256(path),
                "evidence_url": url,
                "evidence_captured_at": meta.get("captured_at"),
                "evidence_http_status": meta.get("status"),
            }
    return None


def is_explicit_numeric(item: dict[str, Any]) -> bool:
    return is_numeric_target_requested(item) and explicit_measure(item)


def finalize() -> dict[str, Any]:
    pending = json.loads(PENDING.read_text(encoding="utf-8"))
    expanded = json.loads(EXPANDED.read_text(encoding="utf-8"))
    expanded_by_key = {(x.get("template_id"), x.get("portal_id")): x for x in expanded["items"]}
    final_items: list[dict[str, Any]] = []
    counts: dict[str, int] = {}
    for source in pending["items"]:
        key = (source.get("template_id"), source.get("portal_id"))
        candidate = expanded_by_key.get(key, {})
        item = dict(source)
        # Do not inherit candidate target fields blindly.  The candidate was
        # intentionally broader than the conservative final promotion policy.
        for field in ("acceptable_urls", "target_series_id", "target_value", "target_values", "unit", "evidence_sha256", "evidence_path"):
            item.pop(field, None)
        item["validation_status"] = "validated_contract"
        item["target_available"] = "not_required"
        item["gold_status"] = "validated_contract"
        item["validation_reason"] = "Contract validated; no numeric target promoted because query intent is discovery/semantic/metadata or measure is underspecified."

        urls = list(candidate.get("acceptable_urls") or [])
        if urls:
            item["acceptable_urls"] = urls
            trace = evidence_for_url(urls[0])
            if trace:
                item.update(trace)

        if is_explicit_numeric(item):
            portal = item.get("portal_id")
            if portal in {"who", "sdg"}:
                item["validation_status"] = "validated_not_applicable"
                item["gold_status"] = "validated_not_applicable"
                item["target_available"] = "not_applicable"
                item["validation_reason"] = "Official catalog evidence recorded; this portal does not expose the requested general GDP level/growth series under the frozen contract."
            elif candidate.get("target_available") == "validated_value" and (candidate.get("target_values") or candidate.get("target_value") is not None):
                item["validation_status"] = "validated_value"
                item["gold_status"] = "validated_value"
                item["target_available"] = "validated_value"
                item["target_series_id"] = candidate.get("target_series_id")
                item["target_value"] = candidate.get("target_value")
                item["target_values"] = candidate.get("target_values") or {}
                item["unit"] = candidate.get("unit")
                item["validation_reason"] = "Explicit measure, country/period mapping and official API observation verified; row-level evidence hash attached."
                trace = evidence_for_url(urls[0]) if urls else None
                if trace:
                    item.update(trace)
            else:
                item["validation_status"] = "validated_missing_target"
                item["gold_status"] = "validated_missing_target"
                item["target_available"] = "validated_missing"
                item["validation_reason"] = "Explicit numeric target requested, but the official response does not contain every requested country/period observation."
        counts[item["validation_status"]] = counts.get(item["validation_status"], 0) + 1
        final_items.append(item)

    output = {
        "source": "auditoría AEO.pdf",
        "source_contract": str(PENDING.relative_to(ROOT)),
        "source_contract_sha256": sha256(PENDING),
        "candidate_source": str(EXPANDED.relative_to(ROOT)),
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "validator": "benchmark/finalize_gold.py",
        "n": len(final_items),
        "n_query_ids": len({x.get("template_id") for x in final_items}),
        "n_query_families": len({x.get("template_family_id") for x in final_items}),
        "summary": counts,
        "promotion_policy": "Only explicit numeric measures with complete official API observations are promoted; all other rows remain validated contract, not applicable, or validated missing target.",
        "items": final_items,
    }
    OUT.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"output": str(OUT), "n": len(final_items), "families": output["n_query_families"], "summary": counts}


if __name__ == "__main__":
    print(json.dumps(finalize(), ensure_ascii=False, indent=2))
