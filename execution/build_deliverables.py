"""Build editorial deliverables from one validated production run.

This command is fail-closed: a final run needs the exact 1,800 executions,
pair-level gold PASS, and valid structured/natural outputs for every role.
``--allow-incomplete`` is diagnostic only and cannot update project docs.

Individual reports follow the AEO auditor report-template. The presentation
contains the 16 editorial sections required by the source-of-truth PDF.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from benchmark import production_analysis

OUTPUTS = ROOT / "outputs"
PORTAL_NAMES = {
    "worldbank": "World Bank Open Data",
    "who": "WHO Data",
    "cepalstat": "CEPALSTAT",
    "undata": "UN Data Commons (UNSD)",
    "sdg": "UN SDG Indicators",
}
PORTAL_CONTEXT = {
    "worldbank": {"url": "https://data.worldbank.org/", "host": "data.worldbank.org", "api": "https://api.worldbank.org/v2/", "note": "La API pública por indicador y país constituye la ruta principal de recuperación estructurada."},
    "who": {"url": "https://data.who.int/", "host": "data.who.int", "api": "https://www.who.int/data/gho", "note": "Se separa el indicador sanitario de cualquier consulta económica general que no sea aplicable al catálogo GHO."},
    "cepalstat": {"url": "https://statistics.cepal.org/portal/cepalstat/", "host": "statistics.cepal.org", "api": "https://statistics.cepal.org/portal/cepalstat/api.html", "note": "La respuesta debe conservar datos, metadatos, dimensiones, fuente, notas y códigos del indicador para resolver PIB y sus variantes."},
    "undata": {"url": "https://unstats.un.org/UNSDWebsite/undatacommons/", "host": "unstats.un.org", "api": "https://unstats.un.org/unsd/amaapi/", "note": "La recuperación debe preservar serie, país, período, unidad y fuente UNSD; los targets no disponibles quedan como missing validado."},
    "sdg": {"url": "https://unstats.un.org/sdgs/", "host": "unstats.un.org", "api": "https://unstats.un.org/SDGAPI/", "note": "Se distingue un indicador SDG relacionado con PIB de un nivel de PIB genérico, evitando convertir no aplicable en cero."},
}
DIMENSIONS = [
    ("bots", "Acceso y gobernanza de bots", 10),
    ("discovery", "Descubrimiento técnico", 15),
    ("rendering", "Renderizado e interacción", 20),
    ("structured_data", "Datos estructurados", 15),
    ("api", "API para agentes de código", 25),
    ("citability", "Autoridad y citabilidad", 15),
]
SECTION_TITLES = [
    "AEO y preparación para agentes", "Las seis dimensiones AEO", "Metodología, alcance y límites", "Los cinco portales", "Benchmark y unidad de análisis", "Resultados por portal", "Modelos y roles", "Desambiguación semántica", "Red team y controles adversariales", "AEO ↔ preparación para IA", "Estadística y asociación", "Buenas prácticas observadas", "Recomendaciones para CEPALSTAT", "Ficha AI-friendly de indicador", "Ejemplos de PIB y disambiguación", "Conclusiones y criterios de aceptación",
]


def safe(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def fmt(value: Any, digits: int = 2) -> str:
    if value is None or value == "":
        return "NA"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def pct(value: Any) -> str:
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return "NA"


def read_manifest(run_dir: Path) -> dict[str, Any]:
    path = run_dir / "run_manifest.json"
    if not path.exists():
        raise SystemExit(f"Missing run manifest: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_matrix_rows() -> dict[str, dict[str, Any]]:
    with production_analysis.MATRIX.open(encoding="utf-8", newline="") as fh:
        result: dict[str, dict[str, Any]] = {}
        for row in csv.DictReader(fh):
            portal_id = production_analysis.PORTAL_NAMES.get(row.get("portal", ""))
            if portal_id:
                result[portal_id] = row
        return result


def lookup(analysis: dict[str, Any], key: str, portal_id: str) -> dict[str, Any]:
    for row in analysis.get(key, []):
        if row.get("portal_id") == portal_id:
            return row
    return {}


def portal_summary(analysis: dict[str, Any], portal_id: str) -> dict[str, Any]:
    return lookup(analysis, "portal_summary", portal_id)


def adversarial_lookup(analysis: dict[str, Any], portal_id: str) -> dict[str, int]:
    result: dict[str, int] = defaultdict(int)
    prefix = f"{portal_id}:"
    for key, value in (analysis.get("adversarial_verdicts") or {}).items():
        if key.startswith(prefix):
            result[key[len(prefix):]] += int(value)
    return dict(result)


def model_names(analysis: dict[str, Any]) -> list[str]:
    return sorted({str(row.get("model")) for row in analysis.get("model_summary", []) if row.get("model")})


def dimensional_table(row: dict[str, Any]) -> str:
    lines = ["| Dimensión | Peso | Puntaje | Diagnóstico | Confianza |", "|---|---:|---:|---|---|"]
    for key, label, weight in DIMENSIONS:
        value = row.get(key, "NA")
        try:
            diagnosis = "fortaleza relativa" if float(value) >= weight * 0.75 else "prioridad de mejora"
        except (TypeError, ValueError):
            diagnosis = "no evaluado"
        lines.append(f"| {label} | {weight} | {value} | {diagnosis} | {row.get('confidence', 'NA')} |")
    lines.append(f"| **Total** | **100** | **{row.get('score', 'NA')}** | **{row.get('status', 'NA')}** | **{row.get('confidence', 'NA')}** |")
    return "\n".join(lines)


def evidence_table(context: dict[str, str], run_dir: Path) -> str:
    evidence = f"`{run_dir / 'evidence'}`"
    return "\n".join([
        "| URL/recurso | Estado | Content-Type | Redirect final | Resultado | Evidencia |",
        "|---|---:|---|---|---|---|",
        f"| `/robots.txt`, `/sitemap.xml`, `/llms.txt` | congelado | no resumido | allowlist | ver manifiesto | {evidence} |",
        f"| [Portal]({context['url']}) | fuente primaria | HTML/API | según evidencia | benchmark AEO | {evidence} |",
        f"| [API/documentación]({context['api']}) | fuente primaria | JSON/OpenAPI/catálogo | según evidencia | recuperación estructurada | {evidence} |",
    ])


def report_for_portal(portal_id: str, run_dir: Path, analysis: dict[str, Any], matrix_row: dict[str, Any], manifest: dict[str, Any]) -> str:
    name = PORTAL_NAMES[portal_id]; context = PORTAL_CONTEXT[portal_id]; summary = portal_summary(analysis, portal_id)
    adv = adversarial_lookup(analysis, portal_id)
    models = sorted({str(r.get("model")) for r in analysis.get("model_summary", []) if r.get("portal_id") == portal_id and r.get("model")})
    adv_text = ", ".join(f"{key}={value}" for key, value in sorted(adv.items())) or "NA"
    return f"""# Auditoría AEO y preparación para agentes de IA de {name}

