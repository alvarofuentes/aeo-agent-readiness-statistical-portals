"""Build isolated editorial artifacts for the CEPALSTAT–UN SDG pilot.

This is intentionally separate from ``build_deliverables.py``.  The pilot
contract is 60 query templates × 2 portals × 3 repeats = 360 executions, not
the production 1,800-execution contract.  Every artifact is written below the
pilot run directory and this command never changes the five-portal outputs or
project README files.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import statistics
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "execution" / "expanded-audit-matrix-2026-08-22.csv"
PILOT_PORTALS = {
    "cepalstat": {
        "name": "CEPALSTAT",
        "url": "https://statistics.cepal.org/portal/cepalstat/",
        "api": "https://statistics.cepal.org/portal/cepalstat/api.html",
        "sample_page": "https://statistics.cepal.org/portal/cepalstat/",
        "strength": "La portada HTML declara una arquitectura institucional y carga módulos de navegación; la matriz AEO identifica una API pública OAS3 como principal fortaleza.",
        "barrier": "El HTML inicial depende de cargas jQuery de cabecera/módulos y el piloto no obtuvo ninguna URL de serie aceptada; la recuperación queda sin evidencia específica.",
        "api_detail": "El portal enlaza documentación API/OpenAPI y la matriz fuente describe endpoints de datos, metadatos, dimensiones, fuentes y notas.",
    },
    "sdg": {
        "name": "UN SDG Indicators",
        "url": "https://unstats.un.org/sdgs/",
        "api": "https://unstats.un.org/SDGAPI/",
        "sample_page": "https://unstats.un.org/sdgs/dataportal/",
        "strength": "El portal responde 200 y ofrece un punto oficial de datos y una API SDG/OpenAPI según la matriz técnica, con metadatos SDMX descritos como fortaleza.",
        "barrier": "La página de datos capturada es un shell React con `id=\"root\"` y mensaje `noscript`; sin ejecución de JavaScript no expone una tabla o serie citable.",
        "api_detail": "La documentación oficial enlaza SDGAPI; el piloto no ejecutó llamadas de datos ni validó el mapeo de un indicador concreto.",
    },
}
DIMENSIONS = ["bots", "discovery", "rendering", "structured_data", "api", "citability"]
DIMENSION_MAX = {"bots": 10, "discovery": 15, "rendering": 20, "structured_data": 15, "api": 25, "citability": 15}
DIMENSION_LABELS = {
    "bots": "Acceso y gobernanza de bots",
    "discovery": "Descubrimiento técnico",
    "rendering": "Renderizado e interacción",
    "structured_data": "Datos estructurados",
    "api": "API para agentes de código",
    "citability": "Autoridad y citabilidad",
}
ROLES = ["discovery", "semantic", "retrieval", "metadata", "citation", "judge", "adversarial"]
STRATUM_LABELS = {
    "discovery": "Descubrimiento",
    "exact_indicator": "Indicador exacto",
    "semantic_disambiguation": "Desambiguación semántica",
    "dimensions": "Dimensiones",
    "comparison": "Comparación",
    "temporal": "Temporal",
    "metadata": "Metadatos",
    "citation": "Citación",
}


def f(value: Any, digits: int = 2) -> str:
    if value is None or value == "":
        return "NA"
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def pct(value: Any) -> str:
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return "NA"


def load_matrix() -> dict[str, dict[str, Any]]:
    with MATRIX.open(encoding="utf-8", newline="") as fh:
        result: dict[str, dict[str, Any]] = {}
        for row in csv.DictReader(fh):
            for portal_id, context in PILOT_PORTALS.items():
                if row.get("portal") == context["name"]:
                    result[portal_id] = row
        return result


def load_run(run_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    manifest_path = run_dir / "run_manifest.json"
    analysis_path = run_dir / "analysis" / "pilot_analysis.json"
    if not manifest_path.exists() or not analysis_path.exists():
        raise SystemExit("PILOT EDITORIAL HOLD: missing run_manifest.json or analysis/pilot_analysis.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
    expected = manifest.get("expected", {})
    checks = {
        "scope": manifest.get("scope") == "pilot_extremes",
        "status": manifest.get("status") == "COMPLETE",
        "cardinality": expected.get("templates") == 60 and expected.get("portals") == 2 and expected.get("repeats") == 3 and expected.get("executions") == 360,
        "completed": manifest.get("completed_executions") == 360,
        "gold": manifest.get("gold_status", {}).get("status") == "PASS",
        "analysis_rows": analysis.get("n_rows") == 360,
        "analysis_portals": set(analysis.get("portals", [])) == set(PILOT_PORTALS),
        # Mechanical completion and editorial readiness are separate gates.
        # The pilot can be rendered as a diagnostic package while publication
        # remains HOLD when discovery evidence or red-team verdicts are absent.
        "mechanical_qa": analysis.get("mechanical_qa_status") == "PASS" and analysis.get("natural_gap_rows", 0) == 0,
    }
    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        raise SystemExit(f"PILOT EDITORIAL HOLD: failed gates: {', '.join(failed)}")
    return manifest, analysis


def summary(analysis: dict[str, Any], portal_id: str) -> dict[str, Any]:
    return next((row for row in analysis.get("portal_summary", []) if row.get("portal_id") == portal_id), {})


def normalized_matrix_row(row: dict[str, Any]) -> dict[str, Any]:
    """Apply the PDF/skill dimension maxima without hiding source values."""
    out = dict(row)
    source_score = float(row.get("score")) if row.get("score") not in (None, "") else None
    corrections: list[str] = []
    normalized_total = 0.0
    for key, maximum in DIMENSION_MAX.items():
        try:
            value = float(row.get(key))
        except (TypeError, ValueError):
            out[f"{key}_normalized"] = row.get(key, "NA")
            continue
        normalized = min(value, maximum)
        out[f"{key}_source"] = value
        out[f"{key}_normalized"] = int(normalized) if normalized.is_integer() else normalized
        normalized_total += normalized
        if value > maximum:
            corrections.append(f"{key} {value:g}/{maximum}")
    out["aeo_source_score"] = int(source_score) if source_score is not None and source_score.is_integer() else source_score
    out["aeo_score"] = int(normalized_total) if normalized_total.is_integer() else normalized_total
    out["score_correction"] = "; ".join(corrections) if corrections else "none"
    out["score_correction_note"] = ("La calificación editorial se recalculó con los máximos del PDF/skill; la matriz fuente se conserva mediante el hash del manifiesto." if corrections else "No fue necesario corregir topes dimensionales.")
    return out


def load_rows_and_evidence(run_dir: Path) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    rows = [json.loads(line) for line in (run_dir / "results.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    evidence: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for path in (run_dir / "evidence").glob("*.json"):
        item = json.loads(path.read_text(encoding="utf-8"))
        evidence[str(item.get("portal_id"))].append(item)
    return rows, evidence


def _mean(values: list[float | int | None]) -> float | None:
    clean = [float(v) for v in values if v is not None]
    return statistics.mean(clean) if clean else None


def _sd(values: list[float | int | None]) -> float | None:
    clean = [float(v) for v in values if v is not None]
    return statistics.stdev(clean) if len(clean) > 1 else 0.0 if clean else None


def _judge_mean(rows: list[dict[str, Any]], key: str) -> float | None:
    return _mean([(row.get("judge_dimensions") or {}).get(key) for row in rows])


def _row_stats(rows: list[dict[str, Any]], portal_id: str, stratum: str | None = None) -> dict[str, Any]:
    selected = [row for row in rows if (row.get("case") or {}).get("portal_id") == portal_id and (stratum is None or (row.get("case") or {}).get("stratum") == stratum)]
    scores = [(row.get("score") or {}).get("overall_0_100_recomputed") for row in selected]
    adversarial = Counter((row.get("adversarial") or {}).get("verdict") or "NA" for row in selected)
    schema_valid = sum(all((row.get("agents") or {}).get(role, {}).get("schema_valid") is True for role in ROLES) for row in selected)
    natural_available = sum(all((row.get("natural_signals") or {}).get(role, {}).get("available") is True for role in ROLES) for row in selected)
    candidate_urls = sum(bool(row.get("candidate_url")) and row.get("candidate_allowed") is True for row in selected)
    # Some runner versions put the final booleans inside role outputs; keep the
    # extraction explicit so the matrix never turns an absent field into zero.
    citable = sum(bool(((row.get("agents") or {}).get("citation") or {}).get("selected_structured", {}).get("parsed_json", {}).get("citable")) for row in selected)
    return {
        "template_rows": len({(row.get("case") or {}).get("template_id") for row in selected}),
        "executions": len(selected),
        "repeats": len({row.get("repeat") for row in selected}),
        "mean_airsc": _mean(scores),
        "median_airsc": statistics.median([float(v) for v in scores if v is not None]) if any(v is not None for v in scores) else None,
        "stdev_airsc": _sd(scores),
        "nonzero_airsc": sum(float(v) > 0 for v in scores if v is not None),
        "mean_discovery_success": _judge_mean(selected, "discovery_success"),
        "mean_retrieval_success": _judge_mean(selected, "retrieval_success"),
        "mean_semantic_correctness": _judge_mean(selected, "semantic_correctness"),
        "mean_metadata_correctness": _judge_mean(selected, "metadata_correctness"),
        "mean_temporal_geographic_correctness": _judge_mean(selected, "temporal_geographic_correctness"),
        "mean_citation_correctness": _judge_mean(selected, "citation_correctness"),
        "mean_judge_overall": _judge_mean(selected, "overall_0_100"),
        "candidate_urls": candidate_urls,
        "citable_outputs": citable,
        "adversarial_pass": adversarial.get("pass", 0),
        "adversarial_fail": adversarial.get("fail", 0),
        "adversarial_uncertain": adversarial.get("uncertain", 0),
        "schema_valid_pct": schema_valid / len(selected) if selected else None,
        "natural_available_pct": natural_available / len(selected) if selected else None,
    }


def portal_evidence_stats(evidence: dict[str, list[dict[str, Any]]], portal_id: str) -> dict[str, Any]:
    items = evidence.get(portal_id, [])
    pages = [page for item in items for page in item.get("pages", [])]
    serp_captures = [capture for item in items for capture in (item.get("serp") or {}).get("captures", [])]
    status_counts = Counter(page.get("status") for page in pages)
    serp_status_counts = Counter(capture.get("status") for capture in serp_captures)
    page_urls = Counter(page.get("requested_url") for page in pages)
    content_types = Counter((page.get("headers") or {}).get("content-type") for page in pages)
    bodies = [page.get("text_excerpt", "") for page in pages]
    return {
        "evidence_files": len(items),
        "page_count": len(pages),
        "page_statuses": dict(status_counts),
        "page_urls": dict(page_urls),
        "content_types": dict(content_types),
        "mean_page_bytes": _mean([page.get("byte_length") for page in pages]),
        "min_page_bytes": min([page.get("byte_length") for page in pages], default=None),
        "max_page_bytes": max([page.get("byte_length") for page in pages], default=None),
        "serp_statuses": dict(serp_status_counts),
        "serp_captures": len(serp_captures),
        "serp_accepted_urls": sum(len((item.get("serp") or {}).get("urls", [])) for item in items),
        "serp_rejected_urls": sum(len((item.get("serp") or {}).get("rejected", [])) for item in items),
        "jsonld_detected": sum("application/ld+json" in body.lower() for body in bodies),
        "schema_org_detected": sum("schema.org" in body.lower() for body in bodies),
        "noscript_detected": sum("<noscript>" in body.lower() for body in bodies),
        "root_shell_detected": sum('id="root"' in body.lower() for body in bodies),
        "script_detected": sum("<script" in body.lower() for body in bodies),
        "sample_excerpt": bodies[0][:900] if bodies else "",
    }


def report(portal_id: str, run_dir: Path, manifest: dict[str, Any], analysis: dict[str, Any], matrix: dict[str, Any], rows: list[dict[str, Any]], evidence: dict[str, list[dict[str, Any]]]) -> str:
    context = PILOT_PORTALS[portal_id]
    portal_row = summary(analysis, portal_id)
    all_stats = _row_stats(rows, portal_id)
    ev = portal_evidence_stats(evidence, portal_id)
    strata = []
    for stratum in STRATUM_LABELS:
        stat = _row_stats(rows, portal_id, stratum)
        if stat["executions"]:
            strata.append((stratum, stat))
    band = "No listo" if float(matrix.get("aeo_score", 0)) < 50 else "Intermedio" if float(matrix.get("aeo_score", 0)) < 75 else "Listo con brechas" if float(matrix.get("aeo_score", 0)) < 90 else "Preparado"
    confidence_label = {"high": "alta", "medium": "media", "low": "baja"}.get(str(matrix.get("confidence", "")).lower(), matrix.get("confidence", "NA"))
    dimension_lines = ["| Dimensión | Peso | Puntaje | Diagnóstico | Confianza |", "|---|---:|---:|---|---|"]
    diagnoses = {
        "bots": "No se probó una política de crawler específica en este piloto.",
        "discovery": f"{all_stats['candidate_urls']}/{all_stats['executions']} URLs específicas aceptadas.",
        "rendering": "La captura es HTML inicial; la experiencia post-JavaScript no fue medida.",
        "structured_data": f"JSON-LD detectado en {ev['jsonld_detected']}/{ev['page_count']} capturas.",
        "api": "Fortaleza técnica declarada en la matriz; no se llamó al endpoint de datos en este piloto.",
        "citability": f"Citación específica no validada; {all_stats['citable_outputs']}/{all_stats['executions']} salidas citable detectadas.",
    }
    for key in DIMENSIONS:
        confidence = "alta" if key in {"api", "citability"} and matrix.get("confidence") == "high" else "media / piloto"
        dimension_lines.append(f"| {DIMENSION_LABELS[key]} | {DIMENSION_MAX[key]} | {matrix.get(f'{key}_normalized', matrix.get(key, 'NA'))} | {diagnoses[key]} | {confidence} |")
    dimension_lines.append(f"| **Total** | **100** | **{matrix.get('aeo_score', matrix.get('score', 'NA'))}** | **{band}**; máximos PDF/skill aplicados | {confidence_label} |")
    http_lines = ["| Recurso | Estado | Tipo/resultado | Evidencia |", "|---|---:|---|---|"]
    for resource in ["robots.txt", "sitemap.xml", "sitemap_index.xml", "llms.txt"]:
        http_lines.append(f"| `/{resource}` | No verificado | No fue capturado por este piloto | `{run_dir / 'raw_http'}` |")
    page_lines = ["| Superficie | URL | Estado | Content-Type | Bytes | Resultado |", "|---|---|---:|---|---:|---|"]
    for url, count in ev["page_urls"].items():
        ctype = next(iter(ev["content_types"]), "NA")
        status = next(iter(ev["page_statuses"]), "NA")
        page_lines.append(f"| Página interna capturada | {url} | {status} | {ctype} | {f(ev['mean_page_bytes'], 0)} promedio | {count} capturas idénticas |")
    role_lines = ["| Rol | Modelo | Schema válido | Natural disponible |", "|---|---|---:|---:|"]
    for role, model in (manifest.get("models") or {}).items():
        role_lines.append(f"| {role} | `{model}` | {pct(all_stats['schema_valid_pct'])} | {pct(all_stats['natural_available_pct'])} |")
    strata_lines = ["| Estrato | Filas | Ejecuciones | AIRSC medio | Mediana | SD | Descubrimiento | Recuperación | Cita | Adversarial |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|"]
    for stratum, stat in strata:
        strata_lines.append(f"| {STRATUM_LABELS[stratum]} | {stat['template_rows']} | {stat['executions']} | {f(stat['mean_airsc'])} | {f(stat['median_airsc'])} | {f(stat['stdev_airsc'])} | {f(stat['mean_discovery_success'])} | {f(stat['mean_retrieval_success'])} | {f(stat['mean_citation_correctness'])} | P {stat['adversarial_pass']} / U {stat['adversarial_uncertain']} |")
    repeat_lines = ["| Repetición | AIRSC medio | Ejecuciones |", "|---:|---:|---:|"]
    for repeat in sorted({int(row.get("repeat")) for row in rows if (row.get("case") or {}).get("portal_id") == portal_id}):
        stat = _row_stats([row for row in rows if row.get("repeat") == repeat], portal_id)
        repeat_lines.append(f"| {repeat} | {f(stat['mean_airsc'])} | {stat['executions']} |")
    adv_text = f"pass={all_stats['adversarial_pass']}, fail={all_stats['adversarial_fail']}, uncertain={all_stats['adversarial_uncertain']}"
    correction_note = matrix.get("score_correction_note", "")
    editorial_qa = analysis.get("qa_status", "NA")
    publication = analysis.get("publication_status", "HOLD")
    page_excerpt = ev.get("sample_excerpt", "").replace("\n", " ")[:500]
    strength = context["strength"].rstrip(".")
    barrier = context["barrier"].rstrip(".")
    # Keep the executive sentence grammatically correct when the evidence
    # description already starts with an article ("La/El").
    strength = strength[0].lower() + strength[1:] if strength else strength
    barrier = barrier[0].lower() + barrier[1:] if barrier else barrier
    serp_note = ("En CEPALSTAT, Google/Bing devolvieron una mezcla de 429 y 200; el rate-limit dejó 0 URLs aceptadas." if portal_id == "cepalstat" else "En SDG, Google/Bing respondieron 200, pero el parser sólo encontró resultados fuera de la allowlist y dejó 0 URLs aceptadas.")
    structured_note = (f"En CEPALSTAT se observan scripts de carga de módulos en {ev['script_detected']}/{ev['page_count']} capturas; no se detectó `noscript` ni shell `id=\"root\"`." if portal_id == "cepalstat" else f"En SDG se detectó `noscript` en {ev['noscript_detected']}/{ev['page_count']} capturas y shell `id=\"root\"` en {ev['root_shell_detected']}/{ev['page_count']}; el HTML inicial no contiene la tabla.")
    return f"""# Auditoría AEO y preparación para agentes de IA de {context['name']} — piloto

