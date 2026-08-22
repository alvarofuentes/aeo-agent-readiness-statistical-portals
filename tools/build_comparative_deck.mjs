import fs from "node:fs/promises";
import path from "node:path";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const ROOT = process.cwd();
const OUT = path.join(ROOT, "outputs", "aeo-comparative-deck-2026-08-22.pptx");
const PNG_DIR = path.join(ROOT, "tmp", "aeo-ppt-2026-08-22", "rendered");
const W = 1280;
const H = 720;
const C = {
  ink: "#111111",
  muted: "#5F6368",
  rule: "#B8BCC4",
  panel: "#F2F2F2",
  blue: "#3D8DFF",
  lightBlue: "#D0EDFA",
  cyan: "#6DCBF4",
  pale: "#EAF5FB",
  white: "#FFFFFF",
  amber: "#F5C45A",
  low: "#F6D6D0",
  mid: "#FFF0C2",
  high: "#CFEEDB",
};
const portals = ["Banco Mundial", "WHO Data", "Statista", "CEPALSTAT"];
const fullScores = [77, 77, 60, 45];
const coreScores = [90.9, 83.6, 65.5, 58.2];
const dimensions = [
  ["Bots", [7, 7, 4, 3]],
  ["Descubrimiento", [12, 12, 10, 2]],
  ["Renderizado", [13, 16, 13, 8]],
  ["Datos estructurados", [7, 8, 7, 2]],
  ["API", [24, 21, 14, 21]],
  ["Citabilidad", [14, 13, 12, 9]],
];

async function writeBlob(path, blob) {
  await fs.writeFile(path, new Uint8Array(await blob.arrayBuffer()));
}

function rect(slide, left, top, width, height, fill, line = "none", radius = false) {
  return slide.shapes.add({
    geometry: radius ? "roundRect" : "rect",
    position: { left, top, width, height },
    fill,
    line: { style: "solid", fill: line, width: line === "none" ? 0 : 1 },
  });
}

function text(slide, value, left, top, width, height, style = {}, name) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    name,
    position: { left, top, width, height },
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  shape.text = value;
  shape.text.style = {
    fontSize: style.fontSize ?? 20,
    typeface: "Helvetica Neue",
    color: style.color ?? C.ink,
    bold: style.bold ?? false,
    italic: style.italic ?? false,
    alignment: style.alignment ?? "left",
    verticalAlignment: style.verticalAlignment ?? "top",
    autoFit: style.autoFit ?? "shrinkText",
    insets: style.insets ?? { top: 0, right: 0, bottom: 0, left: 0 },
  };
  return shape;
}

function footer(slide, n) {
  text(slide, String(n).padStart(2, "0"), 1184, 665, 54, 24, { fontSize: 14, color: C.muted, alignment: "right", verticalAlignment: "bottom" });
  rect(slide, 42, 650, 1196, 1, C.rule);
  text(slide, "AEO / AI readiness · 22 agosto 2026", 42, 662, 400, 22, { fontSize: 12, color: C.muted });
}

function header(slide, title, kicker, n) {
  text(slide, kicker.toUpperCase(), 42, 32, 500, 24, { fontSize: 13, color: C.blue, bold: true });
  text(slide, title, 42, 62, 1180, 68, { fontSize: 36, bold: true, autoFit: "shrinkText" });
  footer(slide, n);
}

function notes(slide, lines) {
  slide.speakerNotes.textFrame.setText(["[Sources]", ...lines]);
  slide.speakerNotes.setVisible(true);
}

function scoreFill(v, max = 25) {
  const pct = v / max;
  return pct >= 0.75 ? C.high : pct >= 0.5 ? C.mid : C.low;
}

function addBullet(slide, label, body, left, top, width, color = C.blue) {
  rect(slide, left, top + 4, 10, 10, color, "none", true);
  text(slide, label, left + 22, top, width - 22, 26, { fontSize: 22, bold: true });
  text(slide, body, left + 22, top + 30, width - 22, 76, { fontSize: 18, color: C.muted });
}

