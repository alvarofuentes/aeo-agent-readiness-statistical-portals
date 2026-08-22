# Auditoría AEO y preparación para agentes de IA de CEPALSTAT

**Portal auditado:** [CEPALSTAT — Portal de Datos y Publicaciones Estadísticas](https://statistics.cepal.org/portal/cepalstat/)  
**Fecha de corte:** 20 de agosto de 2026  
**Audiencia:** responsables técnicos, SEO/AEO, datos abiertos y arquitectura digital de la CEPAL  
**Calificación global:** **45/100 — Parcialmente preparado, todavía “No Listo para Agentes”**

## 1. Resumen ejecutivo

CEPALSTAT posee una base sólida para la automatización: publica una API REST y una especificación OpenAPI legible por máquina. Un agente de código puede obtener el árbol temático, identificar un indicador y descargar sus datos, dimensiones, metadatos, fuentes y notas sin recurrir al web scraping.

La preparación del portal para Answer Engine Optimization (AEO) es, sin embargo, sustancialmente menor que la preparación de su API. Las comprobaciones HTTP directas confirmaron que el host no publica `robots.txt`, un sitemap en las ubicaciones convencionales examinadas ni `llms.txt`. El rastreo queda implícitamente permitido en la capa robots, pero no existe gobernanza diferenciada ni un inventario que oriente a buscadores y agentes hacia los indicadores canónicos.

En la interfaz web, los temas, definiciones, dimensiones y fuentes presentan un grado útil de indexabilidad. La recuperación de observaciones numéricas históricas continúa dependiendo de selectores, estado dinámico, el botón **Aplicar**, gráficos y controles de descarga. Esto aumenta el costo para un agente y favorece que un LLM cite una portada, ficha metodológica o fuente secundaria en lugar del registro estadístico exacto.

Tampoco se detectaron señales públicas de JSON-LD con `Dataset`, `DataCatalog` o `DataDownload`. Debido a una limitación del entorno de navegación, esta conclusión se expresa correctamente como **“no detectado”**, no como ausencia categórica en todo el código fuente.

### Veredicto

CEPALSTAT está **bien encaminado para integraciones programáticas**, pero todavía no está preparado para que un agente genérico descubra, interprete y cite sus series de forma directa y reproducible. La oportunidad principal no es crear otra API: es hacer que la API existente, sus descargas y sus entidades estadísticas sean descubribles desde HTML, sitemaps, JSON-LD y URLs canónicas.

## 2. Calificación consolidada

| Dimensión | Peso | Puntaje | Diagnóstico |
|---|---:|---:|---|
| Acceso y gobernanza de bots | 10 | 3 | Rastreo implícitamente permitido, sin política explícita |
| Descubrimiento técnico | 15 | 2 | Sin sitemap discoverable en las rutas comprobadas ni `llms.txt` |
| Renderizado y acceso sin interacción | 20 | 8 | Metadatos indexables; series numéricas dependientes de controles |
| Datos estructurados Schema.org | 15 | 2 | JSON-LD crítico no detectado |
| API y documentación para agentes de código | 25 | 21 | API pública potente; OpenAPI presenta inconsistencias |
| Autoridad, atribución y citabilidad | 15 | 9 | Autoridad institucional fuerte; entidad estadística fragmentada |
| **Total** | **100** | **45** | **Parcialmente preparado; todavía No Listo para Agentes** |

Escala utilizada:

- 0–24: No Listo.
- 25–49: Preparación baja o parcial; todavía No Listo.
- 50–74: Preparación intermedia.
- 75–89: Listo con brechas.
- 90–100: Preparado para Agentes.

## 3. Metodología, alcance y limitaciones

La revisión combinó:

1. Comprobaciones HTTP directas de archivos de control y descubrimiento, ejecutadas desde PowerShell y aportadas por el usuario.
2. Recuperación e indexación web de la portada, páginas temáticas, dashboards y fichas técnicas.
3. Inspección de la [documentación Open Data/API](https://statistics.cepal.org/portal/cepalstat/open-data.html?lang=en) y de la [especificación OpenAPI oficial](https://api-cepalstat.cepal.org/apispec_1.json).
4. Comparación entre el contenido textual recuperable de la interfaz y las entidades que expone la API.

El plugin de navegador no pudo iniciar Playwright debido a un fallo local de cifrado de Windows (`CryptUnprotectData`). Por esta razón, no fue posible guardar el HTML inicial, desactivar JavaScript ni observar la secuencia de red de los controles. Las conclusiones que dependen de esas pruebas se identifican como parciales o inferidas.

La auditoría no afirma que sea imposible que exista un sitemap en una ruta no examinada. El hallazgo verificable es que **no se encontró un sitemap discoverable en las ubicaciones estándar y específicas comprobadas**, y que tampoco puede estar declarado desde `robots.txt` porque ese archivo devuelve 404.

## 4. Capa 1 — Acceso y descubrimiento para bots

### 4.1 Evidencia HTTP directa

Las siguientes respuestas fueron obtenidas el 20 de agosto de 2026:

| Recurso comprobado | Estado | Servidor / tipo | Resultado |
|---|---:|---|---|
| `https://statistics.cepal.org/robots.txt` | 404 | nginx; `text/html` | No existe en la ruta normativa del host |
| `https://statistics.cepal.org/sitemap.xml` | 404 | nginx; `text/html` | No existe en la ubicación canónica examinada |
| `https://statistics.cepal.org/sitemap_index.xml` | 404 | nginx; `text/html` | No existe índice en la ubicación común examinada |
| `https://statistics.cepal.org/portal/cepalstat/sitemap.xml` | 404 | nginx 1.31.3; `text/html` | No existe sitemap en la ruta específica examinada |
| `https://statistics.cepal.org/llms.txt` | 404 | nginx; `text/html` | No existe en la raíz del host |

**Nivel de confianza:** alto. Los códigos HTTP fueron observados directamente; no son inferencias derivadas de un índice de búsqueda.

### 4.2 Interpretación de `robots.txt`

La ausencia de `robots.txt` no constituye un bloqueo. Bajo el [Robots Exclusion Protocol, RFC 9309](https://www.rfc-editor.org/rfc/rfc9309), una respuesta 4xx representa un archivo no disponible y los crawlers compatibles pueden acceder a los recursos. En consecuencia:

- No hay una prohibición publicada para `OAI-SearchBot`, `GPTBot`, `PerplexityBot`, `Google-Extended`, `ClaudeBot` o `Claude-Web`.
- Tampoco hay reglas generales bajo `User-agent: *`.
- No se distingue entre búsqueda, recuperación para respuestas, entrenamiento u otros usos automatizados.
- Este resultado no descarta controles independientes en nginx, un WAF, limitación de frecuencia o bloqueos por IP.

El problema principal es de **gobernanza**, no de denegación de acceso: CEPALSTAT queda abierto por omisión, en lugar de declarar una política institucional deliberada.

### 4.3 Sitemap

No se encontró un sitemap en las cuatro ubicaciones convencionales o específicas examinadas. Además, al no existir `robots.txt`, no hay una declaración `Sitemap:` que permita descubrir otra ubicación.

La navegación temática sí expone categorías como [Demográficos y sociales](https://statistics.cepal.org/portal/cepalstat/dashboard.html?lang=es&theme=1), [Económicos](https://statistics.cepal.org/portal/cepalstat/dashboard.html?lang=es&theme=2), [Ambientales](https://statistics.cepal.org/portal/cepalstat/dashboard.html?lang=es&theme=3) y [Temas transversales](https://statistics.cepal.org/portal/cepalstat/dashboard.html?lang=es&theme=4). Sin un sitemap, un agente debe descubrir esa jerarquía mediante enlaces, parámetros o la API.

Un sitemap útil debería separar, o etiquetar mediante índices, al menos:

- Portada y páginas temáticas.
- Indicadores y fichas técnicas.
- Perfiles regionales y nacionales.
- Publicaciones estadísticas.
- Catálogo Open Data/API.
- Fechas de modificación y versiones lingüísticas.

### 4.4 `llms.txt`

`https://statistics.cepal.org/llms.txt` devolvió 404. Aunque `llms.txt` es una convención emergente y no reemplaza a `robots.txt` ni a un sitemap XML, resultaría especialmente útil para proporcionar:

- Descripción institucional y alcance geográfico.
- Catálogo temático resumido.
- Enlace a OpenAPI y URL base de la API.
- Procedimiento para descubrir `indicator_id`.
- Reglas de atribución y citación.
- Significado de dimensiones, fuentes, notas y actualizaciones.
- Ejemplos de consultas reproducibles.

## 5. Capa 2 — Barreras de renderizado e interacción

### 5.1 Página principal

La [portada de CEPALSTAT](https://statistics.cepal.org/portal/cepalstat/index.html?lang=es) es parcialmente visible para índices capaces de procesar la aplicación. Se recuperaron temas, principales cifras regionales, indicadores más consultados, actualizaciones y señales institucionales de CEPAL y Naciones Unidas.

Por tanto, no hay evidencia suficiente para calificar la portada como una SPA totalmente vacía. No obstante, el crawler HTTP de bajo nivel no produjo contenido textual analizable en la apertura directa, mientras el índice de búsqueda sí mostró contenido. Esto es compatible con una dependencia de JavaScript, renderizado diferido o diferencias de procesamiento entre crawlers, pero no demuestra por sí solo CSR puro.

**Conclusión:** contenido editorial y cifras destacadas razonablemente indexables para buscadores avanzados; experiencia potencialmente frágil para agentes sin JavaScript.

### 5.2 Página interna de indicador

Se utilizó como muestra el indicador **“Población total, según sexo”**. La [ficha técnica del indicador 4788](https://statistics.cepal.org/portal/cepalstat/technical-sheet.html?indicator_id=4788&lang=es) expone de forma indexable:

- Nombre y ruta temática.
- Definición.
- Unidad de medida.
- Metodología.
- Cobertura temporal.
- Países, territorios y desagregación por sexo.
- Fuente institucional.

Este es un hallazgo positivo: un LLM puede comprender qué mide la serie. Sin embargo, el dashboard usa una ruta genérica (`dashboard.html`) cuyo estado depende de parámetros y selección de dimensiones. En la evidencia recuperada aparecen controles para país, año y otras dimensiones, el botón **Aplicar**, gráficos y botones de descarga, pero no una tabla plana y citable con todas las observaciones históricas.

### 5.3 Muros de interacción

1. **Selectores multidimensionales:** el usuario debe establecer país, período, sexo u otras desagregaciones.
2. **Aplicación explícita del filtro:** el botón **Aplicar** introduce una acción posterior a la carga.
3. **Gráfico como representación central:** la representación visual puede ocultar los valores subyacentes a un agente textual.
4. **Descargas mediante botones:** XML, JSON y XLSX deben ser enlaces HTML con `href` real para resultar descubribles sin eventos JavaScript.
5. **Elementos “Ver más”:** parte de los indicadores y actualizaciones queda tras una expansión interactiva.
6. **Ruta y título genéricos:** numerosos indicadores comparten `dashboard.html` y títulos poco específicos.
7. **Entidad fragmentada:** dashboard, ficha técnica, publicaciones y banco de datos representan partes de una misma serie en URLs diferentes.

El resultado es una asimetría: **las definiciones son más fáciles de recuperar que las observaciones numéricas reproducibles**.

## 6. Capa 3 — Datos estructurados Schema.org

No se detectaron bloques JSON-LD públicos asociados con los tipos críticos:

- `Dataset`.
- `DataCatalog`.
- `DataDownload`.
- `Organization` o `GovernmentOrganization`.

Tampoco se detectaron señales indexadas de `application/ld+json` en las páginas examinadas. Debido a que no se pudo inspeccionar el código fuente inicial ni el DOM renderizado mediante Playwright, este resultado debe registrarse como:

> **JSON-LD crítico no detectado con la evidencia disponible; ausencia y sintaxis pendientes de validación directa del código fuente.**

No corresponde informar errores de sintaxis Schema.org concretos sin recuperar los bloques. La carencia verificable es la falta de señales estructuradas detectables que permitan asociar inequívocamente una serie, sus distribuciones, cobertura, productor y fecha de actualización.

### Marcado recomendado

En la portada:

- `DataCatalog` para CEPALSTAT.
- `Organization` o `GovernmentOrganization` para CEPAL y su relación con Naciones Unidas.
- `WebSite` y `SearchAction` para la búsqueda de indicadores.

En cada indicador:

- `Dataset` con nombre, descripción, identificador persistente y URL canónica.
- `variableMeasured`, `spatialCoverage` y `temporalCoverage`.
- `creator`, `publisher`, `isBasedOn` y `citation`.
- `dateModified`, licencia y versión lingüística.
- `distribution` con un `DataDownload` por formato y `contentUrl` directo.

El JSON-LD debe generarse desde los mismos metadatos que alimentan la API para evitar divergencias.

## 7. Capa 4 — API para agentes de código

### 7.1 Capacidades verificadas

CEPALSTAT publica una [interfaz Open Data/API](https://statistics.cepal.org/portal/cepalstat/open-data.html?lang=en) y una [especificación OpenAPI](https://api-cepalstat.cepal.org/apispec_1.json) que declara OpenAPI 3.0.3 y la versión 1.9.13 de la API pública.

Endpoints principales:

```text
GET /cepalstat/api/v1/thematic-tree

GET /cepalstat/api/v1/indicator/{indicator_id}/areas
GET /cepalstat/api/v1/indicator/{indicator_id}/metadata
GET /cepalstat/api/v1/indicator/{indicator_id}/dimensions
GET /cepalstat/api/v1/indicator/{indicator_id}/records
GET /cepalstat/api/v1/indicator/{indicator_id}/data
GET /cepalstat/api/v1/indicator/{indicator_id}/sources
GET /cepalstat/api/v1/indicator/{indicator_id}/footnotes
GET /cepalstat/api/v1/indicator/{indicator_id}/publications
```

La API permite que un agente evite el scraping: puede obtener el árbol temático, identificar el `indicator_id`, conocer las dimensiones y recuperar datos, metadatos, fuentes y notas. La documentación declara opciones JSON, XML, YAML, CSV y Excel mediante el parámetro `format`.

No se detectó una interfaz SQL pública. La integración documentada es REST.

### 7.2 Defectos de la especificación OpenAPI

La inspección de la especificación oficial reveló una mezcla de estructuras OpenAPI 3 y Swagger 2:

- Se declara `openapi: 3.0.3`, pero se usa `host` en vez de `servers`.
- Aparece `produces` dentro de operaciones, estructura heredada de Swagger 2.
- Se conserva un campo superior `definitions`, aunque los modelos principales están bajo `components.schemas`.
- No se observan `operationId` estables para generación de SDKs y herramientas.

También hay inconsistencias entre ejemplos y esquemas:

- El ejemplo de áreas usa `theme_id` y `theme_name`, mientras el esquema declara `themes_id` y `themes_name`.
- El ejemplo de publicaciones devuelve `body.publications`, pero el esquema de respuesta define la colección bajo una propiedad `metadata`.
- `source_id` se declara como string, aunque los ejemplos lo representan como entero.
- Los formatos admitidos por el parámetro `format` no se corresponden plenamente con los tipos de contenido declarados mediante `produces`.

Estas diferencias pueden causar una URL base incompleta, modelos generados incorrectamente, errores de validación y herramientas que requieran correcciones manuales.

### 7.3 Fricción semántica de la API

El filtro `members` recibe IDs numéricos separados por comas. Un agente debe:

1. Encontrar el indicador.
2. Consultar sus dimensiones.
3. Traducir países, períodos y categorías a IDs internos.
4. Construir `members`.
5. Resolver nuevamente los IDs de la respuesta para producir una tabla legible.

La API es potente, pero no resulta “plug-and-play”. Un endpoint complementario con parámetros legibles reduciría drásticamente esta fricción, por ejemplo:

```text
GET /indicator/4788/observations?country=CHL&year=2025&sex=total
```

## 8. Riesgos para citación y visibilidad en respuestas de IA

Un LLM puede reconocer la autoridad de CEPAL y recuperar definiciones, pero tiene dificultades para enlazar una afirmación numérica con una observación reproducible. Los riesgos principales son:

- Citar la portada en vez del indicador exacto.
- Citar la ficha técnica sin país, período o valor.
- Omitir unidad, desagregación o condición de proyección.
- Usar una publicación secundaria porque presenta una tabla HTML más sencilla.
- Interpretar el gráfico sin acceso seguro a sus valores.
- Confundir indicadores con nombres similares o IDs históricos distintos.
- Separar el dato de sus fuentes y notas metodológicas.

Una fuente menos autoritativa, pero con URLs estables y tablas HTML planas, puede terminar siendo más fácil de citar que CEPALSTAT. Este es el principal déficit AEO del portal.

## 9. Plan de remediación priorizado

### P0 — Quick wins, 0 a 2 semanas

1. Publicar `robots.txt` con política institucional explícita para crawlers generales, búsqueda asistida por IA y entrenamiento, y declarar la ubicación del sitemap.
2. Publicar `sitemap.xml` o un índice de sitemaps con temas, indicadores, fichas técnicas, perfiles y publicaciones.
3. Publicar `llms.txt` con catálogo, OpenAPI, atribución y ejemplos de consulta.
4. Convertir descargas JSON, CSV/XLSX y XML en enlaces HTML directos con `href`, no solo botones con eventos.
5. Mostrar una tabla inicial accesible de observaciones, aunque sea una vista limitada, sin exigir un clic en **Aplicar**.
6. Asignar título, descripción, `canonical` y encabezado únicos a cada indicador.

### P1 — AEO, semántica y API, 2 a 6 semanas

1. Implementar `DataCatalog` en la portada y `Dataset`/`DataDownload` por indicador.
2. Serializar CEPAL, Naciones Unidas, fuentes y responsables con `Organization` y relaciones explícitas.
3. Enlazar recíprocamente dashboard, ficha técnica, publicaciones, banco de datos y endpoint API.
4. Reparar OpenAPI: añadir `servers`, eliminar campos heredados, corregir tipos y nombres, e incorporar `operationId`.
5. Validar la especificación en integración continua y bloquear despliegues que introduzcan errores.
6. Publicar ejemplos ejecutables en `curl`, Python, R y JavaScript.
7. Incorporar un endpoint de observaciones con filtros legibles y una respuesta tabular normalizada.

### P2 — Preparación avanzada, 6 a 12 semanas

1. Publicar metadatos DCAT/StatDCAT-AP y evaluar SDMX para intercambio estadístico.
2. Crear landing pages estáticas por dataset con previsualización HTML y CSV directo.
3. Establecer identificadores persistentes, política de versiones y fechas ISO 8601.
4. Publicar reglas de citación legibles por máquina y ejemplos de citas completas.
5. Medir acceso de bots, errores API, uso de sitemaps y cobertura de resultados enriquecidos.

## 10. Criterios de aceptación para “Preparado para Agentes”

CEPALSTAT debería considerarse preparado cuando:

- `robots.txt`, sitemap y `llms.txt` respondan 200 y sean coherentes entre sí.
- Cada indicador tenga URL canónica, título único, descripción y tabla accesible sin JavaScript.
- Cada página de indicador incluya JSON-LD `Dataset` válido y descargas `DataDownload` directas.
- Un agente pueda pasar de una consulta temática a datos citables sin interacción física con el DOM.
- OpenAPI valide sin errores y genere un cliente funcional sin modificaciones manuales.
- Los valores recuperados incluyan indicador, país, período, unidad, dimensiones, fuente, notas y fecha de actualización.
- Existan pruebas automáticas de paridad entre HTML, JSON-LD, API y archivos descargables.

## 11. Anexo de evidencia y confianza

| Hallazgo | Evidencia | Confianza |
|---|---|---|
| `robots.txt` no disponible | HTTP 404 observado directamente | Alta |
| Sin reglas explícitas para bots de IA | Consecuencia directa de la ausencia del archivo | Alta |
| `sitemap.xml` no disponible | HTTP 404 observado directamente | Alta |
| `sitemap_index.xml` no disponible | HTTP 404 observado directamente | Alta |
| Sitemap específico del portal no disponible | HTTP 404 observado directamente | Alta |
| No hay sitemap discoverable convencional | Cuatro rutas comprobadas y ausencia de declaración en robots | Alta para rutas convencionales; no exhaustiva para rutas desconocidas |
| `llms.txt` no disponible | HTTP 404 observado directamente | Alta |
| Fichas técnicas indexables | Contenido recuperado de la ficha del indicador 4788 | Alta |
| Series numéricas detrás de controles | Selectores, **Aplicar** y descargas detectados en páginas indexadas | Media-alta |
| Dependencia exacta de CSR | No se pudo comparar HTML inicial con DOM renderizado | No determinada |
| JSON-LD crítico no detectado | Búsqueda e inspección indirecta sin bloques visibles | Media; requiere validación del fuente |
| API REST y OpenAPI disponibles | Documentación y especificación oficiales accesibles | Alta |
| Inconsistencias OpenAPI | Inspección directa de `apispec_1.json` | Alta |

## 12. Fuentes primarias consultadas

- [CEPALSTAT — Portal principal](https://statistics.cepal.org/portal/cepalstat/)
- [Página principal en español](https://statistics.cepal.org/portal/cepalstat/index.html?lang=es)
- [Indicadores demográficos y sociales](https://statistics.cepal.org/portal/cepalstat/dashboard.html?lang=es&theme=1)
- [Indicadores económicos](https://statistics.cepal.org/portal/cepalstat/dashboard.html?lang=es&theme=2)
- [Indicadores ambientales](https://statistics.cepal.org/portal/cepalstat/dashboard.html?lang=es&theme=3)
- [Temas transversales](https://statistics.cepal.org/portal/cepalstat/dashboard.html?lang=es&theme=4)
- [Ficha técnica: Población total, según sexo](https://statistics.cepal.org/portal/cepalstat/technical-sheet.html?indicator_id=4788&lang=es)
- [Open Data/API](https://statistics.cepal.org/portal/cepalstat/open-data.html?lang=en)
- [Especificación OpenAPI oficial](https://api-cepalstat.cepal.org/apispec_1.json)
- [Robots Exclusion Protocol — RFC 9309](https://www.rfc-editor.org/rfc/rfc9309)

---

**Resultado final:** **45/100 — Parcialmente preparado, todavía “No Listo para Agentes”.** La API constituye una ventaja competitiva importante, pero debe conectarse con mecanismos de descubrimiento, HTML accesible, datos estructurados y URLs citables para que CEPALSTAT se convierta en una fuente de primera elección para agentes y motores de respuesta.
