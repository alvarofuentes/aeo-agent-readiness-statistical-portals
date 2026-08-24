# Ejecutar el benchmark multiagente en macOS + Ollama

## 1. Preparación

```bash
git checkout feat/expanded-aeo-audit-2026-08-22
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip -r benchmark/requirements.txt
```

No se requiere SDK de Ollama: el runner usa `http://127.0.0.1:11434`.

Comprobar Ollama:

```bash
ollama list
curl -s http://127.0.0.1:11434/api/tags | python3 -m json.tool
```

## 2. Preflight obligatorio

Antes de tocar Ollama o ejecutar consultas:

```bash
python benchmark/self_check.py
```

Debe terminar con `SELF-CHECK PASS`. El preflight verifica que el banco canónico contiene exactamente 120 consultas, cinco portales, la distribución declarada de estratos y los IDs Q001-Q120.

## 3. Generar el banco sólo para reproducibilidad

```bash
python benchmark/query_bank.py
python benchmark/self_check.py
```

El archivo canónico es `benchmark/query-bank-120.csv`. El runner no lo regenera silenciosamente: si falta o tiene una estructura distinta, falla antes de iniciar el benchmark.

## 4. Smoke test

Ejecutar primero una prueba pequeña:

```bash
python benchmark/ollama_multiagent.py --max-queries 5 --repeats 1
```

Revisar `benchmark/results/run_manifest.json` y `benchmark/results/results.csv`. Debe haber una fila por consulta, sin errores de conexión a Ollama y con `schema_failures=0` para una ejecución limpia.

Si el smoke test falla, **no ejecutar aún el benchmark completo**.

## 5. Benchmark completo

```bash
python benchmark/ollama_multiagent.py --repeats 3
```

Esto produce hasta 1.800 ejecuciones: 120 consultas × 5 portales × 3 repeticiones, usando evidencia web congelada por consulta/portal. La repetición 1 usa la asignación primaria; las siguientes pueden rotar el modelo de semántica/juez/adversarial cuando hay varios modelos instalados, para medir sensibilidad entre familias.

## 6. Analizar resultados

```bash
python benchmark/analyze_results.py
```

Produce:

- `benchmark/results/results.jsonl`
- `benchmark/results/results.csv`
- `benchmark/results/portal_summary.csv`
- `benchmark/results/stratum_summary.csv`
- `benchmark/results/analysis_summary.json`

También puede ejecutarse el analizador compacto:

```bash
python benchmark/analyze_agent_benchmark.py benchmark/results/results.csv
```

La asociación portal-level se calcula separadamente del AEO score con Spearman, Kendall y permutación exacta. El número de ejecuciones repetidas no se trata como observaciones independientes de portal.

## 7. Selección de modelos

Por defecto el runner busca primero modelos con `gemma` para semántica/juez/adversarial y `qwen` para retrieval. Se pueden fijar modelos explícitamente con variables `AEO_MODEL_<ROLE>` o mediante `benchmark/config.yaml`.

Ejemplo:

```bash
export AEO_MODEL_DISCOVERY='gemma4:latest'
export AEO_MODEL_SEMANTIC='gemma4:latest'
export AEO_MODEL_RETRIEVAL='qwen3:latest'
export AEO_MODEL_METADATA='gemma4:latest'
export AEO_MODEL_CITATION='qwen3:latest'
export AEO_MODEL_JUDGE='qwen3:latest'
export AEO_MODEL_ADVERSARIAL='gemma4:latest'
```

Usar los nombres exactos devueltos por `ollama list`.

## Roles

- discovery: localiza el recurso oficial.
- semantic: resuelve la elección del indicador.
- retrieval: determina si el dato puede recuperarse sin adivinar.
- metadata: valida definición/unidad/frecuencia/dimensiones.
- citation: verifica evidencia citable.
- judge: puntúa el desempeño con independencia del AEO score.
- adversarial: intenta refutar la respuesta del juez usando sólo la evidencia congelada.

## 8. Integridad de resultados

No modificar manualmente `results.jsonl` ni `results.csv`. Conservar `run_manifest.json`, que registra modelos, repeticiones y endpoint local de Ollama. Los errores de parsing/schema quedan registrados; no se reparan silenciosamente.

## 9. Cierre

Después de completar y validar el benchmark, subir el contenido de `benchmark/results/`. La fase siguiente actualizará matriz, informes y **regenerará la PPT final** exclusivamente a partir de los resultados validados. La presentación existente es una versión intermedia y no debe tratarse como el entregable final.