**Portal auditado:** [{name}]({context['url']})  
**Host:** `{context['host']}`  
**Fecha de corte:** {manifest.get('completed_at') or manifest.get('date_tag') or '2026-08-23'}  
**Página/recurso interno de muestra:** consultas del banco de 120 preguntas y evidencia HTTP congelada; no se declara una única URL interna como muestra.  
**Calificación global:** **{matrix_row.get('score', 'NA')}/100 — {matrix_row.get('status', 'NA')}**

## 1. Resumen ejecutivo

El puntaje técnico AEO de **{matrix_row.get('score', 'NA')}/100** se contrasta con una visibilidad operacional AIRSC media de **{fmt(summary.get('mean_airsc'))}** y mediana **{fmt(summary.get('median_airsc'))}**. La cobertura válida es **{summary.get('n_valid', 'NA')}/{summary.get('n_total', 'NA')} ({pct(summary.get('coverage'))})**. Este resultado es descriptivo: no demuestra que AEO cause visibilidad. {context['note']}

## 2. Calificación consolidada

{dimensional_table(matrix_row)}

## 3. Metodología, alcance y limitaciones

Se ejecutan 120 consultas × 5 portales × 3 repeticiones (**1.800 ejecuciones**, cinco pasadas de 360), con discovery, semantic, retrieval, metadata, citation, judge y adversarial. La unidad inferencial es el portal (**n=5**); las 24 familias y repeticiones se usan como sensibilidad, no como observaciones independientes. El score se recomputa fuera del juez y no transforma `not_applicable`, ausencia validada o transporte fallido en cero. Modelos observados: **{', '.join(models) or 'registrados en el manifiesto'}**. Gold: **{manifest.get('gold_status', {}).get('status', 'NA')}**. Evidencia: `{run_dir}`.

## 4. Acceso y descubrimiento para bots

### Evidencia HTTP

{evidence_table(context, run_dir)}

### Política de crawlers

La interpretación se limita a la evidencia HTTP congelada y a la allowlist del portal. No se infiere disponibilidad para agentes desde un resultado de búsqueda que redirija fuera del host permitido.

### Sitemap y `llms.txt`

Se reportan como hallazgos de descubrimiento y gobernanza, no como garantía de recuperación semántica. Las URLs canónicas deben conservar el identificador del indicador.

## 5. Renderizado y muros de interacción

El benchmark separa descubrimiento, recuperación, semántica y citabilidad. Una página que requiere interacción o JavaScript puede seguir siendo descubrible, pero pierde visibilidad si el valor, unidad, período o fuente no están disponibles en la respuesta recuperada. El estado concreto queda respaldado por la evidencia congelada; no se extrapola desde AEO a causalidad.

## 6. Datos estructurados

