import fs from "node:fs/promises";
import path from "node:path";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const ROOT = path.resolve(process.argv[2]);
const RUN_DIR = path.resolve(process.argv[3]);
const DATE_TAG = process.argv[4] || "2026-08-23";
if (!ROOT || !RUN_DIR) throw new Error("usage: node build_pilot_ppt_artifact.mjs <repo> <run_dir> <date_tag>");

const analysis = JSON.parse(await fs.readFile(path.join(RUN_DIR, "analysis", "pilot_analysis.json"), "utf8"));
const manifest = JSON.parse(await fs.readFile(path.join(RUN_DIR, "run_manifest.json"), "utf8"));
const payload = JSON.parse(await fs.readFile(path.join(RUN_DIR, "editorial", "pilot-editorial-payload.json"), "utf8"));
const runRel = path.relative(ROOT, RUN_DIR);
const outputDir = path.join(RUN_DIR, "editorial");
const qcDir = path.join(outputDir, "ppt-qc");
await fs.mkdir(qcDir, { recursive: true });

const PORTALS = [
  ["cepalstat", "CEPALSTAT", "https://statistics.cepal.org/portal/cepalstat/", "https://statistics.cepal.org/portal/cepalstat/api.html"],
  ["sdg", "UN SDG Indicators", "https://unstats.un.org/sdgs/", "https://unstats.un.org/SDGAPI/"],
];
const SECTIONS = [
  "Objetivo del piloto", "Las seis dimensiones AEO", "Metodología y límites", "Los dos portales", "Contrato y gates", "Resultados observados", "Modelos y roles", "Desambiguación semántica", "Red team y citabilidad", "AEO ↔ AIRSC", "Estabilidad por repetición", "Buenas prácticas", "Recomendaciones para CEPALSTAT", "Ficha AI-friendly", "Ejemplos de PIB", "Conclusiones y siguiente decisión",
];
const n = (x, fallback = "NA") => x === null || x === undefined || x === "" ? fallback : (typeof x === "number" ? (Number.isInteger(x) ? String(x) : x.toFixed(2)) : String(x));
const pct = (x) => x === null || x === undefined ? "NA" : `${(Number(x) * 100).toFixed(1)}%`;
const rowFor = (id) => (analysis.portal_summary || []).find((r) => r.portal_id === id) || {};
const sumFor = (id) => (payload.summary_rows || []).find((r) => r.portal_id === id) || {};
const strataFor = (id) => (payload.strata_rows || []).filter((r) => r.portal_id === id);
const compFor = (label) => (payload.comparative_rows || []).find((r) => r.metric === label) || {};
const evidenceFor = (id) => (payload.evidence || {})[id] || {};
const matrixText = await fs.readFile(path.join(outputDir, "pilot-results-matrix-60x2x3.csv"), "utf8");
const aeo = { cepalstat: "NA", sdg: "NA" };
const aeoSource = { cepalstat: "NA", sdg: "NA" };
for (const line of matrixText.split(/\r?\n/).slice(1)) {
  const cells = line.split(",");
  if (cells[0] === "cepalstat") { aeo.cepalstat = cells[3]; aeoSource.cepalstat = cells[4]; }
  if (cells[0] === "sdg") { aeo.sdg = cells[3]; aeoSource.sdg = cells[4]; }
}
const models = [...new Set((manifest.models ? Object.values(manifest.models) : []).filter(Boolean))].sort();

const deck = Presentation.create({ slideSize: { width: 1280, height: 720 } });

function box(slide, text, left, top, width, height, style = {}) {
  const shape = slide.shapes.add({ geometry: "textbox", position: { left, top, width, height }, fill: "none", line: { style: "solid", fill: "none", width: 0 } });
  shape.text = text;
  shape.text.style = { fontSize: style.fontSize || 20, color: style.color || "slate-800", bold: Boolean(style.bold) };
  return shape;
}

function notes(slide, sourceText) {
  slide.speakerNotes.textFrame.setText(`[Sources]\n${sourceText}\n[/Sources]`);
  slide.speakerNotes.setVisible(true);
}

