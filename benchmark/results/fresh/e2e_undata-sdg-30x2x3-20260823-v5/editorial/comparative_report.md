# Comparativo E2E — who · cepalstat · worldbank · undata · sdg

**Run editorial:** `e2e_undata-sdg-30x2x3-20260823-v5` · **Fuentes:** e2e_cepalstat-worldbank-30x2x3-20260823-v12, e2e_who-30x1x3-20260823-v4, e2e_undata-sdg-30x2x3-20260823-v5 · **Muestra:** 450 ejecuciones live

## Resultado separado por capa

| Portal | E2E PASS | E2E rate | Errores selección modelo | Score técnico | Confianza | No verificados | API directa | Exportación estructurada |
|---|---:|---:|---:|---:|---|---:|---|---|
| who | 0/90 | 0.0% | 8 (8.9%) | 85/100 | high | 0 | PASS | NOT_TESTED () |
| cepalstat | 90/90 | 100.0% | 0 (0.0%) | 75/100 | high | 0 | PASS | PASS (xlsx) |
| worldbank | 90/90 | 100.0% | 0 (0.0%) | 100/100 | high | 0 | PASS | NOT_TESTED () |
| undata | 84/90 | 93.3% | 0 (0.0%) | 85/100 | high | 0 | PASS | NOT_TESTED () |
| sdg | 15/90 | 16.7% | 0 (0.0%) | 85/100 | high | 0 | PASS | NOT_TESTED () |

## Dimensiones técnicas

| Portal | Descubrimiento | API/acceso de datos | Renderizado | Marcado HTML estructurado | Autoridad/cita | Accesibilidad |
|---|---|---|---|---|---|---|
| who | PASS | PASS | PASS | ABSENT | PASS | PASS |
| cepalstat | PASS | PASS | PASS | ABSENT | PASS | ABSENT |
| worldbank | PASS | PASS | PASS | PASS | PASS | PASS |
| undata | PASS | PASS | PASS | ABSENT | PASS | PASS |
| sdg | PASS | PASS | PASS | ABSENT | PASS | PASS |

## Interpretación por portal

- **who:** La recuperación de transporte fue 100.0%, pero 8/90 filas conservaron un error de selección semántica; no debe leerse como fallo de API. Score técnico 85/100; `ABSENT` describe ausencia comprobada del marcado HTML embebido y `NOT_VERIFIED` sería una brecha bloqueante.
- **cepalstat:** La muestra pasó selección y recuperación en todas las filas; la lectura técnica queda separada del resultado operacional. Score técnico 75/100; `ABSENT` describe ausencia comprobada del marcado HTML embebido y `NOT_VERIFIED` sería una brecha bloqueante.
- **worldbank:** La muestra pasó selección y recuperación en todas las filas; la lectura técnica queda separada del resultado operacional. Score técnico 100/100; `ABSENT` describe ausencia comprobada del marcado HTML embebido y `NOT_VERIFIED` sería una brecha bloqueante.
- **undata:** La ruta API fue verificable, pero 84/90 filas pasaron el gate completo; las restantes requieren revisar dimensiones/criterio de respuesta. Score técnico 85/100; `ABSENT` describe ausencia comprobada del marcado HTML embebido y `NOT_VERIFIED` sería una brecha bloqueante.
- **sdg:** La ruta API fue verificable, pero 15/90 filas pasaron el gate completo; las restantes requieren revisar dimensiones/criterio de respuesta. Score técnico 85/100; `ABSENT` describe ausencia comprobada del marcado HTML embebido y `NOT_VERIFIED` sería una brecha bloqueante.

## Método y límites

- Evidencia live por repetición: 450 ejecuciones agregadas desde 3 manifiestos `COMPLETE`; no se usó gold ni captura congelada para el retrieval.
- La unidad de comparación es el portal (n=5). Consulta y repetición son medidas agrupadas; estas cifras no demuestran causalidad entre AEO técnico y visibilidad.
- Una consulta específica puede tener una sola URL correcta. El criterio es indicador + definición + unidad + período + geografía + fuente, no cantidad de enlaces.
- El incidente de transporte SDG en la corrida v4 se conserva fuera del consolidado; fue verificado con GET aislado y la corrida v5 se relanzó desde cero.

## Próximas acciones

- Priorizar la discriminación explícita de metadatos en CEPALSTAT y repetir sólo después de cambios trazables.
- Mantener el ledger y las compuertas fail-closed en cualquier ampliación al contrato canónico de 1.800 filas.
- Ver `recommendations-and-best-practices.md` para mejoras CEPALSTAT y ejemplos de robots.txt/llms.txt.
