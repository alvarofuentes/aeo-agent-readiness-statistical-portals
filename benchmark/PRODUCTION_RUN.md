# Runner de producción y reanudación (histórico)

Este documento describe el contrato retirado de evidencia congelada. No usarlo
para la evaluación activa; el flujo vigente está documentado en
`benchmark/README.md` y usa `fresh_e2e_runner.py`.

El runner canónico es `benchmark/production_runner.py`. Es el único flujo que
debe producir el benchmark final; los runners históricos y los smokes quedan
separados.

## Perfil local canónico

El despliegue usa una instancia Ollama por modelo. Así se evitan descargas y
evicciones cruzadas durante los roles:

| Endpoint | Modelo | Roles | `num_predict` estructurado |
|---|---|---|---:|
| `http://127.0.0.1:11435` + `11438` | `qwen3.5:9b-mlx` | discovery, semantic, retrieval, metadata, citation (pool por rol) | 160 |
| `http://127.0.0.1:11436` | `llama3.2:latest` | adversarial | 160 |
| `http://127.0.0.1:11437` | `mistral:latest` | judge | 192 |

Parámetros comunes: `think=false`, contexto máximo de 3000 caracteres,
contexto de reintento de 1800, temperatura 0, 96 tokens para la respuesta
natural, tres repeticiones, `parallel_workers=1` por fila y
`parallel_role_workers=4` para los roles independientes. El valor de
160/192/160 de la tabla se aplica a las respuestas estructuradas por rol.

Iniciar cada servidor —en terminales separadas— con el mismo directorio local
de modelos y `OLLAMA_MAX_LOADED_MODELS=3`:

```bash
OLLAMA_HOST=127.0.0.1:11435 \
OLLAMA_MODELS=/Volumes/CorgDisk/ollama-data/models \
OLLAMA_MAX_LOADED_MODELS=3 ollama serve
```

```bash
OLLAMA_HOST=127.0.0.1:11436 \
OLLAMA_MODELS=/Volumes/CorgDisk/ollama-data/models \
OLLAMA_MAX_LOADED_MODELS=3 ollama serve
```

```bash
OLLAMA_HOST=127.0.0.1:11437 \
OLLAMA_MODELS=/Volumes/CorgDisk/ollama-data/models \
OLLAMA_MAX_LOADED_MODELS=3 ollama serve
```

La asignación de modelos y endpoints está en `benchmark/config.yaml`. El
techo de política es 40B para modelos locales con tamaño conocido; los
modelos `:cloud` y tamaños no verificados se rechazan. No iniciar
`qwen3-coder:30b-a3b-q4_K_M`: se excluyó del canónico por riesgo de OOM.

## Preflight sin modelos

```bash
python3 benchmark/production_runner.py --plan
```

Debe informar 120 plantillas, 600 pares, cinco pasadas de 360 y 1.800
ejecuciones, con `status: PASS` para cardinalidad, política y gold.

## Preflight con los tres endpoints

Con los tres servidores activos:

```bash
python3 benchmark/production_runner.py --execute --plan
```

Este paso debe confirmar HTTP/JSON para Qwen 9B en 11435, Llama en 11436 y
Mistral en 11437. Las sondas no se incorporan al resultado. El preflight del
nuevo despliegue es obligatorio porque el Qwen 9B había fallado con HTTP 500 en
un endpoint anterior.

## Smoke diagnóstico

Sólo para diagnóstico, nunca para publicar resultados:

```bash
python3 benchmark/production_runner.py \
  --execute --allow-incomplete-gold --max-executions 1 \
  --only-passes 1 --run-id gate-smoke-YYYYMMDD --resume
```

## Benchmark final

El gold pair-level está cerrado en
`benchmark/gold_standards_final_2026-08-23.json`. Después de confirmar el
preflight de los tres endpoints, ejecutar o reanudar el brazo canónico:

```bash
python3 benchmark/production_runner.py \
  --execute --run-id production-YYYYMMDD --resume
```

El resultado se escribe en `benchmark/results/production/<run-id>/`:

- `evidence/` y `raw_http/`: evidencia congelada y cuerpos HTTP;
- `results.jsonl`: outputs naturales, estructurados, judge y adversarial;
- `checkpoint.json`: claves completadas para reanudar;
- `run_manifest.json`: modelos, endpoints, hashes, cardinalidad, parámetros de
  runtime y estado.

La ejecución completa aún no está validada. No ejecutar análisis ni generar
entregables editoriales a partir de una corrida con `HOLD_INTERRUPTED`, con
menos de 1.800 filas o con schema inválido en algún rol.

## Qwen coder 30B: trazabilidad, no ejecución

`benchmark/config.experimental-qwen30b.yaml` conserva el diseño de una prueba
anterior, pero no debe ejecutarse en este perfil. La condición Qwen coder no
demostró throughput con contexto real y el hardware presentó riesgo de OOM.
Sus resultados no se incorporan al benchmark canónico.

La clave de ejecución es `pass<1..5>__Q<id>__<portal>__repeat<1..3>`. Una
interrupción deja el manifiesto en `HOLD`; no se convierten fallos de modelo ni
fallos de schema en ceros.
