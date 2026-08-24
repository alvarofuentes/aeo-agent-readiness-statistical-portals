# Recomendaciones editoriales y de implementación

**Base:** `e2e_cepalstat-worldbank-30x2x3-20260823-v10` · evidencia live de 180 ejecuciones. Las tasas y estados se calculan desde la matriz; no se convierten estados pendientes en ceros.

## 1. CEPALSTAT: mejoras prioritarias

1. **Discriminación de metadatos en la búsqueda:** exponer como campos filtrables y visibles `scope` (país/agregado vs subnacional), geografía, frecuencia, unidad, base de precios y desagregación por actividad. El caso `MODEL_SELECTION_ERROR` de la matriz debe poder evitarse con esos campos, pero el benchmark conserva la elección original para medirla.
2. **Resultado de búsqueda orientado a series:** devolver ID, etiqueta canónica, definición, unidad, frecuencia, cobertura geográfica, última actualización, fuente y URL/API de la serie en un único resultado.
3. **API de dimensiones explícita:** documentar nombres y códigos de cada dimensión, incluyendo áreas subnacionales, y publicar ejemplos de filtros para una observación nacional y una subnacional.
4. **Citabilidad estable:** enlazar cada serie a una URL canónica que preserve indicador, dimensiones y período; permitir descargar la respuesta JSON con esos parámetros.
5. **Renderizado y datos estructurados:** incorporar JSON-LD/microdatos en HTML inicial o capturar un DOM estable; cerrar las filas del ledger antes de declarar ausencia.

## 2. Prácticas transferibles observadas en portales estadísticos

- Separar en la interfaz y API el objeto indicador de sus dimensiones; no mezclar nivel, crecimiento y per cápita en etiquetas casi idénticas.
- Hacer que la respuesta de una consulta específica llegue a una serie/observación reproducible, aunque sea una sola URL.
- Mantener una nota de fuente y fecha de actualización junto al valor, no en una pantalla desconectada.
- Probar cada cambio con preguntas naturales que incluyan near-matches: total vs actividad, anual vs trimestral, corriente vs constante y país vs área subnacional.

## 3. Ejemplos de archivos de orientación para agentes

Los siguientes son ejemplos mínimos ilustrativos; deben adaptarse a las rutas reales y validarse contra la política de rastreo institucional.

### robots.txt

```text
User-agent: *
Allow: /portal/
Allow: /api/
Disallow: /admin/
Disallow: /session/
Sitemap: https://datos.ejemplo.org/sitemap.xml
```
La regla debe permitir las páginas y APIs públicas que sostienen las citas, bloquear sólo áreas privadas o sensibles y declarar el sitemap canónico.

### llms.txt

```text
# Portal estadístico
Descripción: catálogo oficial de indicadores y observaciones.

## Rutas recomendadas
- Catálogo: https://datos.ejemplo.org/api/indicators
- Serie: https://datos.ejemplo.org/indicator/{id}
- API: https://datos.ejemplo.org/api/

## Cómo citar
Conservar indicador, geografía, período, unidad, fuente y fecha de actualización.
## Evitar
No usar el primer resultado sin verificar alcance, frecuencia o unidad.
```

## 4. Criterio para ampliar a tres portales

La ampliación sólo debe iniciarse cuando el piloto CEPALSTAT/World Bank cierre con manifiesto COMPLETE, sin alertas abiertas y con una matriz/editorial QA. En ese momento se reutiliza el mismo contrato y se agregan los tres portales restantes sin mezclar sus resultados con esta muestra.

World Bank en este piloto: 89/90 E2E PASS; CEPALSTAT: 90/90 E2E PASS. Estos valores son descriptivos del run y no prueban causalidad.