La dimensión `structured_data` es **{matrix_row.get('structured_data', 'NA')}**/15. La validez de schema de cada rol es un gate de corrida, no un sustituto de la auditoría del portal. Cada indicador debe exponer identificador, definición, unidad, período, geografía, fuente y endpoint en JSON-LD o representación equivalente.

## 7. APIs y acceso para agentes de código

La dimensión `api` es **{matrix_row.get('api', 'NA')}**/25. Mantener documentación, endpoint, parámetros, códigos exactos y formatos de error junto al objeto estadístico. {context['note']}

## 8. Citabilidad y visibilidad en motores de respuesta

La dimensión `citability` es **{matrix_row.get('citability', 'NA')}**/15. La evidencia debe permitir citar URL estable, indicador exacto, unidad, período, geografía y fuente. Una única URL específica puede ser la respuesta correcta para una pregunta muy restringida; no se penaliza esa precisión cuando la evidencia y el valor son correctos.

## 9. Plan de remediación

### P0 — 0 a 2 semanas

1. Publicar identificadores y canonicales estables para indicadores; evitar navegación dependiente de sesión.
2. Mantener robots/sitemap y enlazar la documentación API desde la página del indicador.

### P1 — 2 a 6 semanas

1. Adjuntar definición, unidad, frecuencia, precio base, geografía, período, fuente y notas a cada respuesta.
2. Agregar JSON-LD o ficha machine-readable coherente con el API.

### P2 — 6 a 12 semanas

1. Ejecutar benchmark pre/post de 120 consultas con cinco pasadas de 360 y revisión adversarial.
2. Publicar ejemplos de preguntas y reglas `do_not_confuse_with` para indicadores cercanos.

## 10. Criterios de aceptación para “Preparado para Agentes”

- La URL canónica y el identificador resuelven a página humana y representación machine-readable.
- El agente recupera valor, unidad, período, geografía y fuente sin inferir parámetros.
- La cita contiene URL estable y provenance; no depende de redirección fuera de allowlist.
- El benchmark conserva 1.800 ejecuciones, gold PASS y outputs naturales disponibles.

## 11. Anexo de evidencia y confianza

| Hallazgo | Clasificación | Evidencia | Confianza |
|---|---|---|---|
| Puntaje AEO y dimensiones | Verificado | `execution/expanded-audit-matrix-2026-08-22.csv` | {matrix_row.get('confidence', 'NA')} |
| AIRSC medio y cobertura | Verificado | `{run_dir / 'analysis' / 'production_analysis.json'}` | alta si gate PASS |
| Diferencias por familias/repetición | Verificado | `production_family_summary.csv`, `production_repeat_summary.csv` | descriptiva |
| Veredictos adversariales | Verificado | manifiesto y `results.jsonl` ({adv_text}) | descriptiva |
| Causalidad AEO → visibilidad | No establecido | asociación portal-level n=5 | no aplicable |

## 12. Fuentes primarias

