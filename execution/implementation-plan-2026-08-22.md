# Plan de implementación: relación entre AEO y visibilidad

Estado de ejecución: **HOLD metodológico antes del benchmark completo**.

La fuente de verdad es `auditoría AEO.pdf`. El README se usa solo para
inventariar artefactos. Se permite este anexo explícitamente etiquetado como
piloto; la actualización editorial de cierre sólo ocurrirá después de
regenerar los resultados derivados del benchmark de cinco portales.

## Anexo editorial del piloto operativo (no cierre final)

El piloto `pilot_cepalstat-sdg-60x2x3-20260823` se documenta como un alcance
aislado para validar el runtime y no reemplaza los 15 puntos del benchmark
canónico:

- 60 filas de plantilla × 2 portales (CEPALSTAT y UN SDG) × 3 repeticiones =
  360 ejecuciones;
- manifiesto y evidencia bajo `benchmark/results/pilot/`, con
  `production_benchmark=false`;
- gold independiente en `benchmark/gold_pilot_cepalstat_sdg_60.json`;
- análisis sólo descriptivo en `benchmark/pilot_analysis.py`;
- no habilita el Gate 13, la relación AEO–visibilidad, ni la regeneración final
  de matrices, cinco informes, PPT o README de cierre.

La etapa editorial del piloto quedó ejecutada como un paquete aislado y
diagnóstico (matrices, dos informes, informe comparativo y PPT). Su decisión
de publicación es **HOLD** porque las capturas no aceptaron URLs específicas
de series y el adversarial fue `uncertain` en las 360 filas. No se confunde con
la etapa 15 del benchmark canónico.

Advertencia: las 60 filas conservan copias de procedencia del banco heredado y
contienen 12 textos de consulta únicos. El piloto se considera completo sólo
en su mecánica (360/360), con una limitación de diversidad semántica que debe
quedar visible en cualquier mención editorial.

## Plan operativo de 15 puntos

1. Fijar el PDF como fuente de verdad y eliminar Statista del universo activo.
2. Inventariar banco, configuración, scores AEO, skills, modelos y artefactos
   históricos sin mezclarlos con la ejecución nueva; verificar
   `.agents/skills/aeo-agent-readiness-auditor/SKILL.md` y su plantilla de
   informe como skill activa del proyecto.
3. Materializar 120 IDs canónicos y conservar `template_family_id` para las
   24 familias de texto repetidas del banco heredado.
4. Expandir los IDs a cinco portales: 600 pares únicos y tres repeticiones por
   par; registrar cinco pasadas de 360.
5. Congelar la política de modelos: solo modelos locales con tamaño verificable,
   sin `:cloud` y con techo experimental de 40B tras el levantamiento explícito
   del límite de 24B; registrar digest, tamaño y probe HTTP/JSON.
6. Congelar evidencia HTTP con SERP separada, páginas del portal, candidato de
   discovery, headers, cuerpo, redirects, hashes y allowlist.
7. Ejecutar el smoke CEPALSTAT exacto del PDF en salida natural y estructurada,
   conservando ambas respuestas RAW.
8. Construir gold contracts por consulta/portal y validar manual/API los
   valores, unidades, periodos, geografía y series aceptables.
9. Definir schema tipado, dimensiones `NA`, estados de transporte y checks
   semánticos; nunca convertir schema inválido en cero.
10. Ejecutar el runner único con orquestador determinista: discovery, fetch del
    candidato, roles, juez independiente y adversarial independiente.
11. Ejecutar un smoke integral y bloquear si faltan roles, hashes, retries,
    checkpoint o allowlist.
12. Correr las cinco pasadas reanudables de 360; no sobreescribir históricos.
13. Aplicar QA de cardinalidad, duplicados, cobertura, schema, disponibilidad,
    adversarial y reproducibilidad del score recomputado.
14. Agregar por consulta/portal y portal; calcular AIRSC, sensibilidad por
    familia/estrato/modelo/repetición y asociación descriptiva AEO–AIRSC con
    `n=5` portales, sin lenguaje causal.
