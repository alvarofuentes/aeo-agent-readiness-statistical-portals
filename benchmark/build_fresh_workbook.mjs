#!/usr/bin/env node
import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const runDir = path.resolve(process.argv[2] || "");
const baseDirs = process.argv.slice(3).filter(Boolean).map((p) => path.resolve(p));
if (!runDir) throw new Error("Usage: build_fresh_workbook.mjs <complete-run-dir>");
const manifest = JSON.parse(await fs.readFile(path.join(runDir, "run_manifest.json"), "utf8"));
let results = (await fs.readFile(path.join(runDir, "results.jsonl"), "utf8"))
  .split(/\r?\n/).filter(Boolean).map(JSON.parse);
if (manifest.status !== "COMPLETE" || results.length !== Number(manifest.expected_executions)) {
  throw new Error(`Workbook blocked: ${manifest.status} ${results.length}/${manifest.expected_executions}`);
}
const editorialDir = path.join(runDir, "editorial");
const ledger = JSON.parse(await fs.readFile(path.join(editorialDir, "editorial_payload.json"), "utf8")).unverified_ledger || [];
for (const baseDir of baseDirs) {
  const baseManifest = JSON.parse(await fs.readFile(path.join(baseDir, "run_manifest.json"), "utf8"));
  const baseResults = (await fs.readFile(path.join(baseDir, "results.jsonl"), "utf8")).split(/\r?\n/).filter(Boolean).map(JSON.parse);
  if (baseManifest.status !== "COMPLETE" || baseResults.length !== Number(baseManifest.expected_executions)) throw new Error(`Base workbook blocked: ${baseManifest.status} ${baseResults.length}/${baseManifest.expected_executions}`);
  results = baseResults.concat(results);
}

const str = (v) => v == null ? "" : typeof v === "string" ? v : JSON.stringify(v, null, 0);
const compact = (v, n = 500) => { const s = str(v); return s.length <= n ? s : s.slice(0, n) + "…"; };
const matrixRows = results.map(r => {
  const c = r.candidate || {}, m = r.metadata || {};
  return [r.portal_id, r.execution_id, r.fresh_template_id, r.repeat, r.stratum || "", r.query,
    c.id || "", c.name || "", (c.selection_metadata || {}).scope || "", (c.selection_metadata || {}).country_scope || "",
    r.selection_status || "", r.selection_failure_class || "", compact(r.selection_error), r.e2e_status || "",
    r.retrieval_status || "", r.value_found ? "sí" : "no", r.rows_returned || 0, r.citation_url || "",
    m.missing ? compact(m.missing) : "", r.model_endpoint || "", compact(r.calls, 350)];
});
const matrixHeaders = ["Portal", "Ejecución", "Plantilla", "Repetición", "Estrato", "Consulta", "Candidato ID", "Candidato elegido por el modelo", "Alcance", "Cobertura geográfica", "Selección", "Clase de fallo", "Diagnóstico de selección", "Gate E2E", "Recuperación", "Valor", "Filas", "Cita URL", "Metadatos faltantes", "Endpoint Ollama", "Llamadas"];

const wb = Workbook.create();
const summary = wb.worksheets.add("Resumen");
const matrix = wb.worksheets.add("Matriz E2E");
const selection = wb.worksheets.add("Selección modelo");
const unresolved = wb.worksheets.add("Ledger técnico");
const sources = wb.worksheets.add("Fuentes");
const navy = "#17324D", teal = "#0F766E", light = "#E8F1F5", amber = "#FEF3C7", red = "#FEE2E2", gray = "#5B6770";
function title(sheet, text, endCol) {
  sheet.mergeCells(`A1:${endCol}1`); sheet.getRange("A1").values = [[text]];
  sheet.getRange(`A1:${endCol}1`).format = { fill: navy, font: { bold: true, color: "#FFFFFF", size: 16 }, verticalAlignment: "center" };
  sheet.getRange("A1").format.rowHeight = 28;
}
function header(sheet, range) {
  sheet.getRange(range).format = { fill: teal, font: { bold: true, color: "#FFFFFF" }, wrapText: true, verticalAlignment: "center" };
  sheet.getRange(range).format.rowHeight = 28;
}
function body(sheet, range) { sheet.getRange(range).format = { font: { color: "#1F2937", size: 10 }, wrapText: false, verticalAlignment: "center" }; }

