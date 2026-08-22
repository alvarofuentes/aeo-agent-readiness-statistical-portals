# Ejecutar el benchmark multiagente en macOS + Ollama

## 1. Preparación

```bash
git checkout feat/expanded-aeo-audit-2026-08-22
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip pyyaml
```

No se requiere SDK de Ollama: el runner usa `http://127.0.0.1:11434`.

Comprobar Ollama:

```bash
ollama list
curl -s http://127.0.0.1:11434/api/tags | python3 -m json.tool
```

## 2. Generar el banco de 120 consultas

```bash
python benchmark/query_bank.py
```

El banco queda en `benchmark/query_bank_120.csv`.

## 3. Ejecutar primero una prueba pequeña

```bash
python benchmark/ollama_multiagent.py --max-queries 5 --repeats 1
```

Revisar `benchmark/results/run_manifest.json` para verificar los modelos detectados y asignados a cada rol.

## 4. Ejecutar el benchmark completo

```bash
python benchmark/ollama_multiagent.py --repeats 3
```

Esto produce hasta 1.800 ejecuciones: 120 consultas × 5 portales × 3 repeticiones, usando evidencia web congelada por consulta/portal.

## 5. Analizar resultados

```bash
python benchmark/analyze_results.py
```

Produce:

- `benchmark/results/results.jsonl`
- `benchmark/results/results.csv`
- `benchmark/results/portal_summary.csv`
- `benchmark/results/analysis_summary.json`

La asociación portal-level se calcula separadamente del AEO score con Spearman y permutación exacta. El número de ejecuciones repetidas no se trata como observaciones independientes.

## 6. Selección de modelos

Por defecto el runner busca primero modelos con `gemma` para semántica/juez/adversarial y `qwen` para retrieval. Se pueden fijar modelos explícitamente:

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
- adversarial: intenta refutar la respuesta.

## 7. Después de ejecutar

No modificar manualmente los resultados. Subir el contenido de `benchmark/results/` y el manifiesto de modelos. La fase siguiente actualizará automáticamente matriz, informes y PPT a partir de estos resultados.

**Importante:** la PPT final debe regenerarse después de completar este benchmark. La presentación actualmente existente es sólo una versión técnica intermedia y no debe tratarse como el entregable final validado.
