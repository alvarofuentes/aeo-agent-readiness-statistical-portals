#!/usr/bin/env python3
"""Build evidence-backed Markdown/CSV/JSON editorial outputs for a fresh run."""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

WEIGHTS = {
    "discovery": 15,
    "retrieval": 25,
    "rendering": 20,
    "structured_data": 15,
    "authority_citation": 15,
    "accessibility": 10,
}

DIMENSION_LABELS = {
    "discovery": "Descubrimiento técnico",
    "retrieval": "API y acceso de datos",
    "rendering": "Renderizado/interacción",
    "structured_data": "Marcado HTML estructurado",
    "authority_citation": "Autoridad/cita",
    "accessibility": "Accesibilidad",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})


def compact(value: Any, limit: int = 700) -> str:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True) if isinstance(value, (dict, list)) else str(value or "")
    return text if len(text) <= limit else text[:limit] + "..."


def technical_rows(run_dir: Path, source_run: str | None = None) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    probes = []
    for path in sorted((run_dir / "evidence" / "technical").glob("*.json")):
        # The focused CEPALSTAT export review is a technical evidence artifact,
        # not an E2E row. Attach its compact result to each CEPAL probe so the
        # editorial layer can distinguish embedded HTML markup from API/XLSX
        # access without changing the six-dimension score.
        if path.name == "cepalstat_export_review.json":
            continue
        probes.append(read_json(path))
    export_review_path = run_dir / "evidence" / "technical" / "cepalstat_export_review.json"
    if export_review_path.exists():
        review = read_json(export_review_path)
        observations = review.get("observations", [])
        formats = sorted({"xlsx" if str(item.get("artifact_type")) == "xlsx" else str(item.get("artifact_type")) for item in observations})
        selection_case = next((item for item in observations if "indicator/2203/data" in str(item.get("requested_url")) and "members=224" in str(item.get("requested_url"))), None)
        for probe in probes:
            if probe.get("portal_id") != "cepalstat":
                continue
            probe["data_export_status"] = review.get("status", "NOT_VERIFIED")
            probe["data_export_formats"] = formats
            probe["data_export_selection_preserved"] = bool(selection_case and selection_case.get("selection_preserved_in_first_row"))
            # Use an absolute repo path because a combined editorial run may
            # consume the CEPALSTAT probe from a different clean run.
            probe["data_export_evidence_path"] = str(export_review_path.resolve())
            probe["data_export_observations"] = len(observations)
    ledger = []
    for probe in probes:
        for check in probe.get("unverified_checks", []):
            ledger.append({"portal_id": probe.get("portal_id"), "repeat": probe.get("repeat"), **check, "source_run": source_run or run_dir.name, "source_evidence_path": str((run_dir / "evidence" / "technical" / f"{probe.get('portal_id')}__repeat-{probe.get('repeat')}.json").relative_to(run_dir))})
    return probes, ledger


