# Plan operativo de 15 gates: AEO técnico y visibilidad de agentes

Fecha de corte: 2026-08-22/23  
Fuente de verdad: `auditoría AEO.pdf`  
Orquestador: proceso Python determinista  
Adversarial: rol obligatorio posterior al juez  
Política de modelos: solo Ollama local, sin `:cloud` ni tamaños desconocidos;
el límite histórico de 24B fue levantado por el usuario. El techo experimental
actual es 40B. El brazo canónico usa Qwen 3.5 9B MLX con réplicas controladas,
Mistral como juez y Llama como adversarial; Qwen coder 30B queda como brazo
experimental separado porque su smoke de contexto real presentó riesgo de OOM.

## Contrato de ejecución

El banco fuente conserva 120 instancias `Q001`–`Q120`. El banco materializado
`benchmark/query-bank-expanded-600.csv` aplica cada instancia a los cinco
portales. El runner reanudable ejecuta tres repeticiones por combinación:

```text
120 consultas × 5 portales = 600 pares consulta/portal
600 pares × 3 repeticiones = 1.800 ejecuciones
1 pasada de portal = 120 × 3 = 360 ejecuciones
```

La unidad portal-level para la relación AEO-visibilidad sigue siendo el portal
(`n=5`), no las 1.800 filas.

## Alcance piloto aislado

El piloto `pilot_cepalstat-sdg-60x2x3-20260823` valida el despliegue actual en
dos portales sin alterar este contrato:

```text
60 filas de plantilla × 2 portales × 3 repeticiones = 360 ejecuciones
```

Su estado `COMPLETE` significa únicamente que cerró sus 360 claves en
`benchmark/results/pilot/`. El manifiesto marca `production_benchmark=false`.
Además, las 60 filas contienen 12 textos únicos por copias de procedencia del
banco heredado; por ello el piloto tiene una limitación de diversidad
semántica y no es una muestra de 60 intenciones independientes.

El piloto puede documentar transporte, evidencia, schema, juez y adversarial
como diagnóstico. No cambia los criterios de los Gates 3, 10 o 13 del
benchmark canónico y no habilita análisis portal-level con `n=5`.

La fase editorial aislada sí se materializó bajo el run del piloto (matriz de
resultados, matriz comparativa, dos informes, informe comparativo y PPT). Su
estado de publicación es **HOLD**: la evidencia congelada aceptó 0 URLs
específicas de series y los veredictos adversariales fueron `uncertain` en las
360 filas. Esto no cierra los Gates 14–15 canónicos.

## Gates y checkpoints

| # | Gate | Criterio de avance | Estado actual | Checkpoint |
|---:|---|---|---|---|
| 1 | Fuente de verdad y alcance | PDF leído; cinco portales activos; Statista fuera | PASS | `auditoría AEO.pdf` |
| 2 | Banco canónico y skill | 120 IDs contiguos, estratos/columnas válidos y skill `aeo-agent-readiness-auditor` presente | PASS | `benchmark/self_check.py`; `.agents/skills/aeo-agent-readiness-auditor/SKILL.md` |
| 3 | Cardinalidad materializada | 600 pares únicos y 1.800 ejecuciones declaradas | PASS | `benchmark/cardinality_check.py` |
| 4 | Política de modelos | Inventario local; modelos locales verificables, techo experimental `<=40B`; `:cloud` excluido | PASS | `benchmark/model_policy.py` |
| 5 | Transporte de modelos | Cada modelo elegido responde a `/api/chat` dentro del timeout | PASS aislado en piloto Qwen/Mistral/Llama; pendiente confirmación de corrida canónica | `benchmark/results/pilot/pilot_cepalstat-sdg-60x2x3-20260823/run_manifest.json` |
| 6 | Evidencia y allowlist | Evidencia congelada por par; URLs solo del portal; hash reproducible | PASS aislado en piloto / pendiente final | `benchmark/results/pilot/.../evidence/`; `ollama_multiagent.py` |
| 7 | Smoke World Bank | Cinco consultas históricas ejecutadas; outputs RAW y errores conservados | PASS histórico | `benchmark/results/` |
| 8 | Smoke CEPALSTAT | Cinco casos del PDF y comparación libre/JSON | PASS diagnóstico | `benchmark/results/pdf_cepalstat_natural_vs_structured_2026-08-22.json` |
| 9 | Decisión de schema | Separar schema compliance, utilidad semántica, retrieval y corrección | PASS diagnóstico | envelope normalizado; score recomputado y `NA` conservado |
| 10 | Gold standards | Casos esperados por consulta/portal y reglas de `NA` completas | PASS | `benchmark/gold_standards_final_2026-08-23.json` cubre 600 pares; valores validados y `not_applicable` explícitos |
| 11 | Runner integrado | discovery → fetch → semantic → retrieval → metadata → citation → judge → adversarial; checkpoints | PASS estructural / PASS piloto / pendiente final | `benchmark/production_runner.py`; `benchmark/pilot_analysis.py` |
| 12 | Smoke final | Al menos World Bank y CEPALSTAT pasan con el runner final; sin transporte roto | PASS parcial; piloto separado | World Bank histórico y piloto CEPALSTAT/SDG; no sustituye el smoke de cinco portales |
| 13 | Benchmark completo | Cinco pasadas de 360; manifiesto completo con 1.800 claves únicas | HOLD — el piloto no lo completa | `benchmark/results/pilot/...` es sólo piloto; falta `benchmark/results/production/<run-final>/` |
| 14 | Análisis y entregables | Agregación agrupada, pruebas exactas y resultados por portal/modelo/estrato | PENDIENTE DEL GATE 13 | `benchmark/production_analysis.py`; `execution/build_deliverables.py` |
| 15 | Documentación final | PPT, matrices, informes y toolkit actualizados; README/estado actualizados al final | PENDIENTE DEL GATE 14 | `execution/finalize_after_run.sh` |