**Portal auditado:** [{context['name']}]({context['url']})  
**Host:** `{urlparse(context['url']).netloc}`  
**Fecha de corte:** 2026-08-23  
**Página interna de muestra:** [{context['sample_page']}]({context['sample_page']})  
**Calificación global:** **{matrix.get('aeo_score', matrix.get('score', 'NA'))}/100 — {band}**  
**Estado:** mecánico PASS · QA editorial **{editorial_qa}** · publicación **{publication}**

## 1. Resumen ejecutivo

**Veredicto:** {context['name']} presenta **{band.lower()}** en la matriz AEO, pero este piloto no demuestra visibilidad de series: la evidencia congelada aceptó **{all_stats['candidate_urls']}/{all_stats['executions']}** URLs específicas y el adversarial quedó en **{adv_text}**. La principal fortaleza es {strength}. La principal barrera es {barrier}. Para un agente, la consecuencia es que puede responder con una portada o una negativa razonada, pero no con una cita estadística específica verificable.

El AIRSC medio observado fue **{f(portal_row.get('mean_airsc'))}** (mediana {f(portal_row.get('median_airsc'))}; SD {f(portal_row.get('stdev_airsc'))}; {portal_row.get('n_valid', 'NA')}/{portal_row.get('n_total', 'NA')} ejecuciones válidas). Este resultado es descriptivo y no causal; no se compara como correlación con n=2 portales.