- [Portal oficial]({context['url']})
- [API o documentación oficial]({context['api']})
- [Matriz AEO congelada](../execution/expanded-audit-matrix-2026-08-22.csv)
- [Fuente de verdad metodológica](../auditoría%20AEO.pdf)
"""


def write_reports(run_dir: Path, analysis: dict[str, Any], manifest: dict[str, Any], date_tag: str, output_root: Path) -> list[Path]:
    output_root.mkdir(parents=True, exist_ok=True); matrix_rows = load_matrix_rows(); generated: list[Path] = []
    for portal_id in PORTAL_NAMES:
        path = output_root / f"aeo-agent-readiness-{safe(portal_id)}-{date_tag}.md"
        path.write_text(report_for_portal(portal_id, run_dir, analysis, matrix_rows.get(portal_id, {}), manifest), encoding="utf-8"); generated.append(path)
    comparison = output_root / f"aeo-comparative-report-{date_tag}.md"
    comparison.write_text(comparative_report(run_dir, analysis, matrix_rows, manifest, date_tag), encoding="utf-8"); generated.append(comparison)
    return generated


def comparative_report(run_dir: Path, analysis: dict[str, Any], matrix_rows: dict[str, dict[str, Any]], manifest: dict[str, Any], date_tag: str) -> str:
    lines = [f"# Comparación AEO–visibilidad — {date_tag}", "", f"Run validado: `{run_dir}`. Gold: **{manifest.get('gold_status', {}).get('status', 'NA')}**.", "", "## 1. Resumen ejecutivo", "", f"La asociación portal-level usa cinco observaciones: Spearman **{fmt(analysis.get('spearman_rho'))}**, Kendall **{fmt(analysis.get('kendall_tau'))}** y permutación exacta **{fmt(analysis.get('spearman_exact_p'))}**. Es descriptiva/no causal; familias y repeticiones son sensibilidad agrupada.", "", "## 2. Matriz comparativa", "", "| Portal | AEO | AIRSC medio | AIRSC mediana | Cobertura | API/25 | Schema failures | Adversarial | Modelos |", "|---|---:|---:|---:|---:|---:|---:|---|---|"]
    for portal_id, name in PORTAL_NAMES.items():
        m = matrix_rows.get(portal_id, {}); s = portal_summary(analysis, portal_id); adv = adversarial_lookup(analysis, portal_id)
        models = sorted({str(r.get('model')) for r in analysis.get('model_summary', []) if r.get('portal_id') == portal_id and r.get('model')})
        adv_text = ", ".join(f"{k}={v}" for k, v in sorted(adv.items())) or "NA"
        lines.append(f"| {name} | {m.get('score', 'NA')} | {fmt(s.get('mean_airsc'))} | {fmt(s.get('median_airsc'))} | {s.get('n_valid', 'NA')}/{s.get('n_total', 'NA')} ({pct(s.get('coverage'))}) | {m.get('api', 'NA')} | {s.get('schema_failures', 'NA')} | {adv_text} | {', '.join(models) or 'NA'} |")
    lines += ["", "## 3. Lectura de dimensiones", "", "La matriz técnica separa acceso de bots, descubrimiento, renderizado, datos estructurados, API y citabilidad. Un portal puede tener una API fuerte y una arquitectura de descubrimiento débil; el total AEO no se interpreta como una sola causa del resultado del agente.", "", "## 4. Sensibilidad y red team", "", "Las tablas de familias, repeticiones, estratos, modelos y veredictos adversariales están en `analysis/production_*_summary.csv`. Sirven para localizar inestabilidad; no aumentan el n portal-level.", "", "## 5. Recomendación editorial", "", "Publicar los cinco informes individuales junto con esta matriz, el deck y la evidencia congelada. Conservar la distinción entre una respuesta de una sola URL correctamente específica y una respuesta incompleta o no citable.", "", "## 6. Limitaciones", "", "La correlación usa n=5 portales y no controla confusores. El benchmark mide visibilidad bajo preguntas/modelos fijos; no es tráfico orgánico, ranking ni prueba causal. NA y missing validados permanecen explícitos.", "", "## 7. Fuentes", "", "- `execution/expanded-audit-matrix-2026-08-22.csv` — puntajes AEO congelados.", "- `benchmark/query-bank-120.csv` — banco de consultas y familias.", f"- `{run_dir}` — evidencia y resultados.", "- `auditoría AEO.pdf` — fuente de verdad metodológica y editorial."]
    return "\n".join(lines) + "\n"


def write_matrices(analysis: dict[str, Any], date_tag: str, output_root: Path) -> tuple[Path, Path]:
    output_root.mkdir(parents=True, exist_ok=True); matrix_rows = load_matrix_rows()
    fields = ["portal_id", "portal", "url", "aeo_score", *[key for key, _, _ in DIMENSIONS], "mean_airsc", "median_airsc", "n_valid", "n_total", "coverage", "schema_failures", "adversarial_verdicts", "family_count", "repeat_count", "model_count"]
    rows: list[dict[str, Any]] = []
    for portal_id, name in PORTAL_NAMES.items():
        m = matrix_rows.get(portal_id, {}); s = portal_summary(analysis, portal_id)
        families = {r.get("template_family_id") for r in analysis.get("family_summary", []) if r.get("portal_id") == portal_id}; repeats = {r.get("repeat") for r in analysis.get("repeat_summary", []) if r.get("portal_id") == portal_id}; models = {r.get("model") for r in analysis.get("model_summary", []) if r.get("portal_id") == portal_id}
        rows.append({"portal_id": portal_id, "portal": name, "url": PORTAL_CONTEXT[portal_id]["url"], "aeo_score": m.get("score"), **{key: m.get(key) for key, _, _ in DIMENSIONS}, "mean_airsc": s.get("mean_airsc"), "median_airsc": s.get("median_airsc"), "n_valid": s.get("n_valid"), "n_total": s.get("n_total"), "coverage": s.get("coverage"), "schema_failures": s.get("schema_failures"), "adversarial_verdicts": json.dumps(adversarial_lookup(analysis, portal_id), ensure_ascii=False, sort_keys=True), "family_count": len(families), "repeat_count": len(repeats), "model_count": len(models)})
    matrix = output_root / f"aeo-results-matrix-{date_tag}.csv"; comparative = output_root / f"aeo-comparative-matrix-{date_tag}.csv"
    with matrix.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields); writer.writeheader(); writer.writerows(rows)
    def descending_rank(value_key: str) -> dict[str, int]:
        numeric_rows = [(row["portal_id"], float(row[value_key])) for row in rows if row.get(value_key) not in (None, "")]
        return {portal_id: rank for rank, (portal_id, _) in enumerate(sorted(numeric_rows, key=lambda item: item[1], reverse=True), start=1)}
    aeo_rank = descending_rank("aeo_score"); airsc_rank = descending_rank("mean_airsc")
    comparison_fields = [*fields, "aeo_rank", "airsc_rank", "rank_delta", "airsc_minus_aeo"]
    comparison_rows = []
    for row in rows:
        item = dict(row); item["aeo_rank"] = aeo_rank.get(row["portal_id"]); item["airsc_rank"] = airsc_rank.get(row["portal_id"])
        item["rank_delta"] = (item["aeo_rank"] - item["airsc_rank"]) if item["aeo_rank"] and item["airsc_rank"] else None
        item["airsc_minus_aeo"] = (float(row["mean_airsc"]) - float(row["aeo_score"])) if row.get("mean_airsc") not in (None, "") and row.get("aeo_score") not in (None, "") else None
        comparison_rows.append(item)
    with comparative.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=comparison_fields); writer.writeheader(); writer.writerows(comparison_rows)
    return matrix, comparative


def add_slide(prs: Any, title: str, body: str, section_number: int | None = None) -> Any:
    from pptx.util import Inches, Pt
    from pptx.dml.color import RGBColor
    slide = prs.slides.add_slide(prs.slide_layouts[6]); bg = slide.background.fill; bg.solid(); bg.fore_color.rgb = RGBColor(248, 250, 252)
    header = slide.shapes.add_shape(1, Inches(0), Inches(0), Inches(13.333), Inches(0.7)); header.fill.solid(); header.fill.fore_color.rgb = RGBColor(25, 54, 93); header.line.fill.background()
    title_box = slide.shapes.add_textbox(Inches(0.55), Inches(0.11), Inches(12.2), Inches(0.48)); p = title_box.text_frame.paragraphs[0]; p.text = f"{section_number:02d} · {title}" if section_number else title; p.font.size = Pt(35); p.font.bold = True; p.font.color.rgb = RGBColor(255, 255, 255)
    body_box = slide.shapes.add_textbox(Inches(0.65), Inches(1.0), Inches(12.0), Inches(5.9)); tf = body_box.text_frame; tf.clear(); tf.word_wrap = True
    for index, line in enumerate(body.split("\n")):
        paragraph = tf.paragraphs[0] if index == 0 else tf.add_paragraph(); paragraph.text = line; paragraph.font.size = Pt(16); paragraph.font.color.rgb = RGBColor(35, 43, 53); paragraph.space_after = Pt(7)
    footer = slide.shapes.add_textbox(Inches(0.65), Inches(7.05), Inches(12), Inches(0.25)); footer.text_frame.text = "AEO · evidencia congelada · asociación descriptiva/no causal"; footer.text_frame.paragraphs[0].font.size = Pt(8); footer.text_frame.paragraphs[0].font.color.rgb = RGBColor(90, 100, 110)
    return slide


def write_ppt(analysis: dict[str, Any], date_tag: str, manifest: dict[str, Any], output_root: Path = OUTPUTS) -> Path:
    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.dml.color import RGBColor
    output_root.mkdir(parents=True, exist_ok=True); path = output_root / f"aeo-comparative-deck-{date_tag}.pptx"
    prs = Presentation(); prs.slide_width = Inches(13.333); prs.slide_height = Inches(7.5)
    title = prs.slides.add_slide(prs.slide_layouts[6]); title.background.fill.solid(); title.background.fill.fore_color.rgb = RGBColor(25, 54, 93)
    tb = title.shapes.add_textbox(Inches(0.8), Inches(1.5), Inches(11.8), Inches(2.5)); p = tb.text_frame.paragraphs[0]; p.text = "AEO y visibilidad de agentes"; p.font.size = Pt(50); p.font.bold = True; p.font.color.rgb = RGBColor(255, 255, 255)
    sub = title.shapes.add_textbox(Inches(0.85), Inches(4.1), Inches(11.5), Inches(1.4)); p = sub.text_frame.paragraphs[0]; p.text = "Cinco portales estadísticos · 120 consultas · 1.800 ejecuciones · editorial final"; p.font.size = Pt(24); p.font.color.rgb = RGBColor(220, 230, 240)
    matrix_rows = load_matrix_rows(); summaries = {r.get("portal_id"): r for r in analysis.get("portal_summary", [])}; models = ", ".join(model_names(analysis)) or "registrados en el manifiesto"
    add_slide(prs, SECTION_TITLES[0], "Objetivo: evaluar si la preparación técnica AEO se asocia con la visibilidad operacional de agentes.\nResultado: la asociación se resume a nivel portal y no establece causalidad.\nFuente: auditoría AEO.pdf y skill aeo-agent-readiness-auditor.", 1)
    add_slide(prs, SECTION_TITLES[1], "Bots (10) · descubrimiento (15) · renderizado (20) · datos estructurados (15) · API (25) · citabilidad (15).\nEl puntaje AEO es técnico y congelado; AIRSC se recomputa desde la respuesta estructurada validada.", 2)
    add_slide(prs, SECTION_TITLES[2], "120 consultas × 5 portales × 3 repeticiones = 1.800 ejecuciones, en cinco pasadas de 360.\nRoles: discovery, semantic, retrieval, metadata, citation, judge y adversarial.\nUnidad inferencial: n=5 portales. No se convierten NA, missing o transporte fallido en cero.", 3)
    add_slide(prs, SECTION_TITLES[3], "\n".join(f"{i}. {PORTAL_NAMES[i]} — {PORTAL_CONTEXT[i]['url']}" for i in PORTAL_NAMES), 4)
    add_slide(prs, SECTION_TITLES[4], f"Cardinalidad: {analysis.get('n_rows', 'NA')} filas · {analysis.get('n_portals', 'NA')} portales.\nGold: {manifest.get('gold_status', {}).get('status', 'NA')} · estado del run: {manifest.get('status', 'NA')}.\nLas 24 familias y las repeticiones son sensibilidad agrupada. Modelos observados: {models}.", 5)
    portal_lines = ["Portal | AEO | AIRSC medio | cobertura", "---|---:|---:|---:"]
    for portal_id, name in PORTAL_NAMES.items():
        m = matrix_rows.get(portal_id, {}); s = summaries.get(portal_id, {}); portal_lines.append(f"{name} | {m.get('score', 'NA')} | {fmt(s.get('mean_airsc'))} | {s.get('n_valid', 'NA')}/{s.get('n_total', 'NA')} ({pct(s.get('coverage'))})")
    add_slide(prs, SECTION_TITLES[5], "\n".join(portal_lines), 6)
    model_lines = [f"Modelos registrados: {models}"]
    for row in analysis.get("model_summary", [])[:12]:
        model_lines.append(f"{row.get('portal_id')} · {row.get('role')} · {row.get('model')} → AIRSC {fmt(row.get('mean_airsc'))} (n={row.get('n_valid')})")
    add_slide(prs, SECTION_TITLES[6], "\n".join(model_lines), 7)
    add_slide(prs, SECTION_TITLES[7], "La precisión semántica requiere indicador, definición, unidad, período, geografía, precio base, frecuencia y fuente.\nHipótesis operativa: una consulta muy específica puede devolver correctamente una sola URL; no se penaliza esa respuesta si el objeto es correcto y citable.\nEn CEPALSTAT, PIB nominal/real/per cápita y moneda deben quedar separados.", 8)
    adv_lines = ["Los veredictos adversariales se reportan por portal; no se esconden detrás del promedio."]
    for portal_id, name in PORTAL_NAMES.items():
        adv = adversarial_lookup(analysis, portal_id); adv_lines.append(f"{name}: " + (", ".join(f"{k}={v}" for k, v in sorted(adv.items())) or "NA"))
    add_slide(prs, SECTION_TITLES[8], "\n".join(adv_lines), 9)
    add_slide(prs, SECTION_TITLES[9], "AEO mide condiciones del portal; AIRSC mide el resultado de recuperación/semántica/citación bajo el benchmark.\nLa relación puede verse afectada por cobertura, especificidad, modelo, redirecciones y aplicabilidad. Por eso la lectura es de preparación relativa, no causalidad.", 10)
    add_slide(prs, SECTION_TITLES[10], f"Spearman: {fmt(analysis.get('spearman_rho'))}\nKendall: {fmt(analysis.get('kendall_tau'))}\nPermutación exacta: {fmt(analysis.get('spearman_exact_p'))}\nAdvertencia: n=5 y resultados descriptivos.", 11)
    add_slide(prs, SECTION_TITLES[11], "Identificadores canónicos · metadata junto al valor · API documentada · JSON-LD coherente · robots/sitemap enlazados · unidades y períodos explícitos · provenance y URL estable · ejemplos de consultas y reglas de no confusión.", 12)
    add_slide(prs, SECTION_TITLES[12], "P0: canonicales, robots/sitemap y API desde cada indicador.\nP1: ficha machine-readable con definición, unidad, período, geografía, fuente y dimensiones.\nP2: benchmark pre/post, vocabulario controlado, `similar_indicators` y `do_not_confuse_with`.", 13)
    add_slide(prs, SECTION_TITLES[13], "Ficha mínima: indicator_id, label, definition, unit, frequency, geography, period, value, source, provenance_url, api_url, dimensions y disambiguation_rules.\nLa ficha debe ser legible por humanos y agentes, sin obligar a inferir códigos.", 14)
    add_slide(prs, SECTION_TITLES[14], "Ejemplo editorial: ante “PIB de Chile 2019” el agente debe resolver si se solicita nivel corriente, constante, per cápita, crecimiento o moneda local.\nLa respuesta correcta puede ser una sola URL, siempre que esa URL exponga el indicador exacto y su contexto.", 15)
    add_slide(prs, SECTION_TITLES[15], f"Publicar cinco informes individuales, matrices, análisis de familias/modelos/repeticiones, red team, deck y evidencia.\nAceptar solo con 1.800 filas, gold PASS, schema/natural outputs completos y QA visual del deck.\nConclusión estadística: Spearman {fmt(analysis.get('spearman_rho'))}; no causalidad demostrada.", 16)
    prs.save(path); return path


def write_cepalstat_toolkit(run_dir: Path, analysis: dict[str, Any], date_tag: str) -> Path:
    path = ROOT / "cepalstat-agent-readiness-kit" / f"benchmark-integration-{date_tag}.md"
    path.write_text(f"""# Integración del benchmark AEO — CEPALSTAT ({date_tag})

