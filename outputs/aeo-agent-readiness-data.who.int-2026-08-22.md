# Auditoría AEO y AI readiness — WHO Data (`data.who.int`)

**Fecha de auditoría:** 22 de agosto de 2026 (America/Santiago)  
**Alcance:** portada, índice de indicadores, una ficha de indicador representativa, políticas de crawling, datos estructurados/metadatos y documentación/API oficial.  
**Indicador representativo:** [Under-five mortality rate (per 1000 live births)](https://data.who.int/indicators/i/E3CAF2B/2322814), descubierto desde la portada como “Featured indicator”. Como control de citabilidad también se revisó [Life expectancy at birth (years)](https://data.who.int/indicators/i/A21CFC2/90E2E48).

## Veredicto ejecutivo

WHO Data presenta una preparación alta para agentes que necesitan **descubrir, interpretar y citar** indicadores oficiales. Sus principales activos son: un índice de indicadores legible y enlazable; fichas individuales con identificadores, definición, periodicidad, cobertura, metodología, licencia y plantilla de cita; descargas CSV; y una documentación OData actual que explica JSON/CSV, `$metadata`, filtros, paginación y endpoints públicos/privados.

La principal cautela es operativa: parte de la documentación histórica del GHO/Athena se encuentra retirada o en transición, y la ficha `data.who.int` no expone de forma verificable en esta auditoría un endpoint OData específico para cada indicador. Además, la presencia efectiva de JSON-LD/Schema.org, canonicales y el comportamiento del DOM tras JavaScript no pudo verificarse con inspección de código fuente del navegador en este entorno; se registra como **no verificado**, no como ausente.

**Puntaje integral estimado: 77/100 (confianza media-alta).**  
**Puntaje armonizado:** 77/100 en esta auditoría; no fue necesario excluir una dimensión completa, pero la dimensión de datos estructurados debe interpretarse con menor confianza por la falta de inspección directa del HTML fuente.

## Matriz cuantitativa

| Dimensión | Peso | Evidencia observada | Estado | Puntos |
|---|---:|---|---|---:|
| Acceso y gobernanza de bots | 10 | `https://data.who.int/robots.txt` responde y declara numerosos agentes; el grupo `User-agent: *` bloquea `/immunizationdata` y su subruta; publica un sitemap hacia `http://www.who.int/sitemaps/sitemapindex.xml`. No hay reglas explícitas para GPTBot, OAI-SearchBot, ClaudeBot u otros agentes de IA. | Verificado parcialmente | 7 |
| Descubrimiento técnico | 15 | La portada enlaza a Indicators, Countries y Dashboards; el índice `/indicators` expone 88 indicadores y las fichas tienen URLs persistentes. El sitemap indicado está en `who.int`, no en `data.who.int`, y la apertura directa de `/sitemap.xml` devolvió error interno. Canonical/hreflang no se pudieron inspeccionar en fuente. | Verificado parcialmente | 12 |
| Renderizado e interacción | 20 | El contenido esencial de portada, índice y ficha fue recuperable como HTML/texto: títulos, definiciones, enlaces de descarga y metadatos aparecen sin depender de una sesión autenticada. Las fichas incluyen controles Overview/Metadata y descargas. No se pudo comparar de forma instrumental HTML inicial vs DOM post-JavaScript ni probar todos los filtros en navegador. | Verificado con limitación | 16 |
| Datos estructurados | 15 | Las fichas exponen metadatos semánticos ricos (nombre, identificador, código, unidad, cobertura, periodicidad, fuente, método y licencia). WHO documenta un Data Description Schema orientado a formatos legibles por máquina y a APIs. No se verificó directamente JSON-LD/Schema.org en el código fuente. | Verificado parcialmente; JSON-LD no verificado | 8 |
| API y acceso para agentes de código | 25 | La documentación xMart/OData describe endpoints públicos y privados, JSON y CSV, `$metadata`, `$count`, `$top`, `$skip`, `$select`, `$filter`, streaming, `@odata.nextLink`, límites y ejemplos; la plataforma declara que cada tabla/vista visible puede tener endpoint OData. Las fichas ofrecen CSV directo. Athena/GHO antiguo está retirado y el OData legado aparece en transición/deprecación. No se identificó desde la ficha un endpoint específico de indicador con esquema público estable. | Fuerte, con transición de plataforma | 21 |
| Autoridad, atribución y citabilidad | 15 | Fichas con título preciso, definición, identificador único, código, estado, fecha de actualización, institución publicadora (WHO), licencia CC BY 4.0, metodología, cobertura y texto de Citation. | Verificado | 13 |
| **Total** | **100** |  |  | **77** |

### Criterio de puntuación

Los puntos no equivalen a una medición de tráfico o de ranking. Se asignan por cobertura de señales auditables para un agente: acceso, descubrimiento, extracción, semántica, recuperación programática y citación. “No verificado” no se penaliza como “ausente”, pero reduce el máximo prudente cuando una afirmación no puede ser confirmada.

## Evidencia primaria por superficie

### Portada

La portada [WHO Data](https://data.who.int/) identifica explícitamente la organización, ofrece navegación a Indicators/Countries/Dashboards, publica el informe World Health Statistics 2025 y presenta el indicador destacado de mortalidad de menores de cinco años con definición, enlace “Visit indicator” y descarga de datos. La página es, por tanto, una buena puerta de entrada semántica para agentes de búsqueda.

### Índice de indicadores

El [índice de indicadores](https://data.who.int/indicators) es rastreable y muestra 88 elementos. Cada elemento incluye título, fecha de actualización, definición breve, tipo de valor y dimensiones cuando aplican. Entre los elementos se encuentran “Life expectancy at birth (years)” y “Under-five mortality rate (per 1000 live births)”, lo que permite descubrir la ficha representativa por enlaces internos y no solo por un buscador externo.

### Ficha representativa: mortalidad de menores de cinco años

La ficha [Under-five mortality rate](https://data.who.int/indicators/i/E3CAF2B/2322814) contiene:

- título y unidad (“per 1000 live births”);
- definición y relación con SDG 3.2.1;
- identificador único `2322814` y código `MDG_0000000007`;
- fecha de actualización (15 May 2024), periodicidad anual y próxima actualización esperada;
- proveedor/publicador y licencia CC BY 4.0;
- tipo de dato, cobertura temporal 1931–2020, cobertura espacial mundial, granularidad nacional y 199 países/territorios;
- intervalos de confianza, procedencia “Official Estimate” y método “Adjusted Predicted”;
- metodología de medición, agregación, validación UN IGME, fuentes y limitaciones;
- descarga CSV directa: `https://srhdpeuwpubsa.blob.core.windows.net/whdh/DATADOT/INDICATOR/2322814_ALL_LATEST.csv`;
- texto de citación WHO para reutilización.

El control [Life expectancy at birth](https://data.who.int/indicators/i/A21CFC2/90E2E48) mantiene el mismo patrón: identificador `90E2E48`, código `WHOSIS_000001`, definición, publicación WHO, CC BY 4.0, cobertura y descarga CSV (`90E2E48_ALL_LATEST.csv`). La consistencia de plantilla entre dos fichas reduce ambigüedad para agentes.

### Robots, sitemap y gobernanza

El [robots.txt](https://data.who.int/robots.txt) existe y contiene un inventario amplio de agentes bloqueados. En el bloque global, solo se observó `Disallow: /immunizationdata` y `Disallow: /immunizationdata/*`; no se encontró una directiva específica para agentes de IA modernos. El archivo publica `Sitemap: http://www.who.int/sitemaps/sitemapindex.xml`. La URL local `https://data.who.int/sitemap.xml` devolvió un error interno al intentar abrirla; esto no demuestra que el sitemap de `who.int` sea inválido, pero sí que la ruta canónica de `data.who.int` no quedó verificada.

### Datos estructurados y esquema de descripción

La auditoría textual confirma metadatos semánticos completos en las fichas, pero no permite afirmar que exista JSON-LD embebido. La documentación oficial [Data Description Schema](https://data.who.int/products/data-description-schema) explica un esquema común para nombres de columnas, metadatos, consultas API y archivos, y declara que busca facilitar formatos legibles por máquinas y consultas consistentes. Esto es una fortaleza de modelado de datos, pero no sustituye la comprobación de `script type="application/ld+json"` o vocabularios Schema.org en el HTML.

### APIs y documentación oficial

La documentación vigente [OData API de xMart](https://extranet.who.int/xmart4/docs/xmart_api/use_API.html) establece que las tablas/vistas visibles pueden ofrecer URL consumibles por software remoto; la API devuelve JSON por defecto y también CSV, es de solo lectura y distingue endpoints públicos y privados. Documenta `$metadata`, `$count`, `$top`, `$skip`, `$select`, `$filter`, streaming, límites y `@odata.nextLink`, además de ejemplos de filtros por país. La página [xMart de WHO Data](https://data.who.int/about/data/whdh/xmart) explica que los modelos son accesibles como endpoints OData y que el sistema está optimizado para análisis y difusión mediante `data.who.int`.

El [legacy GHO/Athena](https://www.who.int/data/gho/legacy) advierte que la interfaz Minerva/Athena está retirada y que el OData GHO antiguo está en transición/deprecación. Esta señal es crítica para AI readiness: hay capacidad programática documentada, pero los agentes y clientes deben preferir la plataforma actual y no depender de ejemplos Athena antiguos.

## Hallazgos destacables

1. **Excelente citabilidad de fichas.** El identificador, código, definición, unidad, fecha de actualización, cobertura, metodología, licencia y texto de cita están cerca del contenido principal.
2. **Descargas directas y reutilizables.** Las fichas enlazan CSV en formato estable por indicador, con nombres derivados del identificador.
3. **Metadatos de calidad estadística.** La ficha no se limita al valor: declara procedencia, método de estimación, incertidumbre, fuentes, periodicidad y advertencias de interpretación.
4. **API documentada para tareas de código.** xMart/OData ofrece patrones estándar de consulta, selección, filtrado, paginación y formatos, adecuados para agentes programáticos.
5. **Navegación multilingüe y arquitectura por indicadores.** La portada y el índice son claros; el patrón de URL `/indicators/i/<grupo>/<id>` es relativamente persistente.

## Puntos de dolor y mejoras prioritarias

### P0 — estabilizar descubrimiento y APIs

- Publicar un sitemap específico de `data.who.int` o redirigir/documentar de forma explícita el sitemap de `who.int` para el subdominio.
- Añadir una página de API de primer nivel en `data.who.int` que mapee cada indicador a su endpoint actual, esquema, versión y ejemplo de consulta; no obligar al agente a inferir la ruta desde la documentación general de xMart.
- Marcar claramente qué endpoints Athena/OData son históricos, cuáles están deprecados y cuál es el reemplazo estable, con fechas de retiro y política de versionado.

### P1 — hacer explícita la legibilidad para agentes

- Documentar reglas para GPTBot, OAI-SearchBot, ClaudeBot, Google-Extended y otros agentes, incluyendo la política deseada para contenido y descargas.
- Añadir JSON-LD/Schema.org verificable para `Dataset`, `DataCatalog`, `DefinedTerm` o `StatisticalVariable`, manteniendo la ficha humana como fuente primaria.
- Ofrecer un índice JSON/CSV de indicadores con `id`, `code`, `title`, `definition`, `unit`, `updated`, `download_url`, `api_url`, `license` y `citation`.

### P2 — mejorar interacción y control de versiones

- Exponer filtros y selecciones como URLs reproducibles, no solo como estado de controles.
- Mostrar versión/fecha del archivo descargable y checksum o identificador de release.
- Hacer visible en la interfaz que la cobertura temporal disponible puede ser anterior a la fecha de actualización de la ficha, evitando que un agente interprete “updated 2024” como “dato 2024”.

## Limitaciones y estados de evidencia

- La inspección se realizó con recuperación web textual; no se ejecutó una sesión de navegador con DevTools para comparar HTML inicial, DOM post-JavaScript, accesibilidad completa, headers HTTP y recursos bloqueados.
- Por lo anterior, JSON-LD, Schema.org, `canonical`, `hreflang`, `Content-Security-Policy`, `X-Robots-Tag` y comportamiento exacto de controles interactivos están **no verificados**, no “ausentes”.
- El intento de abrir `https://data.who.int/sitemap.xml` devolvió error interno en el recuperador; se sí verificó que `robots.txt` declara un sitemap en `who.int`.
- Las descargas CSV fueron detectadas como enlaces oficiales, pero el recuperador no renderiza el contenido `text/csv`; no se recalculó checksum ni se inspeccionaron encabezados del archivo dentro de esta auditoría.
- El endpoint OData público de xMart está documentado con ejemplos de `refmart`; no se pudo demostrar desde la ficha que `2322814` o `90E2E48` tengan un endpoint OData público individualmente mapeado.
- WHO Data marca las fichas como BETA y sujetas a cambios; las URLs y APIs deben revalidarse antes de una comparación longitudinal.

## Conclusión para la comparación de cuatro portales

WHO Data debería clasificarse como fuerte en autoridad/citabilidad, API y metadatos de indicador; medio-alto en descubrimiento y renderizado; y medio en gobernanza explícita de agentes y structured data verificable. Para la tabla comparativa se recomienda conservar el puntaje integral de **77/100**, acompañarlo de una etiqueta de confianza “media-alta” y no imputar como fallos las comprobaciones de JSON-LD/DOM que el entorno no permitió completar. En el análisis de direccionamiento, WHO ofrece condiciones favorables para ser citado cuando la consulta pide un indicador de salud concreto, pero la transición Athena → xMart puede producir fallos de agente si el modelo recupera documentación heredada o no encuentra el endpoint de datos actual.

## Fuentes primarias consultadas

- [WHO Data — portada](https://data.who.int/)
- [WHO Data — Indicators](https://data.who.int/indicators)
- [Under-five mortality rate (per 1000 live births)](https://data.who.int/indicators/i/E3CAF2B/2322814)
- [Life expectancy at birth (years)](https://data.who.int/indicators/i/A21CFC2/90E2E48)
- [robots.txt](https://data.who.int/robots.txt)
- [Data Description Schema](https://data.who.int/products/data-description-schema)
- [xMart](https://data.who.int/about/data/whdh/xmart)
- [WHO xMart OData API documentation](https://extranet.who.int/xmart4/docs/xmart_api/use_API.html)
- [GHO/Athena legacy notice](https://www.who.int/data/gho/legacy)
- [CSV — under-five mortality](https://srhdpeuwpubsa.blob.core.windows.net/whdh/DATADOT/INDICATOR/2322814_ALL_LATEST.csv)
- [CSV — life expectancy](https://srhdpeuwpubsa.blob.core.windows.net/whdh/DATADOT/INDICATOR/90E2E48_ALL_LATEST.csv)

