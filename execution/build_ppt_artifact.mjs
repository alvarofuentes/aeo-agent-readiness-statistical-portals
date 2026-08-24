import fs from "node:fs/promises";
import path from "node:path";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const ROOT = process.argv[2] ? path.resolve(process.argv[2]) : path.resolve(new URL("..", import.meta.url).pathname);
const RUN_DIR = process.argv[3] ? path.resolve(process.argv[3]) : "";
const DATE_TAG = process.argv[4] || "2026-08-23";
if (!RUN_DIR) throw new Error("usage: node build_ppt_artifact.mjs <repo> <run_dir> <date_tag>");

const analysis = JSON.parse(await fs.readFile(path.join(RUN_DIR, "analysis", "production_analysis.json"), "utf8"));
const manifest = JSON.parse(await fs.readFile(path.join(RUN_DIR, "run_manifest.json"), "utf8"));
const runRel = path.relative(ROOT, RUN_DIR) || ".";
const matrixPath = path.join(ROOT, "execution", "expanded-audit-matrix-2026-08-22.csv");
const matrixText = await fs.readFile(matrixPath, "utf8");

const PORTALS = [
  ["worldbank", "World Bank Open Data", "https://data.worldbank.org/"],
  ["who", "WHO Data", "https://data.who.int/"],
  ["cepalstat", "CEPALSTAT", "https://statistics.cepal.org/portal/cepalstat/"],
  ["undata", "UN Data Commons (UNSD)", "https://unstats.un.org/UNSDWebsite/undatacommons/"],
  ["sdg", "UN SDG Indicators", "https://unstats.un.org/sdgs/"],
];
const SECTIONS = [
  "AEO y preparación para agentes", "Las seis dimensiones AEO", "Metodología, alcance y límites", "Los cinco portales", "Benchmark y unidad de análisis", "Resultados por portal", "Modelos y roles", "Desambiguación semántica", "Red team y controles adversariales", "AEO ↔ preparación para IA", "Estadística y asociación", "Buenas prácticas observadas", "Recomendaciones para CEPALSTAT", "Ficha AI-friendly de indicador", "Ejemplos de PIB y disambiguación", "Conclusiones y criterios de aceptación",
];

const n = (x, fallback = "NA") => x === null || x === undefined || x === "" ? fallback : (typeof x === "number" ? (Number.isInteger(x) ? String(x) : x.toFixed(2)) : String(x));
const pct = (x) => x === null || x === undefined ? "NA" : `${(Number(x) * 100).toFixed(1)}%`;
const portalSummary = (id) => (analysis.portal_summary || []).find((r) => r.portal_id === id) || {};
const matrixScore = (id) => {
  const row = matrixText.split(/\r?\n/).slice(1).map((line) => line.split(","));
  const index = { "World Bank Open Data": "worldbank", "WHO Data": "who", CEPALSTAT: "cepalstat", "UN Data Commons (UNSD)": "undata", "UN SDG Indicators": "sdg" };
  for (const cells of row) if (index[cells[0]] === id) return cells[1];
  return "NA";
};
const models = [...new Set((analysis.model_summary || []).map((r) => r.model).filter(Boolean))].sort();

const deck = Presentation.create({ slideSize: { width: 1280, height: 720 } });
const outputDir = path.join(ROOT, "outputs");
const qcDir = path.join(outputDir, "ppt-qc", DATE_TAG);
await fs.mkdir(outputDir, { recursive: true });
await fs.mkdir(qcDir, { recursive: true });

function box(slide, text, left, top, width, height, style = {}) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    position: { left, top, width, height },
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  shape.text = text;
  shape.text.style = { fontSize: style.fontSize || 20, color: style.color || "slate-800", bold: Boolean(style.bold) };
  return shape;
}

function notes(slide, sourceText) {
  slide.speakerNotes.textFrame.setText(`[Sources]\n${sourceText}\n[/Sources]`);
  slide.speakerNotes.setVisible(true);
}