Este anexo conecta el kit CEPALSTAT con la corrida validada `{run_dir}`. No sustituye evidencia HTTP ni afirma que una recomendación ya esté implementada.

## Gate de publicación

- 120 consultas × 5 portales × 3 repeticiones = 1.800 ejecuciones.
- Gold pair-level: **PASS** en el manifiesto.
- AIRSC recomputado fuera del juez; NA y missing validados permanecen explícitos.
- Las consultas PIB se desambiguaron por indicador, unidad, precio, período, geografía y fuente.

## Ficha de indicador recomendada

`indicator_id`, `label`, `definition`, `unit`, `frequency`, `geography`, `period`, `value`, `source`, `provenance_url`, `api_url`, `dimensions`, `similar_indicators`, `do_not_confuse_with` y `disambiguation_rules`.

## Resultado a incorporar en un pre/post

`analysis/production_family_summary.csv` permite comparar familias semánticas; `production_repeat_summary.csv` y `production_model_summary.csv` auditan estabilidad. La asociación portal-level tiene n=5 y no debe presentarse como causal.

## Criterios de aceptación CEPALSTAT

1. Un identificador canónico resuelve a página humana y representación machine-readable.
2. Datos, metadatos, dimensiones, notas y fuente se recuperan sin adivinar relaciones de endpoint.
3. Una pregunta PIB muy específica puede producir una sola URL correcta y citable.
4. La respuesta conserva unidad, período, geografía, fuente y provenance.
""", encoding="utf-8")
    return path


def update_project_docs(analysis: dict[str, Any], run_dir: Path, date_tag: str, artifacts: list[Path]) -> list[Path]:
    """Update project-facing docs only after all derived artifacts exist."""
    output_names = "\n".join(f"- `{path.relative_to(ROOT)}`" for path in artifacts)
    toolkit = write_cepalstat_toolkit(run_dir, analysis, date_tag); output_names += f"\n- `{toolkit.relative_to(ROOT)}`"
    (ROOT / "README.md").write_text("# AEO y visibilidad de agentes en portales estadísticos\n\nEste repositorio implementa la evaluación de la relación entre puntaje AEO técnico y visibilidad/recuperación de agentes. Fuente metodológica: `auditoría AEO.pdf`; skill: `.agents/skills/aeo-agent-readiness-auditor`.\n\n## Universo y contrato\n\nWorld Bank Open Data, WHO Data, CEPALSTAT, UN Data Commons y UN SDG Indicators. Statista queda fuera. Contrato: 120 consultas × 5 portales × 3 repeticiones = 1.800 ejecuciones, en cinco pasadas de 360. La asociación es portal-level (`n=5`).\n\n## Resultado validado\n\n" + f"Run: `{run_dir}`. Filas: {analysis.get('n_rows')}; portales: {analysis.get('n_portals')}; Spearman: {analysis.get('spearman_rho')}; Kendall: {analysis.get('kendall_tau')}; permutación exacta: {analysis.get('spearman_exact_p')}. Lectura descriptiva/no causal.\n\n## Entregables regenerados\n\n{output_names}\n\n## Reproducibilidad\n\nEjecutar `python benchmark/self_check.py`, validar `python -m benchmark.production_runner --execute --plan` y reanudar con `--resume`. No publicar sin 1.800 ejecuciones y gold PASS.\n", encoding="utf-8")
    (ROOT / "execution" / "README.md").write_text(f"# Ejecución AEO {date_tag}\n\nFuente: `auditoría AEO.pdf`. Run validado: `{run_dir}`.\n\nEvidencia HTTP, RAW/JSON, schema, score recomputado, juez y adversarial se preservan. Métricas: {analysis.get('n_rows')} filas; {analysis.get('n_portals')} portales; Spearman {analysis.get('spearman_rho')}; Kendall {analysis.get('kendall_tau')}; permutación exacta {analysis.get('spearman_exact_p')}. Asociación descriptiva/no causal.\n\n## Artefactos\n\n{output_names}\n", encoding="utf-8")
    (ROOT / "benchmark" / "README.md").write_text("# Benchmark AEO de cinco portales\n\nRunner canónico: `production_runner.py`. Contrato: 120 × 5 × 3 = 1.800 ejecuciones y cinco pasadas de 360; asociación portal-level.\n\n## Flujo\n\n1. `python self_check.py` y `python cardinality_check.py`.\n2. `python -m production_runner --execute --plan`.\n3. Ejecutar/reanudar con `--run-id <id> --resume`.\n4. Generar entregables con `python execution/build_deliverables.py <run_dir> --update-docs --skip-ppt` después de QA del deck artifact-tool.\n\nModelos, digest, evidencia, schema y estados adversariales quedan en manifiesto y JSONL.\n", encoding="utf-8")
    gate_path = ROOT / "execution" / "gate-status-2026-08-22.md"
    gate_base = gate_path.read_text(encoding="utf-8") if gate_path.exists() else "# Estado de gates de ejecución\n"
    gate_marker = "\n## Cierre editorial ejecutado\n"
    gate_base = gate_base.split(gate_marker, 1)[0]
    gate_base += gate_marker + f"\n- Gate 13 Benchmark completo: **PASS** — `{run_dir}`, {analysis.get('n_rows')} ejecuciones, cinco portales y tres repeticiones.\n- Gate 14 Análisis y entregables: **PASS** — matrices, cinco informes, comparación, sensibilidad, red team y deck regenerados.\n- Gate 15 Documentación final: **PASS** — README raíz, execution README, benchmark README, estado de gates, plan y toolkit CEPALSTAT actualizados después del QA editorial.\n- Gold: **{read_manifest(run_dir).get('gold_status', {}).get('status', 'NA')}**; lectura estadística: descriptiva/no causal con unidad portal-level n=5.\n"
    gate_path.write_text(gate_base, encoding="utf-8")
    plan_path = ROOT / "execution" / "implementation-plan-15-gates-2026-08-22.md"
    plan_base = plan_path.read_text(encoding="utf-8") if plan_path.exists() else "# Plan operativo de 15 gates\n"
    plan_marker = "\n## Cierre ejecutado\n"
    plan_base = plan_base.split(plan_marker, 1)[0]
    plan_base += plan_marker + f"\nEl run `{run_dir}` cerró los gates 13–15 con {analysis.get('n_rows')} ejecuciones válidas. Se conservaron la hipótesis de una sola URL específica cuando es correcta y la separación entre AEO técnico y visibilidad operacional. Los documentos finales se actualizaron únicamente después de matrices, informes, matriz comparativa y PPT artifact-tool con QA de overflow.\n"
    plan_path.write_text(plan_base, encoding="utf-8")
    return [ROOT / "README.md", ROOT / "execution" / "README.md", ROOT / "benchmark" / "README.md", gate_path, plan_path, toolkit]


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("run_dir", type=Path); parser.add_argument("--date-tag", default="2026-08-23"); parser.add_argument("--allow-incomplete", action="store_true"); parser.add_argument("--update-docs", action="store_true"); parser.add_argument("--skip-ppt", action="store_true", help="reuse an already QA'd PPTX so the final docs pass cannot overwrite it")
    if args.allow_incomplete and args.update_docs:
        raise SystemExit("DELIVERABLES HOLD: --allow-incomplete is incompatible with --update-docs")
    manifest = read_manifest(args.run_dir)
    if not args.allow_incomplete and (manifest.get("status") != "COMPLETE" or manifest.get("completed_executions") != 1800 or manifest.get("gold_status", {}).get("status") != "PASS"):
        raise SystemExit("DELIVERABLES HOLD: require COMPLETE manifest, 1,800 rows and PASS gold status")
    jsonl = args.run_dir / "results.jsonl"
    if not jsonl.exists():
        raise SystemExit(f"Missing results: {jsonl}")
    analysis_dir = args.run_dir / "analysis"; analysis = production_analysis.run(jsonl, analysis_dir)
    output_root = ROOT / "outputs" / "diagnostic" / args.date_tag if args.allow_incomplete else OUTPUTS
    matrices = write_matrices(analysis, args.date_tag, output_root); reports = write_reports(args.run_dir, analysis, manifest, args.date_tag, output_root)
    deck = OUTPUTS / f"aeo-comparative-deck-{args.date_tag}.pptx"
    if not args.skip_ppt:
        deck = write_ppt(analysis, args.date_tag, manifest, output_root)
    elif not deck.exists():
        raise SystemExit(f"DELIVERABLES HOLD: --skip-ppt requested but missing QA'd deck: {deck}")
    artifacts = [*matrices, *reports, deck]
    docs = update_project_docs(analysis, args.run_dir, args.date_tag, artifacts) if args.update_docs else []
    print(json.dumps({"analysis": str(analysis_dir), "matrices": [str(path) for path in matrices], "reports": [str(path) for path in reports], "ppt": str(deck), "docs_updated": bool(docs), "docs": [str(path) for path in docs]}, ensure_ascii=False, indent=2)); return 0


if __name__ == "__main__":
    raise SystemExit(main())
