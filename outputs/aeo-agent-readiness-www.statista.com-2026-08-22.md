# Auditoría AEO y AI readiness — Statista

**Fecha de corte:** 2026-08-22 (America/Santiago)  
**Portal:** [Statista](https://www.statista.com/)  
**Tipo:** portal estadístico privado / comercial  
**Alcance:** portada, una página pública de estadística, página de mapa/sitemap, documentación pública de API y superficies de acceso para agentes. No se utilizó autenticación ni se intentó eludir controles de acceso.

## Resumen ejecutivo

Statista tiene una capa editorial pública muy visible y citable: las páginas de estadísticas exponen título, valor o serie, unidad, región, período de encuesta, fecha de publicación, autor, fuente y formatos de citación. La página pública analizada fue [Number of internet users worldwide 2005–2025](https://www.statista.com/statistics/273018/number-of-internet-users-worldwide/). El buscador indexa el contenido y devuelve tablas y metadatos suficientes para descubrir la página sin sesión.

La principal limitación es el modelo de acceso: el propio material de ayuda indica que aproximadamente 7% de las estadísticas son básicas y que aproximadamente 93% son Premium; la información de fuente detallada, descargas y datos completos puede requerir una cuenta o suscripción. La API existe y está bien descrita conceptualmente, pero el acceso está orientado a clientes de Statista Connect/enterprise y requiere autorización. Durante esta auditoría, las recuperaciones directas a `www.statista.com` y `de.statista.com` devolvieron HTTP 403 desde el entorno de auditoría; por eso robots, JSON-LD y el DOM completo no se pudieron verificar de forma independiente.

## Puntaje cuantitativo

| Dimensión | Peso | Evidencia resumida | Puntos |
|---|---:|---|---:|
| Acceso y gobernanza de bots | 10 | `robots.txt` devolvió 403; no se pudo verificar allowlist de bots IA ni política de uso automatizado. Un índice externo identifica `Sitemap: https://www.statista.com/sitemap/`, pero no sustituye la verificación primaria. | 4 |
| Descubrimiento técnico | 15 | El buscador indexa portada, temas y fichas `/statistics/`; [mapa HTML de Statista](https://www.statista.com/map/) funciona como índice por industrias, países y temas. No se pudo verificar `sitemap.xml` XML ni `llms.txt` en origen. | 10 |
| Renderizado e interacción | 20 | Los resultados indexados contienen encabezado, tabla/serie, fuente y metadatos; la ficha pública ofrece vista de gráfico/tabla y descarga. El gráfico se anuncia como carga dinámica y el HTML/DOM inicial no pudo inspeccionarse por 403. | 13 |
| Datos estructurados | 15 | No se pudo verificar directamente JSON-LD, RDFa, Microdata, DCAT o Schema.org en las páginas por 403. La estructura editorial visible es semántica y consistente, pero no es evidencia de marcado formal. | 7 |
| API y acceso para agentes de código | 25 | [Statista Connect](https://www.statista.com/getting-started/more-statista-services-what-is-statista-connect) documenta Search API, Data API y Research AI API con respuestas JSON; la [documentación REST v2](https://de.statista.com/api/v2/doc/) lista endpoints de estadísticas, infografías, estudios y market insights. El acceso es autorizado/enterprise; no hubo consulta anónima reproducible. | 14 |
| Autoridad, atribución y citabilidad | 15 | La ficha expone fuente (ITU), release date, región, período, autor y múltiples formatos de citación; la ayuda describe páginas de estadística con contexto y origen. Los detalles completos y descargas pueden pedir registro o plan. | 12 |
| **Total integral** | **100** |  | **60/100** |

### Puntaje armonizado por cobertura de evidencia

La auditoría tuvo una limitación de acceso uniforme a las superficies de origen de Statista. Para evitar que un 403 del entorno se interprete como ausencia comprobada, se calcula una sensibilidad excluyendo las dimensiones más afectadas por esa limitación (D1, acceso/robots, y D4, marcado estructurado):

`(10 + 13 + 14 + 12) / (15 + 20 + 25 + 15) × 100 = 65,3/100`.

Por tanto:

- **Integral:** 60/100.
- **Armonizado (D1 y D4 no verificables directamente):** 65/100.
- **Cobertura de evidencia primaria:** 75% del peso (D2, D3, D5 y D6 con evidencia de búsqueda/documentación; D3 conserva incertidumbre de DOM).

El puntaje armonizado no afirma que robots o JSON-LD estén bien implementados; solo evita penalizar dos veces una comprobación que no fue posible completar desde este entorno.

## Evidencia por superficie

### Portada

[Statista — The Statistics Portal](https://www.statista.com/) declara cobertura de más de 170 industrias, más de 150 países y más de un millón de hechos/estadísticas. La portada tiene buscador, temas populares y enlaces a Statistics, Consumer Insights, Market Insights, Research AI y Statista Connect. Es una entrada clara para descubrimiento humano y para sistemas de búsqueda.

### Ficha pública de estadística

La página [Number of internet users worldwide 2005–2025](https://www.statista.com/statistics/273018/number-of-internet-users-worldwide/) fue elegida porque aparece sin autenticación en los resultados indexados y expone una serie mundial con valores, fuente ITU, región, período 2005–2025, fecha de publicación y formatos de citación. El resultado de búsqueda también muestra el botón “Download for free”, seguido de una solicitud de registro para mostrar información detallada de fuentes. Esto crea una ruta de descubrimiento abierta, pero una ruta de reutilización parcialmente cerrada.

### Índice / sitemap humano

[Statista Map](https://www.statista.com/map/) funciona como sitemap HTML: organiza industrias, países, regiones y estadísticas recientes/más vistas, y enlaza a páginas de topics y statistics. Un índice externo de robots identifica `https://www.statista.com/sitemap/` como la ubicación del sitemap, pero esta referencia no se trató como evidencia primaria.

### Robots, sitemap XML y llms.txt

| Recurso | Resultado | Interpretación |
|---|---|---|
| `https://www.statista.com/robots.txt` | HTTP 403 desde el entorno | No verificable directamente; el bloqueo puede ser una política anti-bot del portal o una limitación del recuperador. |
| `https://www.statista.com/sitemap.xml` | No recuperable por el entorno | No se afirma que no exista; el mapa HTML sí está indexado. |
| `https://www.statista.com/sitemap/` | Referenciado por índice externo; el mapa HTML abre vía búsqueda | Buen sustituto de descubrimiento humano, no equivalente a XML para agentes. |
| `https://www.statista.com/llms.txt` | No verificable | No se encontró evidencia primaria de un archivo `llms.txt`. |
| `https://www.statista.com/llms-full.txt` | No verificable | No se encontró evidencia primaria. |

### API y acceso programático

[Statista Connect](https://www.statista.com/getting-started/more-statista-services-what-is-statista-connect) describe:

- Search API (`search/statistics`) para buscar por palabra clave o lenguaje natural y devolver título, descripción, fecha, industria, geografía, tipo de contenido y enlace.
- Data API (`data/statistic`) para obtener puntos de gráfico y metadatos estructurados.
- Research AI API (`research-ai/ask`) para consultas de investigación.

La [documentación REST v2](https://de.statista.com/api/v2/doc/) lista operaciones `GET /api/v2/statistics`, `GET /api/v2/statistics/{id}`, además de infographics, studies y marketinsights, y modelos de respuesta. No fue posible ejecutar una llamada anónima ni verificar el esquema de autorización desde este entorno; la evidencia disponible presenta la API como un servicio de Statista Connect para clientes/integraciones.

## Barreras y fortalezas comparables

### Aspectos destacables

1. **Citación editorial fuerte:** una ficha puede incluir fuente, fecha, región, período, autor y varias formas de cita.
2. **Descubrimiento amplio:** portadas, topics, estadísticas y mapa HTML se indexan con títulos y resúmenes ricos.
3. **Modelo de datos explícito:** la API documentada separa búsqueda de recuperación de datos y promete JSON con puntos y metadatos.
4. **Capacidad específica para IA:** Statista Connect menciona API de Research AI, integraciones y MCP; esto es una ventaja potencial para agentes autorizados.

### Puntos de dolor y mejoras prioritarias

1. **Acceso de agentes (P0):** publicar una ruta pública, con límites y términos claros, para metadatos y una muestra de datos; documentar autenticación, rate limits y errores en OpenAPI accesible sin sesión.
2. **Transparencia de bots (P0):** hacer `robots.txt` accesible a recuperadores legítimos y documentar explícitamente GPTBot/OAI-SearchBot, ClaudeBot, PerplexityBot y otros agentes, junto con la política de uso.
3. **Estructura de datos (P1):** añadir JSON-LD verificable por ficha con `Dataset`, `DataCatalog`, `Observation`/`StatisticalVariable`, `variableMeasured`, `spatialCoverage`, `temporalCoverage`, `unitText`, `creator`, `citation` y `isBasedOn`.
4. **Acceso sin registro a evidencia mínima (P1):** mantener visible la cifra principal, unidad, período, fuente, metodología y un enlace permanente aunque la descarga masiva siga siendo premium.
5. **Renderizado robusto (P1):** entregar en HTML inicial una tabla o bloque de datos mínimo y usar JavaScript solo para enriquecer gráfico, filtros y descarga.
6. **Mapa machine-readable (P2):** exponer sitemap XML indexable y un catálogo DCAT/JSON con URLs canónicas de ficha, tema, cobertura y fecha de actualización; añadir `llms.txt` si la organización decide adoptarlo.

## Limitaciones y confianza

- No se inició sesión, no se usaron credenciales, no se intentó evadir paywalls, CAPTCHA ni controles anti-bot.
- Las recuperaciones directas a Statista devolvieron 403; por ello robots, DOM completo, headers, canonicales y JSON-LD quedan como **no verificados**, no como ausentes.
- La evidencia de contenido procede de resultados de búsqueda y páginas públicas de ayuda/documentación. Los snippets pueden reflejar una fecha de rastreo distinta de la fecha de corte.
- La afirmación de que la mayoría del contenido es premium se basa en la propia guía de Statista, que describe aproximadamente 7% Basic y 93% Premium; no se extrapola a cada ficha individual.
- **Confianza global:** media para descubrimiento, citabilidad y API documentada; baja-media para bots, renderizado profundo y structured data.

## Fuentes consultadas

- [Statista homepage](https://www.statista.com/)
- [Public statistic: number of internet users worldwide 2005–2025](https://www.statista.com/statistics/273018/number-of-internet-users-worldwide/)
- [Statista Map](https://www.statista.com/map/)
- [Getting Started — Statistics](https://www.statista.com/getting-started/content-types-overview-statistics)
- [Getting Started — Statista Connect/API](https://www.statista.com/getting-started/more-statista-services-what-is-statista-connect)
- [Statista Connect API](https://www.statista.com/business/connect-api/)
- [Statista REST API v2 documentation](https://de.statista.com/api/v2/doc/)
- [Statista business/data description](https://www.statista.com/business/our-data)