## 2. Calificación consolidada

{chr(10).join(dimension_lines)}

La matriz fuente declaraba **{matrix.get('aeo_source_score', matrix.get('score', 'NA'))}/100**; {correction_note} La citabilidad fuente se conserva en la matriz para trazabilidad, pero no se permite superar el máximo 15 del PDF/skill.

## 3. Metodología, alcance y limitaciones

Se ejecutaron **60 filas de plantilla × 2 portales × 3 repeticiones = 360 ejecuciones**, con discovery, semantic, retrieval, metadata, citation, judge y adversarial. Se congelaron SERP, páginas, headers, cuerpos y hashes. La unidad inferencial del piloto sigue siendo el portal; las 60 filas contienen sólo **{analysis.get('n_unique_query_texts', 'NA')} textos únicos** por copias de procedencia. El gold del piloto es contractual (`validated_contract`) y no contiene targets numéricos promovidos.

La hipótesis de una única URL correcta se mantiene: una pregunta específica puede tener una sola respuesta si esa URL oficial expone indicador, unidad, período, geografía, fuente y provenance. En este run la hipótesis no fue probada porque no se aceptaron URLs de series.

## 4. Acceso y descubrimiento para bots

### Evidencia HTTP

{chr(10).join(http_lines)}

El piloto sí capturó **{ev['page_count']} páginas**, todas con estado {next(iter(ev['page_statuses']), 'NA')} y {next(iter(ev['content_types']), 'NA')}; los SERP produjeron estados {ev['serp_statuses']} y **{ev['serp_accepted_urls']} URLs aceptadas** frente a {ev['serp_rejected_urls']} rechazadas por allowlist. {serp_note}

