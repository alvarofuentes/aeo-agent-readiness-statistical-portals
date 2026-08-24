#!/usr/bin/env python3
"""Verify CEPALSTAT's machine-readable export path without changing E2E rows.

This is a focused technical review. It checks the public API's ``format=excel``
response, preserves the returned XLSX, and reads the workbook XML with the
standard library so the selected indicator, dimensions, value, unit and source
can be audited without treating HTML JSON-LD as the only form of structure.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen


NS = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def inline_text(cell: ET.Element) -> str:
    return " ".join((node.text or "") for node in cell.findall(".//x:t", NS)).strip()


def read_first_sheet(path: Path) -> dict[str, object]:
    """Return sheet names and first rows from an XLSX archive."""
    import zipfile

    with zipfile.ZipFile(path) as archive:
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        sheets = [sheet.attrib.get("name", "") for sheet in workbook.findall(".//x:sheet", NS)]
        sheet_path = "xl/worksheets/sheet1.xml"
        root = ET.fromstring(archive.read(sheet_path))
        rows = []
        for row in root.findall(".//x:row", NS)[:5]:
            values = []
            for cell in row.findall("x:c", NS):
                if cell.attrib.get("t") == "inlineStr":
                    values.append(inline_text(cell))
                else:
                    value = cell.find("x:v", NS)
                    values.append((value.text or "") if value is not None else "")
            rows.append(values)
    return {"sheet_names": sheets, "first_sheet_rows": rows}


def fetch(url: str, output: Path) -> dict[str, object]:
    started = time.perf_counter()
    request = Request(url, headers={"User-Agent": "AEO-CEPALSTAT-Export-Review/1.0", "Accept": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"})
    with urlopen(request, timeout=60) as response:
        body = response.read()
        headers = {str(k): str(v) for k, v in response.headers.items()}
        status = int(response.status)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(body)
    parsed = read_first_sheet(output)
    first_row = parsed["first_sheet_rows"][1] if len(parsed["first_sheet_rows"]) > 1 else []
    return {
        "requested_url": url,
        "captured_at": now_iso(),
        "http_status": status,
        "content_type": headers.get("Content-Type", ""),
        "content_disposition": headers.get("Content-Disposition", ""),
        "bytes": len(body),
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "sha256": hashlib.sha256(body).hexdigest(),
        "artifact_path": str(output),
        "artifact_type": "xlsx" if body[:2] == b"PK" else "unknown",
        **parsed,
        "selection_preserved_in_first_row": bool(first_row),
    }


def run_review(run_dir: Path) -> dict[str, object]:
    export_dir = run_dir / "evidence" / "exports"
    cases = {
        "indicator_2203_CHL_2024": "https://api-cepalstat.cepal.org/cepalstat/api/v1/indicator/2203/data?lang=es&format=excel&in=1&path=1&members=224%2C29194",
        "indicator_2800_default": "https://api-cepalstat.cepal.org/cepalstat/api/v1/indicator/2800/data?lang=es&format=excel&in=1&path=1",
        "indicator_4271_default": "https://api-cepalstat.cepal.org/cepalstat/api/v1/indicator/4271/data?lang=es&format=excel&in=1&path=1",
    }
    observations = []
    for label, url in cases.items():
        artifact = export_dir / f"{label}.xlsx"
        observations.append(fetch(url, artifact))
    for observation in observations:
        artifact = Path(observation["artifact_path"])
        observation["artifact_path"] = str(artifact.relative_to(run_dir))
        observation["content_type_ok"] = observation["content_type"].lower().startswith("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        observation["http_ok"] = observation["http_status"] == 200
        observation["workbook_ok"] = observation["artifact_type"] == "xlsx" and bool(observation["sheet_names"])
    result = {
        "portal_id": "cepalstat",
        "review_type": "machine_readable_data_export",
        "captured_at": now_iso(),
        "protocol_note": "This evidence is separate from embedded HTML JSON-LD/microdata. It tests the API's Excel export and selected dimensions.",
        "status": "PASS" if all(o["http_ok"] and o["content_type_ok"] and o["workbook_ok"] for o in observations) else "NOT_VERIFIED",
        "observations": observations,
    }
    output = run_dir / "evidence" / "technical" / "cepalstat_export_review.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args()
    result = run_review(args.run_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