def technical_summary(portal: str, probes: list[dict[str, Any]], rows: list[dict[str, Any]], ledger: list[dict[str, Any]]) -> dict[str, Any]:
    p = [x for x in probes if x.get("portal_id") == portal]
    dim_values = {dim: [x.get("dimensions", {}).get(dim) for x in p] for dim in WEIGHTS}
    score = sum(WEIGHTS[dim] for dim, values in dim_values.items() if any(v == "PASS" for v in values))
    unallocated = sum(WEIGHTS[dim] for dim, values in dim_values.items() if any(v == "NOT_VERIFIED" for v in values) and not any(v == "PASS" for v in values))
    pr = [r for r in rows if r.get("portal_id") == portal]
    direct_calls = [call for r in pr for call in (r.get("calls") or [])]
    direct_ok = bool(direct_calls) and all(c.get("status") == 200 for c in direct_calls)
    latest = p[-1] if p else {}
    return {
        "portal_id": portal,
        "evidence_date": datetime.now(timezone.utc).date().isoformat(),
        "technical_score": score,
        "technical_score_unallocated_weight": unallocated,
        "technical_confidence": "limited" if ledger or unallocated else "high",
        "technical_dimensions": {dim: ("PASS" if any(v == "PASS" for v in values) else "NOT_VERIFIED" if any(v == "NOT_VERIFIED" for v in values) else "ABSENT" if any(v == "ABSENT" for v in values) else "FAIL") for dim, values in dim_values.items()},
        "e2e_queries": len(pr),
        "e2e_passes": sum(r.get("e2e_status") == "PASS" for r in pr),
        "e2e_pass_rate": round(sum(r.get("e2e_status") == "PASS" for r in pr) / len(pr), 4) if pr else None,
        "selection_error_count": sum(r.get("selection_failure_class") == "MODEL_SELECTION_ERROR" for r in pr),
        "selection_error_rate": round(sum(r.get("selection_failure_class") == "MODEL_SELECTION_ERROR" for r in pr) / len(pr), 4) if pr else None,
        "selection_status_pass_rate": round(sum(r.get("selection_status") == "PASS" for r in pr) / len(pr), 4) if pr else None,
        "candidate_count_mean": round(mean([r.get("candidate_count", 0) for r in pr]), 2) if pr else None,
        "specific_url_rate": round(sum(bool(r.get("citation_url")) for r in pr) / len(pr), 4) if pr else None,
        "metadata_complete_rate": round(sum(not (r.get("metadata") or {}).get("missing") for r in pr) / len(pr), 4) if pr else None,
        "citation_reproducible_rate": round(sum(bool(r.get("citation_url")) and r.get("retrieval_status") == "PASS" for r in pr) / len(pr), 4) if pr else None,
        "robots_status": latest.get("well_known", {}).get(next((u for u in latest.get("well_known", {}) if u.endswith("robots.txt")), ""), {}).get("status", "NOT_VERIFIED"),
        "sitemap_status": latest.get("well_known", {}).get(next((u for u in latest.get("well_known", {}) if u.endswith("sitemap.xml")), ""), {}).get("status", "NOT_VERIFIED"),
        "llms_status": latest.get("well_known", {}).get(next((u for u in latest.get("well_known", {}) if u.endswith("llms.txt")), ""), {}).get("status", "NOT_VERIFIED"),
        "jsonld_initial_status": latest.get("jsonld_initial_status", "NOT_VERIFIED"),
        "jsonld_rendered_status": latest.get("jsonld_rendered_status", "NOT_VERIFIED"),
        "jsonld_rendered": latest.get("jsonld_rendered_status", "NOT_VERIFIED"),
        "structured_markup_scope": "embedded_html_initial_and_rendered",
        "api_direct_verified": "PASS" if direct_ok else "NOT_VERIFIED",
        "data_export_status": latest.get("data_export_status", "NOT_TESTED"),
        "data_export_formats": ",".join(latest.get("data_export_formats", [])),
        "data_export_selection_preserved": latest.get("data_export_selection_preserved", "NOT_TESTED"),
        "data_export_evidence_path": latest.get("data_export_evidence_path", ""),
        "unverified_count": len([x for x in ledger if x.get("portal_id") == portal]),
        "status": "verified_sample" if pr and not ledger else "verified_sample_with_unverified_checks",
        "source_evidence_path": "evidence/technical/ and evidence/raw/",
    }


