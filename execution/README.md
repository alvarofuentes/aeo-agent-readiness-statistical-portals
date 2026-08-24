# Ejecución AEO live — 2026-08-23

Esta carpeta documenta el protocolo vigente para evaluar visibilidad de agentes
y preparación técnica de cinco portales estadísticos. La evidencia congelada y
los entregables anteriores están archivados en
`deprecated/2026-08-23-five-portal-evaluations/`.

## Universo y muestra vigente

Portales: World Bank Open Data, WHO Data, CEPALSTAT, UN Data Commons/UNSD y UN
SDG Indicators. La evaluación editorial live reúne 30 plantillas, tres
repeticiones y 450 ejecuciones en tres manifiestos independientes:

- CEPALSTAT/WB: 180 filas.
- WHO aislado: 90 filas.
- UNData/SDG: 180 filas.

El contrato canónico del PDF (120 × 5 × 3 = 1.800) se conserva como ampliación
futura; no se afirma haberlo ejecutado en esta fase.

## Protocolo E2E

`benchmark/fresh_e2e_runner.py` consulta el catálogo y la serie oficial en cada
repetición. El modelo descompone la pregunta y propone un indicador; la primera
selección se conserva sin sustitución. Si el indicador es semánticamente
incorrecto, la fila registra `MODEL_SELECTION_ERROR`, sus metadatos y
near-matches, y el retrieval se ejecuta igualmente para medir el coste de la
discriminación.

La hipótesis operacional admite que una consulta específica devuelva una sola
URL: es un PASS si esa URL corresponde al indicador, período, geografía, unidad,
frecuencia, base de precios y fuente solicitados.

La capa técnica (robots, sitemap, llms.txt, HTML inicial, DOM post-JavaScript,
marcado JSON-LD/microdatos, API aislada, exportaciones machine-readable y
citabilidad) se informa por separado y no se suma al resultado E2E. La etiqueta
`structured_data=ABSENT` sólo describe el marcado embebido; no niega una API o
una descarga XLSX/CSV verificada.

## Gates fail-closed

- `NOT_VERIFIED` de recuperación limpia: detener, escribir `review_alert.json`,
  revisar la solicitud real y relanzar desde un directorio nuevo.
- Cero observaciones después de dos intentos: detener y revisar ruta,
  dimensiones y selección; no convertir en cero ni reordenar candidatos.
- Reset/timeout/HTTP 5xx transitorio: reintentar una vez; si persiste, mantener
  `NOT_VERIFIED` y activar el gate.
- Un `MODEL_SELECTION_ERROR` no activa por sí solo el gate de transporte: es un
  resultado de visibilidad semántica y debe quedar visible en la matriz.

## Corridas y entregables

Corridas limpias:

```text
benchmark/results/fresh/e2e_cepalstat-worldbank-30x2x3-20260823-v12/
benchmark/results/fresh/e2e_who-30x1x3-20260823-v4/
benchmark/results/fresh/e2e_undata-sdg-30x2x3-20260823-v5/
```

El paquete editorial final está en el último directorio, bajo `editorial/`:
matriz de 450 filas, cinco informes detallados, comparativo, recomendaciones,
planilla y PPT con QA de render y overflow. El ledger técnico final tiene cero
filas `NOT_VERIFIED`; el incidente v4 queda conservado como diagnóstico y no
entra al consolidado.

Para cambios futuros, ejecutar primero un bloque de dos portales; si aparece
una compuerta, aislar uno, resolver la evidencia, relanzar desde cero y sólo
entonces continuar con el siguiente bloque.
