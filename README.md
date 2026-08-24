# AEO y AI readiness de portales estadísticos

Repositorio reproducible de la evaluación comparada de cinco portales
estadísticos globales. El benchmark principal del PDF permanece separado del
piloto operativo y todavía no está cerrado.

- Banco Mundial (`data.worldbank.org`)
- WHO Data (`data.who.int`)
- CEPALSTAT (`statistics.cepal.org`)
- UN Data Commons / UNSD (`unstats.un.org`)
- UN SDG Indicators (`unstats.un.org`)

Statista queda fuera del universo activo.

El proyecto aplica la habilidad `aeo-agent-readiness-auditor` en seis dimensiones: bots/gobernanza, descubrimiento, renderizado, **marcado estructurado embebido en HTML/DOM** (JSON-LD, microdatos o equivalente), API para agentes de código y autoridad/citabilidad. La API, JSON/XML y las exportaciones CSV/XLSX son acceso estructurado de datos y se informan por separado; `structured_data=ABSENT` nunca significa que el portal carezca de API o descargas.

## Entregables

Los artefactos de `outputs/` corresponden a evaluaciones históricas o a
entregables que sólo se consideran finales después del cierre validado del
benchmark de cinco portales.

- `outputs/aeo-agent-readiness-*.md`: informes por portal.
- `outputs/aeo-comparative-report-2026-08-22.md`: comparación ejecutiva.
- `outputs/aeo-comparative-matrix-2026-08-22.csv`: matriz cuantitativa completa y armonizada.
- `outputs/aeo-referral-pilot-2026-08-22.csv`: resultados del piloto de direccionamiento.
- `outputs/aeo-referral-pilot-analysis-2026-08-22.py`: cálculo reproducible, incluido Spearman.
- `outputs/aeo-referral-pilot-analysis-2026-08-22.ipynb`: notebook companion; requiere Jupyter.
- `outputs/`: entregables locales regenerables (los binarios no se versionan).
- `audit_evidence/`: evidencia HTTP archivada de la evaluación previa.
- `tools/audit_http.py`: utilidad de captura HTTP.
- `tools/build_comparative_deck.mjs`: builder portable de la presentación.

## Evaluación E2E live y fase editorial cerrada

La ejecución final se hizo desde cero, sin evidencia congelada: 30 plantillas ×
5 portales × 3 repeticiones = **450 ejecuciones**. Se mantuvieron tres
manifiestos independientes para aplicar el fallback operativo (dos portales y
luego uno cuando fue necesario):

- `e2e_cepalstat-worldbank-30x2x3-20260823-v12` — 180/180.
- `e2e_who-30x1x3-20260823-v4` — 90/90, aislado por estabilidad del endpoint.
- `e2e_undata-sdg-30x2x3-20260823-v5` — 180/180, relanzado desde limpio tras
  un reset transitorio de conexión diagnosticado y verificado con GET aislado.

El [comparativo editorial](benchmark/results/fresh/e2e_undata-sdg-30x2x3-20260823-v5/editorial/comparative_report.md),
los [informes por portal](benchmark/results/fresh/e2e_undata-sdg-30x2x3-20260823-v5/editorial/),
la [matriz de 450 filas](benchmark/results/fresh/e2e_undata-sdg-30x2x3-20260823-v5/editorial/execution_matrix_450.csv)
y el [visor HTML de respuestas](benchmark/results/fresh/e2e_undata-sdg-30x2x3-20260823-v5/editorial/model_response_viewer.html)
son los artefactos versionados vigentes. La planilla, PPT y documentos Word
se conservan localmente como salidas regenerables y quedan fuera del remoto.

Para revisar las preguntas, alternativas y respuestas de los modelos está
disponible el [visor HTML de respuestas](benchmark/results/fresh/e2e_undata-sdg-30x2x3-20260823-v5/editorial/model_response_viewer.html).
Es un artefacto estático con filtros por portal, estado, estrato y repetición;
incluye el detalle de cada decisión, comparación lado a lado entre repeticiones
y exportación de la selección filtrada a CSV o JSON. Se regenera con:

