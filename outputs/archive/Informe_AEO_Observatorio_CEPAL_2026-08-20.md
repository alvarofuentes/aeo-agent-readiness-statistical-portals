# Auditoría de preparación AEO y para agentes de IA

## Observatorio Regional de Planificación para el Desarrollo de América Latina y el Caribe

**Sitio evaluado:** <https://observatorioplanificacion.cepal.org>  
**Fecha de evaluación:** 20 de agosto de 2026  
**Organización:** Comisión Económica para América Latina y el Caribe (CEPAL)  
**Resultado global:** **63/100 — Preparación intermedia**

> El Observatorio dispone de un corpus excepcionalmente valioso, con buena cobertura regional, URLs estables, páginas temáticas y fichas con metadatos útiles. Su principal brecha no es de contenido: es de entrega técnica, semántica explícita y acceso programático. Hoy un buscador puede rastrear buena parte del sitio, pero un motor de respuestas o un agente debe inferir demasiado, atravesar páginas con advertencias de JavaScript, interpretar iconos sin nombre y extraer datos desde HTML o PDF sin una API documentada.

---

## 1. Resumen ejecutivo

### Veredicto

El sitio está **bien posicionado como repositorio institucional**, pero todavía no funciona como una fuente plenamente preparada para respuestas generativas ni para agentes autónomos. Tiene autoridad de dominio, contenido sustantivo y una arquitectura temática reconocible. Sin embargo, la portada y la sección de inversión pública presentaron respuestas vacías en el acceso automatizado; varias páginas incluyen el aviso “Sorry, you need to enable JavaScript” aunque luego entregan contenido; algunos componentes dinámicos quedan como “Loading map ...”; y hay señales de redirecciones o canónicos inconsistentes entre HTTP y HTTPS.

El mayor potencial está en transformar las fichas ya existentes —países, planes, sistemas, leyes, documentos y notas— en **entidades explícitas, enlazadas y consultables por máquina**. Esto requiere HTML estable sin dependencia crítica de JavaScript, datos estructurados Schema.org, una API abierta con OpenAPI, descargas JSON/CSV y una política clara para crawlers de IA.

### Principales fortalezas