function slide(title, body, source, section = null, opts = {}) {
  const s = deck.slides.add();
  s.background.fill = opts.title ? "slate-900" : "slate-50";
  if (!opts.title) {
    s.shapes.add({ geometry: "rect", position: { left: 0, top: 0, width: 1280, height: 72 }, fill: "blue-900", line: { style: "solid", fill: "none", width: 0 } });
    box(s, `${String(section).padStart(2, "0")} · ${title}`, 52, 15, 1170, 44, { fontSize: 30, color: "white", bold: true });
    box(s, "AEO · evidencia congelada · asociación descriptiva/no causal", 52, 684, 1170, 18, { fontSize: 10, color: "slate-500" });
    box(s, body, 62, 105, 1155, 548, { fontSize: opts.fontSize || 20, color: "slate-800" });
  } else {
    box(s, title, 78, 150, 1120, 120, { fontSize: 48, color: "white", bold: true });
    box(s, body, 82, 322, 1100, 130, { fontSize: 25, color: "slate-200" });
    box(s, "Fuente de verdad: auditoría AEO.pdf · cinco portales · editorial final", 82, 570, 1100, 28, { fontSize: 15, color: "slate-400" });
  }
  notes(s, source);
  return s;
}

slide("AEO y visibilidad de agentes", "Cinco portales estadísticos · 120 consultas · 1.800 ejecuciones\nPlan ejecutado con evidencia HTTP, salidas naturales y estructuradas, juez y red team.", `auditoría AEO.pdf; ${runRel}/run_manifest.json`, null, { title: true });
slide(SECTIONS[0], "Objetivo: evaluar si la preparación técnica AEO se asocia con la visibilidad operacional de agentes.\nLa asociación se resume a nivel portal y no establece causalidad.", "auditoría AEO.pdf; .agents/skills/aeo-agent-readiness-auditor/SKILL.md", 1);
slide(SECTIONS[1], "Bots 10 · descubrimiento 15 · renderizado 20 · datos estructurados 15 · API 25 · citabilidad 15.\nEl puntaje AEO es técnico y congelado; AIRSC se recomputa desde la respuesta estructurada validada.", "execution/expanded-audit-matrix-2026-08-22.csv; auditoría AEO.pdf", 2);
slide(SECTIONS[2], "120 consultas × 5 portales × 3 repeticiones = 1.800 ejecuciones, en cinco pasadas de 360.\nRoles: discovery, semantic, retrieval, metadata, citation, judge y adversarial.\nUnidad inferencial: n=5 portales; NA y missing no se convierten en cero.", "auditoría AEO.pdf; benchmark/query-bank-120.csv; benchmark/production_runner.py", 3);
slide(SECTIONS[3], PORTALS.map(([, name, url], i) => `${i + 1}. ${name} — ${url}`).join("\n"), "auditoría AEO.pdf; benchmark/config.yaml", 4, { fontSize: 19 });
slide(SECTIONS[4], `Cardinalidad observada: ${n(analysis.n_rows)} filas · ${n(analysis.n_portals)} portales.\nGold: ${manifest.gold_status?.status || "NA"} · estado: ${manifest.status || "NA"}.\n24 familias y repeticiones son sensibilidad agrupada; modelos: ${models.join(", ") || "registrados en manifiesto"}.`, `${runRel}/run_manifest.json; benchmark/gold_standards_final_2026-08-23.json; benchmark/production_analysis.py`, 5, { fontSize: 19 });
const resultLines = ["Portal | AEO | AIRSC medio | cobertura", "---|---:|---:|---:"];
for (const [id, name] of PORTALS) { const r = portalSummary(id); resultLines.push(`${name} | ${matrixScore(id)} | ${n(r.mean_airsc)} | ${n(r.n_valid)}/${n(r.n_total)} (${pct(r.coverage)})`); }
slide(SECTIONS[5], resultLines.join("\n"), `outputs/aeo-results-matrix-${DATE_TAG}.csv; ${runRel}/analysis/production_analysis.json`, 6, { fontSize: 18 });
const modelLines = [`Modelos registrados: ${models.join(", ") || "NA"}`];
for (const row of (analysis.model_summary || []).slice(0, 10)) modelLines.push(`${row.portal_id} · ${row.role} · ${row.model} → AIRSC ${n(row.mean_airsc)} (n=${n(row.n_valid)})`);
slide(SECTIONS[6], modelLines.join("\n"), `${runRel}/analysis/production_model_summary.csv; benchmark/config.yaml`, 7, { fontSize: 17 });
slide(SECTIONS[7], "La precisión semántica requiere indicador, definición, unidad, período, geografía, precio base, frecuencia y fuente.\nUna consulta muy específica puede devolver correctamente una sola URL; no se penaliza si el objeto es exacto y citable.\nEn CEPALSTAT, PIB nominal/real/per cápita y moneda deben quedar separados.", "auditoría AEO.pdf; execution/implementation-plan-15-gates-2026-08-22.md", 8, { fontSize: 19 });
const advCounts = analysis.adversarial_verdicts || {};
const advLines = ["Veredictos adversariales por portal (sin esconderlos detrás del promedio):"];
for (const [id, name] of PORTALS) {
  const counts = Object.entries(advCounts).filter(([key]) => key.startsWith(`${id}:`)).map(([key, value]) => `${key.slice(id.length + 1)}=${value}`);
  advLines.push(`${name}: ${counts.join(", ") || "NA"}`);
}
slide(SECTIONS[8], advLines.join("\n"), `${runRel}/analysis/production_analysis.json; benchmark/production_runner.py`, 9, { fontSize: 18 });
slide(SECTIONS[9], "AEO mide condiciones del portal; AIRSC mide recuperación, semántica y citación bajo el benchmark.\nLa relación puede verse afectada por cobertura, especificidad, modelo, redirecciones y aplicabilidad. La lectura es de preparación relativa, no causalidad.", "auditoría AEO.pdf; benchmark/production_analysis.py", 10, { fontSize: 19 });
slide(SECTIONS[10], `Spearman: ${n(analysis.spearman_rho)}\nKendall: ${n(analysis.kendall_tau)}\nPermutación exacta: ${n(analysis.spearman_exact_p)}\nAdvertencia: n=5 y resultados descriptivos.`, `${runRel}/analysis/production_analysis.json; benchmark/production_analysis.py`, 11, { fontSize: 27 });
slide(SECTIONS[11], "Identificadores canónicos · metadata junto al valor · API documentada · JSON-LD coherente · robots/sitemap enlazados · unidades y períodos explícitos · provenance y URL estable · ejemplos de consultas y reglas de no confusión.", "auditoría AEO.pdf; .agents/skills/aeo-agent-readiness-auditor/SKILL.md", 12, { fontSize: 19 });
slide(SECTIONS[12], "P0: canonicales, robots/sitemap y API desde cada indicador.\nP1: ficha machine-readable con definición, unidad, período, geografía, fuente y dimensiones.\nP2: benchmark pre/post, vocabulario controlado, similar_indicators y do_not_confuse_with.", "execution/implementation-plan-15-gates-2026-08-22.md; cepalstat-agent-readiness-kit", 13, { fontSize: 20 });
slide(SECTIONS[13], "Ficha mínima: indicator_id, label, definition, unit, frequency, geography, period, value, source, provenance_url, api_url, dimensions y disambiguation_rules.\nDebe ser legible por humanos y agentes, sin obligar a inferir códigos.", "cepalstat-agent-readiness-kit; auditoría AEO.pdf", 14, { fontSize: 20 });
slide(SECTIONS[14], "Ante “PIB de Chile 2019”, el agente debe resolver si se solicita nivel corriente, constante, per cápita, crecimiento o moneda local.\nLa respuesta correcta puede ser una sola URL si expone el indicador exacto y su contexto.", "auditoría AEO.pdf; execution/implementation-plan-15-gates-2026-08-22.md", 15, { fontSize: 22 });
slide(SECTIONS[15], `Publicar cinco informes individuales, matrices, análisis de familias/modelos/repeticiones, red team, deck y evidencia.\nAceptar solo con 1.800 ejecuciones, gold PASS, schema/natural completos y QA visual.\nConclusión estadística: Spearman ${n(analysis.spearman_rho)}; no causalidad demostrada.`, `${runRel}/run_manifest.json; execution/README.md; auditoría AEO.pdf`, 16, { fontSize: 19 });

for (const [index, s] of deck.slides.items.entries()) {
  const blob = await deck.export({ slide: s, format: "png", scale: 1 });
  await fs.writeFile(path.join(qcDir, `slide-${String(index + 1).padStart(2, "0")}.png`), new Uint8Array(await blob.arrayBuffer()));
}
const montage = await deck.export({ format: "webp", montage: true, scale: 1 });
await fs.writeFile(path.join(qcDir, "deck-montage.webp"), new Uint8Array(await montage.arrayBuffer()));
const pptx = await PresentationFile.exportPptx(deck);
const out = path.join(outputDir, `aeo-comparative-deck-${DATE_TAG}.pptx`);
await pptx.save(out);
console.log(JSON.stringify({ output: out, slides: deck.slides.items.length, qc_dir: qcDir }));
