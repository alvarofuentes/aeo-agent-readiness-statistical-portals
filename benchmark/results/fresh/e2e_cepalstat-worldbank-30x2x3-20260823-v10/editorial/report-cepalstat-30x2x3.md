# Evaluación E2E y preparación AEO — cepalstat

**Fecha de evidencia:** 2026-08-23
**Run:** `e2e_cepalstat-worldbank-30x2x3-20260823-v10`

## Veredicto

La prueba operacional recuperó `PASS` en **90/90** ejecuciones (100.0%). Se registraron **0** errores de selección semántica del modelo (0.0%); esos casos conservan el indicador elegido y su recuperación, sin sustitución automática. La puntuación técnica es **50/100**, con confianza **limited** y peso no asignado de **50** por estados no verificados.

Las capas son independientes: el E2E mide recuperación de una consulta; la capa técnica mide condiciones de acceso y citabilidad. No se suman ni promedian.

## Matriz E2E

| Consulta | Repetición | Candidato | Selección | Recuperación | Valor | Metadatos | Cita | Evidencia |
|---|---:|---|---|---|---|---|---|---|
| FRESH-Q001 · Encuentra la fuente oficial para el PIB de Chile y dame la URL de la s | 1 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q002 · ¿Dónde puedo consultar oficialmente el PIB de Argentina para 2024? | 1 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q003 · Localiza el indicador oficial de PIB de Brazil y explica por qué esa p | 1 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q004 · Encuentra una página o API oficial con datos de PIB para Mexico y cita | 1 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q005 · ¿Cuál fue el PIB total de Colombia en 2024? | 1 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q006 · Dame el valor de PIB total de Peru para 2023 y 2024. | 1 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q007 · Busca la serie oficial de PIB a precios corrientes de Uruguay y devuel | 1 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q008 · ¿Qué indicador usarías para responder: PIB en dólares corrientes de Co | 1 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q009 · Para Ecuador en 2024, ¿debo usar PIB nivel o crecimiento del PIB? Expl | 1 | `2207` Tasa de crecimiento del producto interno brut | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q010 · Distingue correctamente entre PIB total y PIB por actividad económica  | 1 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q011 · Un usuario pide el tamaño de la economía de Chile. ¿Es mejor PIB total | 1 | `2205` Producto interno bruto (PIB) total anual por  | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q012 · Un usuario pide el crecimiento económico de Argentina. ¿Qué serie corr | 1 | `2207` Tasa de crecimiento del producto interno brut | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q013 · Un usuario pide una comparación internacional del PIB de Brazil. ¿Qué  | 1 | `2207` Tasa de crecimiento del producto interno brut | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q014 · Compara el PIB de Mexico entre 2023 y 2024 y conserva la misma unidad  | 1 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q015 · ¿El dato de PIB de Colombia es anual o trimestral? Verifica la frecuen | 1 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q016 · ¿El PIB de Peru está expresado en moneda nacional, USD o USD por habit | 1 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q017 · Compara el PIB de Uruguay y Costa Rica en 2024 usando una medida estad | 1 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q018 · Compara el crecimiento del PIB de Costa Rica y Ecuador en 2024. | 1 | `2207` Tasa de crecimiento del producto interno brut | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q019 · ¿Qué economía es mayor en 2024, Ecuador o Bolivia? Define la medida us | 1 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q020 · ¿Cuál es el último año disponible para el PIB de Bolivia? Indica fecha | 1 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q021 · Compara 2019, 2020 y 2024 para el PIB de Chile. | 1 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q022 · ¿Qué significa exactamente el indicador de PIB que encontraste para Ar | 1 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q023 · ¿Quién produce el dato de PIB de Brazil, cuál es la fuente y qué metod | 1 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q024 · Responde con el PIB de Mexico en 2024 y proporciona una cita o URL ver | 1 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q025 · Encuentra la fuente oficial para el PIB de Chile y dame la URL de la s | 1 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q026 · ¿Dónde puedo consultar oficialmente el PIB de Argentina para 2024? | 1 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q027 · Localiza el indicador oficial de PIB de Brazil y explica por qué esa p | 1 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q028 · Encuentra una página o API oficial con datos de PIB para Mexico y cita | 1 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q029 · ¿Cuál fue el PIB total de Colombia en 2024? | 1 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q030 · Dame el valor de PIB total de Peru para 2023 y 2024. | 1 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q001 · Encuentra la fuente oficial para el PIB de Chile y dame la URL de la s | 2 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q002 · ¿Dónde puedo consultar oficialmente el PIB de Argentina para 2024? | 2 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q003 · Localiza el indicador oficial de PIB de Brazil y explica por qué esa p | 2 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q004 · Encuentra una página o API oficial con datos de PIB para Mexico y cita | 2 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q005 · ¿Cuál fue el PIB total de Colombia en 2024? | 2 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q006 · Dame el valor de PIB total de Peru para 2023 y 2024. | 2 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q007 · Busca la serie oficial de PIB a precios corrientes de Uruguay y devuel | 2 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q008 · ¿Qué indicador usarías para responder: PIB en dólares corrientes de Co | 2 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q009 · Para Ecuador en 2024, ¿debo usar PIB nivel o crecimiento del PIB? Expl | 2 | `2207` Tasa de crecimiento del producto interno brut | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q010 · Distingue correctamente entre PIB total y PIB por actividad económica  | 2 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q011 · Un usuario pide el tamaño de la economía de Chile. ¿Es mejor PIB total | 2 | `2205` Producto interno bruto (PIB) total anual por  | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q012 · Un usuario pide el crecimiento económico de Argentina. ¿Qué serie corr | 2 | `2207` Tasa de crecimiento del producto interno brut | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q013 · Un usuario pide una comparación internacional del PIB de Brazil. ¿Qué  | 2 | `2207` Tasa de crecimiento del producto interno brut | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q014 · Compara el PIB de Mexico entre 2023 y 2024 y conserva la misma unidad  | 2 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q015 · ¿El dato de PIB de Colombia es anual o trimestral? Verifica la frecuen | 2 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q016 · ¿El PIB de Peru está expresado en moneda nacional, USD o USD por habit | 2 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q017 · Compara el PIB de Uruguay y Costa Rica en 2024 usando una medida estad | 2 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q018 · Compara el crecimiento del PIB de Costa Rica y Ecuador en 2024. | 2 | `2207` Tasa de crecimiento del producto interno brut | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q019 · ¿Qué economía es mayor en 2024, Ecuador o Bolivia? Define la medida us | 2 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q020 · ¿Cuál es el último año disponible para el PIB de Bolivia? Indica fecha | 2 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q021 · Compara 2019, 2020 y 2024 para el PIB de Chile. | 2 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q022 · ¿Qué significa exactamente el indicador de PIB que encontraste para Ar | 2 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q023 · ¿Quién produce el dato de PIB de Brazil, cuál es la fuente y qué metod | 2 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q024 · Responde con el PIB de Mexico en 2024 y proporciona una cita o URL ver | 2 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q025 · Encuentra la fuente oficial para el PIB de Chile y dame la URL de la s | 2 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q026 · ¿Dónde puedo consultar oficialmente el PIB de Argentina para 2024? | 2 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q027 · Localiza el indicador oficial de PIB de Brazil y explica por qué esa p | 2 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q028 · Encuentra una página o API oficial con datos de PIB para Mexico y cita | 2 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q029 · ¿Cuál fue el PIB total de Colombia en 2024? | 2 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q030 · Dame el valor de PIB total de Peru para 2023 y 2024. | 2 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q001 · Encuentra la fuente oficial para el PIB de Chile y dame la URL de la s | 3 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q002 · ¿Dónde puedo consultar oficialmente el PIB de Argentina para 2024? | 3 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q003 · Localiza el indicador oficial de PIB de Brazil y explica por qué esa p | 3 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q004 · Encuentra una página o API oficial con datos de PIB para Mexico y cita | 3 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q005 · ¿Cuál fue el PIB total de Colombia en 2024? | 3 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q006 · Dame el valor de PIB total de Peru para 2023 y 2024. | 3 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q007 · Busca la serie oficial de PIB a precios corrientes de Uruguay y devuel | 3 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q008 · ¿Qué indicador usarías para responder: PIB en dólares corrientes de Co | 3 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q009 · Para Ecuador en 2024, ¿debo usar PIB nivel o crecimiento del PIB? Expl | 3 | `2207` Tasa de crecimiento del producto interno brut | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q010 · Distingue correctamente entre PIB total y PIB por actividad económica  | 3 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q011 · Un usuario pide el tamaño de la economía de Chile. ¿Es mejor PIB total | 3 | `2205` Producto interno bruto (PIB) total anual por  | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q012 · Un usuario pide el crecimiento económico de Argentina. ¿Qué serie corr | 3 | `2207` Tasa de crecimiento del producto interno brut | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q013 · Un usuario pide una comparación internacional del PIB de Brazil. ¿Qué  | 3 | `2207` Tasa de crecimiento del producto interno brut | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q014 · Compara el PIB de Mexico entre 2023 y 2024 y conserva la misma unidad  | 3 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q015 · ¿El dato de PIB de Colombia es anual o trimestral? Verifica la frecuen | 3 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q016 · ¿El PIB de Peru está expresado en moneda nacional, USD o USD por habit | 3 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q017 · Compara el PIB de Uruguay y Costa Rica en 2024 usando una medida estad | 3 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q018 · Compara el crecimiento del PIB de Costa Rica y Ecuador en 2024. | 3 | `2207` Tasa de crecimiento del producto interno brut | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q019 · ¿Qué economía es mayor en 2024, Ecuador o Bolivia? Define la medida us | 3 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q020 · ¿Cuál es el último año disponible para el PIB de Bolivia? Indica fecha | 3 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q021 · Compara 2019, 2020 y 2024 para el PIB de Chile. | 3 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q022 · ¿Qué significa exactamente el indicador de PIB que encontraste para Ar | 3 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q023 · ¿Quién produce el dato de PIB de Brazil, cuál es la fuente y qué metod | 3 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q024 · Responde con el PIB de Mexico en 2024 y proporciona una cita o URL ver | 3 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q025 · Encuentra la fuente oficial para el PIB de Chile y dame la URL de la s | 3 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q026 · ¿Dónde puedo consultar oficialmente el PIB de Argentina para 2024? | 3 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q027 · Localiza el indicador oficial de PIB de Brazil y explica por qué esa p | 3 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q028 · Encuentra una página o API oficial con datos de PIB para Mexico y cita | 3 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q029 · ¿Cuál fue el PIB total de Colombia en 2024? | 3 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q030 · Dame el valor de PIB total de Peru para 2023 y 2024. | 3 | `2203` Producto interno bruto (PIB) total anual a pr | **PASS** | **PASS** | sí | completo | sí | `evidence/raw/` |

