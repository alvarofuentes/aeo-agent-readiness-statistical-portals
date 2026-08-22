# Auditoría AEO y AI readiness — World Bank Open Data

**Fecha de corte:** 2026-08-22  
**Host principal:** https://data.worldbank.org/  
**API oficial:** https://api.worldbank.org/v2/  
**Página de indicador:** https://data.worldbank.org/indicator/SP.POP.TOTL (Population, total)  
**Página interna nativa:** https://data.worldbank.org/static/pages/en/about/get-started.html  
**Método:** aeo-agent-readiness-auditor, con pesos 10/15/20/15/25/15.  
**Resultado estricto:** **77/100**. **Resultado armonizado:** **84/100** al excluir simétricamente las dimensiones cuya evidencia no pudo verificarse de forma independiente en este entorno (bots/gobernanza y datos estructurados). **Cobertura verificable:** 75% del peso.

## Veredicto ejecutivo

World Bank Open Data es un portal con una base técnica fuerte para agentes de IA que necesitan encontrar y recuperar datos: las páginas tienen URLs estables por indicador, texto semántico suficiente, enlaces directos a descargas y una API oficial v2 sin autenticación. La principal oportunidad no está en el acceso programático, sino en hacer que los valores y sus metadatos sean igualmente recuperables desde el HTML inicial, declarar de forma explícita el soporte para crawlers/agentes y reforzar la capa de datos estructurados.

El indicador de población total es fácilmente identificable y proporciona título, licencia CC BY-4.0, rango temporal 1960–2025, fuentes y enlaces CSV/XML/Excel. Sin embargo, en la representación no interactiva observada, el bloque “All Countries and Economies” presenta los encabezados pero no la tabla de valores; esto sugiere dependencia parcial de JavaScript para completar la experiencia de consulta. La API documentada compensa ampliamente esta limitación para agentes de código.

## Matriz cuantitativa

| Dimensión | Peso | Puntaje | Estado de evidencia | Hallazgo principal |
|---|---:|---:|---|---|
| Acceso y gobernanza de bots | 10 | 7 | Inferido / no verificado | No se pudo obtener robots.txt de forma directa desde el cliente de auditoría; un índice externo reproducía una política User-agent: * Allow:* con exclusiones acotadas y sitemap, pero no se toma como verificación primaria. No se verificó llms.txt ni reglas específicas de crawlers de IA. |
| Descubrimiento técnico | 15 | 12 | Verificado + inferido | Portada, índice de países, índice de indicadores y URLs limpias por código (SP.POP.TOTL) son rastreables en texto; sitemap del subdominio no fue verificable por la herramienta. Navegación interna enlaza DataBank, catálogo, microdatos, ayuda y desarrolladores. |
| Renderizado e interacción | 20 | 13 | Verificado | HTML inicial incluye título, descripción, fuentes, licencia, rango temporal, controles de descarga y enlaces de navegación. Los valores del cuadro por país aparecen vacíos en la vista textual, por lo que el detalle interactivo/mapa/tabla parece depender parcialmente de JavaScript. |
| Datos estructurados | 15 | 7 | No verificado / inferido | Se observan metadatos legibles y vocabulario consistente, pero no fue posible confirmar JSON-LD, Schema.org, DCAT o rel=canonical mediante una inspección de fuente independiente. No atribuir la ausencia a un fallo del sitio. |
| API y acceso para agentes de código | 25 | 24 | Verificado | API Indicators v2 oficial, pública y sin claves; consultas por país/indicador/fecha, paginación, múltiples indicadores, filtros MRV/MRNEV, formatos JSON, XML, JSON-stat, CSV, Excel y documentación de llamadas. |
| Autoridad, atribución y citabilidad | 15 | 14 | Verificado | Dominio institucional primario; página del indicador identifica Population, total, fuentes UN/NSO/Eurostat, licencia CC BY-4.0 y período; API permite citar endpoint reproducible. Falta confirmar si cada valor visible en la UI queda acompañado por unidad/año en HTML estático. |
| **Total estricto** | **100** | **77** | **Confianza media** | Excelente superficie de API; citabilidad web y gobernanza de bots requieren comprobaciones adicionales. |

### Puntaje armonizado para comparación entre portales

Debido a limitaciones del entorno (fallo de inicialización de terminal y restricciones de apertura directa de robots.txt/JSON-LD), se excluyen para todos los portales las dimensiones de bots/gobernanza (10) y datos estructurados (15). No se imputa el bloqueo del cliente al sitio.

    (12 + 13 + 24 + 14) / (15 + 20 + 25 + 15) × 100 = 84/100

La cifra armonizada no significa que el portal obtenga cero en las dimensiones excluidas; significa que no se utilizan en el ranking común hasta contar con evidencia equivalente.

## Evidencia primaria

### Portada

La portada declara “World Bank Open Data” y “Free and open access to global development data”, ofrece búsqueda y navegación por economía o indicador, y enlaza plataformas complementarias: DataBank, Microdata Library y Data Catalog. También mantiene una sección de ayuda para desarrolladores y enlaces de API.

- https://data.worldbank.org/ (HTML observado el 2026-08-22; contenido textual disponible sin interacción).
- Evidencia relevante: la representación textual incluye título del portal, promesa de acceso abierto, búsqueda, enlaces a DataBank/Catalog/Microdata y “For Developers”.

### Página de indicador: Population, total

La página tiene un identificador estable y legible por máquina/humano (SP.POP.TOTL). Expone:

