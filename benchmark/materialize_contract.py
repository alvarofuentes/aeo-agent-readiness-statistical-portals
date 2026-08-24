"""Materialize the PDF's 120-template / five-portal execution contract."""
from __future__ import annotations

import csv
import json
from pathlib import Path

from .runner_production import PORTAL_IDS, expand_rows, load_rows

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    rows = load_rows()
    template_path = ROOT / "benchmark" / "query-templates-120.csv"
    fields = ["query_id", "source_portal_id", "template_family_id", "stratum", "query", "country", "country_code"]
    with template_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows({key: row[key] for key in fields} for row in rows)
    expanded = expand_rows(rows, None)
    manifest = {
        "source_of_truth": "auditoría AEO.pdf",
        "template_file": str(template_path),
        "n_templates": len(rows),
        "n_portals": len(PORTAL_IDS),
        "n_query_portal_pairs": len(expanded),
        "repeats": 3,
        "expected_executions": len(expanded) * 3,
        "unique_template_families": len({row["template_family_id"] for row in rows}),
        "duplicate_family_note": "The source CSV contains 120 IDs but 24 repeated text families; retain family_id for clustered sensitivity analysis.",
        "status": "READY_WITH_CLUSTERED_FAMILY_WARNING",
    }
    (ROOT / "benchmark" / "execution-contract-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
