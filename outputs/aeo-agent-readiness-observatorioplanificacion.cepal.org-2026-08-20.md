# Auditoría AEO y de preparación para agentes de IA

## Observatorio Regional de Planificación para el Desarrollo de América Latina y el Caribe

**Sitio evaluado:** <https://observatorioplanificacion.cepal.org>  
**Organización:** Comisión Económica para América Latina y el Caribe (CEPAL)  
**Fecha de evaluación:** 20 de agosto de 2026  
**Resultado:** **23/100 — No preparado (Not Ready)**  
**Confianza:** media-alta para la entrega HTTP, el código cliente y la API; limitada para el DOM final renderizado por Chrome.

> **Nota de sustitución.** Este informe reemplaza, como evaluación vigente, el archivo `Informe_AEO_Observatorio_CEPAL_2026-08-20.md`. El informe anterior se basó principalmente en páginas de la versión antigua que aún aparecían indexadas y no recorrió los estados generados por los selectores de la implementación actual. Varias de aquellas URLs ahora responden `404`. La puntuación anterior de 63/100 no debe utilizarse para describir el portal vigente.

---

## 1. Resumen ejecutivo

El Observatorio contiene información pública de gran valor y dispone de una API JSON accesible, pero la implementación vigente no entrega el contenido esencial en el HTML inicial. La portada, las páginas temáticas y los módulos de planes, instituciones, marcos normativos, metodologías y sistemas llegan al cliente como **shells HTML casi vacías**. JavaScript carga fragmentos adicionales, consulta una API Kobo y recién entonces construye listados, filtros y fichas.

Este patrón afecta directamente la preparación AEO y para agentes:

- Un agente que no ejecute JavaScript recibe contenedores vacíos, un título genérico y ningún contenido principal.
- Las selecciones hechas por el usuario se conservan principalmente en un campo oculto del navegador y no generan una URL completa, estable y reproducible.
- Las fichas pueden añadir `?id=<identificador>` al historial, pero el HTML inicial de esa URL sigue siendo genérico y vacío.
- La API completa responde, pero las consultas con parámetros de filtro —incluida la consulta de registros aprobados usada por la interfaz— devolvieron `502 Bad Gateway` durante la auditoría.
- No existen en las rutas convencionales `robots.txt`, sitemaps, `llms.txt`, OpenAPI ni documentación de API.
- No se detectó JSON-LD en las páginas iniciales ni en los fragmentos examinados; tampoco hay descripciones meta, canónicos o encabezados H1 en las shells principales.

La consecuencia es clara: **el contenido dinámico sí cambia el diagnóstico**. Aunque una persona con un navegador compatible puede interactuar con la interfaz cuando todos los componentes funcionan, un crawler o agente debe reconstruir una aplicación cliente, descubrir endpoints no documentados, reproducir filtros internos y tolerar fallas de API. Eso no constituye una fuente robusta, citable ni autónomamente utilizable.

### Fortalezas

- Autoridad institucional de CEPAL/Naciones Unidas.
- Cobertura regional y taxonomías útiles de país, tema, tipo de instrumento, escala, temporalidad y vigencia.
- API JSON pública con CORS abierto para la colección completa.
- Identificadores de registros y enlaces directos a documentos fuente.
- Fichas de detalle que pueden representarse mediante el parámetro `id` cuando JavaScript y la API funcionan.
- Algunos controles personalizados incorporan atributos ARIA apropiados.

### Riesgos críticos

- Contenido esencial ausente del HTML inicial.
- Consultas filtradas de la API con error `502` en la fecha de prueba.
- Estados de filtro no reproducibles mediante URL.
- Descubrimiento técnico deficiente: sin sitemap ni enlaces HTML iniciales hacia las entidades.
- API sin documentación ni contrato OpenAPI; respuesta completa incluye estados no aprobados y campos internos.
- Sin datos estructurados ni metadatos de página suficientes para que un motor identifique, cite y desambigüe entidades.

---

## 2. Puntaje de preparación AEO y para agentes

La evaluación utiliza las seis dimensiones y pesos definidos por el skill `aeo-agent-readiness-auditor`.

