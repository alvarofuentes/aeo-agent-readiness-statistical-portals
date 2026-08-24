# Comparativo E2E — who

**Run editorial:** `e2e_who-30x1x3-20260823-v4` · **Fuentes:** e2e_who-30x1x3-20260823-v4 · **Muestra:** 90 ejecuciones live

## Resultado separado por capa

| Portal | E2E PASS | E2E rate | Errores selección modelo | Score técnico | Confianza | No verificados | API directa |
|---|---:|---:|---:|---:|---|---:|---|
| who | 0/90 | 0.0% | 8 (8.9%) | 85/100 | high | 0 | PASS |

## Dimensiones técnicas

| Portal | Descubrimiento | Recuperación | Renderizado | Datos estructurados | Autoridad/cita | Accesibilidad |
|---|---|---|---|---|---|---|
| who | PASS | PASS | PASS | ABSENT | PASS | PASS |

## Interpretación por portal

- **who:** La recuperación de transporte fue 100.0%, pero 8/90 filas conservaron un error de selección semántica; no debe leerse como fallo de API. Score técnico 85/100; `ABSENT` describe ausencia comprobada y `NOT_VERIFIED` sería una brecha bloqueante.

## Método y límites

- Evidencia live por repetición: 90 ejecuciones agregadas desde 1 manifiestos `COMPLETE`; no se usó gold ni captura congelada para el retrieval.
- La unidad de comparación es el portal (n=5). Consulta y repetición son medidas agrupadas; estas cifras no demuestran causalidad entre AEO técnico y visibilidad.
- Una consulta específica puede tener una sola URL correcta. El criterio es indicador + definición + unidad + período + geografía + fuente, no cantidad de enlaces.
- El incidente de transporte SDG en la corrida v4 se conserva fuera del consolidado; fue verificado con GET aislado y la corrida v5 se relanzó desde cero.

## Próximas acciones

- Priorizar la discriminación explícita de metadatos en CEPALSTAT y repetir sólo después de cambios trazables.
- Mantener el ledger y las compuertas fail-closed en cualquier ampliación al contrato canónico de 1.800 filas.
- Ver `recommendations-and-best-practices.md` para mejoras CEPALSTAT y ejemplos de robots.txt/llms.txt.