async function main() {
  await fs.mkdir(PNG_DIR, { recursive: true });
  const p = Presentation.create({ slideSize: { width: W, height: H } });

  // 1. Cover — Codex Grid slide-08 silhouette.
  {
    const s = p.slides.add();
    s.background.fill = C.white;
    rect(s, 720, 42, 518, 574, C.pale, C.rule, true);
    rect(s, 760, 84, 438, 4, C.blue);
    text(s, "AUDITORÍA COMPARADA", 42, 46, 560, 26, { fontSize: 14, color: C.blue, bold: true });
    text(s, "AEO y preparación\npara agentes de IA", 42, 112, 600, 150, { fontSize: 52, bold: true, autoFit: "shrinkText" });
    text(s, "Banco Mundial · WHO Data · Statista · CEPALSTAT", 42, 302, 580, 44, { fontSize: 24, color: C.muted });
    text(s, "Seis dimensiones, evidencia primaria y un piloto de direccionamiento.", 42, 370, 560, 72, { fontSize: 21, color: C.ink });
    text(s, "22 agosto 2026", 42, 598, 300, 26, { fontSize: 16, color: C.muted });
    text(s, "04", 1168, 665, 54, 24, { fontSize: 14, color: C.muted, alignment: "right", verticalAlignment: "bottom" });
    notes(s, [
      "https://data.worldbank.org/",
      "https://data.who.int/",
      "https://www.statista.com/",
      "https://statistics.cepal.org/portal/cepalstat/",
    ]);
  }

  // 2. Executive takeaway — metrics silhouette.
  {
    const s = p.slides.add();
    header(s, "La preparación técnica no garantiza el direccionamiento", "Lectura ejecutiva", 2);
    text(s, "El Banco Mundial y WHO Data lideran el puntaje integral; el piloto de búsqueda favorece al Banco Mundial por cobertura y ajuste a consultas generalistas.", 42, 142, 1160, 58, { fontSize: 24, color: C.muted });
    const cards = [
      ["77/100", "Banco Mundial y WHO Data", C.lightBlue],
      ["60/100", "Statista: citabilidad con acceso restringido", C.panel],
      ["45/100", "CEPALSTAT: API fuerte, capa web frágil", C.panel],
    ];
    cards.forEach((d, i) => {
      const x = 42 + i * 404;
      rect(s, x, 248, 374, 210, d[2], C.rule, true);
      text(s, d[0], x + 28, 278, 320, 70, { fontSize: 48, bold: true });
      text(s, d[1], x + 28, 364, 320, 62, { fontSize: 21, color: C.muted });
    });
    addBullet(s, "Fortaleza transversal", "Las cuatro páginas tienen una vía de datos o metadatos que puede servir a un agente.", 42, 500, 560, C.blue);
    addBullet(s, "Brecha transversal", "Las observaciones exactas siguen siendo menos descubribles que las definiciones y las portadas.", 650, 500, 560, C.amber);
    notes(s, [
      "outputs/aeo-comparative-matrix-2026-08-22.csv",
      "outputs/aeo-comparative-report-2026-08-22.md",
    ]);
  }

  // 3. Score chart — Codex Grid slide-20 chart-led silhouette.
  {
    const s = p.slides.add();
    header(s, "El ranking cambia cuando se iguala la evidencia", "Puntajes", 3);
    s.charts.add("bar", {
      position: { left: 42, top: 142, width: 670, height: 450 },
      categories: portals,
      series: [
        { name: "Integral", categories: portals, values: fullScores, fill: C.cyan },
        { name: "Núcleo comparable", categories: portals, values: coreScores, fill: C.blue },
      ],
      hasLegend: true,
      legend: { position: "bottom", overlay: false },
      dataLabels: { showValue: true },
      chartFill: C.white,
      chartLine: { style: "solid", width: 0, fill: C.white },
      xAxis: { visible: true, textStyle: { typeface: "Helvetica Neue", fontSize: "12px", color: C.ink } },
      yAxis: { visible: true, max: 100, majorUnit: 20, majorGridlines: { style: "solid", width: 1, fill: "#EDEDED" }, textStyle: { typeface: "Helvetica Neue", fontSize: "12px", color: C.ink } },
      barOptions: { direction: "column", grouping: "clustered", gapWidth: 70 },
    });
    rect(s, 764, 170, 450, 348, C.panel, C.rule, true);
    text(s, "Qué significa", 798, 204, 360, 34, { fontSize: 24, bold: true });
    text(s, "El núcleo comparable conserva solo descubrimiento, API y citabilidad —las dimensiones que sí pudimos observar de forma más uniforme.", 798, 258, 360, 100, { fontSize: 20, color: C.muted });
    text(s, "World Bank sube a 90,9 por su API y URLs reproducibles. CEPALSTAT sube, pero permanece último: su problema central es la conexión entre descubrimiento web y dato observable.", 798, 386, 360, 100, { fontSize: 20, color: C.ink });
    notes(s, [
      "outputs/aeo-comparative-matrix-2026-08-22.csv",
      "https://datahelpdesk.worldbank.org/knowledgebase/articles/889392",
      "https://data.who.int/products/data-description-schema",
      "https://www.statista.com/getting-started/more-statista-services-what-is-statista-connect",
      "https://api-cepalstat.cepal.org/apispec_1.json",
    ]);
  }

  // 4. Dimension heatmap — table evidence silhouette.
  {
    const s = p.slides.add();
    header(s, "La API es la ventaja más consistente; el descubrimiento es la brecha más desigual", "Dimensiones", 4);
    const x0 = 42, y0 = 150, labelW = 310, cellW = 210, rowH = 66;
    text(s, "Puntaje por dimensión", x0, y0 - 32, 300, 24, { fontSize: 16, color: C.muted, bold: true });
    portals.forEach((name, i) => text(s, name, x0 + labelW + i * cellW, y0 - 32, cellW - 10, 24, { fontSize: 16, bold: true, alignment: "center" }));
    dimensions.forEach(([name, vals], r) => {
      const y = y0 + r * rowH;
      rect(s, x0, y, labelW - 10, rowH - 8, C.panel, "none");
      text(s, name, x0 + 16, y + 17, labelW - 40, 28, { fontSize: 19, bold: true });
      vals.forEach((v, c) => {
        const max = r === 0 ? 10 : r === 1 ? 15 : r === 2 ? 20 : r === 3 ? 15 : r === 4 ? 25 : 15;
        rect(s, x0 + labelW + c * cellW, y, cellW - 10, rowH - 8, scoreFill(v, max), C.white);
        text(s, `${v}/${max}`, x0 + labelW + c * cellW, y + 14, cellW - 10, 30, { fontSize: 22, bold: true, alignment: "center" });
      });
    });
    text(s, "Verde = fortaleza relativa · amarillo = funcional con brechas · rojo = fricción relevante", 42, 590, 820, 28, { fontSize: 16, color: C.muted });
    text(s, "La lectura debe combinar puntaje con confianza de evidencia.", 860, 590, 350, 28, { fontSize: 16, color: C.muted, alignment: "right" });
    notes(s, ["outputs/aeo-comparative-matrix-2026-08-22.csv"]);
  }

  // 5. World Bank + WHO.
  {
    const s = p.slides.add();
    header(s, "Banco Mundial y WHO Data: dos caminos distintos hacia la citabilidad", "Portales públicos", 5);
    const cols = [42, 650];
    const data = [
      ["BANCO MUNDIAL", "API v2 pública, sin clave, con JSON/JSON-stat/CSV/XML/Excel y filtros reproducibles.", "Hacer visibles los valores sin JavaScript; publicar política de crawlers y structured data verificable."],
      ["WHO DATA", "Fichas con identificador, unidad, cobertura, periodicidad, método, licencia y texto de cita.", "Mapear cada indicador a un endpoint OData estable; aclarar sitemap, agentes IA y JSON-LD."],
    ];
    data.forEach((d, i) => {
      const x = cols[i];
      rect(s, x, 152, 544, 438, i === 0 ? C.pale : C.panel, C.rule, true);
      text(s, d[0], x + 26, 178, 490, 28, { fontSize: 16, color: C.blue, bold: true });
      text(s, "Destacable", x + 26, 236, 160, 28, { fontSize: 22, bold: true });
      text(s, d[1], x + 26, 276, 480, 96, { fontSize: 20, color: C.muted });
      rect(s, x + 26, 400, 488, 1, C.rule);
      text(s, "Mejora prioritaria", x + 26, 430, 220, 28, { fontSize: 22, bold: true });
      text(s, d[2], x + 26, 470, 480, 90, { fontSize: 20, color: C.ink });
    });
    notes(s, [
      "outputs/aeo-agent-readiness-data.worldbank.org-2026-08-22.md",
      "outputs/aeo-agent-readiness-data.who.int-2026-08-22.md",
      "https://datahelpdesk.worldbank.org/knowledgebase/articles/898581-api-basic-call-structures",
      "https://data.who.int/products/data-description-schema",
    ]);
  }

  // 6. Statista + CEPALSTAT.
  {
    const s = p.slides.add();
    header(s, "Statista y CEPALSTAT: citabilidad editorial frente a acceso programático", "Portales con fricción", 6);
    const cols = [42, 650];
    const data = [
      ["STATISTA", "Las fichas públicas muestran fuente, período, fecha, autor y formatos de cita.", "Paywall/registro y API autorizada reducen la llegada; ofrecer evidencia mínima pública y documentación OpenAPI de muestra."],
      ["CEPALSTAT", "REST/OpenAPI público, metadatos de fuentes, notas y dimensiones.", "Sitemap, `llms.txt`, tablas HTML planas, URLs canónicas por indicador y reparación de OpenAPI."],
    ];
    data.forEach((d, i) => {
      const x = cols[i];
      rect(s, x, 152, 544, 438, i === 0 ? C.panel : C.pale, C.rule, true);
      text(s, d[0], x + 26, 178, 490, 28, { fontSize: 16, color: C.blue, bold: true });
      text(s, "Destacable", x + 26, 236, 160, 28, { fontSize: 22, bold: true });
      text(s, d[1], x + 26, 276, 480, 96, { fontSize: 20, color: C.muted });
      rect(s, x + 26, 400, 488, 1, C.rule);
      text(s, "Mejora prioritaria", x + 26, 430, 220, 28, { fontSize: 22, bold: true });
      text(s, d[2], x + 26, 470, 480, 90, { fontSize: 20, color: C.ink });
    });
    notes(s, [
      "outputs/aeo-agent-readiness-www.statista.com-2026-08-22.md",
      "outputs/auditoria-aeo-agent-readiness-cepalstat-2026-08-20.md",
      "https://www.statista.com/getting-started/more-statista-services-what-is-statista-connect",
      "https://api-cepalstat.cepal.org/apispec_1.json",
    ]);
  }

  // 7. Cross-portal priorities.
  {
    const s = p.slides.add();
    header(s, "Las mejoras prioritarias son repetibles entre portales", "Hoja de ruta", 7);
    const rows = [
      ["P0", "Hacer descubrible el acceso", "robots.txt accesible, sitemap declarado, enlaces directos a datos y política clara para crawlers IA."],
      ["P1", "Hacer citable la observación", "Dataset/JSON-LD, tabla HTML inicial, unidad-período-geografía visibles y URL canónica por indicador."],
      ["P2", "Hacerlo reproducible a escala", "OpenAPI validado, versionado, identificadores persistentes, checksums, monitoreo y pruebas de paridad."],
    ];
    rows.forEach((d, i) => {
      const y = 156 + i * 142;
      rect(s, 42, y, 116, 104, i === 0 ? C.blue : C.panel, C.rule, true);
      text(s, d[0], 42, y + 30, 116, 42, { fontSize: 32, bold: true, color: i === 0 ? C.white : C.ink, alignment: "center" });
      text(s, d[1], 194, y + 14, 360, 34, { fontSize: 24, bold: true });
      text(s, d[2], 194, y + 54, 940, 52, { fontSize: 20, color: C.muted });
      if (i < 2) rect(s, 100, y + 108, 2, 34, C.blue);
    });
    notes(s, ["outputs/aeo-comparative-report-2026-08-22.md"]);
  }

  // 8. Referral pilot.
  {
    const s = p.slides.add();
    header(s, "El piloto sugiere relación, pero también revela un fuerte efecto de tema", "Direccionamiento", 8);
    s.charts.add("bar", {
      position: { left: 42, top: 160, width: 650, height: 410 },
      categories: portals,
      series: [{ name: "Exposición en top-10", categories: portals, values: [87.5, 25, 0, 12.5], fill: C.blue }],
      hasLegend: false,
      dataLabels: { showValue: true },
      chartFill: C.white,
      chartLine: { style: "solid", width: 0, fill: C.white },
      xAxis: { visible: true, textStyle: { typeface: "Helvetica Neue", fontSize: "12px", color: C.ink } },
      yAxis: { visible: true, max: 100, majorUnit: 20, majorGridlines: { style: "solid", width: 1, fill: "#EDEDED" }, textStyle: { typeface: "Helvetica Neue", fontSize: "12px", color: C.ink } },
      barOptions: { direction: "column", grouping: "clustered", gapWidth: 90 },
    });
    rect(s, 748, 172, 464, 348, C.panel, C.rule, true);
    text(s, "Resultado estadístico", 780, 208, 380, 32, { fontSize: 24, bold: true });
    text(s, "rho = 0,80", 780, 258, 380, 64, { fontSize: 48, bold: true, color: C.blue });
    text(s, "n = 4 portales · 8 consultas neutrales", 780, 334, 380, 28, { fontSize: 18, color: C.muted });
    text(s, "El Banco Mundial domina las consultas generalistas. WHO aparece en salud; CEPALSTAT en América Latina; Statista no aparece en este banco de estadísticas oficiales.", 780, 388, 380, 100, { fontSize: 20, color: C.ink });
    text(s, "Lectura correcta: señal descriptiva, no causalidad.", 780, 520, 380, 28, { fontSize: 17, color: C.muted, bold: true });
    notes(s, [
      "outputs/aeo-referral-pilot-2026-08-22.csv",
      "outputs/aeo-referral-pilot-analysis-2026-08-22.py",
      "https://data.worldbank.org/indicator/SP.POP.TOTL",
      "https://data.who.int/indicators/i/E3CAF2B/2322814",
      "https://statistics.cepal.org/portal/cepalstat/dashboard.html?area_id=930&indicator_id=5554&lang=en",
    ]);
  }

  // 9. Caveats and next step.
  {
    const s = p.slides.add();
    header(s, "La conclusión es accionable, pero debe conservar sus límites", "Lectura metodológica", 9);
    addBullet(s, "Puntaje", "El puntaje integral sigue la rúbrica de seis dimensiones. El núcleo comparable excluye bots, DOM y JSON-LD para igualar la evidencia.", 42, 160, 560, C.blue);
    addBullet(s, "Entorno", "El navegador interactivo local falló por cifrado de Windows; no se convirtió ese fallo en una penalización del sitio.", 42, 310, 560, C.amber);
    addBullet(s, "Direccionamiento", "La búsqueda web funciona como proxy de descubrimiento. El piloto debe ampliarse con más consultas, agentes y un panel mayor para inferencia.", 42, 460, 560, C.blue);
    rect(s, 688, 166, 526, 354, C.pale, C.rule, true);
    text(s, "Siguiente fase recomendada", 724, 204, 430, 32, { fontSize: 24, bold: true });
    text(s, "1. Separar readiness técnico de apertura comercial.\n\n2. Igualar el paquete mínimo por portal (home, catálogo, indicador, API).\n\n3. Repetir con 40–60 consultas estratificadas y 3 agentes navegadores.\n\n4. Recalcular con controles por tema, autoridad y paywall; reportar IC.", 724, 258, 430, 220, { fontSize: 20, color: C.ink });
    notes(s, ["outputs/aeo-comparative-report-2026-08-22.md", "outputs/aeo-referral-pilot-analysis-2026-08-22.py"]);
  }

  // 10. Appendix.
  {
    const s = p.slides.add();
    header(s, "Método y fuentes primarias", "Apéndice", 10);
    text(s, "Seis dimensiones ponderadas", 42, 146, 430, 30, { fontSize: 24, bold: true });
    text(s, "Bots 10 · Descubrimiento 15 · Renderizado 20\nDatos estructurados 15 · API 25 · Citabilidad 15", 42, 194, 470, 110, { fontSize: 21, color: C.muted });
    text(s, "Evidencia y entregables", 42, 340, 430, 30, { fontSize: 24, bold: true });
    text(s, "Tres informes AEO fechados por subagentes especializados · revisión adversarial · informe base CEPALSTAT · matriz comparativa · CSV y script del piloto · notebook no ejecutado por falta de Jupyter en el entorno.", 42, 388, 500, 120, { fontSize: 20, color: C.muted });
    rect(s, 650, 146, 564, 386, C.panel, C.rule, true);
    text(s, "Fuentes primarias", 686, 178, 480, 30, { fontSize: 24, bold: true });
    text(s, "World Bank Data / API\ndata.who.int / Data Description Schema\nStatista / Statista Connect\nCEPALSTAT / OpenAPI\nRFC 9309 — Robots Exclusion Protocol", 686, 232, 480, 170, { fontSize: 20, color: C.ink });
    text(s, "Todos los informes y datos de apoyo quedan en outputs/.", 686, 454, 480, 28, { fontSize: 17, color: C.muted });
    notes(s, [
      "outputs/aeo-agent-readiness-data.worldbank.org-2026-08-22.md",
      "outputs/aeo-agent-readiness-data.who.int-2026-08-22.md",
      "outputs/aeo-agent-readiness-www.statista.com-2026-08-22.md",
      "outputs/auditoria-aeo-agent-readiness-cepalstat-2026-08-20.md",
      "https://www.rfc-editor.org/rfc/rfc9309",
    ]);
  }

  for (const [i, slide] of p.slides.items.entries()) {
    const stem = `slide-${String(i + 1).padStart(2, "0")}`;
    await writeBlob(`${PNG_DIR}/${stem}.png`, await p.export({ slide, format: "png", scale: 1 }));
    await fs.writeFile(`${PNG_DIR}/${stem}.layout.json`, await (await slide.export({ format: "layout" })).text());
  }
  await writeBlob(`${PNG_DIR}/montage.webp`, await p.export({ format: "webp", montage: true, scale: 1 }));
  const pptx = await PresentationFile.exportPptx(p);
  await pptx.save(OUT);
  console.log(OUT);
}

main().catch((err) => {
  console.error(err);
  process.exitCode = 1;
});