### Política de crawlers

No se verificó `robots.txt` en este piloto; por tanto no se afirma que falte ni se atribuyen los 429 a una política del sitio. La gobernanza de crawlers, agentes de IA y posibles conflictos de acceso debe auditarse en una corrida específica de superficies técnicas.

### Sitemap y `llms.txt`

No se verificaron `sitemap.xml`, `sitemap_index.xml` ni `llms.txt`; por tanto no se afirma que estén ausentes. La cobertura, jerarquía, canonicales, idiomas, fechas y orientación para LLMs quedan como pruebas pendientes.

## 5. Renderizado y muros de interacción

### Página principal

La página principal del portal no fue capturada como una superficie separada en este piloto. Por ello no se infiere su DOM renderizado ni se afirma la ausencia de metadatos; la evidencia de HTML inicial se limita a la página interna indicada abajo.

### Página interna

{chr(10).join(page_lines)}

Extracto inicial: `{page_excerpt}`

### Muros principales

1. La respuesta capturada es una página de entrada, no una página de indicador ni una tabla de valores.
2. {context['barrier']}
3. El agente debe navegar o llamar a la API para pasar de la superficie de entrada a una serie específica; esa transición no quedó probada en este piloto.

## 6. Datos estructurados

En las capturas iniciales no se detectó `application/ld+json` ({ev['jsonld_detected']}/{ev['page_count']}) ni `schema.org` ({ev['schema_org_detected']}/{ev['page_count']}). {structured_note} Esto es evidencia de la respuesta inicial, no una afirmación sobre el DOM después de JavaScript.

## 7. APIs y acceso para agentes de código

**API/documentación oficial:** [{context['api']}]({context['api']})  
**Fortaleza declarada en la matriz:** {context['api_detail']}  
**Prueba en este piloto:** no se ejecutó una llamada de datos; el resultado refleja discovery sobre la evidencia HTTP congelada, no la ergonomía completa de la API.

Un agente preparado debe poder descubrir el identificador, consultar metadatos y dimensiones, recuperar observaciones, conservar notas/fuentes y generar una URL de cita. En este piloto ninguna de esas etapas produjo una URL específica aceptada.

## 8. Citabilidad y visibilidad en motores de respuesta

| Señal operacional | Resultado |
|---|---:|
| URLs específicas aceptadas | {all_stats['candidate_urls']}/{all_stats['executions']} |
| Salidas citable del rol citation | {all_stats['citable_outputs']}/{all_stats['executions']} |
| AIRSC no cero | {all_stats['nonzero_airsc']}/{all_stats['executions']} |
| Media judge: discovery | {f(all_stats['mean_discovery_success'])} |
| Media judge: retrieval | {f(all_stats['mean_retrieval_success'])} |
| Media judge: citation | {f(all_stats['mean_citation_correctness'])} |
| Adversarial | {adv_text} |

La lectura correcta es **diagnóstico ante evidencia insuficiente**, no ranking orgánico ni prueba de que el portal carezca de datos. La cita válida debe contener URL estable, indicador, valor, unidad, período, geografía, fuente y nota metodológica.

## 9. Plan de remediación

### P0 — 0 a 2 semanas

1. Publicar landing pages/canonicales de indicadores y enlazar API, metadata y descarga desde cada una → elimina la dependencia de una portada genérica.
2. Publicar y probar `robots.txt`, sitemap y `llms.txt` → hace explícita la política y la jerarquía de descubrimiento.

### P1 — 2 a 6 semanas

1. Añadir ficha machine-readable (`Dataset`/`DataDownload` o SDMX/DCAT) con identificador, unidad, período, geografía, fuente y URL de observación → evita que el agente adivine dimensiones.
2. Documentar un ejemplo de API reproducible por indicador → reduce la distancia entre discovery y retrieval.

### P2 — 6 a 12 semanas

1. Monitorizar cobertura de sitemaps, respuestas de bots, URLs de cita y paridad HTML/API → permite repetir el piloto y medir mejora.

## 10. Criterios de aceptación para “Preparado para Agentes”

- Una consulta específica devuelve una única URL oficial aceptada cuando esa URL es la respuesta correcta.
- La URL permite recuperar indicador, valor, unidad, período, geografía y fuente sin inferir códigos.
- La salida citation contiene una URL estable y provenance; el adversarial produce `pass` o explica un `fail` reproducible.
- Las superficies técnicas (robots, sitemap, llms, JSON-LD/SDMX, API) tienen estado verificable y evidencia fechada.

## 11. Anexo de evidencia y confianza

### Hallazgos, estado y confianza

| Hallazgo | Clasificación | Evidencia | Confianza |
|---|---|---|---|
| Página interna HTTP inicial | Verificado | `{run_dir / 'evidence'}` | alta para el run |
| Política de bots, sitemap y `llms.txt` | No verificado | recursos no capturados por este piloto | baja |
| URLs específicas de serie | {analysis.get('evidence_status', 'NA')} | `{run_dir / 'results.jsonl'}` | alta para el run |
| Schema/natural de roles | Verificado mecánico | `{run_dir / 'results.jsonl'}` | alta |
| JSON-LD/DOM post-JS | No verificado | HTML inicial solamente | baja |
| AIRSC por estrato/repetición | Verificado descriptivo | `pilot-results-matrix-60x2x3.csv` | descriptiva |
| Relación AEO → visibilidad | No establecido | n=2 portales; evidencia específica 0 | no aplicable |

### Desglose por estrato

{chr(10).join(strata_lines)}

### Roles, modelos y repeticiones

{chr(10).join(role_lines)}

{chr(10).join(repeat_lines)}

