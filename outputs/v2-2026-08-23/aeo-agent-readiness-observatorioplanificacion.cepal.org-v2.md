# Auditoría AEO y preparación para agentes de IA del Observatorio Regional de Planificación — v2

**Portal auditado:** [Observatorio Regional de Planificación para el Desarrollo de América Latina y el Caribe](https://observatorioplanificacion.cepal.org/es/)  
**Host:** `observatorioplanificacion.cepal.org`  
**Fecha de corte:** 2026-08-23  
**Página interna de muestra:** [Plan Nacional de Desarrollo 2025-2029. Ecuador no se detiene](https://observatorioplanificacion.cepal.org/es/planes-programas-e-instrumentos/?id=50678)  
**Consulta end-to-end:** `Plan Nacional de Desarrollo 2025-2029 Ecuador`  
**Calificación técnica v2:** **40/100 — preparación baja o parcial; aún no preparado**  
**Gate de visibilidad operacional:** **PASS en 1 consulta representativa**

## 1. Resumen ejecutivo

Esta v2 vuelve a evaluar el portal desde cero. No reutiliza la puntuación ni las conclusiones del informe anterior. La prueba parte de una pregunta en lenguaje natural, la introduce en el buscador del propio portal, conserva los dos candidatos devueltos, selecciona el registro exacto y abre su ficha específica.

El resultado es distinto de una prueba basada sólo en la portada: el Observatorio **sí puede resolver y citar una consulta concreta** cuando el agente utiliza la búsqueda interna. La consulta devolvió dos coincidencias cercanas: el plan nacional (`id=50678`) y su plan plurianual de inversiones (`id=50679`). La selección correcta exige distinguir el tipo de instrumento y el área temática. La ficha seleccionada entregó nombre, país, institución responsable, período 2025–2029, vigencia, escala, temporalidad, descripción, ocho dimensiones presentes y dos enlaces oficiales: el PDF del organismo responsable y la descarga preservada por CEPAL.

La brecha principal no es la inexistencia del contenido; es su **entrega técnica y descubrimiento machine-readable**. En la evidencia actual, la portada y la ficha se pueblan después de JavaScript, no hay `robots.txt`, sitemap ni `llms.txt`, y no se detectaron JSON-LD ni microdatos en el DOM renderizado. La API usada por el cliente está identificada como ruta de datos, pero su respuesta HTTP independiente y su documentación pública no se volvieron a probar en esta pasada. Por eso el score técnico queda separado del gate end-to-end.

## 2. Calificación consolidada

| Dimensión | Peso | Puntaje | Diagnóstico | Confianza |
|---|---:|---:|---|---|
| Acceso y gobernanza de bots | 10 | 4 | La portada responde y no publica una política `robots.txt`; no se repitió la matriz de user-agents. | Media |
| Descubrimiento técnico | 15 | 6 | Hay enlaces navegables al catálogo y búsqueda interna funcional; faltan robots, sitemap y `llms.txt`. | Alta |
| Renderizado e interacción | 20 | 10 | El catálogo y la ficha aparecen en el DOM después de JavaScript; la consulta requiere buscador y selección de resultado. | Alta |
| Datos estructurados | 15 | 0 | No se detectaron JSON-LD ni microdatos en el DOM renderizado; la inspección del HTML inicial queda no verificada. | Media |
| API para agentes de código | 25 | 8 | El cliente declara una ruta JSON de datos y el portal carga 360 registros, pero no se completó una llamada HTTP independiente ni se validó documentación. | Media |
| Autoridad y citabilidad | 15 | 12 | La ficha específica tiene contexto completo y enlaces oficiales estables al PDF del organismo y a la copia CEPAL. | Alta |
| **Total** | **100** | **40** | **Preparación baja o parcial; aún no preparado** | |

**Aritmética:** `4 + 6 + 10 + 0 + 8 + 12 = 40`. La puntuación técnica no se suma al gate operacional: son medidas diferentes.

## 3. Metodología, alcance y limitaciones

Se usó un navegador real sobre el portal público, sin autenticación ni fuentes secundarias. La evidencia de la consulta se guardó en [`planning-e2e-2026-08-23.json`](evidence/planning-e2e-2026-08-23.json).

El flujo observado fue:

1. recibir la consulta natural;
2. descomponerla en entidad, país, período y tipo de instrumento;
3. escribirla en `Buscar por palabra`;
4. registrar las dos coincidencias devueltas;
5. seleccionar el plan nacional y abrir `?id=50678`;
6. validar contexto, enlaces oficiales y citabilidad.

Esta pasada no ejecutó todavía el benchmark masivo ni una llamada HTTP independiente contra la API. Tampoco pretende inferir rendimiento de otros modelos a partir de una única consulta. El gate PASS significa que la cadena completa funcionó para este caso representativo.

## 4. Prueba end-to-end de visibilidad

| Paso | Evidencia observada | Resultado |
|---|---|---|
| Consulta recibida | `Plan Nacional de Desarrollo 2025-2029 Ecuador` | PASS |
| Descomposición | entidad `Plan Nacional de Desarrollo`; Ecuador; 2025–2029; tipo `plan` | PASS |
| Búsqueda interna | [catálogo de planes](https://observatorioplanificacion.cepal.org/es/planes-programas-e-instrumentos/) devolvió `Resultados (2)` | PASS |
| Candidatos | `50678` plan nacional y `50679` plan plurianual de inversiones | PASS; no se ocultó el near-match |
| Selección específica | [ficha `id=50678`](https://observatorioplanificacion.cepal.org/es/planes-programas-e-instrumentos/?id=50678) | PASS |
| Contexto | país, área, período, vigencia, escala, temporalidad, institución y descripción | PASS |
| Citación primaria | [PDF del organismo](https://www.planificacion.gob.ec/wp-content/uploads/2025/08/PlanNacionalDeDesarrollo25-29_EcuadorNoSeDetiene.pdf) y [descarga CEPAL](https://documentosexternos.cepal.org/bitstreams/de1a1790-d5c7-4b31-8be2-cc217a2a41cc/download) | PASS |

### Qué debe aprender el agente

La coincidencia `50679` demuestra que una consulta muy específica puede devolver más de una URL válida. La respuesta correcta no es elegir la primera ni penalizar al portal por no devolver una sola página: es conservar los candidatos y aplicar reglas de desambiguación por tipo de instrumento y área temática.

## 5. Acceso y descubrimiento para bots

| Recurso | URL | Estado observado | Lectura |
|---|---|---:|---|
| `robots.txt` | [`/robots.txt`](https://observatorioplanificacion.cepal.org/robots.txt) | 404 | No hay política publicada. Esto no equivale a bloqueo. |
| `sitemap.xml` | [`/sitemap.xml`](https://observatorioplanificacion.cepal.org/sitemap.xml) | 404 | No hay cobertura técnica declarada de entidades. |
| `sitemap_index.xml` | [`/sitemap_index.xml`](https://observatorioplanificacion.cepal.org/sitemap_index.xml) | 404 | No hay índice alternativo. |
| `llms.txt` | [`/llms.txt`](https://observatorioplanificacion.cepal.org/llms.txt) | 404 | No hay guía específica para agentes. |

La portada actual sí expone enlaces navegables a países, geoportal, recursos y documentos. El catálogo se puede alcanzar mediante una URL estable y su buscador permite recuperar una coincidencia específica. El descubrimiento sigue dependiendo demasiado de una interacción interna y no de un mapa de entidades para máquinas.

## 6. Renderizado y muros de interacción

La portada actual cargó las cifras `360`, `392`, `276` y `372`, además de enlaces temáticos y documentales. La ficha específica cargó todos los campos de contexto y los enlaces de citación. En ambas superficies el contenido visible depende de JavaScript; esta v2 no captura la respuesta HTML inicial antes de ejecutar scripts, por lo que esa comparación queda **no verificada** y no se convierte en una afirmación de “shell vacía”.

El buscador requiere introducir texto y activar `Buscar`. La selección de la ficha se materializa en la interfaz mediante una fila con `id=50678` y la ruta `?id=50678` permite una recuperación específica después de resolver el candidato. Es una barrera de interacción moderada, no un fracaso de recuperación.

## 7. Datos estructurados

En la portada y la ficha renderizadas no se detectaron bloques `application/ld+json`, microdatos ni RDFa. Tampoco se observó `lang`, `canonical` o `meta description` en el DOM inspeccionado. La ausencia en el HTML inicial no se declara porque esa captura no formó parte de esta pasada.

La ficha sí ofrece una estructura semántica visible para un agente: nombre, institución, país, período, vigencia, escala, temporalidad, descripción, dimensiones y enlaces primarios. La brecha es que esa estructura no está expresada además en un vocabulario machine-readable estándar.

## 8. API y acceso para agentes de código

La página declara en sus scripts una ruta de datos con el patrón:

```text
https://api-kobo.cepal.org/api-kobo/data?dataset=<portal-dataset>&query=<json-filter>
```

El cliente usa esa vía para poblar el catálogo y la ficha. En la sesión actual el catálogo mostró 360 resultados y la ficha específica cargó correctamente. La llamada HTTP independiente, su contrato, paginación, filtros legibles y documentación OpenAPI no se volvieron a ejecutar; quedan como una tarea explícita de la siguiente pasada y no reciben puntos adicionales.

## 9. Autoridad y citabilidad

La citabilidad es la dimensión más fuerte de la prueba. La respuesta puede conservar:

- el nombre exacto del plan;
- la institución nacional responsable;
- país, período 2025–2029, vigencia, escala y temporalidad;
- una descripción de propósito y alcance;
- el enlace al PDF oficial del organismo responsable;
- la descarga preservada por CEPAL;
- enlaces relacionados a marcos normativos, sistema nacional de planificación y otro instrumento.

La URL `?id=50678` es reproducible y específica. La citación es sólida para el caso probado, aunque todavía no se ha validado estabilidad histórica, checksum o versionado del registro.

## 10. Plan de remediación

### P0 — 0 a 2 semanas

1. Publicar `robots.txt`, sitemap de fichas y `llms.txt` con las rutas canónicas del catálogo. → Corrige descubrimiento técnico.
2. Mantener una URL canónica por ficha y declarar `lang`, `canonical` y descripción. → Reduce ambigüedad de entidad.
3. Publicar un estado de error explícito cuando la carga de datos falle. → Evita que un agente confunda “Cargando” con ausencia de contenido.

### P1 — 2 a 6 semanas

1. Añadir JSON-LD `Dataset`/`GovernmentOrganization`/`BreadcrumbList` por ficha, con identificador, período, país, institución, distribución y licencia. → Hace citable el registro sin inferencias.
2. Documentar la API de datos con ejemplos de búsqueda por texto, `id`, país, tema y estado de vigencia. → Reduce la dependencia de inspeccionar JavaScript.
3. Exponer una tabla HTML o respuesta JSON estable para cada ficha. → Permite recuperación programática y validación de paridad.

### P2 — 6 a 12 semanas

1. Versionar registros, enlaces y archivos con fecha de actualización y checksum. → Hace auditable el cambio de contenido.
2. Añadir pruebas sintéticas que reproduzcan la consulta `Plan Nacional de Desarrollo 2025-2029 Ecuador`. → Evita regresiones de búsqueda, selección y citación.
3. Publicar un vocabulario de tipos de instrumento y reglas `similar_to` / `do_not_confuse_with`. → Formaliza el caso observado entre `50678` y `50679`.

## 11. Criterios de aceptación para “Preparado para Agentes”

- La consulta de referencia devuelve el candidato exacto y conserva los near-matches.
- La ficha específica es accesible sin depender de una interacción física no reproducible.
- El registro expone nombre, definición, país, período, vigencia, institución, fuente y URL canónica.
- La ficha tiene JSON-LD válido y consistente con el contenido visible.
- `robots.txt`, sitemap y `llms.txt` existen y apuntan al catálogo real.
- La API documenta búsqueda, filtros, paginación, errores y versionado.
- La prueba end-to-end pasa en tres ejecuciones consecutivas y con dos agentes distintos.

## 12. Anexo de evidencia y confianza

| Hallazgo | Clasificación | Evidencia | Confianza |
|---|---|---|---|
| El buscador devuelve dos coincidencias para la consulta | Verificado | DOM de la página de catálogo; `Resultados (2)` | Alta |
| `50678` es el plan nacional correcto | Verificado | Fila del catálogo y ficha específica | Alta |
| La ficha entrega contexto y dos URLs oficiales | Verificado | DOM de `?id=50678` | Alta |
| `robots.txt`, sitemaps y `llms.txt` devuelven 404 | Verificado | Navegación directa a los cuatro recursos | Alta |
| No hay JSON-LD ni microdatos en el DOM renderizado | Verificado | Inspección de portada y ficha renderizadas | Alta |
| No hay JSON-LD ni microdatos en el HTML inicial | No verificado | No se capturó la respuesta antes de JavaScript | — |
| La API independiente permite recuperar `id=50678` | No verificado | La ruta se observó en scripts; falta llamada HTTP aislada | — |
| El gate end-to-end pasa para una consulta | Verificado | Flujo completo de búsqueda → ficha → citación | Alta |

## 13. Integración con la evaluación de portales estadísticos

La observación técnica debe entrar como una capa separada en cada informe estadístico:

| Capa | Qué mide | Cómo se reporta |
|---|---|---|
| Visibilidad operacional | Consulta natural → búsqueda del portal → indicador/serie → valor → unidad → fuente → URL | Gate por consulta y cobertura; nunca se convierte un fallo de transporte en cero |
| Preparación técnica | Bots, descubrimiento, renderizado, estructurado, API y citabilidad | Score 0–100 con evidencia, fecha y confianza |
| Desambiguación | Candidatos, near-matches, dimensiones y reglas de selección | Tabla de candidatos y regla aplicada |
| Reproducibilidad | URL específica, parámetros, respuesta y captura | Evidencia primaria enlazada por fila |

El nuevo comparativo no debe calcular una correlación AEO–visibilidad mezclando estas capas sin control. La matriz futura debe añadir, por portal, `technical_score`, `technical_confidence`, `e2e_pass_rate`, `candidate_count`, `specific_url_rate`, `metadata_complete_rate`, `citation_reproducible_rate`, `robots_status`, `sitemap_status`, `llms_status`, `jsonld_rendered`, `api_direct_verified` y `evidence_date`.

## 14. Fuentes primarias

- [Portada del Observatorio](https://observatorioplanificacion.cepal.org/es/)
- [Catálogo de planes, políticas e instrumentos](https://observatorioplanificacion.cepal.org/es/planes-programas-e-instrumentos/)
- [Ficha del Plan Nacional de Desarrollo 2025–2029](https://observatorioplanificacion.cepal.org/es/planes-programas-e-instrumentos/?id=50678)
- [PDF oficial del Plan Nacional de Desarrollo de Ecuador](https://www.planificacion.gob.ec/wp-content/uploads/2025/08/PlanNacionalDeDesarrollo25-29_EcuadorNoSeDetiene.pdf)
- [Descarga preservada por CEPAL](https://documentosexternos.cepal.org/bitstreams/de1a1790-d5c7-4b31-8be2-cc217a2a41cc/download)
- [Ruta de datos declarada por el cliente](https://api-kobo.cepal.org/api-kobo/data)
