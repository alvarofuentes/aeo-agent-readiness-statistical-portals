import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const ROOT = path.resolve(process.argv[2] || process.cwd());
const RUN_DIR = path.resolve(process.argv[3] || path.join(ROOT, "benchmark/results/e2e_smoke_2026-08-23"));
const OUTPUT_DIR = path.resolve(process.argv[4] || path.join(ROOT, "outputs/e2e-smoke-2026-08-23"));
const PREVIEW_DIR = path.join(RUN_DIR, "sheet-previews");
const results = JSON.parse(await fs.readFile(path.join(RUN_DIR, "e2e_results.json"), "utf8"));
await fs.mkdir(OUTPUT_DIR, { recursive: true });
await fs.mkdir(PREVIEW_DIR, { recursive: true });

const n = (value) => value === null || value === undefined ? "" : value;
const jsonCell = (value) => value === null || value === undefined ? "" : JSON.stringify(value, null, 0);
const sourceFile = (name) => path.relative(ROOT, path.join(RUN_DIR, name));

const summaryRows = results.map((result) => {
  const search = result.search;
  const retrieval = result.retrieval;
  const verdict = result.verdict;
  const source = retrieval.source && typeof retrieval.source === "object" ? retrieval.source.description : retrieval.source;
  return [
    result.portal_id,
    result.query,
    search.decomposition.concept,
    search.decomposition.country,
    search.decomposition.year,
    search.series_code || search.indicator_id,
    search.candidate_url,
    retrieval.request_url,
    retrieval.value === null || retrieval.value === undefined ? null : Number(retrieval.value),
    retrieval.unit,
    source,
    retrieval.rows_returned,
    retrieval.rows_after_dimension_filter,
    verdict.metadata_complete,
    verdict.citation_citable,
    verdict.e2e_pass,
    verdict.reason,
  ];
});

const stepRows = results.flatMap((result) => result.steps.map((step) => [
  result.portal_id,
  step.step,
  step.status,
  step.input === null || step.input === undefined ? "" : typeof step.input === "string" ? step.input : jsonCell(step.input),
  step.evidence_url,
  step.detail,
]));

const candidateRows = results.flatMap((result) => {
  const search = result.search;
  const matches = search.matches?.length ? search.matches : search.selected ? [search.selected] : [];
  return matches.map((candidate, index) => [
    result.portal_id,
    index + 1,
    candidate.text || candidate.series_description || candidate.indicator_description,
    search.indicator_id,
    candidate.indicator_code,
    candidate.series_code,
    candidate.series_uri,
    Boolean(candidate === search.selected || JSON.stringify(candidate) === JSON.stringify(search.selected)),
    search.candidate_url,
    search.capture_method,
  ]);
});

const evidenceRows = results.flatMap((result) => {
  const search = result.search;
  const retrieval = result.retrieval;
  const isCepal = result.portal_id === "cepalstat";
  return [
    [result.portal_id, "catálogo / búsqueda textual", search.catalog_url, search.capture_method, "observada", isCepal ? sourceFile("cepal_search_capture.json") : sourceFile("sdg_search_capture.json"), "El catálogo se consultó con texto; no se usó sólo la portada."],
    [result.portal_id, "candidato específico", search.candidate_url, search.capture_method, search.candidate_allowed ? "allowlisted" : "rejected", "", "URL oficial de indicador/serie/API."],
    [result.portal_id, "recuperación de datos", retrieval.request_url, retrieval.capture_method, retrieval.http_status, isCepal ? sourceFile("cepal_api_capture.json") : sourceFile("sdg_browser_capture.json"), `Filas recibidas=${retrieval.rows_returned}; filas seleccionadas=${retrieval.rows_after_dimension_filter}.`],
    [result.portal_id, "superficie de metadatos", search.technical_url || search.series_url, search.capture_method, "observada", isCepal ? sourceFile("cepal_browser_capture.json") : sourceFile("sdg_browser_capture.json"), "Definición, unidad, fuente y periodo revisados."],
  ];
});

const qaRows = results.flatMap((result) => {
  const v = result.verdict;
  return [
    [result.portal_id, "consulta descompuesta", true, "Concepto, geografía, periodo y dimensiones explicitados."],
    [result.portal_id, "búsqueda interna del catálogo", v.search_success, "Se encontró un indicador/serie específico dentro del portal."],
    [result.portal_id, "candidato oficial", v.candidate_allowed, "La URL no es homepage ni un dominio externo."],
    [result.portal_id, "valor recuperado", v.retrieval_success, "El dato aparece en la respuesta estructurada."],
    [result.portal_id, "metadatos completos", v.metadata_complete, "Se comprobó unidad, fuente, definición/metodología y periodo."],
    [result.portal_id, "cita reproducible", v.citation_citable, "La salida se puede reconstruir con una URL oficial específica."],
    [result.portal_id, "puerta end-to-end", v.e2e_pass, v.reason],
  ];
});