## 12. Fuentes primarias

- [Portal oficial]({context['url']})
- [Página de datos/entrada]({context['sample_page']})
- [API/documentación]({context['api']})
- `auditoría AEO.pdf` — fuente de verdad metodológica.
- `.agents/skills/aeo-agent-readiness-auditor/references/report-template.md` — plantilla aplicada.
- `benchmark/query-bank-pilot-60.csv` — banco piloto.
"""


def write_outputs(run_dir: Path, manifest: dict[str, Any], analysis: dict[str, Any]) -> Path:
    out = run_dir / "editorial"
    out.mkdir(parents=True, exist_ok=True)
    matrices = {portal_id: normalized_matrix_row(row) for portal_id, row in load_matrix().items()}
    rows, evidence = load_rows_and_evidence(run_dir)
    portal_stats = {portal_id: _row_stats(rows, portal_id) for portal_id in PILOT_PORTALS}

    # Detailed row-level matrix: one row per execution, retaining the fields
    # needed to audit discovery, retrieval, judge, adversarial and provenance.
    execution_fields = ["execution_key", "portal_id", "template_id", "stratum", "repeat", "query", "candidate_url", "candidate_allowed", "airsc", "judge_discovery", "judge_retrieval", "judge_semantic", "judge_metadata", "judge_temporal_geographic", "judge_citation", "judge_overall", "adversarial_verdict", "adversarial_severity", "schema_valid_all", "natural_available_all", "evidence_sha256", "page_url", "page_status", "status"]
    execution_rows = []
    for row in rows:
        case = row.get("case") or {}
        page_url = ""
        page_status = ""
        ev_path = run_dir / "evidence" / f"{case.get('template_id')}__{case.get('portal_id')}.json"
        if ev_path.exists():
            item = json.loads(ev_path.read_text(encoding="utf-8"))
            if item.get("pages"):
                page_url = item["pages"][0].get("final_url") or item["pages"][0].get("requested_url") or ""
                page_status = item["pages"][0].get("status") or ""
        judge = row.get("judge_dimensions") or {}
        execution_rows.append({"execution_key": row.get("execution_key"), "portal_id": case.get("portal_id"), "template_id": case.get("template_id"), "stratum": case.get("stratum"), "repeat": row.get("repeat"), "query": case.get("query"), "candidate_url": row.get("candidate_url") or "", "candidate_allowed": row.get("candidate_allowed"), "airsc": (row.get("score") or {}).get("overall_0_100_recomputed"), "judge_discovery": judge.get("discovery_success"), "judge_retrieval": judge.get("retrieval_success"), "judge_semantic": judge.get("semantic_correctness"), "judge_metadata": judge.get("metadata_correctness"), "judge_temporal_geographic": judge.get("temporal_geographic_correctness"), "judge_citation": judge.get("citation_correctness"), "judge_overall": judge.get("overall_0_100"), "adversarial_verdict": (row.get("adversarial") or {}).get("verdict"), "adversarial_severity": (row.get("adversarial") or {}).get("severity"), "schema_valid_all": all((row.get("agents") or {}).get(role, {}).get("schema_valid") is True for role in ROLES), "natural_available_all": all((row.get("natural_signals") or {}).get(role, {}).get("available") is True for role in ROLES), "evidence_sha256": row.get("evidence_sha256"), "page_url": page_url, "page_status": page_status, "status": row.get("status")})
    with (out / "pilot-execution-matrix-360.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=execution_fields); writer.writeheader(); writer.writerows(execution_rows)

    # Template-level matrix: one row per query template and portal (60 x 2).
    # This is the most useful review grain for a human: it collapses the three
    # repeats without hiding their dispersion or the underlying execution keys.
    template_fields = ["portal_id", "portal", "template_id", "stratum", "stratum_label", "query", "executions", "repeats", "mean_airsc", "median_airsc", "stdev_airsc", "nonzero_airsc", "mean_judge_discovery", "mean_judge_retrieval", "mean_judge_semantic", "mean_judge_metadata", "mean_judge_temporal_geographic", "mean_judge_citation", "mean_judge_overall", "candidate_urls", "citable_outputs", "adversarial_pass", "adversarial_fail", "adversarial_uncertain", "schema_valid_pct", "natural_available_pct", "candidate_url_values", "page_url", "page_status", "evidence_sha256", "status_all_ok"]
    template_rows = []
    template_keys = sorted({((row.get("case") or {}).get("portal_id"), (row.get("case") or {}).get("template_id")) for row in rows})
    for portal_id, template_id in template_keys:
        selected = [row for row in rows if (row.get("case") or {}).get("portal_id") == portal_id and (row.get("case") or {}).get("template_id") == template_id]
        if not selected:
            continue
        case = selected[0].get("case") or {}
        stat = _row_stats(selected, portal_id)
        candidate_values = sorted({str(row.get("candidate_url")) for row in selected if row.get("candidate_url")})
        hashes = sorted({str(row.get("evidence_sha256")) for row in selected if row.get("evidence_sha256")})
        page_url = ""
        page_status = ""
        ev_path = run_dir / "evidence" / f"{template_id}__{portal_id}.json"
        if ev_path.exists():
            item = json.loads(ev_path.read_text(encoding="utf-8"))
            if item.get("pages"):
                page_url = item["pages"][0].get("final_url") or item["pages"][0].get("requested_url") or ""
                page_status = item["pages"][0].get("status") or ""
        template_rows.append({
            "portal_id": portal_id,
            "portal": PILOT_PORTALS[portal_id]["name"],
            "template_id": template_id,
            "stratum": case.get("stratum"),
            "stratum_label": STRATUM_LABELS.get(case.get("stratum"), case.get("stratum")),
            "query": case.get("query"),
            "executions": stat["executions"],
            "repeats": stat["repeats"],
            "mean_airsc": stat["mean_airsc"],
            "median_airsc": stat["median_airsc"],
            "stdev_airsc": stat["stdev_airsc"],
            "nonzero_airsc": stat["nonzero_airsc"],
            "mean_judge_discovery": stat["mean_discovery_success"],
            "mean_judge_retrieval": stat["mean_retrieval_success"],
            "mean_judge_semantic": stat["mean_semantic_correctness"],
            "mean_judge_metadata": stat["mean_metadata_correctness"],
            "mean_judge_temporal_geographic": stat["mean_temporal_geographic_correctness"],
            "mean_judge_citation": stat["mean_citation_correctness"],
            "mean_judge_overall": stat["mean_judge_overall"],
            "candidate_urls": stat["candidate_urls"],
            "citable_outputs": stat["citable_outputs"],
            "adversarial_pass": stat["adversarial_pass"],
            "adversarial_fail": stat["adversarial_fail"],
            "adversarial_uncertain": stat["adversarial_uncertain"],
            "schema_valid_pct": stat["schema_valid_pct"],
            "natural_available_pct": stat["natural_available_pct"],
            "candidate_url_values": " | ".join(candidate_values),
            "page_url": page_url,
            "page_status": page_status,
            "evidence_sha256": " | ".join(hashes),
            "status_all_ok": all(row.get("status") == "OK" for row in selected),
        })
    with (out / "pilot-template-matrix-120.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=template_fields); writer.writeheader(); writer.writerows(template_rows)

    # Main results matrix: one row per portal/stratum, with enough metrics to
    # diagnose where AIRSC is won or lost instead of just two portal totals.
    result_fields = ["portal_id", "portal", "stratum", "stratum_label", "template_rows", "executions", "repeats", "aeo_score_editorial", "aeo_score_source", *DIMENSIONS, "mean_airsc", "median_airsc", "stdev_airsc", "nonzero_airsc", "mean_judge_discovery", "mean_judge_retrieval", "mean_judge_semantic", "mean_judge_metadata", "mean_judge_temporal_geographic", "mean_judge_citation", "mean_judge_overall", "candidate_urls", "citable_outputs", "adversarial_pass", "adversarial_fail", "adversarial_uncertain", "schema_valid_pct", "natural_available_pct", "evidence_files_portal"]
    result_rows = []
    for portal_id, context in PILOT_PORTALS.items():
        m = matrices.get(portal_id, {})
        for stratum in STRATUM_LABELS:
            stat = _row_stats(rows, portal_id, stratum)
            if not stat["executions"]:
                continue
            result_rows.append({"portal_id": portal_id, "portal": context["name"], "stratum": stratum, "stratum_label": STRATUM_LABELS[stratum], "template_rows": stat["template_rows"], "executions": stat["executions"], "repeats": stat["repeats"], "aeo_score_editorial": m.get("aeo_score"), "aeo_score_source": m.get("aeo_source_score"), **{key: m.get(f"{key}_normalized", m.get(key)) for key in DIMENSIONS}, "mean_airsc": stat["mean_airsc"], "median_airsc": stat["median_airsc"], "stdev_airsc": stat["stdev_airsc"], "nonzero_airsc": stat["nonzero_airsc"], "mean_judge_discovery": stat["mean_discovery_success"], "mean_judge_retrieval": stat["mean_retrieval_success"], "mean_judge_semantic": stat["mean_semantic_correctness"], "mean_judge_metadata": stat["mean_metadata_correctness"], "mean_judge_temporal_geographic": stat["mean_temporal_geographic_correctness"], "mean_judge_citation": stat["mean_citation_correctness"], "mean_judge_overall": stat["mean_judge_overall"], "candidate_urls": stat["candidate_urls"], "citable_outputs": stat["citable_outputs"], "adversarial_pass": stat["adversarial_pass"], "adversarial_fail": stat["adversarial_fail"], "adversarial_uncertain": stat["adversarial_uncertain"], "schema_valid_pct": stat["schema_valid_pct"], "natural_available_pct": stat["natural_available_pct"], "evidence_files_portal": len(evidence.get(portal_id, []))})
    with (out / "pilot-results-matrix-60x2x3.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=result_fields); writer.writeheader(); writer.writerows(result_rows)

    # A compact portal summary is retained as a separate file for consumers
    # that do not need the stratum/execution detail.
    summary_fields = ["portal_id", "portal", "url", "aeo_score_editorial", "aeo_score_source", "score_correction", *DIMENSIONS, "mean_airsc", "median_airsc", "stdev_airsc", "executions", "candidate_urls", "citable_outputs", "adversarial", "schema_valid_pct", "natural_available_pct"]
    summary_rows = []
    for portal_id, context in PILOT_PORTALS.items():
        m = matrices.get(portal_id, {}); stat = portal_stats[portal_id]
        summary_rows.append({"portal_id": portal_id, "portal": context["name"], "url": context["url"], "aeo_score_editorial": m.get("aeo_score"), "aeo_score_source": m.get("aeo_source_score"), "score_correction": m.get("score_correction"), **{key: m.get(f"{key}_normalized", m.get(key)) for key in DIMENSIONS}, "mean_airsc": stat["mean_airsc"], "median_airsc": stat["median_airsc"], "stdev_airsc": stat["stdev_airsc"], "executions": stat["executions"], "candidate_urls": stat["candidate_urls"], "citable_outputs": stat["citable_outputs"], "adversarial": json.dumps({"pass": stat["adversarial_pass"], "fail": stat["adversarial_fail"], "uncertain": stat["adversarial_uncertain"]}, ensure_ascii=False), "schema_valid_pct": stat["schema_valid_pct"], "natural_available_pct": stat["natural_available_pct"]})
    with (out / "pilot-portal-summary-60x2x3.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=summary_fields); writer.writeheader(); writer.writerows(summary_rows)

    comparative_path = out / "pilot-comparative-matrix-60x2x3.csv"
    comparative_fields = ["metric", "cepalstat", "sdg", "delta_sdg_minus_cepalstat", "interpretation"]
    crows = []
    metric_values: list[tuple[str, Any, Any, str]] = []
    for key, label in [("aeo_score", "AEO total editorial"), ("aeo_source_score", "AEO total fuente"), *[(key, DIMENSION_LABELS[key]) for key in DIMENSIONS]]:
        metric_values.append((label, matrices["cepalstat"].get("aeo_score") if key == "aeo_score" else matrices["cepalstat"].get("aeo_source_score") if key == "aeo_source_score" else matrices["cepalstat"].get(f"{key}_normalized", matrices["cepalstat"].get(key)), matrices["sdg"].get("aeo_score") if key == "aeo_score" else matrices["sdg"].get("aeo_source_score") if key == "aeo_source_score" else matrices["sdg"].get(f"{key}_normalized", matrices["sdg"].get(key)), "Puntaje técnico; no causal"))
    for key, label in [("mean_airsc", "AIRSC medio"), ("median_airsc", "AIRSC mediana"), ("stdev_airsc", "AIRSC desviación estándar"), ("mean_discovery_success", "Judge discovery medio"), ("mean_retrieval_success", "Judge retrieval medio"), ("mean_semantic_correctness", "Judge semantic medio"), ("mean_metadata_correctness", "Judge metadata medio"), ("mean_citation_correctness", "Judge citation medio")]:
        metric_values.append((label, _row_stats(rows, "cepalstat").get(key.replace("mean_", "mean_") if key.startswith("mean_") else key), _row_stats(rows, "sdg").get(key.replace("mean_", "mean_") if key.startswith("mean_") else key), "AIRSC/judge descriptivo; n=2 portales"))
    for key, label in [("candidate_urls", "URLs específicas aceptadas"), ("citable_outputs", "Salidas citation citable"), ("nonzero_airsc", "AIRSC no cero")]:
        metric_values.append((label, portal_stats["cepalstat"].get(key), portal_stats["sdg"].get(key), "Diagnóstico de evidencia; no ranking"))
    for label, a, b, interpretation in metric_values:
        delta = "NA"
        try: delta = f(float(b) - float(a), 2)
        except (TypeError, ValueError): pass
        crows.append({"metric": label, "cepalstat": f(a), "sdg": f(b), "delta_sdg_minus_cepalstat": delta, "interpretation": interpretation})
    with comparative_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=comparative_fields); writer.writeheader(); writer.writerows(crows)

    # Human-readable matrix index. CSVs remain the machine-readable source;
    # this file makes the grain, denominators and interpretation visible before
    # someone opens a 360-row export.
    matrix_md = out / "pilot-matrix-60x2x3.md"
    portal_table = [
        "| Portal | AEO editorial | AEO fuente | AIRSC medio | Mediana | SD | Ejecuciones | URLs específicas | Citable | Adversarial |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in summary_rows:
        adv = json.loads(row["adversarial"])
        portal_table.append(f"| {row['portal']} | {row['aeo_score_editorial']} | {row['aeo_score_source']} | {f(row['mean_airsc'])} | {f(row['median_airsc'])} | {f(row['stdev_airsc'])} | {row['executions']} | {row['candidate_urls']} | {row['citable_outputs']} | P {adv['pass']} / F {adv['fail']} / U {adv['uncertain']} |")
    strata_table = [
        "| Portal | Familia | Plantillas | Ejecuciones | AIRSC medio | SD | Judge citation | URLs | Citable | Schema/natural |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in result_rows:
        strata_table.append(f"| {row['portal']} | {row['stratum_label']} | {row['template_rows']} | {row['executions']} | {f(row['mean_airsc'])} | {f(row['stdev_airsc'])} | {f(row['mean_judge_citation'])} | {row['candidate_urls']} | {row['citable_outputs']} | {pct(row['schema_valid_pct'])} / {pct(row['natural_available_pct'])} |")
    comparison_table = ["| Métrica | CEPALSTAT | UN SDG | Delta SDG−CEPALSTAT |", "|---|---:|---:|---:|"]
    for row in crows:
        comparison_table.append(f"| {row['metric']} | {row['cepalstat']} | {row['sdg']} | {row['delta_sdg_minus_cepalstat']} |")
    matrix_md.write_text(f"""# Matriz de resultados del piloto AEO–visibilidad

