# AEO and Agent Readiness Audit Report Template

Use this template as a skeleton. Replace every bracketed placeholder. Remove sections that are genuinely not applicable, but never remove the evidence and limitation disclosures.

```markdown
# Auditoría AEO y preparación para agentes de IA de [SITIO]

**Portal auditado:** [Nombre](URL)  
**Host:** `[host]`  
**Fecha de corte:** [YYYY-MM-DD]  
**Página interna de muestra:** [Nombre](URL)  
**Calificación global:** **[NN]/100 — [Banda]**

## 1. Resumen ejecutivo

[Veredicto, principal fortaleza, principal barrera y consecuencia para agentes.]

## 2. Calificación consolidada

| Dimensión | Peso | Puntaje | Diagnóstico | Confianza |
|---|---:|---:|---|---|
| Acceso y gobernanza de bots | 10 | | | |
| Descubrimiento técnico | 15 | | | |
| Renderizado e interacción | 20 | | | |
| Datos estructurados | 15 | | | |
| API para agentes de código | 25 | | | |
| Autoridad y citabilidad | 15 | | | |
| **Total** | **100** | **[NN]** | **[Banda]** | |

## 3. Metodología, alcance y limitaciones

[Herramientas, páginas examinadas, evidencia proporcionada por el usuario y pruebas no completadas.]

### Capas separadas

- **Visibilidad operacional:** consulta natural → búsqueda dentro del portal → candidatos → selección semántica → registro/serie → valor → metadatos → cita primaria.
- **Preparación técnica:** bots, descubrimiento, renderizado, datos estructurados, API y citabilidad.

No sumar ni promediar ambas capas.

## 4. Prueba end-to-end de visibilidad

| Paso | Evidencia | Resultado | Confianza |
|---|---|---|---|
| Consulta y descomposición | | | |
| Búsqueda dentro del portal | | | |
| Candidatos y near-matches | | | |
| Selección específica | | | |
| Valor/registro y dimensiones | | | |
| Metadatos completos | | | |
| Cita primaria reproducible | | | |

### Diagnóstico de selección del modelo

| Campo | Resultado |
|---|---|
| `selection_status` | [PASS / FAIL] |
| `selection_failure_class` | [MODEL_SELECTION_ERROR / otro / —] |
| Candidato elegido por el modelo | [ID y nombre exactos] |
| Metadatos esperados vs observados | [scope, geography, period, unit, frequency, price base] |
| Recuperación posterior | [continúa con el candidato original; no se re-selecciona] |

**Gate E2E:** [PASS / FAIL / NOT_VERIFIED / NOT_APPLICABLE]. Una sola URL específica puede ser correcta si el objeto coincide con la pregunta y la evidencia es completa.

Si el modelo escogió una serie semánticamente incompatible, informar `MODEL_SELECTION_ERROR` como resultado separado: conservar el candidato original, sus metadatos y near-matches, continuar la recuperación y no sustituirlo silenciosamente.

## 5. Acceso y descubrimiento para bots

### Evidencia HTTP

| URL | Estado | Content-Type | Redirect final | Resultado | Evidencia |
|---|---:|---|---|---|---|
| `/robots.txt` | | | | | |
| `/sitemap.xml` | | | | | |
| `/sitemap_index.xml` | | | | | |
| `/llms.txt` | | | | | |

### Política de crawlers

[Grupos, Allow/Disallow, agentes de IA actuales, conflictos y controles no verificados.]

### Sitemap y `llms.txt`

[Cobertura, jerarquía, canonicales, idiomas, fechas y orientación para LLMs.]

## 6. Renderizado y muros de interacción

### Página principal

[HTML inicial frente a DOM renderizado.]

### Página interna

[Entidad, metadatos y valores disponibles sin interacción.]

### Muros principales

1. [Barrera y efecto para el agente.]

## 7. Datos estructurados

[JSON-LD, tipos, sintaxis, coherencia, ausencias verificadas o elementos no detectados.]

| Check | Status | Evidence state | Verification gap | Next verification action |
|---|---|---|---|---|
| HTML inicial | [PASS / ABSENT / NOT_VERIFIED] | | | |
| DOM renderizado | [PASS / ABSENT / NOT_VERIFIED] | | | |

## 8. APIs y acceso para agentes de código

[Documentación, especificación, ejemplo de llamada, ergonomía, errores y formatos.]

| Route / identifier | Declared in scripts | Independent HTTP | Status | Gap / next action |
|---|---|---|---|---|
| | | | | |

## 9. Citabilidad y visibilidad en motores de respuesta

[Prueba de cita y puntos donde se pierde valor, unidad, período, fuente o URL estable.]

## 10. Plan de remediación

### P0 — 0 a 2 semanas

1. [Acción concreta → barrera corregida.]

### P1 — 2 a 6 semanas

1. [Acción concreta → barrera corregida.]

### P2 — 6 a 12 semanas

1. [Acción concreta → barrera corregida.]

## 11. Criterios de aceptación para “Preparado para Agentes”

- [Resultado verificable.]

## 12. Integración en comparativos estadísticos

| Campo | Resultado |
|---|---|
| `technical_score` / `technical_confidence` | |
| `e2e_queries` / `e2e_passes` / `e2e_pass_rate` | |
| `candidate_count_mean` / `specific_url_rate` | |
| `metadata_complete_rate` / `citation_reproducible_rate` | |
| `robots_status` / `sitemap_status` / `llms_status` | |
| `jsonld_rendered` / `api_direct_verified` | |
| `evidence_date` / `source_evidence_path` | |
| `status` | |

## 13. Anexo de evidencia y confianza

| Hallazgo | Clasificación | Evidencia | Confianza |
|---|---|---|---|
| | Verificado / Inferido / No verificado / No aplicable | | |

### Ledger obligatorio de instancias no verificadas

| Check ID | Status | Evidence state | Observed evidence | Verification gap | Next verification action |
|---|---|---|---|---|---|
| | NOT_VERIFIED | | | | |

## 14. Fuentes primarias

- [Fuente](URL)
```