15. Regenerar matriz de resultados, cinco informes individuales, matriz
    comparativa, informe comparativo, toolkit CEPALSTAT y PPT; solo después
    actualizar README, execution README, instrucciones y estado del proyecto.

## Contrato del experimento

- Universo: World Bank Open Data, WHO Data, CEPALSTAT, UN Data Commons/UNSD y
  UN SDG Indicators. Statista queda fuera.
- Unidad canónica: 120 plantillas de consulta, aplicadas a cada uno de los
  cinco portales.
- Cardinalidad: `120 × 5 × 3 = 1.800` ejecuciones; cinco pasadas de 360.
- Las repeticiones son medidas agrupadas, no 1.800 observaciones independientes
  a nivel portal.
- El puntaje AEO se congela antes de ejecutar AIRSC y se une por `portal_id`.
- La hipótesis de una única URL pertinente se evalúa como resultado válido
  cuando la URL es oficial, específica y responde a la intención; no se exige
  una lista artificial de URLs.

## Gates ejecutables

1. **Alcance y cardinalidad.** Validar 120 plantillas, cinco portales, 600
   combinaciones y 1.800 filas finales; fallar cerrado ante faltantes,
   duplicados o estratos desbalanceados.
2. **Modelos.** Registrar inventario, digest, tamaño y modelo por rol. El techo
   experimental es `<=40B`; se excluyen todos los `:cloud` y tamaños
   desconocidos. El brazo canónico usa Gemma/Mistral/Llama. Qwen coder 30,5B
   queda en `config.experimental-qwen30b.yaml`: pasó la sonda mínima, pero su
   smoke contextual quedó en HOLD por timeout y no se mezcla con el canónico.
3. **Evidencia.** Congelar una captura por combinación consulta/portal,
   separando SERP, página del portal y recurso candidato. El allowlist debe
   bloquear assets de buscadores, `w3.org` y hosts ajenos al portal.
4. **Salida natural vs. estructurada.** Guardar ambas respuestas RAW y medir
   por separado utilidad semántica, pérdida de información, cumplimiento de
   schema y capacidad de recuperación. `schema_valid=false` nunca equivale a
   fallo semántico.
5. **Smoke CEPALSTAT.** Ejecutar las cinco consultas controladas del PDF con
   todos los roles y adversarial obligatorio; revisar indicador, URL, unidad,
   periodo, geografía, metadata, fuente y valor.
6. **Rúbrica y gold.** Completar estándares de oro por consulta/portal y
   calcular `overall_0_100` desde dimensiones aplicables y pesos declarados; el
   juez no puede escoger libremente el total.
7. **Runner único.** Integrar `discovery → fetch del recurso → semantic /
   retrieval / metadata / citation → judge independiente → adversarial`, con
   retries, checkpoints, hashes y manifiesto reanudable.
8. **Benchmark.** Ejecutar cinco pasadas de 360 solo cuando todos los gates
   anteriores estén en PASS. No convertir errores de transporte, recursos no
   disponibles o dimensiones `NA` en ceros.
9. **Relación estadística.** Agregar por consulta/portal y luego por portal;
   reportar Spearman, Kendall y permutación exacta con `n=5` portales, más
   sensibilidad por estrato, modelo, repetición y veredicto adversarial. El
   lenguaje será descriptivo/no causal.
10. **Entregables.** Regenerar matriz de resultados, cinco informes
    individuales, matriz comparativa, informe comparativo, toolkit CEPALSTAT y
    PPT desde resultados validados. Solo después actualizar README, execution
    README, instrucciones del benchmark y estado del proyecto.

## Criterio de desbloqueo

El benchmark completo permanece en HOLD si falla cualquiera de estos puntos:

- cardinalidad 1.800;
- evidencia fuera del allowlist;
- modelo requerido con error de transporte;
- juez no calibrado o total no reproducible;
- gold incompleto;
- join AEO–portal ambiguo;
- adversarial ausente o no auditable;
- uso de modelos sobre 40B, tamaño desconocido o `:cloud`.