## Runner y reanudación

El runner [`benchmark/production_runner.py`](../benchmark/production_runner.py)
materializa/valida el contrato, registra el orquestador, exige adversarial,
reutiliza evidencia congelada y guarda checkpoints por pasada y una clave única:

```text
execution_key = query_id | portal_id | repeat
```

Los checkpoints se guardan en:

- `benchmark/results/reentrant/results.jsonl`: resultado RAW y salida plana.
- `benchmark/results/reentrant/results.csv`: vista tabular regenerable.
- `benchmark/results/reentrant/run_manifest.json`: modelos, conteo, estado y
  última clave completada.

La reanudación omite únicamente claves ya escritas. Una línea JSONL malformada,
una clave duplicada o un error de modelo deja el manifiesto en `hold`; no se
reparan resultados silenciosamente.

## Criterios de parada

No se autoriza el Gate 13 si falla cualquiera de estos criterios:

1. cardinalidad distinta de 1.800;
2. modelo seleccionado sin tamaño local verificado, modelo `>40B` o `:cloud`;
3. error de transporte no clasificado como `model_unavailable`;
4. schema artificial tratado como medida de corrección;
5. gold standards incompletos para la combinación consultada;
6. evidencia fuera del allowlist, sin hash o mezclada entre repeticiones;
7. juez sin reglas reproducibles de scoring;
8. adversarial ausente, no RAW o no auditable;
9. join AEO–portal ambiguo;
10. resultados de una ejecución parcial presentados como benchmark completo.

La hipótesis de una sola URL pertinente se considera válida cuando la URL es
oficial, específica para la intención y suficiente para el siguiente paso. Se
reportan por separado `portal_discovered`, `specific_resource_discovered` y
`value_retrieved`; no se penaliza la ausencia de una lista artificial de URLs.

## Orden de cierre

Después de cerrar los gates 5, 9, 10 y 12, ejecutar las cinco pasadas. Luego:

1. analizar por consulta/portal y agregar a cinco portales;
2. rehacer matriz de resultados;
3. rehacer cinco informes individuales;
4. rehacer matriz comparativa e informe comparativo;
5. regenerar la PPT final;
6. como última etapa, actualizar README, execution README, instrucciones,
   estado de gates y demás documentos del proyecto.

El benchmark parcial histórico queda en `HOLD` y no debe alimentar conclusiones
finales ni la correlación AEO-visibilidad. El piloto CEPALSTAT/UN SDG puede
alimentar únicamente el anexo descriptivo del piloto, con su limitación de 12
textos únicos, y debe permanecer fuera de matrices, informes y PPT finales.

## Actualización de ejecución live — 2026-08-24

La directiva fue implementada en `benchmark/fresh_e2e_runner.py` y aplicada a
tres corridas limpias: CEPALSTAT/WB (180), WHO aislado (90) y UNData/SDG (180),
450 filas en total. El runner consulta catálogo y serie en cada repetición,
conserva la selección original del modelo, registra `MODEL_SELECTION_ERROR` y
detiene ante `NOT_VERIFIED` limpio o cero observaciones después de dos intentos.
Un reset SDG transitorio activó la compuerta en v4, fue verificado con GET
aislado HTTP 200, se añadió retry para resets y se relanzó v5 desde cero.

La fase editorial final (matriz, cinco informes, comparativo, recomendaciones,
planilla y PPT) se materializó bajo
`benchmark/results/fresh/e2e_undata-sdg-30x2x3-20260823-v5/editorial/` y los
documentos se actualizaron sólo después del QA visual. El contrato canónico
1.800 del PDF queda como ampliación futura; no se afirma que esta fase lo haya
ejecutado.