const methodRows = [
  ["Objetivo", "Validar la cadena completa antes de reiniciar las 360 ejecuciones."],
  ["CEPALSTAT", "Consulta textual del catálogo renderizado → indicador 2203 → API con members=224,29194 → valor, unidad, fuente y ficha técnica."],
  ["UN SDG", "Consulta textual del catálogo Indicator/List → serie SI_POV_DAY1 → API Series/Data para M49=152 y 2024 → selección explícita de dimensiones."],
  ["Gate", "Una prueba sólo vale si hay candidato específico, HTTP 200, valor, metadatos completos y URL oficial reproducible."],
  ["Alcance", "2 consultas end-to-end; el benchmark 60×2×3 queda detenido hasta aprobación del usuario."],
  ["Importante", "SDG devuelve 8 combinaciones para la misma serie; la fila informada es la que cumple Age=ALLAGE, Location=ALLAREA, Sex=BOTHSEX y Reporting Type=G."],
];

const wb = Workbook.create();

const palette = {
  navy: "#12304A",
  teal: "#0E7490",
  pale: "#E6F4F1",
  bluePale: "#E8F0F7",
  green: "#DCFCE7",
  red: "#FEE2E2",
  amber: "#FEF3C7",
  ink: "#172B4D",
  muted: "#5B6B7A",
  line: "#D5DEE8",
};

function setupSheet(name, title, subtitle, headers, rows, widths = []) {
  const sheet = wb.worksheets.add(name);
  sheet.showGridLines = false;
  const colCount = headers.length;
  const endCol = String.fromCharCode(64 + colCount);
  sheet.mergeCells(`A1:${endCol}1`);
  sheet.getRange("A1").values = [[title]];
  sheet.getRange(`A1:${endCol}1`).format = { fill: palette.navy, font: { color: "#FFFFFF", bold: true, size: 16 }, horizontalAlignment: "left", verticalAlignment: "center" };
  sheet.getRange("A1").format.rowHeight = 30;
  sheet.mergeCells(`A2:${endCol}2`);
  sheet.getRange("A2").values = [[subtitle]];
  sheet.getRange(`A2:${endCol}2`).format = { fill: palette.bluePale, font: { color: palette.muted, italic: true, size: 10 }, wrapText: true, verticalAlignment: "center" };
  sheet.getRange("A2").format.rowHeight = 30;
  sheet.getRange(`A4:${endCol}4`).values = [headers];
  sheet.getRange(`A4:${endCol}4`).format = { fill: palette.teal, font: { color: "#FFFFFF", bold: true, size: 10 }, wrapText: true, verticalAlignment: "center", borders: { preset: "outside", style: "thin", color: palette.teal } };
  sheet.getRange(`A4:${endCol}4`).format.rowHeight = 28;
  if (rows.length) {
    sheet.getRangeByIndexes(4, 0, rows.length, colCount).values = rows;
    sheet.getRangeByIndexes(4, 0, rows.length, colCount).format = { font: { color: palette.ink, size: 10 }, wrapText: true, verticalAlignment: "top", borders: { preset: "inside", style: "thin", color: palette.line } };
    sheet.getRangeByIndexes(4, 0, rows.length, colCount).format.rowHeight = 36;
  }
  widths.forEach((width, index) => {
    const cell = sheet.getRangeByIndexes(0, index, Math.max(rows.length + 4, 4), 1);
    cell.format.columnWidth = width;
  });
  sheet.freezePanes.freezeRows(4);
  if (colCount > 2) sheet.freezePanes.freezeColumns(2);
  return sheet;
}

