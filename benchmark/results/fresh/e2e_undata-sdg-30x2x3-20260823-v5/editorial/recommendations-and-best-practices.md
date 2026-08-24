# Recomendaciones editoriales y de implementación

**Base:** `e2e_undata-sdg-30x2x3-20260823-v5` · evidencia live de 450 ejecuciones. Las tasas y estados se calculan desde la matriz; no se convierten estados pendientes en ceros.

## 1. CEPALSTAT: mejoras prioritarias

1. **Discriminación de metadatos en la búsqueda:** exponer como campos filtrables y visibles `scope` (país/agregado vs subnacional), geografía, frecuencia, unidad, base de precios y desagregación por actividad. Si aparece `MODEL_SELECTION_ERROR`, la matriz conserva la elección original para medir el coste de esa ambigüedad.
2. **Resultado de búsqueda orientado a series:** devolver ID, etiqueta canónica, definición, unidad, frecuencia, cobertura geográfica, última actualización, fuente y URL/API de la serie en un único resultado.
3. **API de dimensiones explícita:** documentar nombres y códigos de cada dimensión, incluyendo áreas subnacionales, y publicar ejemplos de filtros para una observación nacional y una subnacional.
4. **Citabilidad estable:** enlazar cada serie a una URL canónica que preserve indicador, dimensiones y período; permitir descargar la respuesta JSON con esos parámetros.
5. **Marcado y acceso estructurado:** incorporar JSON-LD/microdatos en HTML inicial o mantener un DOM estable después de JavaScript; esto es distinto de la API y de la exportación XLSX/CSV. La evaluación captura ahora ambas capas y distingue ausencia comprobada de `NOT_VERIFIED`.
6. **Exportación reproducible:** conservar el indicador, dimensiones seleccionadas, unidad, fuente y metadatos en cada XLSX/CSV/JSON descargado; documentar el parámetro de formato y comprobarlo con una solicitud aislada.

## 2. Prácticas transferibles observadas en portales estadísticos

- Separar en la interfaz y API el objeto indicador de sus dimensiones; no mezclar nivel, crecimiento y per cápita en etiquetas casi idénticas.
- Hacer que la respuesta de una consulta específica llegue a una serie/observación reproducible, aunque sea una sola URL.
- Mantener una nota de fuente y fecha de actualización junto al valor, no en una pantalla desconectada.
- Probar cada cambio con preguntas naturales que incluyan near-matches: total vs actividad, anual vs trimestral, corriente vs constante y país vs área subnacional.
- World Bank ofrece un patrón claro de indicador estable + API de país/año; UNData expone series AMA con códigos de país M49; SDG exige elegir dimensiones de serie; WHO GHO separa catálogo de indicador y endpoint de observaciones. Estos patrones sirven como ejemplos de diseño, no como equivalencia de cobertura.

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

## 4. Criterio para ampliar o mantener el universo

Cada portal se incorpora sólo con manifiesto COMPLETE, sin alertas abiertas, DOM asentado y API directa verificable. Los runs de origen se combinan editorialmente sin sobreescribir la evidencia cruda ni ocultar errores de selección.

Resumen observado: who 0/90 PASS; cepalstat 90/90 PASS; worldbank 90/90 PASS; undata 84/90 PASS; sdg 15/90 PASS. Estas cifras son descriptivas de los runs y no prueban causalidad.