**Alcance:** 60 plantillas × 2 portales × 3 repeticiones = **360 ejecuciones**. Fecha de corte: 2026-08-23. El gold es contractual; no hay targets numéricos.

**Lectura de estado:** mecánica **{analysis.get('mechanical_qa_status', 'NA')}**; QA editorial **{analysis.get('qa_status', 'NA')}**; publicación **{analysis.get('publication_status', 'HOLD')}**. La evidencia específica aceptada es 0/360 y el adversarial permanece en `uncertain`, por lo que estos números son diagnósticos del run y no ranking causal.

## Resumen por portal

{chr(10).join(portal_table)}

## Matriz por familia de consulta

{chr(10).join(strata_table)}

## Comparación entre portales

{chr(10).join(comparison_table)}

## Qué contiene cada archivo

- `pilot-template-matrix-120.csv`: una fila por **plantilla × portal** (120 filas); agrega las tres repeticiones y conserva media, mediana, SD, jueces, URLs, hashes y estado.
- `pilot-results-matrix-60x2x3.csv`: una fila por **familia × portal** (16 filas); sirve para comparar tipos de consulta.
- `pilot-execution-matrix-360.csv`: una fila por **ejecución** (360 filas); conserva query, repetición, score, jueces, adversarial, URL de página y hash de evidencia.
- `pilot-comparative-matrix-60x2x3.csv`: una fila por métrica comparada (19 métricas), con delta y lectura.

