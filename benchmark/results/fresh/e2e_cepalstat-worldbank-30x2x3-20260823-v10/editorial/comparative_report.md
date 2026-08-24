# Comparativo E2E CEPALSTAT vs World Bank

**Run:** `e2e_cepalstat-worldbank-30x2x3-20260823-v10` · **Muestra:** 180 ejecuciones live (30 plantillas × 2 portales × 3 repeticiones)

## Resultado separado por capa

| Portal | E2E PASS | E2E rate | Errores selección modelo | Score técnico | Confianza | No verificados | API directa |
|---|---:|---:|---:|---:|---|---:|---|
| cepalstat | 90/90 | 100.0% | 0 (0.0%) | 50/100 | limited | 6 | PASS |
| worldbank | 89/90 | 98.9% | 0 (0.0%) | 60/100 | limited | 6 | PASS |

## Lectura editorial

- La visibilidad operacional y la preparación técnica se presentan como resultados distintos.
- `MODEL_SELECTION_ERROR` mide una selección semántica incorrecta del modelo; el candidato elegido y su recuperación permanecen intactos para estudiar la discriminación de metadatos.
- `NOT_VERIFIED` no se convirtió en cero ni en ausencia: cada caso conserva su brecha y acción de cierre en `unverified_ledger.csv`.
- La conclusión sólo debe afirmar lo que las 180 recuperaciones live y las sondas técnicas observaron; el DOM post-JavaScript y cualquier ruta API declarada pero no aislada permanecen pendientes.