| Dimensión | Peso | Puntaje | Fundamento resumido |
|---|---:|---:|---|
| Acceso y gobernanza de bots | 10 | 3 | `robots.txt` no existe, por lo que no se publicó una prohibición, pero tampoco hay política explícita para crawlers generales o de IA. |
| Descubrimiento técnico | 15 | 2 | No hay sitemap, `llms.txt` ni enlaces de entidad en el HTML inicial; el menú también se inyecta con JavaScript. |
| Renderizado e interacción | 20 | 3 | El contenido se ensambla del lado cliente; los filtros no son plenamente direccionables y las consultas API usadas por la interfaz fallaron. |
| Datos estructurados | 15 | 0 | No se encontró JSON-LD en shells ni fragmentos; faltan canónicos, descripciones meta y H1 iniciales. |
| API y uso por agentes de código | 25 | 7 | Existe JSON público y CORS, pero no hay documentación/OpenAPI, los filtros devuelven 502 y la respuesta completa requiere depuración cliente. |
| Autoridad y citabilidad | 15 | 8 | CEPAL aporta alta autoridad y fuentes, pero las entidades carecen de HTML citable, URL canónica completa y metadatos uniformes. |
| **Total** | **100** | **23** | **No preparado (Not Ready)** |

### Interpretación de la escala

- **0–24:** No preparado.
- **25–49:** Preparación baja/parcial; aún no preparado.
- **50–74:** Preparación intermedia.
- **75–89:** Preparado con brechas.
- **90–100:** Agent Ready.

La suma es `3 + 2 + 3 + 0 + 7 + 8 = 23`.

---

## 3. Alcance, método y clasificación de evidencia

### Alcance revisado

Se probaron la portada y las rutas actuales derivadas de su navegación:

- [Portada en español](https://observatorioplanificacion.cepal.org/es/) y [portada en inglés](https://observatorioplanificacion.cepal.org/en/).
- [Planificación para el desarrollo](https://observatorioplanificacion.cepal.org/es/planificacion-para-el-desarrollo/).
- [Inversión pública](https://observatorioplanificacion.cepal.org/es/inversion-publica/).
- [Gobierno abierto](https://observatorioplanificacion.cepal.org/es/gobierno-abierto/).
- [Desarrollo y ordenamiento territorial](https://observatorioplanificacion.cepal.org/es/desarrollo-y-ordenamiento-territorial/).
- [Planes, programas e instrumentos](https://observatorioplanificacion.cepal.org/es/planes-programas-e-instrumentos/).
- [Marcos normativos](https://observatorioplanificacion.cepal.org/es/marcos-normativos/).
- [Metodologías](https://observatorioplanificacion.cepal.org/es/metodologias/).
- [Instituciones](https://observatorioplanificacion.cepal.org/es/instituciones/).
- [Sistemas nacionales de planificación](https://observatorioplanificacion.cepal.org/es/sistemas-nacionales-de-planificacion/).
- [Sistemas nacionales de inversión pública](https://observatorioplanificacion.cepal.org/es/sistemas-nacionales-de-inversion-publica/).
- [Países](https://observatorioplanificacion.cepal.org/es/paises/), preguntas frecuentes y geoportal.

También se inspeccionaron los fragmentos HTML y scripts JavaScript cargados por esas rutas, los archivos de claves de datos, la API `api-kobo.cepal.org`, las respuestas HTTP, redirecciones, archivos de descubrimiento y una ficha direccionada mediante `?id=46551`.

### Método

1. Recuperación HTTP directa de shells, fragmentos, scripts, JSON y cabeceras.
2. Comparación entre el HTML inicial y el contenido que el código intenta añadir después.
3. Lectura de la lógica de selección, filtrado, historial, detalle y exportación CSV.
4. Pruebas directas de la API completa, consultas por estado, país, campos e ID.
5. Revisión de rutas convencionales de descubrimiento y documentación.
6. Aplicación de la rúbrica ponderada del skill.

### Clasificación

- **Verificado:** observado directamente en una respuesta HTTP, archivo descargado o código cliente servido por el sitio.
- **Inferido:** consecuencia razonable del código o de una falla verificada, sin confirmación visual completa en el DOM final.
- **No verificado:** no fue posible comprobarlo con el entorno disponible.
- **No aplicable:** el criterio no corresponde al componente examinado.

### Limitación del navegador

El control programático de la pestaña de Chrome no pudo iniciar porque el host nativo de la extensión falló en el entorno local. Por ello, no se atribuyó al sitio ninguna falla causada por esa herramienta y el DOM final renderizado se marca como **no verificado**. La arquitectura dinámica, los estados de filtro, las URLs y las llamadas API sí se verificaron mediante los archivos servidos por el propio portal y solicitudes HTTP directas.

---

## 4. Cómo se construye actualmente el contenido dinámico

El flujo técnico verificado es:

`Ruta pública` → `shell HTML vacía` → `jQuery .load()` → `fragmento de interfaz` → `fetch a API Kobo` → `filtrado en el navegador` → `tabla o ficha en el DOM`

### 4.1 Shell inicial

La portada devuelve un documento de aproximadamente 1 KB cuyo cuerpo contiene solamente:

```html
<header></header>
<nav></nav>
<div id="web-content"></div>
<footer></footer>
```

En `document.ready`, la página carga `include/header.html`, `include/menu.html`, `include/content/homepage.html` y `include/footer.html`. La ruta de planes usa el mismo patrón, pero carga `iframe/planes/web.html` dentro de un `<section>` vacío.

**Clasificación: Verificado.** Esto demuestra que el contenido esencial no está en la respuesta inicial.

### 4.2 Módulos y selecciones

El módulo de planes incorpora siete selectores, botones, tablas y componentes SVG. Los filtros cubren tema, tipo de instrumento, país, escala territorial, temporalidad, vigencia, fechas y palabra clave. La selección se almacena principalmente en `#filter_selected` y la función cliente vuelve a filtrar el conjunto cargado.

Las aplicaciones de instituciones, marcos normativos, metodologías y sistemas repiten el mismo patrón con sus propias colecciones Kobo.

**Clasificación: Verificado.** Los selectores y su lógica están presentes en los fragmentos y scripts descargados.

### 4.3 Persistencia y compartibilidad

- Al abrir una ficha, el código ejecuta `history.pushState` y añade `?id=<id>`.
- Al volver al listado elimina el parámetro `id`.
- El portal reconoce algunos parámetros predefinidos como `theme`, `country` o `territorial_scale` en ciertas rutas.
- Sin embargo, las combinaciones realizadas en la interfaz no se serializan de forma completa y automática en la URL; permanecen en estado cliente.

**Resultado:** una ficha concreta puede llegar a ser compartible, pero una búsqueda multifiltro no es reproducible de manera confiable por otro usuario, crawler o agente.

**Clasificación: Verificado para el código; inferido para el efecto sobre todos los estados visuales.**

### 4.4 Exportación

La descarga CSV se crea en el navegador mediante un `Blob` y un enlace temporal `URL.createObjectURL`, con el nombre `datos_tabla.csv`. No existe una URL estable para citar, automatizar o volver a descargar el mismo conjunto filtrado.

**Clasificación: Verificado.**

---

## 5. Evidencia HTTP y de descubrimiento

| Recurso | Resultado | Tipo/tamaño aproximado | Evidencia e impacto |
|---|---:|---|---|
| `https://observatorioplanificacion.cepal.org/es/` | 200 | `text/html`, 1.036 bytes | Shell sin contenido principal. |
| `/es/planes-programas-e-instrumentos/` | 200 | `text/html`, ~1,1 KB | `<section>` vacío; carga posterior de `iframe/planes/web.html`. |
| `/iframe/planes/web.html?lang=es` | 200 | `text/html`, ~25 KB | Controles y plantillas de interfaz accesibles solo si se descubre la ruta interna. |
| `/robots.txt` | 404 | `text/html` | No hay política publicada. La ausencia no equivale a bloqueo. |
| `/sitemap.xml` | 404 | `text/html` | No hay mapa convencional de URLs. |
| `/sitemap_index.xml` | 404 | `text/html` | No hay índice convencional de sitemaps. |
| `/llms.txt` | 404 | `text/html` | No existe guía complementaria para modelos/agentes. |
| `/es/plans` | 404 | `text/html` | Ruta del portal anterior ya no vigente. |
| `/es/planes/plan-nacional-de-desarrollo-2025-2030` | 404 | `text/html` | Ficha antigua usada en el primer informe. |
| `https://api-kobo.cepal.org/` | 200 | `application/json` | La API declara versión 2.0.0, pero no enlaza documentación. |
| API de planes sin filtro | 200 | `application/json`, 1.558.998 bytes | Devuelve 366 registros y CORS `*`. |
| API de planes con consulta de aprobados | 502 | `application/json` | Falla la misma familia de parámetros usada por la interfaz. |
| `/docs`, `/openapi.json`, `/swagger.json`, `/redoc` en la API | 404 | — | No se descubrió documentación ni contrato ejecutable. |

### Redirecciones y HTTPS

La raíz HTTP redirige hacia HTTPS, pero la raíz HTTPS respondió con `Location: http://observatorioplanificacion.cepal.org/es/`, es decir, una redirección de degradación a HTTP. Además, la cabecera HSTS observada fue `max-age=300`, solo cinco minutos.

**Clasificación: Verificado.** Debe corregirse la cadena para terminar directamente en una única URL HTTPS y ampliarse HSTS después de validar todos los subdominios aplicables.

### Metadatos iniciales

En la muestra de rutas actuales se observó:

- Un `<title>` por shell, normalmente genérico.
- Cero descripciones meta.
- Cero enlaces canónicos.
- Cero bloques JSON-LD.
- Cero H1 en las shells principales.
- Cero `<main>` y cero alternativa `<noscript>`.
- Ausencia de atributo `lang` en el elemento `<html>` de las shells inspeccionadas.

**Clasificación: Verificado.** Algunos fragmentos internos contienen encabezados, pero eso no sustituye metadatos y contenido semántico en la URL pública inicial.

---

## 6. API, calidad de datos y capacidad de los agentes

### 6.1 Lo que funciona

La colección completa de planes respondió `200 OK`, con `Content-Type: application/json`, `Access-Control-Allow-Origin: *` y 366 registros. Los scripts revelan conjuntos equivalentes para instituciones, marcos normativos, metodologías y sistemas nacionales.

En el conjunto de planes se identificaron 360 registros con estado `Approved`, uno `Not Approved` y cinco `On Hold`. Los registros aprobados abarcan 33 países y seis temas.

**Clasificación: Verificado.**

### 6.2 Lo que falla

Las pruebas con `query`, `fields` e identificador devolvieron `502` con el mensaje `Failed to fetch data from Kobo`. El código de la interfaz solicita normalmente:

```text
query={"_validation_status.label":"Approved"}
```

Por tanto, el endpoint base disponible no demuestra que los listados y fichas puedan poblarse correctamente en este momento; la llamada concreta que intenta usar el portal falló durante la auditoría.

**Clasificación: Verificado para la API; impacto en la interfaz inferido, porque no se confirmó visualmente el DOM final.**

### 6.3 Riesgos para agentes

- Un agente que consuma la colección completa debe filtrar por sí mismo estados editoriales.
- La respuesta incluye metadatos internos, UUID, usuario de envío y campos de validación.
- Se encontró al menos un registro aprobado con campos `parsererror`, señal de contenido mal formado.
- No existe un esquema público que defina campos, valores enumerados, relaciones o compatibilidad futura.
- No hay paginación, filtros y ejemplos documentados para consumo seguro.
- Los documentos externos sí utilizan URLs directas y estables en `documentosexternos.cepal.org`, lo que constituye una base favorable para citación documental.

### 6.4 Conjuntos identificados

| Colección | Identificador observado |
|---|---|
| Planes | `aPJUaqc6gbHKCdcXQV3bYh` |
| Instituciones | `aMXsEC6SyQngvcTa3fSC93` |
| Marcos normativos | `aqpKMBhQZJ7QXra8gcyJnn` |
| Metodologías | `agFKiPAwFWfTF2Zfeh9UN9` |
| Sistemas nacionales de planificación | `auat7fCzxrGEmcpQWiTZLu` |
| Sistemas nacionales de inversión pública | `aLtk2nwgLUq4A4hNcJv6xR` |
| Mecanismos de coordinación | `a6VSfrLiDjiG4YYpAmdFb3` |

Estos identificadores se exponen en el código cliente, pero **no constituyen documentación de API** ni garantizan estabilidad contractual.

---

## 7. Datos estructurados, semántica y accesibilidad

### Datos estructurados

No se encontró Schema.org/JSON-LD en las shells ni en los fragmentos principales. Tampoco se observaron metadatos canónicos o sociales suficientes para identificar la entidad mostrada después de una interacción.

El parámetro `?id=46551`, por ejemplo, devuelve inicialmente el mismo título genérico, sin H1, canónico, descripción o JSON-LD del plan correspondiente.

**Clasificación: Verificado.**

### Semántica de interacción

Se observaron aspectos positivos: varios botones de multiselección incorporan `aria-haspopup="listbox"`, `aria-expanded`, `aria-controls`, `aria-label` y `aria-describedby`.

También se encontraron problemas verificables:

- IDs duplicados en planes: `busca_btn`, `search_by_words` y `clear-multiselect5`.
- IDs duplicados en instituciones, marcos normativos, metodologías y la plantilla temática.
- Tarjetas de temas y países implementadas como `<div onclick>` en lugar de enlaces HTML.
- Ausencia de contenido alternativo `<noscript>` para los módulos esenciales.

Los IDs duplicados pueden romper asociaciones ARIA, selección de elementos y automatización. Los `div` con `onclick` reducen la navegación por teclado y no ofrecen a un crawler un enlace semántico directo.

---

## 8. Gobernanza de bots de IA

La ausencia de `robots.txt` significa, en términos del protocolo estándar, que el sitio no publicó restricciones mediante ese archivo; no debe interpretarse como un bloqueo. Sin embargo, tampoco existe una política explícita y verificable para rastreadores de búsqueda o IA.

La gobernanza recomendada debe distinguir al menos:

- Indexación y aparición en búsqueda de ChatGPT mediante `OAI-SearchBot`.
- Control de entrenamiento mediante `GPTBot`.
- Acceso de Anthropic mediante `ClaudeBot` y solicitudes activadas por usuarios mediante `Claude-User`.
- Acceso de Perplexity mediante `PerplexityBot` y `Perplexity-User`.
- Controles de Google relacionados con IA, como `Google-Extended`, sin confundirlos con el rastreo general de Google Search.

Referencias oficiales: [OpenAI — Publishers and Developers FAQ](https://help.openai.com/en/articles/12627856-publishers-and-developers-faq), [Anthropic — web crawling](https://support.anthropic.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler), [Perplexity crawlers](https://docs.perplexity.ai/docs/resources/perplexity-crawlers) y [Google crawlers](https://developers.google.com/crawling/docs/crawlers-fetchers/google-common-crawlers).

La decisión de permitir o restringir cada bot corresponde a CEPAL. El objetivo AEO no exige permitir entrenamiento; sí exige que la política sea deliberada, coherente y comprobable.

---

## 9. Hallazgos priorizados

### P0 — críticos

#### P0.1 Entregar HTML semántico en cada URL pública

Generar del lado servidor o pre-renderizar portada, listados, resultados y fichas. Cada URL debe entregar como mínimo título específico, descripción, H1, contenido principal, enlaces, fuente y fecha sin depender de JavaScript.

**Criterio de aceptación:** con JavaScript deshabilitado, una URL de listado y una ficha muestran el mismo contenido factual esencial que la aplicación interactiva.

#### P0.2 Reparar y monitorear la API filtrada

Corregir las respuestas `502` para `query`, `fields` e ID. Añadir pruebas automáticas para la consulta exacta usada por cada módulo. La interfaz debe mostrar un estado de error explícito y no un contenedor vacío.

**Criterio de aceptación:** la consulta de aprobados, un filtro por país y una consulta por ID responden `200` con JSON válido durante al menos siete días de monitoreo.

#### P0.3 Convertir filtros y fichas en estados direccionables

Serializar todas las selecciones relevantes en parámetros de URL normalizados y resolverlos también en el servidor. Crear URLs permanentes de entidad, por ejemplo `/es/planes/<id>-<slug>`.

**Criterio de aceptación:** copiar, abrir en otra sesión y rastrear una URL reproduce exactamente el resultado o la ficha seleccionada.

#### P0.4 Corregir descubrimiento y transporte

Publicar `robots.txt`, sitemaps por colección y un índice de sitemaps. Corregir la redirección HTTPS→HTTP y definir una única URL canónica por idioma.

**Criterio de aceptación:** las cadenas de redirección terminan directamente en HTTPS; los sitemaps contienen solo URLs 200 canónicas y se actualizan automáticamente.

### P1 — alto impacto

#### P1.1 Publicar una API contractual

Documentar endpoints de solo lectura mediante OpenAPI 3.1, con esquema de campos, ejemplos, paginación, filtros, orden, errores, límites, licencia y versionado. La respuesta por defecto debe excluir registros no aprobados.

#### P1.2 Añadir JSON-LD por plantilla

Implementar `Organization`, `WebSite`, `DataCatalog`, `Dataset`, `BreadcrumbList` y tipos de entidad adecuados, como `Legislation` y `CreativeWork`. Incluir `identifier`, `name`, `description`, `spatialCoverage`, `temporalCoverage`, `publisher`, `dateModified`, `citation`, `isBasedOn` y enlaces a distribuciones JSON/CSV.

#### P1.3 Completar metadatos y multilingüismo

Usar títulos y descripciones específicos, `rel=canonical`, `hreflang="es"`, `hreflang="en"`, `x-default` y atributo `lang` correcto. La ficha seleccionada no debe conservar el título genérico del portal.

#### P1.4 Corregir semántica y accesibilidad

Eliminar IDs duplicados, transformar tarjetas navegables en enlaces reales y conservar controles ARIA únicos y consistentes. Añadir tablas y descripciones accesibles para gráficos y mapas.

### P2 — madurez

- Publicar `llms.txt` como guía complementaria de colecciones, licencias y fuentes canónicas.
- Añadir bloques de “respuesta breve”, “datos clave”, “última verificación” y “cómo citar”.
- Exponer descargas estables por filtro en JSON y CSV, no solo Blob cliente.
- Mantener changelog y política editorial de altas, revisiones, correcciones y vigencia.
- Medir accesos de crawlers, errores de renderizado, cobertura de sitemap y citación en motores de respuesta.

---

## 10. Hoja de ruta de implementación

### 0–15 días

1. Reparar consultas API y agregar health checks.
2. Corregir la redirección HTTPS y aumentar HSTS tras validación.
3. Publicar `robots.txt` y sitemap inicial.
4. Añadir manejo visible de errores en todos los `fetch`.
5. Definir el modelo canónico de URL para cada entidad y combinación de filtros prioritaria.

### 16–45 días

1. Pre-renderizar o servir HTML de listados y fichas.
2. Implementar títulos, H1, descripciones, canónicos y `hreflang`.
3. Corregir IDs duplicados y navegación por teclado.
4. Exponer descargas JSON/CSV estables.
5. Publicar documentación API y borrador OpenAPI.

### 46–90 días

1. Completar JSON-LD por colección.
2. Publicar páginas de entidad permanentes y relaciones bidireccionales.
3. Añadir procedencia, fecha de corte, licencia y cita sugerida.
4. Crear pruebas automáticas sin JavaScript y con renderizado.
5. Repetir la auditoría AEO y probar tareas completas de agentes.

---

## 11. Pruebas de aceptación recomendadas

| Prueba | Resultado esperado |
|---|---|
| Abrir portada sin JavaScript | Propósito, navegación principal y colecciones visibles en HTML. |
| Abrir listado de planes sin JavaScript | Registros aprobados, filtros como enlaces/formulario y paginación accesible. |
| Abrir una ficha por URL | Título específico, H1, fuente, fechas, documento, canónico y JSON-LD. |
| Copiar una búsqueda multifiltro | La nueva sesión reproduce exactamente los filtros y resultados. |
| Consultar API por estado, país e ID | `200`, JSON válido, esquema documentado y errores consistentes. |
| Consultar registro sin autenticar | No aparecen campos internos innecesarios ni estados editoriales no públicos. |
| Validar sitemap | Todas las URLs responden 200, son canónicas y contienen `lastmod` confiable. |
| Validar accesibilidad | IDs únicos, enlaces semánticos, controles etiquetados y navegación por teclado. |
| Validar JSON-LD | Sin errores críticos y correspondencia exacta con el contenido visible. |
| Ejecutar un agente de prueba | Obtiene, filtra, verifica y cita un plan sin scraping específico del DOM. |

### Escenarios de agente

1. “Enumera los planes aprobados vigentes de Chile relacionados con planificación para el desarrollo.”
2. “Abre el plan con ID 46551, identifica su fuente primaria y entrega una cita permanente.”
3. “Compara instituciones responsables de planificación en tres países y señala la fecha de actualización.”
4. “Descarga en CSV los marcos normativos de gobierno abierto, conservando la misma selección en una URL.”

El portal debería permitir completar estos escenarios con API documentada y URLs canónicas, sin ejecutar la lógica interna de la interfaz.

---

## 12. Evidencia de contenido dinámico por módulo

| Módulo | Carga inicial | Interacciones observadas | Riesgo principal |
|---|---|---|---|
| Portada | Fragmento `homepage.html` | Tarjetas, noticias, recursos y cifras alimentadas por `fetch` | La shell no contiene el contenido ni enlaces principales. |
| Planes | `iframe/planes/web.html` | Siete selectores, búsqueda, tablas, ficha y CSV | Estado cliente y API filtrada con 502. |
| Instituciones | Fragmento dedicado | País, tema y otros filtros; tablas y ficha | IDs duplicados y dependencia de API. |
| Marcos normativos | Fragmento dedicado | Filtros, tablas y ficha | Sin URL canónica por selección ni Schema. |
| Metodologías | Fragmento dedicado | Filtros, tablas y ficha | Mismo patrón cliente y sin contrato de API. |
| Sistemas | Fragmento dedicado | Selector de tipo/país y fichas | Entidades no presentes en HTML inicial. |
| Países | `include/content/paises.html` | Tarjetas `<div onclick>` | Navegación no semántica para teclado/crawlers. |
| Temas | `include/content/page.html` | Selección del tema por ruta/código y datos remotos | La plantilla filtra el conjunto en el navegador. |

---

## 13. Evidencia no verificada o no aplicable

- **DOM final y capturas de cada combinación:** no verificado por indisponibilidad del control de Chrome.
- **Paridad visual entre español e inglés:** no verificada exhaustivamente.
- **Comportamiento por user-agent específico:** no verificado de forma concluyente; no se descontaron puntos por bloqueo diferencial.
- **Logs del servidor, frecuencia real de rastreo y volumen de errores:** no verificados.
- **Core Web Vitals y rendimiento de dispositivo móvil:** fuera del alcance de esta auditoría AEO técnica.
- **Decisión institucional sobre entrenamiento de modelos:** no aplicable; corresponde a la política de CEPAL.

---

## 14. Conclusión

El Observatorio tiene un activo institucional y de datos valioso, pero la versión actual exige demasiada reconstrucción cliente para ser una fuente fiable de motores de respuesta y agentes. La barrera principal no es la ausencia de información: es que **la información no existe de forma estable, semántica y reproducible en la URL pública**.

La prioridad debe ser convertir cada listado, filtro y ficha en un recurso web autónomo: HTML útil desde la primera respuesta, URL permanente, metadatos específicos, datos estructurados, API documentada y descarga estable. Reparar las consultas API y preservar únicamente registros públicos aprobados es el primer paso operativo.

Con los P0 resueltos, el sitio puede pasar de 23 puntos a una preparación intermedia. Con HTML de entidad, Schema.org, OpenAPI, procedencia y monitoreo, puede aspirar a la categoría “preparado con brechas” y funcionar como fuente canónica regional para respuestas y agentes.

---

## 15. Fuentes principales

- Portal evaluado: <https://observatorioplanificacion.cepal.org/es/>
- Módulo dinámico de planes: <https://observatorioplanificacion.cepal.org/es/planes-programas-e-instrumentos/>
- API Kobo de CEPAL: <https://api-kobo.cepal.org/>
- OpenAI, políticas para publishers y crawlers: <https://help.openai.com/en/articles/12627856-publishers-and-developers-faq>
- Anthropic, rastreo web: <https://support.anthropic.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler>
- Perplexity, crawlers: <https://docs.perplexity.ai/docs/resources/perplexity-crawlers>
- Google, crawlers comunes: <https://developers.google.com/crawling/docs/crawlers-fetchers/google-common-crawlers>
- Google, creación de `robots.txt`: <https://developers.google.com/search/docs/crawling-indexing/robots/create-robots-txt?hl=es>

### Registro de evidencia local

Las respuestas y archivos examinados se conservaron en `outputs/aeo-http-evidence-2026-08-20/` y `audit_evidence/observatorioplanificacion_2026-08-20/` para permitir una revisión técnica posterior.