## Capa técnica

| Dimensión | Resultado | Peso |
|---|---|---:|
| discovery | PASS | 15 |
| retrieval | NOT_VERIFIED | 25 |
| rendering | PASS | 20 |
| structured_data | NOT_VERIFIED | 15 |
| authority_citation | PASS | 15 |
| accessibility | NOT_VERIFIED | 10 |

## Instancias no verificadas (ledger obligatorio)

Estas filas no significan ausencia ni fallo del portal. Identifican una observación que todavía no se capturó y la acción mínima para cerrarla.

| Check | Estado | Estado de evidencia | Evidencia observada | Brecha | Próxima acción |
|---|---|---|---|---|---|
| `jsonld_rendered_dom` | **NOT_VERIFIED** | `rendered_dom_not_captured` | Only the origin HTML response was captured by the fresh runner. | The DOM after JavaScript hydration was not captured. | Open the same representative page in an instrumented browser and save the settled DOM before classifying JSON-LD/microdata as absent. |
| `api_direct_representative_record` | **NOT_VERIFIED** | `route_declared_only` | The portal API route https://api-cepalstat.cepal.org/cepalstat/api/v1/thematic-tree?lang=es&format=json was requested for its live catalogue. | A representative indicator/record request is validated only when the E2E retrieval row is completed. | Issue one isolated GET for the selected indicator, then validate status, content type, dimensions, value and provenance. |
| `jsonld_rendered_dom` | **NOT_VERIFIED** | `rendered_dom_not_captured` | Only the origin HTML response was captured by the fresh runner. | The DOM after JavaScript hydration was not captured. | Open the same representative page in an instrumented browser and save the settled DOM before classifying JSON-LD/microdata as absent. |
| `api_direct_representative_record` | **NOT_VERIFIED** | `route_declared_only` | The portal API route https://api-cepalstat.cepal.org/cepalstat/api/v1/thematic-tree?lang=es&format=json was requested for its live catalogue. | A representative indicator/record request is validated only when the E2E retrieval row is completed. | Issue one isolated GET for the selected indicator, then validate status, content type, dimensions, value and provenance. |
| `jsonld_rendered_dom` | **NOT_VERIFIED** | `rendered_dom_not_captured` | Only the origin HTML response was captured by the fresh runner. | The DOM after JavaScript hydration was not captured. | Open the same representative page in an instrumented browser and save the settled DOM before classifying JSON-LD/microdata as absent. |
| `api_direct_representative_record` | **NOT_VERIFIED** | `route_declared_only` | The portal API route https://api-cepalstat.cepal.org/cepalstat/api/v1/thematic-tree?lang=es&format=json was requested for its live catalogue. | A representative indicator/record request is validated only when the E2E retrieval row is completed. | Issue one isolated GET for the selected indicator, then validate status, content type, dimensions, value and provenance. |

## Fuentes y trazabilidad

Cada fila conserva la URL oficial consultada, los parámetros y los JSON crudos bajo `evidence/raw/`. Las llamadas declaradas en scripts no se consideran API directa hasta validarse con una solicitud aislada.

## Limitaciones

- El DOM posterior a JavaScript no fue capturado por este runner; por eso JSON-LD/microdatos del estado renderizado quedan `NOT_VERIFIED`.
- El resultado es descriptivo de esta muestra y sus tres repeticiones; no prueba causalidad entre score técnico y visibilidad.
