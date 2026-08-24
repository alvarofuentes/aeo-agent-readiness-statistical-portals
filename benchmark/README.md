# AEO benchmark

Este directorio contiene el benchmark E2E dirigido al portal. Las corridas
históricas y de evidencia congelada están en
`deprecated/2026-08-23-five-portal-evaluations/` y no alimentan los resultados
vigentes.

## Contrato y gates

`fresh_e2e_runner.py` actualiza el catálogo oficial en cada repetición,
selecciona con un modelo local, consulta la serie y escribe evidencia HTTP live.
La primera selección del modelo nunca se reemplaza silenciosamente: si el
indicador no corresponde, la fila conserva candidato y near-matches y se marca
`MODEL_SELECTION_ERROR`.

La muestra editorial vigente reúne tres manifiestos limpios:

1. CEPALSTAT + World Bank: 30 × 2 × 3 = 180.
2. WHO aislado: 30 × 1 × 3 = 90.
3. UNData + SDG: 30 × 2 × 3 = 180.

Total: **450 ejecuciones live**, 30 plantillas, cinco portales y tres
repeticiones. La unidad para cualquier comparación portal-level sigue siendo el
portal; consulta y repetición son medidas agrupadas, no observaciones
independientes.

La capa técnica es independiente del gate E2E e incluye un ledger explícito de
instancias `NOT_VERIFIED`, con estado de evidencia, brecha y próxima acción.
`structured_data` se reserva para marcado JSON-LD/microdatos embebido en el
HTML/DOM; API y descargas CSV/XLSX se registran como acceso estructurado
independiente. En CEPALSTAT el probe live de exportación XLSX está en
`evidence/technical/cepalstat_export_review.json`.
Los builders editoriales consumen sólo manifiestos `COMPLETE` y preservan por
separado `PASS`, `FAIL`, `MODEL_SELECTION_ERROR`, `NOT_VERIFIED` y
`NOT_APPLICABLE`.

## Ejecución live

```bash
python3 benchmark/fresh_e2e_runner.py \
  --model qwen3.5:9b-mlx \
  --endpoints http://127.0.0.1:11436 \
  --portals cepalstat,worldbank \
  --repeats 3 --workers 1
```

El runner también admite `--portals who`, `--portals undata,sdg` y
`--portals sdg`. Se usa un endpoint estable y un worker por defecto; la
paralelización de varios endpoints produjo errores 500 transitorios en el
modelo local.

Cada run escribe manifiesto, JSONL, banco usado, catálogo por repetición,
respuestas crudas, probes técnicos y trazas de selección. Un `NOT_VERIFIED` de
recuperación nunca se convierte en cero. Si aparece en una fila limpia, o si
una consulta tiene cero observaciones después de dos intentos, el manifiesto
pasa a `PAUSED_FOR_REVIEW`, se escribe `review_alert.json` y se debe relanzar
desde un directorio limpio. Los resets de conexión se reintentan una vez; si
persisten, el gate continúa siendo fail-closed.

## Paquete editorial vigente

Está en
`benchmark/results/fresh/e2e_undata-sdg-30x2x3-20260823-v5/editorial/`:

- `execution_matrix_450.csv` y `portal_summary.csv`;
- un informe detallado `report-<portal>-30x2x3.md` por portal;
- `comparative_report.md` y `recommendations-and-best-practices.md`;
- `model_response_viewer.html`, visor estático de preguntas, alternativas,
  decisiones del modelo, resultados E2E y comparación entre repeticiones;
- `unverified_ledger.csv` (sin filas porque los probes técnicos cerraron).

Los entregables binarios regenerables (`.xlsx`, `.pptx` y `.docx`) no se
versionan en Git; permanecen disponibles en el árbol local de trabajo.

El visor se regenera desde la raíz del repositorio con
`python benchmark/build_model_response_viewer.py`. La salida incorpora los
artefactos de los tres manifiestos vigentes y enlaza a sus evidencias sin
copiarlas ni alterarlas.

El contrato canónico del PDF —120 × 5 × 3 = 1.800, cinco pasadas de 360— queda
como ampliación futura. No se debe presentar la muestra editorial de 450 como
si fueran 1.800 ejecuciones.

## Piloto histórico (deprecated)

`benchmark/results/pilot/pilot_cepalstat-sdg-60x2x3-20260823/` contiene el
piloto congelado de 360 filas. Es un diagnóstico de runtime y no una muestra
semántica independiente; su publicación quedó en `HOLD`. El piloto es
recuperable bajo `deprecated/` y no es evidencia para la matriz live actual.

No llamar `production_runner.py` para esta evaluación: implementa el contrato
retirado de evidencia congelada y el gate canónico de 1.800 filas.