```bash
python benchmark/build_model_response_viewer.py
```

El visor incrusta las preguntas, candidatos y `model_raw`, y mantiene enlaces a
los JSON originales, `results.jsonl` y las respuestas crudas de las APIs. No
recalcula ni modifica ninguna evidencia.

La política de selección conserva siempre el primer indicador elegido por el
modelo. Un candidato incorrecto se registra como `MODEL_SELECTION_ERROR`, se
mantienen candidato y near-matches, y no se sustituye retrospectivamente. Un
`NOT_VERIFIED` de recuperación o cero observaciones después de dos intentos
detiene la corrida, escribe `review_alert.json` y obliga a relanzar desde un
directorio limpio.

En CEPALSTAT la revisión live verificó además tres exportaciones XLSX: un caso
filtrado del indicador 2203 (Chile, 2024) y dos indicadores de otras familias.
El archivo conserva datos, dimensiones, unidad, metadatos, fuentes, notas y
créditos; la evidencia está en `evidence/exports/` y
`evidence/technical/cepalstat_export_review.json`.

El contrato canónico del PDF (120 × 5 × 3 = 1.800, cinco pasadas de 360) queda
como ampliación futura; la evaluación editorial vigente es la muestra live de
450 filas y no debe presentarse como 1.800 observaciones independientes.

Los artefactos históricos, incluido el piloto congelado de 360 filas, están
archivados en
`deprecated/2026-08-23-five-portal-evaluations/` y no alimentan la matriz
vigente.

## Reproducir el piloto histórico de direccionamiento

```powershell
python outputs/aeo-referral-pilot-analysis-2026-08-22.py
```

Resultado de referencia histórico: exposición Banco Mundial 0,875; WHO 0,250;
Statista 0,000; CEPALSTAT 0,125; Spearman rho = 0,800 (n=4 portales, 8
consultas). Es una señal exploratoria, no causal y no es comparable directamente
con el piloto operativo nuevo.

## Regenerar la PPT

El builder usa `@oai/artifact-tool` y Node.js. En el entorno de escritorio de Codex se deben configurar `RUNTIME_NODE`, `RUNTIME_NODE_MODULES` y `RUNTIME_BIN_DIR` según las dependencias locales, y ejecutar desde la raíz:

```powershell
node tools/build_comparative_deck.mjs
```

## Repetir la evaluación completa

En un computador con navegador automatizable y acceso HTTP sin las restricciones de este entorno:

1. Repetir cada auditoría con el skill `aeo-agent-readiness-auditor`.
2. Verificar directamente `robots.txt`, `sitemap.xml`, `llms.txt`, headers, DOM post-JavaScript y JSON-LD.
3. Mantener la puntuación estricta de seis dimensiones y documentar estados `Verified`, `Inferred` y `Not verified`.
4. Reportar además el núcleo armonizado (`D2 + D5 + D6`) para comparabilidad histórica.
5. Para repetir la evaluación live actual, ejecutar `benchmark/fresh_e2e_runner.py`
   por bloques de dos portales; si se activa una compuerta, aislar un portal,
   resolver la evidencia y relanzar desde cero. Consolidar sólo manifiestos
   `COMPLETE` con `benchmark/build_fresh_editorial.py`.
6. Congelar fecha, URLs y evidencia sólo como trazabilidad; el runner actual
   vuelve a consultar catálogo y serie en cada repetición.

## Limitaciones conocidas

La ejecución original no pudo inicializar el navegador interactivo por un error local de cifrado de Windows. Por eso bots, DOM y JSON-LD se trataron como no verificables de forma equivalente y se reportó una sensibilidad armonizada. Statista también requiere separar preparación técnica de apertura comercial.

No se incluyen credenciales, tokens ni datos personales en este repositorio.