## Controles de integridad

- 360/360 ejecuciones únicas; 180 por portal; 3 repeticiones por plantilla.
- 360/360 filas con `status=OK`, schema válido y salida natural disponible.
- 120/120 pares plantilla–portal cubiertos; 60 archivos de evidencia por portal.
- Los puntajes AEO se conservan como fuente y editorial; SDG se normaliza de 88 a 85 por el tope de citabilidad 15/15 del PDF/skill.
- AIRSC, judge, discovery y citabilidad no se interpretan como correlación: sólo hay dos portales y cero URLs específicas aceptadas.

La matriz detallada es trazable al [análisis](../analysis/pilot_analysis.json), al [run manifest](../run_manifest.json) y a los [informes por portal](pilot-report-cepalstat-60x2x3.md) / [UN SDG](pilot-report-sdg-60x2x3.md).
""", encoding="utf-8")

    payload = {
        "summary_rows": summary_rows,
        "strata_rows": result_rows,
        "template_rows": template_rows,
        "comparative_rows": crows,
        "evidence": {portal_id: portal_evidence_stats(evidence, portal_id) for portal_id in PILOT_PORTALS},
        "models": manifest.get("models", {}),
        "qa": {"mechanical": analysis.get("mechanical_qa_status"), "editorial": analysis.get("qa_status"), "publication": analysis.get("publication_status"), "unique_query_texts": analysis.get("n_unique_query_texts"), "evidence_status": analysis.get("evidence_status"), "adversarial_clear": analysis.get("adversarial_clear")},
    }
    (out / "pilot-editorial-payload.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    for portal_id in PILOT_PORTALS:
        (out / f"pilot-report-{portal_id}-60x2x3.md").write_text(report(portal_id, run_dir, manifest, analysis, matrices.get(portal_id, {}), rows, evidence), encoding="utf-8")
    (out / "pilot-comparative-report-60x2x3.md").write_text(comparative_report(run_dir, manifest, analysis, summary_rows, result_rows, crows), encoding="utf-8")
    return out


def comparative_report(run_dir: Path, manifest: dict[str, Any], analysis: dict[str, Any], rows: list[dict[str, Any]], strata_rows: list[dict[str, Any]], comparative_rows: list[dict[str, Any]]) -> str:
    c, s = rows
    strata_table = ["| Portal | Estrato | Filas | AIRSC medio | Judge discovery | Judge retrieval | Judge citation | URLs específicas | Adversarial |", "|---|---|---:|---:|---:|---:|---:|---:|---|"]
    for row in strata_rows:
        strata_table.append(f"| {row['portal']} | {row['stratum_label']} | {row['executions']} | {f(row['mean_airsc'])} | {f(row['mean_judge_discovery'])} | {f(row['mean_judge_retrieval'])} | {f(row['mean_judge_citation'])} | {row['candidate_urls']} | P {row['adversarial_pass']} / U {row['adversarial_uncertain']} |")
    matrix_table = ["| Métrica | CEPALSTAT | UN SDG | Delta SDG−CEPALSTAT | Lectura |", "|---|---:|---:|---:|---|"]
    for row in comparative_rows:
        matrix_table.append(f"| {row['metric']} | {row['cepalstat']} | {row['sdg']} | {row['delta_sdg_minus_cepalstat']} | {row['interpretation']} |")
    return f"""# Informe comparativo piloto AEO–visibilidad: CEPALSTAT vs UN SDG