function addSlide(title, body, source, section = null, options = {}) {
  const slide = deck.slides.add();
  slide.background.fill = options.title ? "slate-900" : "slate-50";
  if (options.title) {
    box(slide, title, 78, 140, 1120, 150, { fontSize: 50, color: "white", bold: true });
    box(slide, body, 82, 340, 1100, 100, { fontSize: 24, color: "slate-200" });
    box(slide, "Piloto aislado · CEPALSTAT vs UN SDG · no sustituye el benchmark de cinco portales", 82, 570, 1100, 32, { fontSize: 15, color: "slate-400" });
  } else {
    slide.shapes.add({ geometry: "rect", position: { left: 0, top: 0, width: 1280, height: 78 }, fill: "blue-900", line: { style: "solid", fill: "none", width: 0 } });
    box(slide, `${String(section).padStart(2, "0")} · ${title}`, 52, 15, 1170, 50, { fontSize: 35, color: "white", bold: true });
    box(slide, body, 62, 112, 1155, 540, { fontSize: options.fontSize || 19, color: "slate-800" });
    box(slide, "PILOTO · evidencia congelada · lectura descriptiva/no causal", 52, 684, 1170, 18, { fontSize: 10, color: "slate-500" });
  }
  notes(slide, source);
  return slide;
}