- título “Population, total”;
- referencias a World Population Prospects (UN), bases estadísticas de oficinas nacionales, Eurostat y UN Statistics Division;
- licencia CC BY-4.0;
- período 1960–2025;
- opciones de gráfico Line/Bar/Map y detalles;
- indicadores relacionados;
- enlaces directos de descarga en CSV, XML y Excel;
- acceso a DataBank y tablas WDI.

- https://data.worldbank.org/indicator/SP.POP.TOTL
- Guía de usuario oficial: https://datatopics.worldbank.org/world-development-indicators/user-guide.html

En la vista no interactiva, el encabezado “All Countries and Economies” y sus columnas aparecen, pero no se observan filas con valores. Esto se registra como dependencia parcial de renderizado/interacción, no como prueba de que la tabla no exista para usuarios con JavaScript.

### API y documentación

La documentación oficial confirma que el Indicators API proporciona acceso programático a casi 16.000 series temporales y que no requiere API keys. La llamada representativa recomendada es:

    https://api.worldbank.org/v2/country/all/indicator/SP.POP.TOTL?date=2024&format=json

La documentación también especifica formatos XML, JSON, JSONP y JSON-stat; descargas CSV/XML/Excel; paginación; filtros de fecha; MRV/MRNEV; múltiples indicadores y consulta de notas al pie.

- https://datahelpdesk.worldbank.org/knowledgebase/articles/889392
- https://datahelpdesk.worldbank.org/knowledgebase/articles/898581
- Página API: https://api.worldbank.org/v2/country/all/indicator/SP.POP.TOTL

### Página interna nativa: Getting Started

La página explica que data.worldbank.org utiliza el Data API, que el sitio busca facilitar la localización, descarga y uso de datos, y que se puede acceder a series individuales, descargas masivas, DataBank, widgets y Web API. También describe el catálogo y la biblioteca de microdatos.

- https://data.worldbank.org/static/pages/en/about/get-started.html

## Puntos destacables

- API pública, oficial y sin autenticación, con múltiples formatos y filtros.
- Convención de URLs por indicador que facilita enlace directo, recuperación y citación.
- Licencia explícita CC BY-4.0 en la página de indicador.
- Atribución de fuentes y enlaces a plataformas complementarias.
- Amplia documentación de API y ejemplos reproducibles.
- Arquitectura de portal que conecta indicadores, economías, DataBank, catálogo y microdatos.

## Puntos de dolor y mejoras priorizadas

### P0 — hacer los valores citables sin JavaScript

Incluir en el HTML inicial una tabla o representación accesible de los valores más recientes, con país/economía, año, valor, unidad y enlace de metadatos. Mantener la visualización JS como mejora progresiva. Esto permitiría que agentes que solo leen HTML respondan con un valor exacto y una cita.

### P1 — publicar señales de gobernanza para agentes

Verificar y documentar robots.txt en el propio subdominio data.worldbank.org, declarar reglas para crawlers de IA cuando corresponda y considerar un llms.txt o página equivalente con enlaces canónicos a API, licencia, catálogo y documentación. Replicar la política en api.worldbank.org y datacatalog.worldbank.org.

### P1 — reforzar datos estructurados

Añadir JSON-LD/Schema.org Dataset o DataCatalog con name, description, publisher, license, temporalCoverage, spatialCoverage, variableMeasured, distribution, isBasedOn y sameAs. Cada distribución debe apuntar a JSON/CSV/JSON-stat y al endpoint de API.

### P1 — clarificar unidad, fecha y cobertura en el bloque visible

La ficha muestra rango temporal y columnas, pero la citabilidad de valores concretos depende de completar la tabla. Hacer visible la unidad y el período de cada valor y exponer los filtros elegidos en la URL o en un resumen textual.

### P2 — documentar versionado y frescura

Exponer lastUpdated, fecha de extracción y versión de la base de datos también en el HTML y en metadatos estructurados. Mantener ejemplos con consultas acotadas por país/año para agentes.

## Limitaciones y control de calidad

- El terminal del entorno no pudo inicializarse (CryptUnprotectData), por lo que no se guardaron respuestas HTTP crudas automáticamente.
- La herramienta web rechazó la apertura directa de algunos endpoints (robots.txt y URL API con query string) por restricciones de seguridad; se usó la documentación oficial y la representación indexada de las páginas.
- No se debe convertir “no verificado” en “ausente”. En particular, JSON-LD, canonical, robots del subdominio y comportamiento con user-agents específicos requieren una comprobación posterior desde un navegador/cliente HTTP funcional.
- El puntaje es una auditoría exploratoria con confianza media y fecha de corte 2026-08-22; no es una prueba causal de direccionamiento de agentes.

## Implicaciones para las pruebas de direccionamiento

Hipótesis comprobables en la fase comparativa:

1. La disponibilidad y documentación de la API debería elevar el éxito del agente en consultas que piden un valor exacto y código reproducible.
2. La ausencia de valores en HTML inicial podría reducir la citación de la página web frente a la citación del endpoint API, especialmente en agentes sin navegador.
3. La autoridad institucional, licencia y atribución deberían aumentar la selección como fuente primaria, pero no sustituyen la recuperabilidad técnica.

Las pruebas deben registrar por separado mención de data.worldbank.org, mención de api.worldbank.org, enlace a ficha exacta, exactitud del valor/año/unidad y uso de una fuente secundaria.