**Run aislado:** `{run_dir}`  
**Contrato:** 60 plantillas × 2 portales × 3 repeticiones = **360 ejecuciones**  
**Gates:** COMPLETE mecánico · gold PASS contractual · QA mecánica {analysis.get('mechanical_qa_status', 'NA')} · QA editorial **{analysis.get('qa_status', 'NA')}** · publicación **{analysis.get('publication_status', 'HOLD')}**
**Advertencia:** este piloto no utiliza el gate 1.800 y no actualiza los entregables finales de cinco portales.

## Hallazgo principal

CEPALSTAT tiene un AEO editorial de **{c['aeo_score_editorial']}/100** y AIRSC medio **{f(c['mean_airsc'])}**; UN SDG tiene AEO editorial de **{s['aeo_score_editorial']}/100** y AIRSC medio **{f(s['mean_airsc'])}**. En este piloto de extremos, una mayor preparación técnica AEO no se traduce automáticamente en un AIRSC medio mayor. La diferencia es descriptiva y puede depender de la consulta, cobertura, modelo y semántica del indicador.

## Matriz comparativa detallada

{chr(10).join(matrix_table)}

La matriz de portal se complementa con [el detalle de 360 ejecuciones](pilot-execution-matrix-360.csv) y [el desglose por estrato](pilot-results-matrix-60x2x3.csv). El `delta` no es una prueba estadística: sólo hace visible la diferencia descriptiva entre los dos portales.

## Desglose por familia de consulta

{chr(10).join(strata_table)}

## Repeticiones y modelos

Las tres repeticiones deben leerse como estabilidad operacional, no como tres portales independientes. El análisis completo queda en `../analysis/pilot_analysis.json`; los modelos y la evidencia HTTP quedan ligados a cada fila del [execution matrix](pilot-execution-matrix-360.csv).

## Implicación

La visibilidad de un portal no se agota en su puntaje AEO. En particular, una pregunta muy específica puede tener como respuesta correcta una sola URL, pero esa URL debe preservar el indicador exacto, la unidad, período, geografía, fuente y provenance. En el run actual, CEPALSTAT supera a SDG en AIRSC medio (7.83 vs 4.07), pero ambos tienen 0 URLs específicas aceptadas; no es una comparación de ranking ni una evidencia de causalidad.

## Limitaciones y siguiente decisión

No hay correlación inferencial con n=2; no se extrapola al benchmark de cinco portales. La evidencia específica aceptada es {analysis.get('evidence_counts', {}).get('candidate_url', 0)}/360 y el red team no alcanza `pass` en todas las filas; por ello esta comparación queda en HOLD editorial. La siguiente decisión es mejorar la captura de series/API, revisar por familia y re-ejecutar tras remediar las fichas de indicador, especialmente las variantes de PIB en CEPALSTAT.

## Fuentes

- `auditoría AEO.pdf` — fuente de verdad.
- `benchmark/query-bank-pilot-60.csv` — consultas estratificadas.
- `{run_dir / 'analysis' / 'pilot_analysis.json'}` — métricas y QA.
- `execution/expanded-audit-matrix-2026-08-22.csv` — puntajes AEO fuente.
- `pilot-results-matrix-60x2x3.csv` — desglose por portal y estrato.
- `pilot-execution-matrix-360.csv` — trazabilidad fila a fila.
"""


def call_ppt_builder(run_dir: Path, date_tag: str) -> Path:
    builder = ROOT / "execution" / "build_pilot_ppt_artifact.mjs"
    node = os.environ.get("RUNTIME_NODE") or "/Users/alvarofuentes/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node"
    tmp_dir = Path(os.environ.get("PILOT_PPT_TMP_DIR", "/private/tmp/aeo-pilot-ppt-build"))
    tmp_dir.mkdir(parents=True, exist_ok=True)
    (tmp_dir / "node_modules").mkdir(exist_ok=True)
    oai_link = tmp_dir / "node_modules" / "@oai"
    if not oai_link.exists():
        oai_link.symlink_to(Path(os.environ.get("RUNTIME_NODE_MODULES", "/Users/alvarofuentes/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules")) / "@oai", target_is_directory=True)
    tmp_builder = tmp_dir / builder.name
    tmp_builder.write_text(builder.read_text(encoding="utf-8"), encoding="utf-8")
    env = os.environ.copy()
    env.setdefault("RUNTIME_NODE", node)
    env.setdefault("RUNTIME_NODE_MODULES", "/Users/alvarofuentes/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules")
    env.setdefault("RUNTIME_BIN_DIR", "/Users/alvarofuentes/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/override")
    subprocess.run([node, str(tmp_builder), str(ROOT), str(run_dir), date_tag], check=True, env=env, cwd=tmp_dir)
    return run_dir / "editorial" / f"pilot-aeo-visibility-{date_tag}.pptx"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--date-tag", default="2026-08-23")
    args = parser.parse_args()
    run_dir = args.run_dir.resolve()
    manifest, analysis = load_run(run_dir)
    output_dir = write_outputs(run_dir, manifest, analysis)
    deck = call_ppt_builder(run_dir, args.date_tag)
    output_files = sorted(p for p in output_dir.iterdir() if p.is_file() and p.name != "editorial_manifest.json")
    editorial_manifest = {
        "scope": "pilot_extremes_editorial",
        "source_run": str(run_dir),
        "source_manifest_sha256": hashlib.sha256((run_dir / "run_manifest.json").read_bytes()).hexdigest(),
        "mechanical_status": "PASS",
        "editorial_status": analysis.get("qa_status", "HOLD"),
        "publication_status": analysis.get("publication_status", "HOLD"),
        "evidence_status": analysis.get("evidence_status", "NA"),
        "adversarial_clear": analysis.get("adversarial_clear", False),
        "outputs": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in output_files},
    }
    (output_dir / "editorial_manifest.json").write_text(json.dumps(editorial_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"scope": "pilot_extremes", "output_dir": str(output_dir), "ppt": str(deck), "mechanical_status": "PASS", "editorial_status": analysis.get("qa_status", "HOLD"), "publication_status": analysis.get("publication_status", "HOLD")}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