- **Autoridad y confianza institucional.** El sitio pertenece a CEPAL/Naciones Unidas, identifica su propósito y ofrece una fórmula de citación institucional en [Acerca del Observatorio](https://observatorioplanificacion.cepal.org/es/acerca-de/).
- **Cobertura y profundidad.** Los listados presentan 67 planes, 349 marcos legales y 62 documentos en las páginas observadas, con filtros por país, fecha, tipo y tema: [Planes](https://observatorioplanificacion.cepal.org/es/plans), [Marcos legales](https://observatorioplanificacion.cepal.org/es/regulatory-frameworks) y [Documentos](https://observatorioplanificacion.cepal.org/es/documentos).
- **Contenido rastreable aun sin ejecutar JavaScript.** Aunque aparece una advertencia de JavaScript, el extractor pudo recuperar menús, encabezados, filtros, fichas y texto principal de numerosas páginas.
- **Fichas con metadatos útiles.** Las páginas de detalle incluyen fechas, países, tipos, autores, fuentes, signaturas y enlaces a documentos. Véanse la [Ley Marco de Acceso a la Información Pública](https://observatorioplanificacion.cepal.org/es/marcos-regulatorios/ley-marco-de-acceso-la-informacion-publica-ley-no-10554) y el [Panorama del desarrollo territorial 2024](https://observatorioplanificacion.cepal.org/es/documentos/panorama-del-desarrollo-territorial-de-america-latina-y-el-caribe-2024).
- **Ecosistema bilingüe.** Hay selector español/inglés y páginas equivalentes, lo que amplía la superficie de descubrimiento.

### Principales brechas

- **Entrega técnica inconsistente.** La portada y [Inversión pública](https://observatorioplanificacion.cepal.org/es/inversion-publica) no entregaron cuerpo textual en el extractor usado; además, algunas aperturas terminaron redirigidas a HTTP.
- **Dependencia parcial de JavaScript.** Mapas y métricas quedan incompletos en HTML; por ejemplo, [ODS](https://observatorioplanificacion.cepal.org/es/sdgs) conserva “Loading map ...”, aunque ofrece un enlace alternativo a tabla.
- **Semántica débil o ruidosa.** El HTML extraído expone cadenas de interfaz como “Sobrescribir enlaces de ayuda a la navegación”, nombres de iconos (`gavel`, `record_voice_over`, `attach_money`) y encabezados vacíos. En la [ficha de Chile](https://observatorioplanificacion.cepal.org/es/paises/chile) aparecen también etiquetas genéricas como “description” y “Date”.
- **Sin acceso programático descubierto.** No se encontró una API pública documentada, especificación OpenAPI ni descarga sistemática JSON/CSV durante la muestra. La ausencia no pudo confirmarse de forma exhaustiva por la limitación del entorno, por lo que se registra como “no descubierta”, no como inexistente.
- **Política de crawlers de IA no verificable.** `robots.txt`, `sitemap.xml`, `llms.txt` y `openapi.json` no pudieron recuperarse mediante el acceso disponible. Es prioritario comprobarlos directamente desde infraestructura.
- **Visibilidad limitada para preguntas naturales.** En una muestra exploratoria de cuatro consultas, el dominio del Observatorio no apareció como resultado principal para preguntas como “¿Cómo funciona el sistema nacional de planificación de Chile?”; para la definición del Observatorio aparecieron antes otra comunidad de CEPAL y un PDF del propio dominio. Esto sugiere una oportunidad de crear páginas más orientadas a respuestas.

---

## 2. Puntaje AEO y de preparación para agentes

| Dimensión | Peso | Puntaje | Diagnóstico |
|---|---:|---:|---|
| Acceso técnico y rastreabilidad | 20 | 13 | Gran parte del HTML es recuperable, pero hay respuestas vacías, redirecciones HTTP y componentes que dependen de JavaScript. |
| Arquitectura e indexación | 15 | 12 | Menú amplio, enlaces internos, breadcrumbs y URLs descriptivas; las facetas generan muchas variantes y hay nomenclatura de rutas inconsistente. |
| Capacidad de responder preguntas | 20 | 15 | Contenido sustantivo y especializado, pero faltan resúmenes answer-first, definiciones breves, FAQs y comparaciones listas para citar. |
| Semántica y datos estructurados | 15 | 5 | Jerarquía visible, pero abundan etiquetas de interfaz e iconos sin significado textual; JSON-LD no pudo verificarse. |
| Autoridad, procedencia y citabilidad | 15 | 12 | Marca CEPAL, fuentes y metadatos sólidos; faltan criterios editoriales, responsables y fechas de revisión consistentes por ficha. |
| API, datos abiertos y acción autónoma | 10 | 3 | Los datos están navegables y filtrables, pero no se descubrió una interfaz programática documentada ni exportación homogénea por entidad. |
| Multilingüe y visibilidad en respuestas | 5 | 3 | Español e inglés están presentes, aunque hay mezcla de idiomas y no se verificaron `hreflang`, equivalencias ni canónicos. |
| **Total** | **100** | **63** | **Preparación intermedia** |

### Escala empleada

- **80–100:** preparado para motores de respuesta y agentes.
- **60–79:** preparación intermedia; buen contenido, barreras técnicas o semánticas materiales.
- **40–59:** preparación baja; rastreo o reutilización insuficientes.
- **0–39:** preparación crítica.

---

## 3. Alcance y metodología

La evaluación siguió la lógica del skill solicitado de preparación AEO y para agentes: accesibilidad para crawlers, dependencia de renderizado, arquitectura, capacidad de respuesta, semántica Schema.org, procedencia, multilingüismo, APIs y capacidad de acción autónoma.

### Muestra de páginas

Se recorrieron la portada y los principales tipos de página derivados desde el menú:

1. Portada en español e inglés.
2. [Acerca del Observatorio](https://observatorioplanificacion.cepal.org/es/acerca-de/).
3. [Países](https://observatorioplanificacion.cepal.org/es/countries) y [Chile](https://observatorioplanificacion.cepal.org/es/paises/chile).
4. [Planificación para el desarrollo](https://observatorioplanificacion.cepal.org/es/planning-development).
5. [Planes](https://observatorioplanificacion.cepal.org/es/plans) y una [ficha de plan](https://observatorioplanificacion.cepal.org/es/planes/plan-nacional-de-desarrollo-2025-2030).
6. [Institucionalidad](https://observatorioplanificacion.cepal.org/es/institutionality/sectorial-topic/82) y [Planificación en Chile](https://observatorioplanificacion.cepal.org/es/sistemas-planificacion/planificacion-en-chile).
7. [Inversión pública](https://observatorioplanificacion.cepal.org/es/inversion-publica).
8. [Desarrollo territorial](https://observatorioplanificacion.cepal.org/es/desarrollo-territorial).
9. [Gobierno abierto](https://observatorioplanificacion.cepal.org/es/opengov).
10. [Objetivos de Desarrollo Sostenible](https://observatorioplanificacion.cepal.org/es/sdgs).
11. [Marcos legales](https://observatorioplanificacion.cepal.org/es/regulatory-frameworks) y una [ficha legal](https://observatorioplanificacion.cepal.org/es/marcos-regulatorios/ley-marco-de-acceso-la-informacion-publica-ley-no-10554).
12. [Documentos](https://observatorioplanificacion.cepal.org/es/documentos) y una [ficha de documento](https://observatorioplanificacion.cepal.org/es/documentos/panorama-del-desarrollo-territorial-de-america-latina-y-el-caribe-2024).
13. [Recursos de difusión](https://observatorioplanificacion.cepal.org/es/resources) y una [nota del Observatorio](https://observatorioplanificacion.cepal.org/es/nota/los-ods-y-la-planificacion-territorial-perspectivas-desde-los-departamentos-de-colombia).
14. Una muestra de resultados y filtros parametrizados, páginas en inglés y cuatro consultas naturales sin restricción de dominio.

### Limitaciones

- El runtime seguro local que debía controlar el Navegador y la extensión de Chrome falló antes de iniciar por un error DPAPI (`CryptUnprotectData`). La auditoría continuó mediante el acceso web directo disponible.
- El mismo fallo impidió leer el archivo local completo del skill y ejecutar la generación/renderizado de DOCX. El análisis se mantuvo alineado con la descripción funcional del skill y sus dimensiones habituales, pero no debe confundirse con una inspección de código fuente o de logs del servidor.
- No se inspeccionaron headers HTTP, código fuente crudo, JSON-LD, respuesta por user-agent, Core Web Vitals ni logs. `robots.txt`, sitemaps y endpoints técnicos quedaron como “no verificados”.
- La muestra de visibilidad en preguntas naturales es indicativa, no una medición estadística de ranking ni de menciones en todos los motores generativos.

---

## 4. Hallazgos detallados

### 4.1 Acceso de crawlers y renderizado

**Estado: parcial — impacto alto**

La mayoría de las páginas de listado y detalle entregan suficiente HTML para recuperar el contenido, aun cuando la primera línea muestra el aviso “Sorry, you need to enable JavaScript to visit this website”. Esto es una fortaleza: el contenido no parece ser una SPA completamente opaca.

Sin embargo, la entrega no es uniforme:

- La portada devolvió título y URL, pero ningún cuerpo textual en el extractor.
- La página de inversión pública se resolvió sin líneas de contenido y con una redirección observada hacia `http://.../es/inversion-publica/`.
- Componentes como mapas muestran “Loading map ...” en el HTML. [ODS](https://observatorioplanificacion.cepal.org/es/sdgs) mitiga parcialmente el problema con “Ver mapa como tabla”.
- Algunas cifras introductorias aparecen sin valor, como en [Planificación para el desarrollo](https://observatorioplanificacion.cepal.org/es/planning-development), donde el texto conserva “países presentaron...” y “países tienen...” sin el número visible.

**Riesgo AEO:** un motor de respuestas puede omitir la portada o la sección de inversión, citar datos incompletos o no recuperar la información visual de mapas y gráficos.

**Acción recomendada:** garantizar renderizado del lado del servidor o generación estática de todo contenido esencial; mantener las visualizaciones como mejora progresiva; probar HTML con JavaScript deshabilitado y con user-agents de Googlebot, Bingbot, GPTBot, OAI-SearchBot, ClaudeBot y PerplexityBot.

### 4.2 Arquitectura, enlaces e indexación

**Estado: bueno con deuda técnica — impacto medio-alto**

El menú global enlaza de forma consistente países, planificación, inversión pública, desarrollo territorial, gobierno abierto, ODS y recursos. Las páginas contienen breadcrumbs y los listados enlazan a fichas concretas. La estructura temática es fuerte y favorece el descubrimiento.

Las debilidades observadas son:

- Variantes de facetas incorporadas al path y al query string, por ejemplo segmentos de `country`, `type`, `temporality`, `Caracterización` y `page`. Esto puede producir muchas URLs equivalentes o de escaso valor.
- Rutas en español e inglés mezcladas: `/es/plans`, `/es/planning-development`, `/es/resources`, `/es/documentos`, `/es/planes/...`.
- La ruta raíz usa una redirección de idioma y el buscador encontró también `/index.html?lang=es`, que puede competir con `/es/` si no hay canónicos firmes.
- Se observaron contenidos duplicados o etiquetas repetidas, como “Decreto Ejecutivo N°3 de Ecuador” dos veces en la página temática de planificación.

**Acción recomendada:** definir una matriz de URLs canónicas por tipo de entidad; aplicar `rel=canonical`; usar `noindex,follow` en combinaciones de filtros sin demanda; mantener sitemaps por tipo de contenido; y consolidar la estrategia de slugs e idiomas.

### 4.3 Contenido orientado a respuestas

**Estado: fuerte en profundidad, medio en formato de respuesta — impacto alto**

Las fichas contienen hechos específicos que un motor puede usar. Por ejemplo:

- La [ficha del PND de México 2025–2030](https://observatorioplanificacion.cepal.org/es/planes/plan-nacional-de-desarrollo-2025-2030) identifica temporalidad, tipo, base legal, proceso de aprobación y ejes generales y transversales.
- [Planificación en Chile](https://observatorioplanificacion.cepal.org/es/sistemas-planificacion/planificacion-en-chile) explica formulación, implementación, monitoreo y articulación territorial.
- La [ficha legal de Costa Rica](https://observatorioplanificacion.cepal.org/es/marcos-regulatorios/ley-marco-de-acceso-la-informacion-publica-ley-no-10554) presenta país, fecha, tipo, documento y tema.
- El [documento territorial 2024](https://observatorioplanificacion.cepal.org/es/documentos/panorama-del-desarrollo-territorial-de-america-latina-y-el-caribe-2024) incluye autores, signatura, resumen, fuente, tipo y adjunto.

El contenido, sin embargo, suele iniciar con texto largo o metadatos dispersos. Faltan bloques diseñados para resolver preguntas frecuentes de forma directa:

- “En una frase”.
- “Datos clave”.
- “¿Qué es?”, “¿quién es responsable?”, “¿desde cuándo?”, “¿qué norma lo sustenta?”.
- Tablas comparativas regionales descargables.
- Definiciones de términos y relaciones explícitas entre país, autoridad, plan, norma y fuente.

**Acción recomendada:** añadir a cada plantilla un resumen de 40–80 palabras, una tabla de hechos verificables y 3–6 preguntas frecuentes basadas en consultas reales. No conviene crear FAQs artificiales; deben responder necesidades concretas y ser visibles en HTML.

### 4.4 Semántica, accesibilidad textual y Schema.org

**Estado: débil/no verificado — impacto alto**

El extractor reconoce títulos H1, subtítulos, listas, breadcrumbs y enlaces, pero también expone ruido que reduce la claridad semántica:

- “Sobrescribir enlaces de ayuda a la navegación” aparece como encabezado repetido.
- Los iconos de caracterización se leen como `gavel`, `record_voice_over`, `history`, `insert_chart`, `attach_money` y otros nombres internos.
- Hay encabezados vacíos (`#####`) y enlaces sin texto, especialmente en ODS.
- En la ficha de Chile aparecen etiquetas genéricas en inglés (“description”, “Date”, “Local Plans”) dentro de la versión española.
- El diagrama textual de Planificación en Chile se extrae como una secuencia desordenada de palabras, lo que muestra una alternativa accesible insuficiente.

No fue posible confirmar presencia o ausencia de JSON-LD. Por ello, el puntaje semántico refleja tanto el ruido observable como la falta de evidencia verificable de datos estructurados.

**Acción recomendada:** implementar y validar:

- `Organization` y `WebSite` en todo el dominio.
- `BreadcrumbList` en todas las rutas internas.
- `Dataset` o `DataCatalog` para colecciones regionales y sus descargas.
- `Article`, `Report` o `CreativeWork` para notas y documentos.
- `Legislation` para marcos legales.
- `DefinedTerm`/`DefinedTermSet` para taxonomías y conceptos.
- Entidades `Place`/`Country`, `GovernmentOrganization` y relaciones `about`, `spatialCoverage`, `temporalCoverage`, `author`, `publisher`, `datePublished`, `dateModified`, `citation`, `isBasedOn` y `sameAs`.

Todo icono funcional debe tener nombre accesible y equivalente textual visible; todo mapa o gráfico debe incluir tabla, descripción y descarga de datos.

### 4.5 Autoridad, procedencia y actualización

**Estado: bueno — impacto medio-alto**

La afiliación institucional con CEPAL y Naciones Unidas es una señal fuerte de confianza. La página [Acerca del Observatorio](https://observatorioplanificacion.cepal.org/es/acerca-de/) explica objetivo, públicos y forma de citar. Las fichas de documentos y leyes enlazan fuentes primarias y adjuntos.

Las oportunidades son:

- Mostrar en cada ficha quién la elaboró o revisó dentro de CEPAL/ILPES.
- Separar claramente `fecha del instrumento`, `fecha de publicación`, `última reforma`, `fecha de incorporación al Observatorio` y `última verificación`.
- Publicar criterios editoriales, metodología de selección, alcance por colección y política de correcciones.
- Indicar estado de vigencia del plan o norma y fecha de corte de los datos.
- Usar identificadores persistentes y citas bibliográficas completas.

**Acción recomendada:** incorporar un panel estándar “Procedencia y actualización” con responsable, fuente primaria, fecha de revisión, método, licencia, identificador y sugerencia de cita.

### 4.6 APIs, datos abiertos y preparación para agentes

**Estado: bajo — impacto muy alto**

El sitio ofrece filtros útiles y enlaces a PDF, pero un agente debe navegar y extraer el HTML para responder preguntas comparativas. No se descubrieron durante la muestra:

- Catálogo de API.
- Especificación OpenAPI.
- Esquema de entidades y campos.
- Exportaciones homogéneas JSON/CSV por listado o filtro.
- Endpoints documentados para país, plan, autoridad, marco legal, documento, tema u ODS.

**Acción recomendada:** publicar una API de solo lectura y un catálogo de datos con:

- IDs estables y URLs de entidad.
- JSON-LD y JSON convencional.
- CSV para tablas y filtros.
- OpenAPI 3.1 con ejemplos y límites.
- Paginación, filtros, ordenamiento y campo `updated_at`.
- Licencia y atribución legibles por máquina.
- Versionado y changelog.
- Enlaces desde HTML mediante `Link` headers y `<link rel="alternate" type="application/json">`.

Una primera versión puede limitarse a endpoints `countries`, `plans`, `planning-systems`, `authorities`, `legal-instruments`, `documents`, `topics` y `sdgs`, más relaciones entre ellos.

### 4.7 Multilingüismo

**Estado: parcial — impacto medio**

La existencia de español e inglés es una ventaja. No obstante, las versiones muestran mezclas de idioma en etiquetas y algunas páginas en inglés conservan contenidos o metadatos en español.

**Acción recomendada:** auditar pares de traducción, declarar `hreflang="es"`, `hreflang="en"` y `x-default`, mantener canónicos por idioma y usar IDs de entidad comunes para enlazar traducciones. Cuando un documento no esté traducido, indicarlo explícitamente en lugar de duplicar una página parcialmente localizada.

### 4.8 Visibilidad en búsquedas de pregunta

**Estado: oportunidad — impacto medio**

Una muestra exploratoria de cuatro preguntas mostró que la autoridad temática de CEPAL sí aparece, pero con frecuencia a través del portal general, el repositorio, Comunidades CEPAL o PDFs, no mediante las fichas estructuradas del Observatorio. Esto sugiere que los activos externos y documentales compiten con la fuente web que debería ser canónica.

**Acción recomendada:** crear páginas hub para consultas de alto valor, por ejemplo:

- “¿Qué países de América Latina y el Caribe tienen planes de largo plazo vigentes?”.
- “¿Cómo funciona el sistema nacional de planificación de cada país?”.
- “Comparador de planes nacionales de desarrollo”.
- “Marcos legales de inversión pública por país”.
- “Autoridades responsables de planificación e inversión pública”.

Cada hub debe responder primero, explicar metodología, mostrar fecha de corte, enlazar las fichas y ofrecer los datos descargables.

---

## 5. Matriz priorizada de recomendaciones

| Prioridad | Recomendación | Evidencia/riesgo | Resultado esperado |
|---|---|---|---|
| **P0** | Forzar HTTPS extremo a extremo y corregir redirecciones/canónicos | Portada e inversión pública mostraron redirecciones o respuestas inconsistentes | Fuente única, segura y estable para crawlers y citas |
| **P0** | Entregar HTML completo en portada, inversión pública, métricas, mapas y tablas | Respuestas vacías, valores ausentes y “Loading map ...” | Rastreo y respuesta sin ejecutar JavaScript |
| **P0** | Verificar y publicar `robots.txt` y sitemaps por colección; declarar política para bots de IA | Rutas técnicas no verificables en esta auditoría | Control explícito de acceso y mejor descubrimiento |
| **P1** | Añadir JSON-LD por plantilla y corregir semántica/ARIA | Iconos internos, encabezados vacíos y etiquetas de interfaz | Entidades y relaciones comprensibles por máquina |
| **P1** | Crear API abierta + OpenAPI + descargas JSON/CSV | No se descubrió acceso programático documentado | Comparación y reutilización autónoma confiable |
| **P1** | Incorporar bloques answer-first y “Datos clave” | Contenido profundo, pero poco optimizado para respuestas breves | Mayor probabilidad de cita en respuestas generativas |
| **P1** | Normalizar procedencia, vigencia y fechas de revisión | Metadatos buenos pero heterogéneos | Mejor confianza, frescura y trazabilidad |
| **P1** | Controlar URLs de facetas y paginación | Gran número de combinaciones en path/query | Menos duplicación y mejor presupuesto de rastreo |
| **P2** | Consolidar estrategia multilingüe y `hreflang` | Mezcla español/inglés y rutas heterogéneas | Correspondencia correcta entre versiones |
| **P2** | Crear hubs comparativos orientados a preguntas | Baja presencia de fichas en consultas naturales | Mayor visibilidad AEO y utilidad pública |
| **P2** | Publicar `llms.txt` como guía complementaria, no sustitutiva | No pudo verificarse | Punto de entrada para colecciones y políticas de uso |
| **P2** | Establecer monitoreo AEO | Sin métricas específicas de bots y citas | Mejora continua basada en evidencia |

---

## 6. Hoja de ruta propuesta

### 0–30 días: asegurar acceso y fuente canónica

1. Corregir todas las redirecciones para terminar exclusivamente en HTTPS.
2. Garantizar contenido HTML completo en `/es/`, `/en/` e inversión pública.
3. Probar las plantillas con JavaScript deshabilitado y corregir cifras o tablas ausentes.
4. Auditar `robots.txt`, sitemaps, canónicos, `hreflang` y códigos HTTP.
5. Eliminar ruido semántico visible: encabezados de administración, iconos sin nombre, enlaces vacíos y etiquetas sin traducir.
6. Publicar un inventario técnico de tipos de contenido y campos.

**Criterio de éxito:** todas las URLs prioritarias responden 200 por HTTPS, exponen H1 y contenido principal en HTML, y no dependen de JavaScript para hechos esenciales.

### 31–90 días: hacer explícitas las entidades

1. Implementar JSON-LD por plantilla.
2. Añadir “Resumen”, “Datos clave”, “Fuente”, “Última verificación” y “Cómo citar”.
3. Crear tablas accesibles y descargas CSV para mapas, comparadores y listados.
4. Consolidar URLs de filtros, canónicos y reglas de indexación.
5. Completar equivalencias español/inglés con `hreflang`.
6. Lanzar 5–10 hubs de preguntas prioritarias.

**Criterio de éxito:** validación sin errores críticos en Schema.org, resultados equivalentes con y sin JavaScript y entidades enlazadas mediante IDs persistentes.

### 3–6 meses: habilitar agentes y medición

1. Publicar API de lectura y OpenAPI 3.1.
2. Exponer catálogo de datos, licencia, changelog y versionado.
3. Añadir formatos JSON-LD/CSV y enlaces alternativos desde cada ficha.
4. Implementar pruebas automáticas de HTML, schema, enlaces, sitemaps y accesibilidad.
5. Medir accesos de bots de búsqueda/IA, cobertura de indexación, consultas naturales, citas y errores.
6. Ejecutar una nueva auditoría con inspección de headers, fuente HTML, JSON-LD y logs.

**Criterio de éxito:** un agente puede obtener una lista filtrada de planes, seguir relaciones hacia países, autoridades y normas, verificar fecha/fuente y citar URLs canónicas sin scraping frágil.

---

## 7. Esquema de datos recomendado

La unidad mínima debería ser una entidad con identificador persistente y relaciones explícitas:

| Entidad | Campos mínimos |
|---|---|
| País | ID, nombre, códigos ISO, idiomas, URL canónica |
| Plan | ID, título, país, tipo, temporalidad, vigencia, autoridad, fechas, objetivos, documento fuente, ODS relacionados |
| Sistema de planificación | ID, país, etapas, actores, base legal, escala territorial, fecha de revisión |
| Autoridad | ID, nombre oficial, país, rol, sitio oficial, vigencia |
| Instrumento legal | ID, título, número, país, tipo, fecha, reforma, vigencia, texto/adjunto, temas |
| Documento/nota | ID, título, autores, fecha, signatura/DOI/handle, resumen, temas, idioma, licencia, adjuntos |
| Tema/ODS | ID, nombre, definición, vocabulario, entidades relacionadas |

Las relaciones deben ser navegables en ambos sentidos. Por ejemplo:

`País → tiene plan → Plan → es gestionado por → Autoridad → se sustenta en → Instrumento legal → trata sobre → Tema/ODS`.

---

## 8. Plan de medición

### Indicadores técnicos

- Porcentaje de URLs prioritarias con 200 HTTPS y contenido completo sin JavaScript.
- Cobertura válida en sitemaps y proporción indexada.
- Porcentaje de fichas con JSON-LD válido y sin advertencias críticas.
- Número de enlaces rotos, canónicos conflictivos y duplicados por facetas.
- Tiempo de respuesta y tasa de errores por plantilla y user-agent.

### Indicadores AEO

- Presencia del Observatorio entre las fuentes principales para 30–50 preguntas objetivo.
- Porcentaje de respuestas generativas que citan la ficha canónica en vez de un PDF o portal secundario.
- Clics e impresiones para consultas interrogativas.
- Cobertura de snippets con fecha, autor, país, tipo y fuente correctos.

### Indicadores de agentes y datos abiertos

- Uso de API por endpoint y tasa de respuestas exitosas.
- Porcentaje de colecciones descargables en JSON/CSV.
- Frescura: días desde la actualización de la fuente hasta la publicación en el Observatorio.
- Proporción de entidades con fuente primaria, responsable y fecha de verificación.
- Tasa de tareas completadas por un agente de prueba sin intervención humana.

---

## 9. Conclusión

El Observatorio ya posee el activo más difícil de construir: **contenido regional autorizado, granular y enlazado**. Para elevarse de 63 a más de 80 puntos no necesita multiplicar páginas, sino volver explícita y estable la información que ya tiene. Las tres inversiones con mayor retorno son:

1. HTML completo y canónico por HTTPS, independiente de JavaScript para contenido esencial.
2. Entidades y relaciones expresadas con JSON-LD, metadatos de procedencia y resúmenes answer-first.
3. API abierta con OpenAPI y descargas JSON/CSV.

Con esas mejoras, el sitio puede convertirse no solo en un repositorio consultado por personas, sino en la **fuente canónica regional** que buscadores, asistentes y agentes utilicen para responder y actuar con datos de planificación pública verificables.

