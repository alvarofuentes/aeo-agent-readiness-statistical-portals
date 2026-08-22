# Auditoría AEO y preparación para agentes de IA del Observatorio Regional de Planificación (CEPAL)

**Portal auditado:** [Observatorio Regional de Planificación para el Desarrollo de América Latina y el Caribe](https://observatorioplanificacion.cepal.org/es/)
**Host:** `observatorioplanificacion.cepal.org` · API: `api-kobo.cepal.org`
**Fecha de corte:** 2026-08-20 (verificaciones entre 19:08 y 19:14 UTC)
**Páginas internas de muestra:** [Planes, programas e instrumentos](https://observatorioplanificacion.cepal.org/es/planes-programas-e-instrumentos/) y la ficha `?id=46551`
**Calificación global:** **27/100 — Preparación baja o parcial; aún no preparado**

> El Observatorio conserva un activo institucional y documental de primer orden, con una API subyacente más capaz de lo que su interfaz deja ver. Pero el hallazgo de mayor consecuencia no es de optimización para agentes: **el portal está caído en producción ahora mismo, también para usuarios humanos**. Las nueve peticiones que el sitio dirige a su propia API responden `503`, mientras esa misma API, consultada desde otro origen, responde `200` con los datos completos. Sobre esa falla operativa persisten barreras estructurales: contenido esencial ausente del HTML inicial y del DOM renderizado, cero datos estructurados, estados de filtro no direccionables, e idioma no declarado.

---

## Resumen para la unidad (lectura no técnica)

**¿Qué se evaluó?** Esta auditoría no mide si el sitio se ve bien o si las personas pueden usarlo — mide si un **agente de inteligencia artificial** (un asistente como ChatGPT, Claude o Perplexity, o un buscador que responde preguntas en lugar de solo listar enlaces) es capaz de **encontrar, leer y citar correctamente** la información del Observatorio cuando alguien le pregunta por un plan, una institución o una política pública de la región. Es una disciplina distinta de la ciberseguridad o del diseño web: se llama optimización para motores de respuesta (AEO, por su sigla en inglés) y "preparación para agentes".

**¿Cómo se hizo?** No se trata de opiniones ni de una revisión visual. Cada afirmación de este informe se probó de forma directa: se navegó el sitio con un navegador real, se leyeron las respuestas exactas que entrega el servidor, se revisó el código con el que el sitio arma sus páginas, y se ejecutaron las mismas consultas que hace el propio Observatorio contra su fuente de datos. Todo hallazgo queda etiquetado como *verificado* (comprobado directamente), *inferido* (deducido con alta probabilidad, sin prueba directa) o *no verificado*, para que nadie confunda una conjetura con un hecho.

**¿Qué se obtuvo?** El Observatorio recibió **27 sobre 100 puntos**, en la banda de **"preparación baja o parcial"**. En términos simples: hoy, un asistente de IA que reciba una pregunta sobre los planes o políticas registrados en el Observatorio muy probablemente **no podrá responderla con datos correctos ni citar la fuente**, aunque esa información exista y esté bien documentada dentro del sitio.

**¿Por qué pasa esto, si el contenido es bueno?** El problema no es la calidad ni la autoridad del contenido —ahí el Observatorio está bien posicionado, por ser una fuente oficial de CEPAL con información estable—. El problema es la **entrega técnica**: gran parte del contenido solo aparece después de que el navegador ejecuta un programa interno de la página, un paso que muchos sistemas automáticos no completan; la página no declara en qué idioma está escrita cada versión; y no existe una "ficha de datos" estandarizada que un sistema automático pueda leer sin ambigüedad. A esto se suma un hallazgo más grave y más urgente: **el sitio está fallando en este momento para todos sus usuarios**, no solo para la IA. La página intenta cargar sus cifras y sus listados de planes desde su propia fuente de datos, y esa conexión está devolviendo un error; por eso hoy la portada muestra "Cargando..." de forma indefinida y el listado de planes aparece vacío. Es un problema técnico de configuración, no de contenido.

**¿Qué significa para la visibilidad del Observatorio?** Mientras estas barreras no se corrijan, el Observatorio quedará prácticamente invisible para la nueva generación de asistentes de IA que millones de personas usan para informarse, aunque siga siendo indexable por buscadores tradicionales. Con el tiempo, esto reduce el alcance y la influencia de un instrumento que la región usa para consultar planificación pública.

**¿Cuáles son las medidas más urgentes y más costo-eficientes?**

| Prioridad | Medida | Por qué es urgente o conviene | Costo/esfuerzo estimado |
|---|---|---|---|
| 1 — Urgente, esta semana | Restablecer la conexión del sitio con su propia fuente de datos (el error que hoy deja todo en "Cargando...") | Es una falla activa que afecta a **todos los usuarios**, no solo a la IA; es la que más perjudica la reputación y el uso diario del portal | Bajo: ajuste de configuración de servidor, no desarrollo nuevo |
| 2 — Muy costo-eficiente | Publicar los archivos estándar que indican a los sistemas automáticos qué hay en el sitio y cómo recorrerlo (`robots.txt`, mapa del sitio, guía para IA) | Son archivos de texto simples; su ausencia hoy deja al sitio sin ninguna puerta de entrada ordenada para un sistema automático | Bajo: días de trabajo técnico, sin rediseño |
| 3 — Alto impacto, costo moderado | Etiquetar cada plan y cada institución con datos estructurados estándar (nombre, fecha, país, fuente) legibles por máquina | Es lo que permite que una IA cite un plan específico con precisión, en vez de adivinar o inventar el dato | Medio: trabajo de desarrollo focalizado, reutiliza datos ya existentes |
| 4 — Estructural, mayor esfuerzo | Entregar el contenido esencial de cada página ya listo desde el servidor, sin depender de que un programa lo arme después | Es la causa de fondo de casi todas las demás brechas; es también la más costosa porque implica tocar la arquitectura del sitio | Alto: rediseño técnico, a planificar en fases |

Las medidas 1 y 2 son las de mayor retorno inmediato: no requieren rediseñar el sitio y corrigen tanto la caída actual como la ausencia total de señales de descubrimiento. Las medidas 3 y 4 son las que elevarían de forma sostenida la calificación y la visibilidad del Observatorio en asistentes de IA, pero conviene planificarlas como un proyecto, no como una corrección puntual.

El resto de este documento presenta la evidencia técnica completa que sustenta estas conclusiones, dimensión por dimensión, con el detalle necesario para que el equipo técnico priorice y ejecute.

---

## 1. Síntesis de hallazgos

### Fortalezas verificadas

- Autoridad institucional de CEPAL/Naciones Unidas y URLs estables de documentos en `documentosexternos.cepal.org`.
- API JSON pública con CORS `*`, filtrado por `query`, selección de campos por `fields` y paginación (`count`, `next`, `previous`, `results`).
- 360 registros aprobados en planes y 372 en instituciones, accesibles en una sola llamada.
- Sin discriminación por user-agent: seis agentes de IA distintos reciben `200`.
- Títulos específicos por página una vez renderizado el DOM.

### Riesgos críticos verificados

- **Caída funcional en producción:** las nueve llamadas del portal a su propia API devuelven `503`; la portada y el listado de planes quedan en "Cargando..." indefinido.
- Contenido esencial ausente tanto del HTML inicial (shell de 1.036 bytes) como del DOM ya renderizado; cero JSON-LD y cero microdatos en ambos estados.
- La ficha de un plan (`?id=46551`) no expone el registro ni siquiera después de renderizar.
- Idioma no declarado: sin `lang` ni `hreflang`; la versión en inglés conserva el menú y el `<title>` en español.
- Sin `robots.txt`, sitemap, `llms.txt`, documentación de API ni contrato OpenAPI.

---

## 2. Calificación consolidada

| Dimensión | Peso | Puntaje | Diagnóstico | Confianza |
|---|---:|---:|---|---|
| Acceso y gobernanza de bots | 10 | 4 | Acceso abierto verificado para seis agentes; sin política publicada. | Alta |
| Descubrimiento técnico | 15 | 3 | Sin sitemap ni `llms.txt`. El DOM renderizado sí aporta 35 enlaces internos, útiles solo para rastreadores que ejecutan JS. | Alta |
| Renderizado e interacción | 20 | 2 | Ensamblado íntegro en cliente, sin `<noscript>` ni `<main>`, filtros no direccionables y datos que hoy no cargan por el `503` de la API. | Alta |
| Datos estructurados | 15 | 0 | Cero JSON-LD y cero microdatos, en HTML inicial y en DOM renderizado. | Alta |
| API y uso por agentes de código | 25 | 12 | Filtros, selección de campos y paginación funcionan; sin documentación, sin OpenAPI, con campos internos expuestos y una falla de origen que tira abajo la interfaz. | Alta |
| Autoridad y citabilidad | 15 | 6 | Autoridad alta y documentos fuente estables, pero entidades no citables e idioma no declarado. | Alta |
| **Total** | **100** | **27** | **Preparación baja o parcial; aún no preparado** | |

**Aritmética:** `4 + 3 + 2 + 0 + 12 + 6 = 27`. Pesos: `10 + 15 + 20 + 15 + 25 + 15 = 100`.

Bandas: `0–24` No preparado · `25–49` Preparación baja o parcial · `50–74` Intermedia · `75–89` Preparado con brechas · `90–100` Agent Ready.

*Nota de sensibilidad:* si la API se restableciera, Renderizado e interacción subiría a un techo aproximado de 4/20 — la arquitectura cliente sin `<noscript>` ni estados direccionables seguiría limitando el puntaje incluso con los datos disponibles.

---

## 3. Metodología, alcance y limitaciones

Evidencia obtenida con Chrome real sobre Windows (navegación, ejecución de JavaScript en la página, consola y registro de red), consultas HTTP directas desde el origen de la API, y una prueba de user-agent ejecutada por el propietario del sitio con `curl`. Se reutilizó evidencia HTTP previamente recolectada en `outputs/aeo-http-evidence-2026-08-20/` y `audit_evidence/observatorioplanificacion_2026-08-20/`.

El entorno de auditoría tiene el dominio bloqueado a nivel de proxy de red; esa limitación **no se atribuyó al sitio** en ningún hallazgo, y toda la evidencia procede del navegador o de comandos ejecutados por el propietario del sitio.

**Clasificación de evidencia:** Verificado (observado directamente en respuesta HTTP, DOM, consola, red o salida de comando) · Inferido (soportado por múltiples observaciones, sin prueba directa) · No verificado (prueba no completada) · No aplicable.

**Advertencia metodológica:** una consulta inicial a la API se construyó sobre una ruta supuesta (`/data/<dataset>`) y devolvió `404`. Ese `404` es un artefacto del método de prueba, no evidencia sobre el sitio; la ruta real (`/api-kobo/data?dataset=<id>`) se extrajo del código cliente del portal. Se deja constancia para que no se cite como hallazgo.

---

## 4. Acceso y descubrimiento para bots

### Evidencia HTTP

| URL | Estado | Resultado |
|---|---:|---|
| `/robots.txt` | 404 | Sin política publicada. |
| `/sitemap.xml` | 404 | Sin mapa de URLs. |
| `/sitemap_index.xml` | 404 | Sin índice de sitemaps. |
| `/llms.txt` | 404 | Sin guía complementaria para modelos y agentes. |

La ausencia de `robots.txt` significa, bajo el Protocolo de Exclusión de Robots, que no hay restricciones publicadas — no es evidencia de bloqueo.

### Comportamiento por user-agent

Prueba `curl` ejecutada por el propietario sobre `https://observatorioplanificacion.cepal.org/es/`:

| User-agent | Estado | Bytes |
|---|---:|---:|
| `GPTBot/1.2` | 200 | 1.036 |
| `OAI-SearchBot/1.0` | 200 | 1.036 |
| `ClaudeBot/1.0` | 200 | 1.036 |
| `PerplexityBot/1.0` | 200 | 1.036 |
| `Googlebot/2.1` | 200 | 1.036 |
| `curl/8.0` | 200 | 1.036 |

**Verificado.** No hay bloqueo diferencial: los seis agentes reciben respuestas idénticas. Pero esos 1.036 bytes coinciden exactamente con la shell vacía (`<header></header><nav></nav><div id="web-content"></div><footer></footer>`): el acceso está abierto, pero no hay contenido que rastrear sin ejecutar JavaScript.

### Gobernanza recomendada

CEPAL decide si permite o restringe rastreo, pero el objetivo AEO exige una política deliberada que distinga, con los tokens vigentes: aparición en búsqueda de ChatGPT (`OAI-SearchBot`) frente a entrenamiento (`GPTBot`); rastreo de Anthropic (`ClaudeBot`) frente a peticiones activadas por usuario (`Claude-User`); Perplexity (`PerplexityBot`, `Perplexity-User`); y controles de Google relativos a IA (`Google-Extended`), sin confundirlos con el rastreo general de búsqueda.

---

## 5. Renderizado y muros de interacción

El HTML inicial de la portada mide 1.036 bytes; su `<body>` contiene cuatro contenedores vacíos. Tras ejecutar JavaScript, `#web-content` alcanza 63.644 caracteres: arquitectura de renderizado en cliente puro, verificada directamente.

| Señal | Portada ES | Listado de planes | Ficha `?id=46551` | Portada EN |
|---|---|---|---|---|
| `<title>` específico | Sí | Sí | No (hereda el del listado) | No (en español) |
| Atributo `lang` | Ausente | Ausente | Ausente | Ausente |
| `<h1>` / `<main>` / `<noscript>` | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| `rel=canonical` / meta description | Ausente | Ausente | Ausente | Ausente |
| `hreflang` / Open Graph / JSON-LD | 0 / 0 / 0 | 0 / — / 0 | 0 / — / 0 | 0 / — / 0 |
| Texto renderizado | 3.898 car. | 839 car. | 577 car. | 3.607 car. |

Todas estas ausencias persisten **después** de renderizar: se clasifican como **ausentes**, no como "no detectadas".

**Muros principales:**

1. Sin JavaScript, un agente recibe solo la shell de 1.036 bytes.
2. La ficha de entidad no expone su entidad: con `?id=46551` el DOM renderizado tiene 577 caracteres, conserva el título del listado y **no menciona el identificador 46551**.
3. Sin alternativa `<noscript>` en los módulos esenciales.
4. IDs duplicados confirmados en vivo en el listado de planes (`busca_btn`, `search_by_words`, `clear-multiselect5`), que rompen asociaciones ARIA y la automatización por selector.

**Paridad español/inglés:** `/en/` traduce el cuerpo pero conserva el menú y el `<title>` en español, y ninguna de las dos versiones declara `lang` ni `hreflang`. Un motor no puede determinar en qué idioma está cada página ni asociarlas como alternativas del mismo recurso.

---

## 6. Datos estructurados

No se encontró Schema.org, JSON-LD, microdatos, RDFa ni Open Graph en ninguna de las cuatro páginas examinadas, ni en el HTML inicial ni en el DOM renderizado. Efecto concreto: un motor que llegue a `?id=46551` no dispone de nombre, identificador, cobertura geográfica, período, editor, fecha ni licencia en forma legible por máquina — y en el estado actual, tampoco de forma legible por humanos.

**Clasificación: Ausente**, verificada en ambos estados.

---

## 7. APIs y acceso para agentes de código

### Lo que funciona

Endpoint real, extraído del código cliente del portal: `https://api-kobo.cepal.org/api-kobo/data?dataset=<id>`. Consultas ejecutadas desde el origen de la API, todas con `Access-Control-Allow-Origin: *`:

| Consulta | Estado | Respuesta |
|---|---:|---|
| Planes aprobados + `fields` (consulta exacta del portal) | 200 | `count: 360` |
| Repetición inmediata de la anterior | 200 | Idéntica |
| Planes, `fields=["_id"]` | 200 | `count: 360` |
| Planes, sin `fields` | 200 | `count: 360` (1,5 MB) |
| Destacados | 200 | `count: 3` |
| Instituciones, filtro compuesto | 200 | `count: 372` |

Filtrado por `query`, selección por `fields` y paginación (`count`/`next`/`previous`) funcionan de forma consistente.

### El defecto real: `503` dependiente del origen

Prueba decisiva con la **URL byte a byte idéntica**, ejecutada en el mismo intervalo de minutos:

| Origen de la petición | Estado |
|---|---:|
| `https://api-kobo.cepal.org` | **200** |
| `https://observatorioplanificacion.cepal.org` | **503** |

El registro de red del portal muestra **nueve peticiones a `api-kobo.cepal.org`, las nueve en `503`** (planes, instituciones, metodologías, marcos normativos, destacados y otras dos colecciones). La consola del portal, en dos cargas separadas, registra `TypeError: Failed to fetch` desde `loadAPIContentGlobal`, `loadAPIContentDocuments`, `loadAPIContentNews`, `loadAPIInstituciones`, `loadAPIMetodology` y `loadAPILegalFrameworks`.

La respuesta `503` no lleva cabeceras CORS, así que el navegador la rechaza antes de entregarla al código, que la reporta como fallo de red genérico — el front-end no puede distinguir un servidor caído de un problema de conexión, y por eso muestra "Cargando..." en lugar de un error.

**La observación es Verificada** (registro de red, dos cargas independientes, comparación de origen en el mismo intervalo). **El mecanismo** —rechazo por cabecera `Origin` o `Referer` en un proxy inverso o WAF— **es Inferido**, por no tener acceso a la configuración del servidor.

**Impacto verificado:** la portada muestra "Cargando..." indefinido en sus cuatro cifras clave; el listado de planes muestra `RESULTADOS ()` con "Cargando datos..." permanente y cero filas. Esto no es una barrera AEO: es una caída funcional que afecta a todos los usuarios del portal.

### Riesgos persistentes

Sin documentación pública ni contrato OpenAPI (`/docs`, `/openapi.json`, `/swagger.json`, `/redoc` responden 404). La respuesta por defecto incluye UUID, usuario de envío y campos de validación internos. No hay esquema que defina campos ni valores enumerados. Los identificadores de colección solo se obtienen leyendo el código cliente. La descarga CSV se genera con `Blob`/`createObjectURL`, sin URL estable para citar o automatizar.

---

## 8. Citabilidad y visibilidad en motores de respuesta

Prueba de cita sobre el plan `46551`: la URL devuelve 577 caracteres que no incluyen el registro, el identificador ni ningún metadato del plan. Para construir una cita, un agente debería descubrir por su cuenta el endpoint no documentado, extraer el identificador de colección del código JavaScript, reproducir el filtro de estado editorial, depurar campos internos, y citar una URL que, abierta por un tercero, no muestra el registro citado. La cita **no puede construirse** hoy. Lo único sólido para citación es la URL directa del documento fuente en `documentosexternos.cepal.org`.

---

## 9. Plan de remediación

### P0 — 0 a 2 semanas

1. **Restablecer la entrega de la API al propio portal** → corrige la caída funcional. Revisar la regla de proxy inverso o WAF que devuelve `503` a peticiones con `Origin: observatorioplanificacion.cepal.org`, y añadir cabeceras CORS también a las respuestas de error.
2. **Mostrar error explícito en cada `fetch` fallido** → corrige el "Cargando..." indefinido que oculta la avería a usuarios y operadores.
3. **Monitoreo sintético de la consulta exacta de cada módulo** → corrige la ausencia de detección de la avería.
4. **Publicar `robots.txt`, sitemaps por colección e índice de sitemaps** → corrige el descubrimiento nulo.
5. **Corregir la cadena de redirección HTTPS→HTTP y ampliar HSTS** → corrige la degradación de transporte.

### P1 — 2 a 6 semanas

1. **Entregar HTML semántico desde el servidor** (título, descripción, `<h1>`, `<main>`, contenido, fuente y fecha) en portada, listados y fichas → corrige la shell vacía de 1.036 bytes.
2. **Crear URLs permanentes de entidad** (`/es/planes/<id>-<slug>`) y serializar los filtros en parámetros resolubles en servidor → corrige la no reproducibilidad de estados y la ficha no citable.
3. **Declarar el idioma**: `lang`, `hreflang="es"`/`"en"`/`x-default`, y traducir el menú y `<title>` de `/en/` → corrige la indistinguibilidad de idioma.
4. **Publicar documentación de API y OpenAPI 3.1** con esquema, ejemplos, paginación, errores, límites, licencia y versionado; excluir por defecto registros no aprobados y campos internos → corrige la ausencia de contrato.
5. **Eliminar los IDs duplicados** y convertir las tarjetas navegables en enlaces reales → corrige accesibilidad y automatización.

### P2 — 6 a 12 semanas

1. **Implementar JSON-LD por plantilla** (`Organization`, `WebSite`, `DataCatalog`, `Dataset`, `BreadcrumbList`) con `identifier`, `spatialCoverage`, `temporalCoverage`, `publisher`, `dateModified`, `citation` y `license` → corrige la ausencia total de datos estructurados.
2. **Publicar `llms.txt`** con colecciones, licencias, fuentes canónicas y ejemplos.
3. **Exponer descargas estables por filtro** en JSON y CSV, sustituyendo el `Blob` cliente.
4. **Añadir bloques de "cómo citar" y procedencia**, y establecer pruebas automáticas sin JavaScript más monitoreo de rastreo y de citación en motores de respuesta.

---

## 10. Criterios de aceptación para "Preparado para Agentes"

- Las nueve llamadas del portal a su API responden `200` durante siete días consecutivos de monitoreo.
- Con JavaScript deshabilitado, listado y ficha muestran el contenido factual esencial de la aplicación interactiva.
- Una URL de búsqueda multifiltro, abierta en otra sesión, reproduce exactamente los mismos resultados.
- La ficha de un plan entrega título específico, `<h1>`, canónico, fuente, fechas y JSON-LD válido y coherente con el contenido visible.
- `robots.txt` y sitemaps existen, contienen solo URLs canónicas con `200` y se actualizan automáticamente.
- Cada página declara su idioma y su alternativa mediante `lang` y `hreflang`.
- Un agente completa, sin scraping del DOM: *"Enumera los planes aprobados vigentes de Chile sobre planificación para el desarrollo y entrega una cita permanente de uno de ellos."*

---

## 11. Anexo de evidencia y confianza

| Hallazgo | Clasificación | Confianza |
|---|---|---|
| Nueve llamadas del portal a su API devuelven `503` | Verificado | Alta |
| La misma URL responde `200` desde el origen de la API | Verificado | Alta |
| Mecanismo de rechazo por `Origin`/`Referer` | Inferido | Media |
| API expone paginación y filtrado funcionales | Verificado | Alta |
| Cifras clave y listado de planes en "Cargando..." permanente | Verificado | Alta |
| Ausencia de JSON-LD, `lang`, canónico, `<h1>`, `<main>`, `<noscript>` | Ausente (ambos estados) | Alta |
| Ficha `?id=46551` no expone el registro | Verificado | Alta |
| Sin bloqueo diferencial por user-agent | Verificado | Alta |
| Traducción parcial de `/en/` | Verificado | Alta |
| IDs duplicados en el listado de planes | Verificado | Alta |
| `robots.txt`, sitemaps y `llms.txt` inexistentes | Verificado | Alta |
| `/docs`, `/openapi.json`, `/swagger.json`, `/redoc` | Verificado | Media |
| Logs de servidor, frecuencia real de rastreo | No verificado | — |
| Core Web Vitals y rendimiento móvil | No aplicable | — |
| Decisión institucional sobre entrenamiento de modelos | No aplicable | — |

---

## 12. Fuentes primarias

- Portal evaluado: <https://observatorioplanificacion.cepal.org/es/>
- Versión en inglés: <https://observatorioplanificacion.cepal.org/en/>
- Módulo de planes: <https://observatorioplanificacion.cepal.org/es/planes-programas-e-instrumentos/>
- API de datos: <https://api-kobo.cepal.org/>
- OpenAI, publishers y crawlers: <https://help.openai.com/en/articles/12627856-publishers-and-developers-faq>
- Anthropic, rastreo web: <https://support.anthropic.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler>
- Perplexity, crawlers: <https://docs.perplexity.ai/docs/resources/perplexity-crawlers>
- Google, crawlers comunes: <https://developers.google.com/crawling/docs/crawlers-fetchers/google-common-crawlers>
- Google, creación de `robots.txt`: <https://developers.google.com/search/docs/crawling-indexing/robots/create-robots-txt?hl=es>
