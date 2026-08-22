# Comparación AEO y preparación para agentes — cuatro portales estadísticos

**Fecha de corte:** 22 de agosto de 2026  
**Portales:** Banco Mundial, WHO Data, Statista y CEPALSTAT  
**Método:** habilidad `aeo-agent-readiness-auditor`; seis dimensiones ponderadas a 100 puntos.

## Veredicto ejecutivo

El Banco Mundial y WHO Data alcanzan el mejor puntaje integral (77/100). El Banco Mundial destaca por una API pública y reproducible; WHO Data destaca por metadatos y citabilidad editorial. Statista obtiene 60/100: su experiencia pública es citable, pero el registro, el paywall y el acceso API autorizado reducen la llegada de agentes. CEPALSTAT obtiene 45/100: su API es potente, pero la interfaz y los mecanismos de descubrimiento no conectan bien con las observaciones numéricas.

## Puntajes

| Portal | Integral | Núcleo comparable* | Cobertura de evidencia |
|---|---:|---:|---:|
| Banco Mundial | 77 | 90.9 | 75% |
| WHO Data | 77 | 83.6 | 85% |
| Statista | 60 | 65.5 | 75% |
| CEPALSTAT | 45 | 58.2 | 65% |

\* Núcleo comparable: D2 Descubrimiento + D5 API + D6 Citabilidad, reescalado a 100. Se excluyen D1, D3 y D4 de los cuatro portales porque el entorno no permitió comprobar de forma equivalente robots/DOM/JSON-LD.

## Hallazgos comparados

| Portal | Aspectos destacables | Principales mejoras |
|---|---|---|
| Banco Mundial | API v2 sin clave, múltiples formatos, filtros y documentación abundante. | Hacer los valores visibles sin JavaScript; publicar política de crawlers y señales structured-data verificables. |
| WHO Data | Fichas con identificador, unidad, cobertura, periodicidad, método, licencia y cita. | Mapear cada indicador a un endpoint OData estable; documentar sitemap y agentes IA; publicar JSON-LD. |
| Statista | Fichas públicas con fuente, período, fecha de publicación, autor y formatos de cita. | Evidencia mínima sin registro; política de bots accesible; API/OpenAPI pública de muestra; JSON-LD. |
| CEPALSTAT | API REST/OpenAPI pública y metadatos de fuentes, notas y dimensiones. | Sitemap, `llms.txt`, tablas HTML planas, URLs canónicas por indicador y reparación OpenAPI. |

## Piloto de direccionamiento

Se ejecutaron ocho consultas neutrales en búsqueda web, registrando si cada dominio apareció entre los diez primeros resultados. El resultado fue: Banco Mundial 7/8, WHO 2/8, CEPALSTAT 1/8 y Statista 0/8.

La asociación de Spearman entre el puntaje de núcleo comparable y la tasa de exposición fue **rho = 0.80 (n = 4)**. Es una señal descriptiva, no una prueba causal: la consulta, la autoridad temática y la intención del usuario dominan el resultado. El Banco Mundial aparece con mayor frecuencia en consultas generalistas; WHO y CEPALSTAT aparecen cuando la consulta encaja con salud o América Latina; Statista no aparece en este banco orientado a estadísticas oficiales.

## Limitaciones

- El navegador interactivo no pudo inicializarse por un fallo local de cifrado de Windows; las pruebas de DOM post-JavaScript y JSON-LD se reportan como no verificadas.
- El piloto de direccionamiento usa búsqueda web como proxy de descubrimiento, no una muestra representativa de todos los agentes de IA.
- El puntaje mezcla readiness técnico y apertura comercial; por eso se reporta también el núcleo comparable y no debe leerse como calidad de datos.\n- La ficha pública y homepage de Statista no representan todo su catálogo; la comparación debe entenderse como un paquete mínimo y un piloto.\n- El piloto tiene n=4 portales y 8 consultas: requiere estratificación, repeticiones, controles por tema/paywall e intervalos antes de inferir asociación.\n- Con cuatro portales no se debe inferir causalidad ni generalizar a todo el ecosistema estadístico.

## Fuentes y evidencias

- [Informe Banco Mundial](aeo-agent-readiness-data.worldbank.org-2026-08-22.md)
- [Informe WHO Data](aeo-agent-readiness-data.who.int-2026-08-22.md)
- [Informe Statista](aeo-agent-readiness-www.statista.com-2026-08-22.md)
- [Informe CEPALSTAT](auditoria-aeo-agent-readiness-cepalstat-2026-08-20.md)
- [Registro del piloto](aeo-referral-pilot-2026-08-22.csv)