const portals = [...new Set(results.map(r => r.portal_id))];
title(summary, `Evaluación E2E live · ${portals.join(" vs ")}`, "H");
summary.getRange("A3:B7").values = [
  ["Run", manifest.run_id], ["Evidencia", "Live por repetición · sin caché ni gold congelado"], ["Contrato", `${manifest.template_count} plantillas × ${portals.length} portales × ${manifest.repeat_count} repeticiones; combined rows=${results.length}`], ["Política de selección", "Conservar la primera selección del modelo; no sustituirla"], ["Nota", "MODEL_SELECTION_ERROR es un fallo de visibilidad semántica, no NOT_VERIFIED"]
];
summary.getRange("A3:A7").format = { fill: light, font: { bold: true, color: navy } }; summary.getRange("B3:B7").format = { wrapText: true };
summary.getRange("A10:H10").values = [["Portal", "Ejecuciones", "E2E PASS", "Tasa E2E", "Errores selección", "Tasa selección", "Valor encontrado", "Recuperación NOT_VERIFIED"]]; header(summary, "A10:H10");
summary.getRange(`A11:A${10+portals.length}`).values = portals.map(p => [p]);
const lastDataRow = results.length + 2;
summary.getRange(`B11:B${10+portals.length}`).formulas = portals.map((_,i) => [`=COUNTIF('Matriz E2E'!$A$3:$A$${lastDataRow},A${11+i})`]);
summary.getRange(`C11:C${10+portals.length}`).formulas = portals.map((_,i) => [`=COUNTIFS('Matriz E2E'!$A$3:$A$${lastDataRow},A${11+i},'Matriz E2E'!$N$3:$N$${lastDataRow},"PASS")`]);
summary.getRange(`D11:D${10+portals.length}`).formulas = portals.map((_,i) => [`=C${11+i}/B${11+i}`]);
summary.getRange(`E11:E${10+portals.length}`).formulas = portals.map((_,i) => [`=COUNTIFS('Matriz E2E'!$A$3:$A$${lastDataRow},A${11+i},'Matriz E2E'!$L$3:$L$${lastDataRow},"MODEL_SELECTION_ERROR")`]);
summary.getRange(`F11:F${10+portals.length}`).formulas = portals.map((_,i) => [`=E${11+i}/B${11+i}`]);
summary.getRange(`G11:G${10+portals.length}`).formulas = portals.map((_,i) => [`=COUNTIFS('Matriz E2E'!$A$3:$A$${lastDataRow},A${11+i},'Matriz E2E'!$P$3:$P$${lastDataRow},"sí")`]);
summary.getRange(`H11:H${10+portals.length}`).formulas = portals.map((_,i) => [`=COUNTIFS('Matriz E2E'!$A$3:$A$${lastDataRow},A${11+i},'Matriz E2E'!$O$3:$O$${lastDataRow},"NOT_VERIFIED")`]);
summary.getRange(`D11:D${10+portals.length}`).format.numberFormat = "0.0%"; summary.getRange(`F11:F${10+portals.length}`).format.numberFormat = "0.0%";
const noteRow = 12 + portals.length;
summary.getRange(`A${noteRow}:H${noteRow}`).values = [["Regla de lectura", "La tasa E2E exige selección PASS y recuperación PASS.", "", "", "", "", "", ""]]; summary.mergeCells(`B${noteRow}:H${noteRow}`); summary.getRange(`A${noteRow}:H${noteRow}`).format = { fill: amber, font: { color: "#7C4A03", italic: true }, wrapText: true };
summary.getRange(`A1:H${noteRow}`).format.columnWidth = 18; summary.getRange(`A1:A${noteRow}`).format.columnWidth = 23; summary.getRange(`B1:B${noteRow}`).format.columnWidth = 48; summary.getRange(`A${noteRow}:H${noteRow}`).format.rowHeight = 32;

title(matrix, "Matriz de ejecuciones E2E · evidencia por fila", "U");
matrix.getRange("A2:U2").values = [matrixHeaders]; header(matrix, "A2:U2"); matrix.getRange(`A3:U${matrixRows.length + 2}`).values = matrixRows; body(matrix, `A3:U${matrixRows.length + 2}`); matrix.freezePanes.freezeRows(2); matrix.freezePanes.freezeColumns(2);
matrix.getRange(`K3:K${matrixRows.length + 2}`).conditionalFormats.addCustom('=K3="FAIL"', { fill: red }); matrix.getRange(`L3:L${matrixRows.length + 2}`).conditionalFormats.addCustom('=L3="MODEL_SELECTION_ERROR"', { fill: amber }); matrix.getRange(`N3:N${matrixRows.length + 2}`).conditionalFormats.addCustom('=N3="PASS"', { fill: "#DCFCE7" });
matrix.getRange("A:A").format.columnWidth = 14; matrix.getRange("B:C").format.columnWidth = 24; matrix.getRange("D:E").format.columnWidth = 12; matrix.getRange("F:F").format.columnWidth = 55; matrix.getRange("G:G").format.columnWidth = 14; matrix.getRange("H:H").format.columnWidth = 60; matrix.getRange("I:J").format.columnWidth = 17; matrix.getRange("K:O").format.columnWidth = 18; matrix.getRange("P:Q").format.columnWidth = 12; matrix.getRange("R:R").format.columnWidth = 50; matrix.getRange("S:S").format.columnWidth = 22; matrix.getRange("T:T").format.columnWidth = 28; matrix.getRange("U:U").format.columnWidth = 45;