const summary = setupSheet(
  "Resumen",
  "Smoke test end-to-end · revisión previa al benchmark",
  "Cada fila representa una consulta real: texto → búsqueda dentro del portal → serie/indicador → dato → metadatos → cita. El benchmark masivo permanece detenido.",
  ["Portal", "Consulta", "Concepto", "País", "Año", "Serie / indicador", "URL candidata", "URL de recuperación", "Valor", "Unidad", "Fuente", "Filas recibidas", "Filas seleccionadas", "Metadatos completos", "Cita reproducible", "Gate E2E", "Lectura"],
  summaryRows,
  [14, 42, 34, 12, 8, 18, 42, 60, 16, 20, 30, 14, 16, 16, 16, 12, 34],
);
const method = setupSheet("Método", "Cómo leer esta planilla", "La planilla documenta el comportamiento observable y los gates; no sustituye todavía la ejecución de 360 filas.", ["Elemento", "Descripción"], methodRows, [28, 110]);
const steps = setupSheet("Pasos", "Trazabilidad del flujo por portal", "Un paso fallido invalida la afirmación de visibilidad para esa consulta.", ["Portal", "Paso", "Estado", "Entrada / salida", "URL de evidencia", "Detalle"], stepRows, [14, 24, 12, 70, 60, 38]);
const candidates = setupSheet("Candidatos", "Candidatos encontrados dentro del portal", "La búsqueda devuelve un objeto específico; la homepage no cuenta como candidato.", ["Portal", "Rank", "Etiqueta", "Indicator ID", "Indicator code", "Series code", "Series URI", "Seleccionado", "URL candidata", "Método de captura"], candidateRows, [14, 8, 58, 14, 16, 18, 38, 12, 54, 32]);
const evidence = setupSheet("Evidencia", "Fuentes y respuestas observadas", "Las rutas relativas apuntan a las capturas JSON guardadas junto a esta planilla.", ["Portal", "Rol de evidencia", "URL", "Método", "Estado", "Archivo local", "Detalle"], evidenceRows, [14, 26, 64, 32, 14, 48, 44]);
const qa = setupSheet("QA", "Puertas de aceptación", "PASS aquí significa que la consulta puede sostener una afirmación específica; no significa que el portal completo sea perfecto.", ["Portal", "Aserción", "Pass", "Evidencia / criterio"], qaRows, [14, 28, 10, 100]);

// Semantic number and status formatting.
summary.getRange("E5:E6").format.numberFormat = [["0"], ["0"]];
summary.getRange("I5:I6").format.numberFormat = [["#,##0.########"], ["0.########"]];
for (const range of [summary.getRange("N5:P6"), qa.getRange("C5:C18")]) {
  range.format.horizontalAlignment = "center";
}
for (const row of [5, 6]) {
  summary.getRange(`N${row}:P${row}`).format.fill = palette.green;
}
for (let row = 5; row <= qaRows.length + 4; row += 1) {
  const passed = qa.getRange(`C${row}`).values?.[0]?.[0];
  qa.getRange(`C${row}`).format.fill = passed === true ? palette.green : palette.red;
}
for (let row = 5; row <= stepRows.length + 4; row += 1) {
  const status = steps.getRange(`C${row}`).values?.[0]?.[0];
  steps.getRange(`C${row}`).format.fill = status === "pass" ? palette.green : status === "fail" ? palette.red : palette.amber;
}

const inspectTargets = [
  ["Resumen", "A1:Q7"],
  ["Método", "A1:B10"],
  ["Pasos", `A1:F${Math.min(stepRows.length + 4, 25)}`],
  ["Candidatos", `A1:J${candidateRows.length + 4}`],
  ["Evidencia", `A1:G${evidenceRows.length + 4}`],
  ["QA", `A1:D${qaRows.length + 4}`],
];
for (const [sheetName, range] of inspectTargets) {
  const preview = await wb.render({ sheetName, range, scale: 1, format: "png" });
  await fs.writeFile(path.join(PREVIEW_DIR, `${sheetName.replace(/[^A-Za-z0-9]+/g, "-").toLowerCase()}.png`), new Uint8Array(await preview.arrayBuffer()));
}
const summaryInspect = await wb.inspect({ kind: "region", sheetId: "Resumen", range: "A1:Q7", maxChars: 10000 });
const qaInspect = await wb.inspect({ kind: "region", sheetId: "QA", range: "A1:D18", maxChars: 10000 });
const errors = await wb.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A", options: { useRegex: true, maxResults: 100 } });
await fs.writeFile(path.join(RUN_DIR, "workbook_inspect.json"), JSON.stringify({ summary: summaryInspect, qa: qaInspect, formula_errors: errors }, null, 2));
const xlsx = await SpreadsheetFile.exportXlsx(wb);
const outputPath = path.join(OUTPUT_DIR, "e2e-portal-search-smoke-2026-08-23.xlsx");
await xlsx.save(outputPath);
console.log(JSON.stringify({ output: outputPath, preview_dir: PREVIEW_DIR, sheets: inspectTargets.map((item) => item[0]), formula_errors: errors }, null, 2));