addSlide("Piloto AEO–visibilidad", "CEPALSTAT vs UN SDG\n60 plantillas · 2 portales · 3 repeticiones · 360 ejecuciones", `auditoría AEO.pdf; ${runRel}/run_manifest.json`, null, { title: true });
addSlide(SECTIONS[0], "Pregunta: ¿cómo se comportan dos portales con puntajes AEO extremos cuando reciben las mismas familias de consulta?\n\nObjetivo operativo: separar descubrimiento, recuperación, semántica, citabilidad, judge y red team.\n\nResultado: el run cierra mecánica, pero no demuestra visibilidad específica; la evidencia aceptada es 0/360 URLs.", "auditoría AEO.pdf; benchmark/query-bank-pilot-60.csv; pilot-editorial-payload.json", 1, { fontSize: 21 });
addSlide(SECTIONS[1], `Seis dimensiones con pesos PDF/skill:\nBots 10 · descubrimiento 15 · renderizado 20 · datos estructurados 15 · API 25 · citabilidad 15.\n\nAEO editorial: CEPALSTAT ${aeo.cepalstat}/100 · SDG ${aeo.sdg}/100.\nCorrección trazable: SDG fuente 88 → editorial 85 por citabilidad fuente 18/15.`, "execution/expanded-audit-matrix-2026-08-22.csv; auditoría AEO.pdf; pilot-results-matrix-60x2x3.csv", 2, { fontSize: 21 });
const strataCounts = strataFor("cepalstat").map((r) => `${r.stratum_label}: ${r.template_rows} filas`).join(" · ");
addSlide(SECTIONS[2], `Contrato: 60 plantillas × 2 portales × 3 repeticiones = 360 ejecuciones (2 pasadas de 180).\n\nFamilias: ${strataCounts}.\n\nRoles: discovery → semantic → retrieval → metadata → citation → judge → adversarial.\n\nCada fila conserva query, evidencia, hash, salida natural, schema, score recomputado y veredicto adversarial. El resultado es descriptivo; no se extrapola a cinco portales.`, "auditoría AEO.pdf; benchmark/query-bank-pilot-60.csv; pilot-execution-matrix-360.csv", 3, { fontSize: 18 });
addSlide(SECTIONS[3], PORTALS.map(([id, name, url], i) => { const s = sumFor(id); const e = evidenceFor(id); return `${i + 1}. ${name} — ${url}\n   AEO editorial ${aeo[id]}/100 · AIRSC ${n(s.mean_airsc)} · ${s.executions} ejecuciones\n   Página capturada: ${Object.keys(e.page_urls || {})[0] || "NA"} · status ${Object.keys(e.page_statuses || {})[0] || "NA"}`; }).join("\n\n"), `${runRel}/editorial/pilot-portal-summary-60x2x3.csv; ${runRel}/evidence`, 4, { fontSize: 19 });
addSlide(SECTIONS[4], `Filas: ${n(analysis.n_rows)} · plantillas: ${n(analysis.n_templates)} · textos únicos: ${n(analysis.n_unique_query_texts)}.\nGold: ${manifest.gold_status?.status || "NA"} contractual (${manifest.gold_status?.covered_pairs || "NA"}/${manifest.gold_status?.expected_pairs || "NA"} pares) · run: ${manifest.status || "NA"}.\n\nQA mecánica: ${analysis.mechanical_qa_status || "NA"}. QA editorial: ${analysis.qa_status || "NA"}. Publicación: ${analysis.publication_status || "HOLD"}.\n\nEvidencia específica: 0/360. Adversarial: uncertain en ambos portales.`, `${runRel}/run_manifest.json; ${runRel}/analysis/pilot_analysis.json; ${runRel}/editorial/editorial_manifest.json`, 5, { fontSize: 19 });
const resultLines = ["Portal | AEO | AIRSC | Judge discovery | Judge retrieval | Judge citation | URLs", "---|---:|---:|---:|---:|---:|---:"];
for (const [id, name] of PORTALS) { const s = sumFor(id); const c1 = compFor("Judge discovery medio"); const c2 = compFor("Judge retrieval medio"); const c3 = compFor("Judge citation medio"); const cv = id === "cepalstat" ? c1.cepalstat : c1.sdg; const rv = id === "cepalstat" ? c2.cepalstat : c2.sdg; const citv = id === "cepalstat" ? c3.cepalstat : c3.sdg; resultLines.push(`${name} | ${s.aeo_score_editorial} | ${n(s.mean_airsc)} | ${cv} | ${rv} | ${citv} | ${s.candidate_urls}`); }
resultLines.push("", "Lectura: el mayor AEO editorial no se traduce automáticamente en mayor AIRSC; ambos portales tienen 0 URLs específicas aceptadas.");
addSlide(SECTIONS[5], resultLines.join("\n"), `${runRel}/editorial/pilot-portal-summary-60x2x3.csv; ${runRel}/editorial/pilot-comparative-matrix-60x2x3.csv`, 6, { fontSize: 18 });
const modelLines = ["Rol | Modelo | Cobertura", "---|---|---"];
for (const [role, model] of Object.entries(payload.models || {})) modelLines.push(`${role} | ${model} | 360/360 schema + natural disponibles`);
modelLines.push("", "El juez y el adversarial son modelos separados del pool de generación.", "El adversarial no produjo `pass`: incertidumbre conservada como HOLD.");
addSlide(SECTIONS[6], modelLines.join("\n"), `${runRel}/run_manifest.json; ${runRel}/editorial/pilot-execution-matrix-360.csv`, 7, { fontSize: 17 });
const familyLines = ["Familia | CEPALSTAT AIRSC | SDG AIRSC | Hallazgo"]; for (const r of strataFor("cepalstat")) { const s = strataFor("sdg").find((x) => x.stratum === r.stratum) || {}; familyLines.push(`${r.stratum_label} | ${n(r.mean_airsc)} | ${n(s.mean_airsc)} | ${r.candidate_urls}/${r.executions} URLs`); }
addSlide(SECTIONS[7], "La hipótesis de una sola URL es válida cuando la pregunta es específica y la URL expone el objeto exacto.\n\n" + familyLines.join("\n") + "\n\nEl piloto no alcanzó esa condición: la evidencia congelada sólo contenía superficies de entrada.", "auditoría AEO.pdf; pilot-results-matrix-60x2x3.csv; pilot-execution-matrix-360.csv", 8, { fontSize: 17 });
const adv = PORTALS.map(([id, name]) => { const s = sumFor(id); const e = evidenceFor(id); return `${name}: adversarial ${s.adversarial} · SERP ${JSON.stringify(e.serp_statuses || {})} · URLs aceptadas ${s.candidate_urls}`; }).join("\n");
addSlide(SECTIONS[8], `El red team no se oculta detrás del promedio: ambos portales quedan en uncertain.\n${adv}\n\nLa citabilidad específica sólo se puede aprobar cuando existe URL oficial, indicador, valor, unidad, período, geografía y fuente. El paquete editorial conserva los 360 casos para reauditar por familia.`, `${runRel}/editorial/pilot-portal-summary-60x2x3.csv; ${runRel}/evidence; ${runRel}/results.jsonl`, 9, { fontSize: 18 });
addSlide(SECTIONS[9], `AEO técnico = condiciones del portal. AIRSC = resultado operacional bajo evidencia y modelos fijos.\n\nCEPALSTAT: AEO ${aeo.cepalstat} · AIRSC ${sumFor("cepalstat").mean_airsc}.\nUN SDG: AEO ${aeo.sdg} · AIRSC ${sumFor("sdg").mean_airsc}.\n\nLa lectura correcta es descriptiva: el portal con AEO superior no obtiene AIRSC superior, pero tampoco hay descubrimiento específico para atribuir causalidad.`, "auditoría AEO.pdf; pilot-comparative-matrix-60x2x3.csv; pilot_analysis.py", 10, { fontSize: 20 });
const repeatLines = ["Portal | rep1 | rep2 | rep3 | lectura"]; for (const [id, name] of PORTALS) { const values = (analysis.repeat_summary || []).filter((r) => r.portal_id === id).sort((a, b) => a.repeat - b.repeat).map((r) => n(r.mean_airsc)); repeatLines.push(`${name} | ${values.join(" | ")} | estabilidad operacional`); }
repeatLines.push("", "Las repeticiones no son observaciones independientes de portales; muestran variabilidad del pipeline.");
addSlide(SECTIONS[10], repeatLines.join("\n"), `${runRel}/analysis/pilot_analysis.json; ${runRel}/editorial/pilot-results-matrix-60x2x3.csv`, 11, { fontSize: 18 });
addSlide(SECTIONS[11], `Qué debe quedar junto al valor:\n\n• identificador canónico y label\n• definición, unidad, frecuencia y período\n• geografía y dimensiones\n• fuente, provenance_url y api_url\n• fecha de actualización y licencia\n• reglas do_not_confuse_with\n\nLa evidencia del piloto muestra por qué una landing page de indicador es más útil que una portada genérica.`, "auditoría AEO.pdf; .agents/skills/aeo-agent-readiness-auditor/SKILL.md", 12, { fontSize: 19 });
addSlide(SECTIONS[12], `CEPALSTAT · P0: landing pages/canonicales y API enlazada desde el indicador.\nCEPALSTAT · P1: ficha machine-readable con unidad, período, geografía y fuente.\nUN SDG · P0: ruta de datos estática o prerenderizada y enlace claro a SDGAPI/SDMX.\nUN SDG · P1: mapeo indicador → endpoint, dimensiones y ejemplo de llamada.\n\nP2 común: monitorizar URLs aceptadas, robots/sitemap/llms y paridad HTML/API.`, "cepalstat-agent-readiness-kit/implementation-recommendations.md; auditoría AEO.pdf; pilot reports", 13, { fontSize: 18 });
addSlide(SECTIONS[13], "Ficha mínima de indicador:\n\nindicator_id · label · definition · unit · frequency · geography · period · value · source · provenance_url · api_url · dimensions · similar_indicators · do_not_confuse_with\n\nCriterio de aceptación: el agente no adivina códigos y la cita se reconstruye desde la misma ficha y API.", "cepalstat-agent-readiness-kit/metadata/ai-indicator-schema.json; cepalstat-agent-readiness-kit/metadata/ai-indicator-metadata-template.json", 14, { fontSize: 19 });
addSlide(SECTIONS[14], "“PIB de Chile 2019” no identifica por sí solo una serie.\n\nDebe resolverse si se solicita: PIB corriente, PIB constante, PIB per cápita, crecimiento o moneda local.\n\nUna sola URL puede ser la respuesta correcta si expone indicador, valor, unidad, período, geografía, fuente y provenance. El piloto dejó esta condición como prueba pendiente, no como fallo del modelo.", "cepalstat-agent-readiness-kit/examples/pib-disambiguation.json; auditoría AEO.pdf", 15, { fontSize: 20 });
addSlide(SECTIONS[15], `Cierre del piloto: ${n(analysis.n_rows)} ejecuciones · ${manifest.gold_status?.covered_pairs || "NA"}/${manifest.gold_status?.expected_pairs || "NA"} pares contractuales · schema/natural PASS.\n\nQA editorial: ${analysis.qa_status || "NA"}. Publicación: ${analysis.publication_status || "HOLD"}.\n\nSiguiente decisión: enriquecer evidencia de series/API, repetir el piloto, exigir red-team concluyente y sólo después decidir si se amplía a cinco portales.`, `${runRel}/run_manifest.json; ${runRel}/analysis/pilot_analysis.json; ${runRel}/editorial/editorial_manifest.json`, 16, { fontSize: 19 });

for (const [index, slide] of deck.slides.items.entries()) {
  const blob = await deck.export({ slide, format: "png", scale: 1 });
  await fs.writeFile(path.join(qcDir, `slide-${String(index + 1).padStart(2, "0")}.png`), new Uint8Array(await blob.arrayBuffer()));
}
const montage = await deck.export({ format: "webp", montage: true, scale: 1 });
await fs.writeFile(path.join(qcDir, "deck-montage.webp"), new Uint8Array(await montage.arrayBuffer()));
const pptx = await PresentationFile.exportPptx(deck);
const out = path.join(outputDir, `pilot-aeo-visibility-${DATE_TAG}.pptx`);
await pptx.save(out);
console.log(JSON.stringify({ output: out, slides: deck.slides.items.length, qc_dir: qcDir }));