def report_for_portal(portal: str, rows: list[dict[str, Any]], summary: dict[str, Any], ledger: list[dict[str, Any]], run_dir: Path) -> str:
    pr = [r for r in rows if r.get("portal_id") == portal]
    lines = [f"# Evaluación E2E y preparación AEO — {portal}", "", f"**Fecha de evidencia:** {summary['evidence_date']}", f"**Run:** `{run_dir.name}`", "", "## Veredicto", "", f"La prueba operacional recuperó `PASS` en **{summary['e2e_passes']}/{summary['e2e_queries']}** ejecuciones ({summary['e2e_pass_rate']:.1%}). Se registraron **{summary['selection_error_count']}** errores de selección semántica del modelo ({summary['selection_error_rate']:.1%}); esos casos conservan el indicador elegido y su recuperación, sin sustitución automática. La puntuación técnica es **{summary['technical_score']}/100**, con confianza **{summary['technical_confidence']}** y peso no asignado de **{summary['technical_score_unallocated_weight']}** por estados no verificados.", "", "Las capas son independientes: el E2E mide recuperación de una consulta; la capa técnica mide condiciones de acceso y citabilidad. No se suman ni promedian.", "", "## Matriz E2E", "", "| Consulta | Repetición | Candidato | Selección | Recuperación | Valor | Metadatos | Cita | Evidencia |", "|---|---:|---|---|---|---|---|---|---|"]
    for r in pr:
        candidate = r.get("candidate") or {}
        meta = r.get("metadata") or {}
        selection_label = r.get("selection_failure_class") or r.get("selection_status")
        lines.append(f"| {r.get('fresh_template_id')} · {r.get('query','')[:70]} | {r.get('repeat')} | `{candidate.get('id','')}` {str(candidate.get('name',''))[:45]} | **{selection_label}** | **{r.get('retrieval_status')}** | {'sí' if r.get('value_found') else 'no'} | {'completo' if not meta.get('missing') else 'incompleto'} | {'sí' if r.get('citation_url') else 'no'} | `evidence/raw/` |")
    lines += ["", "## Capa técnica", "", "| Dimensión | Resultado | Peso |", "|---|---|---:|"]
    for dim, weight in WEIGHTS.items():
        lines.append(f"| {DIMENSION_LABELS.get(dim, dim)} (`{dim}`) | {summary['technical_dimensions'].get(dim)} | {weight} |")
    lines += ["", "## Instancias no verificadas (ledger obligatorio)", "", "Estas filas no significan ausencia ni fallo del portal. Identifican una observación que todavía no se capturó y la acción mínima para cerrarla.", "", "| Check | Estado | Estado de evidencia | Evidencia observada | Brecha | Próxima acción |", "|---|---|---|---|---|---|"]
    pl = [x for x in ledger if x.get("portal_id") == portal]
    if not pl:
        lines.append("| — | — | — | No quedaron instancias no verificadas en el ledger. | — | — |")
    else:
        for x in pl:
            lines.append(f"| `{x.get('check_id')}` | **{x.get('status')}** | `{x.get('evidence_state')}` | {x.get('observed_evidence','')} | {x.get('verification_gap','')} | {x.get('next_verification_action','')} |")
    lines += ["", "## Acceso estructurado y exportación", "", f"`structured_data={summary['technical_dimensions'].get('structured_data')}` se refiere exclusivamente a marcado embebido en HTML/DOM (JSON-LD, microdatos o equivalente). No significa que el portal carezca de datos estructurados. La prueba de exportación independiente queda en **{summary.get('data_export_status', 'NOT_TESTED')}**, formatos **{summary.get('data_export_formats', '—')}**, con selección preservada **{summary.get('data_export_selection_preserved', 'NOT_TESTED')}**; evidencia: `{summary.get('data_export_evidence_path') or 'no probada en este run'}`.", "", "## Fuentes y trazabilidad", "", "Cada fila conserva la URL oficial consultada, los parámetros y los JSON crudos bajo `evidence/raw/`. La capa técnica incluye una captura del DOM asentado después de JavaScript y una solicitud aislada del registro representativo.", "", "## Limitaciones", "", "- `ABSENT` significa que la comprobación se ejecutó y no encontró el artefacto embebido (por ejemplo, JSON-LD o robots.txt); no equivale a `NOT_VERIFIED` ni a ausencia de API/exportación.", "- El resultado es descriptivo de esta muestra y sus tres repeticiones; no prueba causalidad entre score técnico y visibilidad.", ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--base-run", action="append", type=Path, help="Optional completed clean run to combine with this run. Repeat for multiple source runs.")
    args = parser.parse_args()
    run_dir = args.run_dir
    manifest_path = run_dir / "run_manifest.json"
    if not manifest_path.exists():
        raise SystemExit("missing run_manifest.json")
    manifest = read_json(manifest_path)
    expected = int(manifest.get("expected_executions", 0))
    results_path = run_dir / "results.jsonl"
    current_rows = [json.loads(line) for line in results_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if manifest.get("status") != "COMPLETE" or len(current_rows) != expected:
        raise SystemExit(f"editorial blocked: manifest={manifest.get('status')} rows={len(current_rows)}/{expected}")
    rows = list(current_rows)
    probes, ledger = technical_rows(run_dir, run_dir.name)
    base_runs = args.base_run or []
    source_runs = [run_dir.name]
    for base_run in base_runs:
        base_manifest_path = base_run / "run_manifest.json"
        base_results_path = base_run / "results.jsonl"
        if not base_manifest_path.exists() or not base_results_path.exists():
            raise SystemExit(f"base editorial blocked: missing manifest/results in {base_run}")
        base_manifest = read_json(base_manifest_path)
        base_expected = int(base_manifest.get("expected_executions", 0))
        base_rows = [json.loads(line) for line in base_results_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if base_manifest.get("status") != "COMPLETE" or len(base_rows) != base_expected:
            raise SystemExit(f"base editorial blocked: manifest={base_manifest.get('status')} rows={len(base_rows)}/{base_expected} in {base_run}")
        base_probes, base_ledger = technical_rows(base_run, base_run.name)
        rows = base_rows + rows
        probes = base_probes + probes
        ledger = base_ledger + ledger
        source_runs.insert(0, base_run.name)
    base_portals = []
    for base_run in base_runs:
        base_portals.extend(read_json(base_run / "run_manifest.json").get("portals", []))
    portals = tuple(dict.fromkeys(base_portals + manifest.get("portals", [])))
    if not portals:
        raise SystemExit("editorial blocked: no portals in manifest")
    out = run_dir / "editorial"
    out.mkdir(parents=True, exist_ok=True)
    fields = ["execution_id", "fresh_template_id", "source_template_id", "portal_id", "repeat", "stratum", "query", "candidate", "candidate_count", "selection_mode", "selection_status", "selection_failure_class", "selection_error", "model_candidate_rejected", "e2e_status", "model", "model_endpoint", "model_ok", "retrieval_status", "value_found", "values", "rows_returned", "metadata", "citation_url", "calls", "elapsed_seconds", "evidence_policy"]
    matrix = []
    for r in rows:
        matrix.append({**r, "candidate": compact(r.get("candidate")), "values": compact(r.get("values")), "metadata": compact(r.get("metadata")), "calls": compact(r.get("calls"))})
    write_csv(out / f"execution_matrix_{len(rows)}.csv", matrix, fields)
    summary_rows = []
    tech_rows = []
    summaries = {}
    for portal in portals:
        summary = technical_summary(portal, probes, rows, ledger)
        summaries[portal] = summary
        summary_rows.append(summary)
        tech_rows.append(summary)
        (out / f"report-{portal}-30x2x3.md").write_text(report_for_portal(portal, rows, summary, ledger, run_dir), encoding="utf-8")
    summary_fields = list(summary_rows[0])
    write_csv(out / "portal_summary.csv", summary_rows, summary_fields)
    ledger_fields = ["portal_id", "repeat", "check_id", "status", "evidence_state", "observed_evidence", "verification_gap", "next_verification_action", "source_run", "source_evidence_path"]
    write_csv(out / "unverified_ledger.csv", ledger, ledger_fields)
    write_csv(out / "technical_layer.csv", tech_rows, list(tech_rows[0]))
    write_json(out / "technical_layer.json", tech_rows)
    comparison = [f"# Comparativo E2E — {' · '.join(portals)}", "", f"**Run editorial:** `{run_dir.name}` · **Fuentes:** {', '.join(source_runs)} · **Muestra:** {len(rows)} ejecuciones live", "", "## Resultado separado por capa", "", "| Portal | E2E PASS | E2E rate | Errores selección modelo | Score técnico | Confianza | No verificados | API directa | Exportación estructurada |", "|---|---:|---:|---:|---:|---|---:|---|---|"]
    for portal in portals:
        s = summaries[portal]
        comparison.append(f"| {portal} | {s['e2e_passes']}/{s['e2e_queries']} | {s['e2e_pass_rate']:.1%} | {s['selection_error_count']} ({s['selection_error_rate']:.1%}) | {s['technical_score']}/100 | {s['technical_confidence']} | {s['unverified_count']} | {s['api_direct_verified']} | {s.get('data_export_status', 'NOT_TESTED')} ({s.get('data_export_formats', '—')}) |")
    comparison += ["", "## Dimensiones técnicas", "", "| Portal | Descubrimiento | API/acceso de datos | Renderizado | Marcado HTML estructurado | Autoridad/cita | Accesibilidad |", "|---|---|---|---|---|---|---|"]
    for portal in portals:
        dims = summaries[portal]["technical_dimensions"]
        comparison.append(f"| {portal} | {dims.get('discovery')} | {dims.get('retrieval')} | {dims.get('rendering')} | {dims.get('structured_data')} | {dims.get('authority_citation')} | {dims.get('accessibility')} |")
    comparison += ["", "## Interpretación por portal", ""]
    for portal in portals:
        s = summaries[portal]
        if s["selection_error_count"]:
            reading = f"La recuperación de transporte fue {s['citation_reproducible_rate']:.1%}, pero {s['selection_error_count']}/{s['e2e_queries']} filas conservaron un error de selección semántica; no debe leerse como fallo de API."
        elif s["e2e_pass_rate"] < 1:
            reading = f"La ruta API fue verificable, pero {s['e2e_passes']}/{s['e2e_queries']} filas pasaron el gate completo; las restantes requieren revisar dimensiones/criterio de respuesta."
        else:
            reading = "La muestra pasó selección y recuperación en todas las filas; la lectura técnica queda separada del resultado operacional."
        comparison.append(f"- **{portal}:** {reading} Score técnico {s['technical_score']}/100; `ABSENT` describe ausencia comprobada del marcado HTML embebido y `NOT_VERIFIED` sería una brecha bloqueante.")
    comparison += ["", "## Método y límites", "", f"- Evidencia live por repetición: {len(rows)} ejecuciones agregadas desde {len(source_runs)} manifiestos `COMPLETE`; no se usó gold ni captura congelada para el retrieval.", "- La unidad de comparación es el portal (n=5). Consulta y repetición son medidas agrupadas; estas cifras no demuestran causalidad entre AEO técnico y visibilidad.", "- Una consulta específica puede tener una sola URL correcta. El criterio es indicador + definición + unidad + período + geografía + fuente, no cantidad de enlaces.", "- El incidente de transporte SDG en la corrida v4 se conserva fuera del consolidado; fue verificado con GET aislado y la corrida v5 se relanzó desde cero.", "", "## Próximas acciones", "", "- Priorizar la discriminación explícita de metadatos en CEPALSTAT y repetir sólo después de cambios trazables.", "- Mantener el ledger y las compuertas fail-closed en cualquier ampliación al contrato canónico de 1.800 filas.", "- Ver `recommendations-and-best-practices.md` para mejoras CEPALSTAT y ejemplos de robots.txt/llms.txt.", ""]
    (out / "comparative_report.md").write_text("\n".join(comparison), encoding="utf-8")
    cepal = summaries.get("cepalstat", summaries[portals[0]])
    wb_summary = summaries.get("worldbank", summaries[portals[0]])
    recommendations = [
        "# Recomendaciones editoriales y de implementación",
        "",
        f"**Base:** `{run_dir.name}` · evidencia live de {len(rows)} ejecuciones. Las tasas y estados se calculan desde la matriz; no se convierten estados pendientes en ceros.",
        "",
        "## 1. CEPALSTAT: mejoras prioritarias",
        "",
        "1. **Discriminación de metadatos en la búsqueda:** exponer como campos filtrables y visibles `scope` (país/agregado vs subnacional), geografía, frecuencia, unidad, base de precios y desagregación por actividad. Si aparece `MODEL_SELECTION_ERROR`, la matriz conserva la elección original para medir el coste de esa ambigüedad.",
        "2. **Resultado de búsqueda orientado a series:** devolver ID, etiqueta canónica, definición, unidad, frecuencia, cobertura geográfica, última actualización, fuente y URL/API de la serie en un único resultado.",
        "3. **API de dimensiones explícita:** documentar nombres y códigos de cada dimensión, incluyendo áreas subnacionales, y publicar ejemplos de filtros para una observación nacional y una subnacional.",
        "4. **Citabilidad estable:** enlazar cada serie a una URL canónica que preserve indicador, dimensiones y período; permitir descargar la respuesta JSON con esos parámetros.",
        "5. **Marcado y acceso estructurado:** incorporar JSON-LD/microdatos en HTML inicial o mantener un DOM estable después de JavaScript; esto es distinto de la API y de la exportación XLSX/CSV. La evaluación captura ahora ambas capas y distingue ausencia comprobada de `NOT_VERIFIED`.",
        "6. **Exportación reproducible:** conservar el indicador, dimensiones seleccionadas, unidad, fuente y metadatos en cada XLSX/CSV/JSON descargado; documentar el parámetro de formato y comprobarlo con una solicitud aislada.",
        "",
        "## 2. Prácticas transferibles observadas en portales estadísticos",
        "",
        "- Separar en la interfaz y API el objeto indicador de sus dimensiones; no mezclar nivel, crecimiento y per cápita en etiquetas casi idénticas.",
        "- Hacer que la respuesta de una consulta específica llegue a una serie/observación reproducible, aunque sea una sola URL.",
        "- Mantener una nota de fuente y fecha de actualización junto al valor, no en una pantalla desconectada.",
        "- Probar cada cambio con preguntas naturales que incluyan near-matches: total vs actividad, anual vs trimestral, corriente vs constante y país vs área subnacional.",
        "- World Bank ofrece un patrón claro de indicador estable + API de país/año; UNData expone series AMA con códigos de país M49; SDG exige elegir dimensiones de serie; WHO GHO separa catálogo de indicador y endpoint de observaciones. Estos patrones sirven como ejemplos de diseño, no como equivalencia de cobertura.",
        "",
        "## 3. Ejemplos de archivos de orientación para agentes",
        "",
        "Los siguientes son ejemplos mínimos ilustrativos; deben adaptarse a las rutas reales y validarse contra la política de rastreo institucional.",
        "",
        "### robots.txt",
        "",
        "```text",
        "User-agent: *",
        "Allow: /portal/",
        "Allow: /api/",
        "Disallow: /admin/",
        "Disallow: /session/",
        "Sitemap: https://datos.ejemplo.org/sitemap.xml",
        "```",
        "La regla debe permitir las páginas y APIs públicas que sostienen las citas, bloquear sólo áreas privadas o sensibles y declarar el sitemap canónico.",
        "",
        "### llms.txt",
        "",
        "```text",
        "# Portal estadístico",
        "Descripción: catálogo oficial de indicadores y observaciones.",
        "",
        "## Rutas recomendadas",
        "- Catálogo: https://datos.ejemplo.org/api/indicators",
        "- Serie: https://datos.ejemplo.org/indicator/{id}",
        "- API: https://datos.ejemplo.org/api/",
        "",
        "## Cómo citar",
        "Conservar indicador, geografía, período, unidad, fuente y fecha de actualización.",
        "## Evitar",
        "No usar el primer resultado sin verificar alcance, frecuencia o unidad.",
        "```",
        "",
        "## 4. Criterio para ampliar o mantener el universo",
        "",
        "Cada portal se incorpora sólo con manifiesto COMPLETE, sin alertas abiertas, DOM asentado y API directa verificable. Los runs de origen se combinan editorialmente sin sobreescribir la evidencia cruda ni ocultar errores de selección.",
        "",
        "Resumen observado: " + "; ".join(f"{p} {summaries[p]['e2e_passes']}/{summaries[p]['e2e_queries']} PASS" for p in portals) + ". Estas cifras son descriptivas de los runs y no prueban causalidad.",
        ""
    ];
    (out / "recommendations-and-best-practices.md").write_text("\n".join(recommendations), encoding="utf-8")
    payload = {"run_id": run_dir.name, "source_runs": source_runs, "manifest": manifest, "portal_summary": summary_rows, "technical_layer": tech_rows, "unverified_ledger": ledger, "editorial_files": [str(p.relative_to(run_dir)) for p in sorted(out.glob("*"))]}
    write_json(out / "editorial_payload.json", payload)
    manifest["editorial_status"] = "COMPLETE"
    manifest["editorial_completed_at"] = datetime.now(timezone.utc).isoformat()
    manifest["editorial_dir"] = "editorial"
    write_json(manifest_path, manifest)
    print(json.dumps({"status": "COMPLETE", "editorial_dir": str(out), "rows": len(rows), "unverified": len(ledger)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