title(selection, "Diagnóstico de selección semántica del modelo", "I");
const selHeaders = ["Portal", "Ejecución", "Consulta", "Candidato elegido", "Alcance observado", "Selección", "Clase", "Mismatches / esperado", "Nota"];
selection.getRange("A2:I2").values = [selHeaders]; header(selection, "A2:I2");
selection.getRange(`A3:I${results.length + 2}`).values = results.map(r => { const c=r.candidate||{}, md=c.selection_metadata||{}, e=r.selection_error||{}; return [r.portal_id,r.execution_id,r.query,`${c.id||""} ${c.name||""}`,`${md.scope||""} · ${md.country_scope||""}`,r.selection_status||"",r.selection_failure_class||"",compact(e.mismatches||e.expected||""),e.note||""]; }); body(selection,`A3:I${results.length+2}`); selection.freezePanes.freezeRows(2); selection.getRange(`G3:G${results.length+2}`).conditionalFormats.addCustom('=G3="MODEL_SELECTION_ERROR"',{fill:amber}); selection.getRange("A:A").format.columnWidth=14; selection.getRange("B:B").format.columnWidth=26; selection.getRange("C:C").format.columnWidth=55; selection.getRange("D:D").format.columnWidth=58; selection.getRange("E:E").format.columnWidth=22; selection.getRange("F:G").format.columnWidth=22; selection.getRange("H:I").format.columnWidth=48;

title(unresolved, "Ledger de instancias técnicas no verificadas", "I");
const ledHeaders = ["Portal", "Repetición", "Check", "Estado", "Estado evidencia", "Observado", "Brecha", "Próxima acción", "Fuente"];
unresolved.getRange("A2:I2").values=[ledHeaders]; header(unresolved,"A2:I2");
const ledgerDisplay = ledger.length ? ledger.map(x=>[x.portal_id,x.repeat,x.check_id,x.status,x.evidence_state,x.observed_evidence,x.verification_gap,x.next_verification_action,x.source_evidence_path]) : [["—","—","—","—","—","No quedaron instancias técnicas no verificadas en la corrida.","—","—","editorial/unverified_ledger.csv"]];
unresolved.getRange(`A3:I${ledgerDisplay.length+2}`).values=ledgerDisplay; body(unresolved,`A3:I${ledgerDisplay.length+2}`); unresolved.freezePanes.freezeRows(2); unresolved.getRange(`D3:D${ledgerDisplay.length+2}`).format={fill: ledger.length ? amber : "#DCFCE7"}; unresolved.getRange("A:A").format.columnWidth=14; unresolved.getRange("B:B").format.columnWidth=12; unresolved.getRange("C:C").format.columnWidth=28; unresolved.getRange("D:E").format.columnWidth=24; unresolved.getRange("F:H").format.columnWidth=60; unresolved.getRange("I:I").format.columnWidth=35;

title(sources, "Fuentes y trazabilidad de la evaluación", "D");
const sourceRows = [["Fuente","Uso","Evidencia local","Estado"], ...portals.map(p=>[`${p} API`,`Catálogo y retrieval`,`evidence/raw + catalog`,`Live`]), ["Technical probes","robots/sitemap/llms/JSON-LD/API/exportación","evidence/technical + evidence/exports","Live + ledger"]];
sources.getRange(`A3:D${sourceRows.length+2}`).values=sourceRows; header(sources,"A3:D3"); body(sources,`A4:D${sourceRows.length+2}`); sources.getRange("A:A").format.columnWidth=24; sources.getRange("B:B").format.columnWidth=42; sources.getRange("C:C").format.columnWidth=40; sources.getRange("D:D").format.columnWidth=18;

for (const sheet of [summary, matrix, selection, unresolved, sources]) { const used = sheet.getUsedRange(); if (used) used.format.font.name = "Aptos"; }
const outputDir = path.join(runDir, "editorial"); await fs.mkdir(outputDir, { recursive: true });
const out = await SpreadsheetFile.exportXlsx(wb); await out.save(path.join(outputDir, "e2e_visibility_workbook.xlsx"));
for (const [sheetName, range] of [["Resumen",`A1:H${noteRow}`],["Matriz E2E","A1:U18"],["Selección modelo","A1:I18"],["Ledger técnico","A1:I12"],["Fuentes","A1:D6"]]) { const blob = await wb.render({ sheetName, range, scale: 1, format: "png" }); await fs.writeFile(path.join(outputDir, `preview-${sheetName.replaceAll(" ","_")}.png`), new Uint8Array(await blob.arrayBuffer())); }
const errorScan = await wb.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A", options: { useRegex: true, maxResults: 100 }, summary: "final formula error scan" }); console.log(errorScan.ndjson);
console.log(JSON.stringify({ status: "COMPLETE", workbook: path.join(outputDir, "e2e_visibility_workbook.xlsx"), rows: results.length, portals, ledger: ledger.length }));
