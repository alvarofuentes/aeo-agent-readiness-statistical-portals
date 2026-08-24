"""Fail-closed descriptive analysis for the two-portal pilot scope.

This is intentionally separate from production_analysis.py: a 360-row pilot
must never be mistaken for the PDF's five-portal, 1,800-execution result.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "execution" / "expanded-audit-matrix-2026-08-22.csv"
ROLES = ["discovery", "semantic", "retrieval", "metadata", "citation", "judge", "adversarial"]


def score(row: dict) -> float | None:
    value = (row.get("score") or {}).get("overall_0_100_recomputed")
    try:
        return float(value) if value is not None and math.isfinite(float(value)) else None
    except (TypeError, ValueError):
        return None


def aeo_scores() -> dict[str, float]:
    mapping = {"World Bank Open Data": "worldbank", "WHO Data": "who", "CEPALSTAT": "cepalstat", "UN Data Commons (UNSD)": "undata", "UN SDG Indicators": "sdg"}
    with MATRIX.open(encoding="utf-8", newline="") as fh:
        return {mapping[row["portal"]]: float(row["score"]) for row in csv.DictReader(fh) if mapping.get(row["portal"]) }


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("run_dir", type=Path); parser.add_argument("--allow-natural-gaps", action="store_true", help="diagnostic only: write results while marking missing natural captures as HOLD") ; args = parser.parse_args()
    run_dir = args.run_dir.resolve(); manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
    expected = manifest.get("expected", {}); portals = manifest.get("scope") and manifest.get("portal_scope") or manifest.get("portals")
    portals = manifest.get("portal_scope") or ["cepalstat", "sdg"]
    if manifest.get("status") != "COMPLETE" or expected.get("executions") != 360 or expected.get("templates") != 60 or expected.get("portals") != 2:
        raise SystemExit("PILOT HOLD: require COMPLETE scope with 60 templates, two portals and 360 executions")
    rows = [json.loads(line) for line in (run_dir / "results.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    templates = expected["templates"]; repeats = expected["repeats"]
    expected_keys = {f"pass{p}__Q{q:03d}__{portal}__repeat{r}" for p, portal in enumerate(portals, 1) for q in range(1, 121) for r in range(1, repeats + 1)}
    # The pilot bank preserves sparse canonical Q IDs; derive the actual IDs.
    bank = ROOT / manifest["bank_file"]
    query_ids = [row["query_id"] for row in csv.DictReader(bank.open(encoding="utf-8", newline=""))]
    expected_keys = {f"pass{p}__{query_id}__{portal}__repeat{r}" for p, portal in enumerate(portals, 1) for query_id in query_ids for r in range(1, repeats + 1)}
    observed = [row.get("execution_key") for row in rows]
    if len(rows) != 360 or len(set(observed)) != 360 or set(observed) != expected_keys:
        raise SystemExit("PILOT HOLD: rows/keys do not match the 360-execution pilot contract")
    values: dict[str, list[float]] = defaultdict(list); repeat_values: dict[tuple[str, int], list[float]] = defaultdict(list); adv = Counter()
    evidence_counts = Counter()
    natural_gaps = []
    natural_by_role = Counter()
    for row in rows:
        if row.get("status") != "OK" or any((row.get("agents") or {}).get(role, {}).get("schema_valid") is not True for role in ROLES):
            raise SystemExit(f"PILOT HOLD: invalid role output in {row.get('execution_key')}")
        missing_natural = [role for role in ROLES if (row.get("natural_signals") or {}).get(role, {}).get("available") is not True]
        if missing_natural:
            natural_gaps.append({"execution_key": row.get("execution_key"), "roles": missing_natural})
            natural_by_role.update(missing_natural)
            if not args.allow_natural_gaps:
                raise SystemExit(f"PILOT HOLD: missing natural output in {row.get('execution_key')}")
        value = score(row); portal = (row.get("case") or {}).get("portal_id")
        if value is not None: values[portal].append(value); repeat_values[(portal, int(row["repeat"]))].append(value)
        adv[(portal, (row.get("adversarial") or {}).get("verdict") or "NA")] += 1
        # Keep discovery/retrieval/citation separate. A schema-valid answer
        # about a frozen homepage is not evidence that the requested series
        # was discovered or cited.
        if row.get("candidate_url"):
            evidence_counts["candidate_url"] += 1
        if row.get("candidate_allowed") is True:
            evidence_counts["candidate_allowed"] += 1
        if (row.get("retrieval") or {}).get("retrievable") is True or (row.get("case") or {}).get("retrievable") is True:
            evidence_counts["retrievable"] += 1
        if (row.get("citation") or {}).get("citable") is True or (row.get("case") or {}).get("citable") is True:
            evidence_counts["citable"] += 1
    summary = []
    matrix = aeo_scores()
    for portal in portals:
        vals = values[portal]
        summary.append({"portal_id": portal, "aeo_score": matrix[portal], "mean_airsc": statistics.mean(vals) if vals else None, "median_airsc": statistics.median(vals) if vals else None, "stdev_airsc": statistics.stdev(vals) if len(vals) > 1 else 0.0, "n_valid": len(vals), "n_total": 180, "coverage": len(vals) / 180, "adversarial": {k[1]: v for k, v in adv.items() if k[0] == portal}})
    unique_query_texts = len({row["query"] for row in csv.DictReader(bank.open(encoding="utf-8", newline=""))})
    adversarial_clear = all((row.get("adversarial") or {}).get("verdict") == "pass" for row in rows)
    evidence_status = "PASS" if evidence_counts["candidate_url"] else "HOLD_NO_SPECIFIC_DISCOVERY"
    if natural_gaps:
        qa_status = "HOLD_NATURAL_CAPTURE"
    elif not adversarial_clear and evidence_counts["candidate_url"] == 0:
        qa_status = "HOLD_EVIDENCE_AND_ADVERSARIAL"
    elif not adversarial_clear:
        qa_status = "HOLD_ADVERSARIAL"
    elif evidence_counts["candidate_url"] == 0:
        qa_status = "HOLD_NO_SPECIFIC_DISCOVERY"
    else:
        qa_status = "PASS"
    result = {"scope": "pilot_extremes", "run_dir": str(run_dir), "n_rows": 360, "n_templates": 60, "n_unique_query_texts": unique_query_texts, "diversity_status": "QUALIFIED" if unique_query_texts < 60 else "PASS", "diversity_note": "60 template rows contain repeated source-provenance copies; interpret as a runtime pilot, not 60 independent semantic intents." if unique_query_texts < 60 else "60 unique query texts.", "portals": portals, "portal_summary": summary, "repeat_summary": [{"portal_id": p, "repeat": r, "mean_airsc": statistics.mean(v) if v else None, "n_valid": len(v)} for (p, r), v in sorted(repeat_values.items())], "interpretation": "descriptive pilot; no correlation or causal claim with n=2 portals", "mechanical_qa_status": "PASS" if not natural_gaps else "HOLD_NATURAL_CAPTURE", "qa_status": qa_status, "publication_status": "PASS" if qa_status == "PASS" and unique_query_texts >= 60 else "HOLD", "evidence_status": evidence_status, "evidence_counts": dict(evidence_counts), "adversarial_clear": adversarial_clear, "natural_gap_rows": len(natural_gaps), "natural_gap_by_role": dict(natural_by_role), "natural_gap_examples": natural_gaps[:20]}
    out = run_dir / "analysis"; out.mkdir(exist_ok=True)
    (out / "pilot_analysis.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    with (out / "pilot_portal_summary.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["portal_id", "aeo_score", "mean_airsc", "median_airsc", "stdev_airsc", "n_valid", "n_total", "coverage", "adversarial"]); writer.writeheader()
        for row in summary: writer.writerow({**row, "adversarial": json.dumps(row["adversarial"], ensure_ascii=False, sort_keys=True)})
    lines = ["# Pilot AEO–visibilidad: CEPALSTAT vs UN SDG", "", "Este informe es descriptivo y no reemplaza el benchmark PDF de cinco portales.", "", f"**QA mecánica:** {result['mechanical_qa_status']} · **QA editorial:** {result['qa_status']} · **publicación:** {result['publication_status']}.", "", "| Portal | AEO | AIRSC medio | Mediana | SD | Cobertura |", "|---|---:|---:|---:|---:|---:|"]
    for row in summary: lines.append(f"| {row['portal_id']} | {row['aeo_score']:.0f} | {row['mean_airsc']:.2f} | {row['median_airsc']:.2f} | {row['stdev_airsc']:.2f} | {row['n_valid']}/{row['n_total']} |")
    lines += ["", "## Alcance", "", f"60 filas de plantilla estratificadas × 2 portales × 3 repeticiones = 360 ejecuciones. Se observaron {unique_query_texts} textos de consulta únicos: las filas conservan copias de procedencia del banco heredado. La comparación contrasta extremos técnicos; no calcula una correlación inferencial con n=2 portales."]
    if unique_query_texts < 60:
        lines += ["", "## QA: diversidad de consultas", "", f"**QUALIFIED_DIVERSITY**: el banco tiene 60 filas, pero sólo {unique_query_texts} textos únicos. Este resultado sirve para validar runtime, evidencia, schema y separación de roles; no debe presentarse como muestra de 60 intenciones semánticas independientes."]
    if natural_gaps:
        lines += ["", "## QA: captura natural", "", f"**HOLD_NATURAL_CAPTURE**: {len(natural_gaps)} filas tienen al menos un rol natural no disponible (por errores de transporte del endpoint local). Los resultados estructurados se conservan para diagnóstico, pero esta salida no es un cierre metodológico completo."]
    if not evidence_counts["candidate_url"]:
        lines += ["", "## QA: descubrimiento específico", "", "**HOLD_NO_SPECIFIC_DISCOVERY**: las 360 ejecuciones conservaron evidencia de la homepage, pero no una URL específica aceptada desde la evidencia congelada. AIRSC debe leerse como diagnóstico de respuesta ante evidencia insuficiente, no como medición de ranking o visibilidad orgánica."]
    if not adversarial_clear:
        lines += ["", "## QA: red team", "", "**HOLD_ADVERSARIAL**: el adversarial no produjo veredictos `pass` en todas las filas; los estados `uncertain` no se convierten en aprobación editorial."]
    lines += ["", "## Siguiente decisión", "", "No ampliar todavía: resolver primero HOLD_NO_SPECIFIC_DISCOVERY/HOLD_ADVERSARIAL con evidencia de series/API y un red-team concluyente. Sólo después decidir si se agregan World Bank, WHO y UN Data Commons para ejecutar el contrato completo de 120 × 5 × 3 = 1.800."]
    (out / "pilot_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"analysis": str(out / "pilot_analysis.json"), "summary": str(out / "pilot_portal_summary.csv")}, ensure_ascii=False, indent=2)); return 0


if __name__ == "__main__":
    raise SystemExit(main())
