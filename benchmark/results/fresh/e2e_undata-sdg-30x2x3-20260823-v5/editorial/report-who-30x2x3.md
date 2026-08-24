# Evaluación E2E y preparación AEO — who

**Fecha de evidencia:** 2026-08-24
**Run:** `e2e_undata-sdg-30x2x3-20260823-v5`

## Veredicto

La prueba operacional recuperó `PASS` en **0/90** ejecuciones (0.0%). Se registraron **8** errores de selección semántica del modelo (8.9%); esos casos conservan el indicador elegido y su recuperación, sin sustitución automática. La puntuación técnica es **85/100**, con confianza **high** y peso no asignado de **0** por estados no verificados.

Las capas son independientes: el E2E mide recuperación de una consulta; la capa técnica mide condiciones de acceso y citabilidad. No se suman ni promedian.

## Matriz E2E

| Consulta | Repetición | Candidato | Selección | Recuperación | Valor | Metadatos | Cita | Evidencia |
|---|---:|---|---|---|---|---|---|---|
| FRESH-Q001 · Encuentra la fuente oficial para el PIB de Chile y dame la URL de la s | 1 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q002 · ¿Dónde puedo consultar oficialmente el PIB de Argentina para 2024? | 1 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q003 · Localiza el indicador oficial de PIB de Brazil y explica por qué esa p | 1 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q004 · Encuentra una página o API oficial con datos de PIB para Mexico y cita | 1 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q005 · ¿Cuál fue el PIB total de Colombia en 2024? | 1 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q006 · Dame el valor de PIB total de Peru para 2023 y 2024. | 1 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q007 · Busca la serie oficial de PIB a precios corrientes de Uruguay y devuel | 1 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q008 · ¿Qué indicador usarías para responder: PIB en dólares corrientes de Co | 1 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q009 · Para Ecuador en 2024, ¿debo usar PIB nivel o crecimiento del PIB? Expl | 1 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q010 · Distingue correctamente entre PIB total y PIB por actividad económica  | 1 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q011 · Un usuario pide el tamaño de la economía de Chile. ¿Es mejor PIB total | 1 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_SELECTION_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q012 · Un usuario pide el crecimiento económico de Argentina. ¿Qué serie corr | 1 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q013 · Un usuario pide una comparación internacional del PIB de Brazil. ¿Qué  | 1 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q014 · Compara el PIB de Mexico entre 2023 y 2024 y conserva la misma unidad  | 1 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q015 · ¿El dato de PIB de Colombia es anual o trimestral? Verifica la frecuen | 1 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q016 · ¿El PIB de Peru está expresado en moneda nacional, USD o USD por habit | 1 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q017 · Compara el PIB de Uruguay y Costa Rica en 2024 usando una medida estad | 1 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q018 · Compara el crecimiento del PIB de Costa Rica y Ecuador en 2024. | 1 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q019 · ¿Qué economía es mayor en 2024, Ecuador o Bolivia? Define la medida us | 1 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q020 · ¿Cuál es el último año disponible para el PIB de Bolivia? Indica fecha | 1 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q021 · Compara 2019, 2020 y 2024 para el PIB de Chile. | 1 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q022 · ¿Qué significa exactamente el indicador de PIB que encontraste para Ar | 1 | `GHED_GGHE-DGDP_SHA2011` Domestic general government health expenditur | **MODEL_SELECTION_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q023 · ¿Quién produce el dato de PIB de Brazil, cuál es la fuente y qué metod | 1 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q024 · Responde con el PIB de Mexico en 2024 y proporciona una cita o URL ver | 1 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q025 · Encuentra la fuente oficial para el PIB de Chile y dame la URL de la s | 1 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q026 · ¿Dónde puedo consultar oficialmente el PIB de Argentina para 2024? | 1 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q027 · Localiza el indicador oficial de PIB de Brazil y explica por qué esa p | 1 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q028 · Encuentra una página o API oficial con datos de PIB para Mexico y cita | 1 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q029 · ¿Cuál fue el PIB total de Colombia en 2024? | 1 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q030 · Dame el valor de PIB total de Peru para 2023 y 2024. | 1 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q001 · Encuentra la fuente oficial para el PIB de Chile y dame la URL de la s | 2 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q002 · ¿Dónde puedo consultar oficialmente el PIB de Argentina para 2024? | 2 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q003 · Localiza el indicador oficial de PIB de Brazil y explica por qué esa p | 2 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q004 · Encuentra una página o API oficial con datos de PIB para Mexico y cita | 2 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q005 · ¿Cuál fue el PIB total de Colombia en 2024? | 2 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q006 · Dame el valor de PIB total de Peru para 2023 y 2024. | 2 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q007 · Busca la serie oficial de PIB a precios corrientes de Uruguay y devuel | 2 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q008 · ¿Qué indicador usarías para responder: PIB en dólares corrientes de Co | 2 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q009 · Para Ecuador en 2024, ¿debo usar PIB nivel o crecimiento del PIB? Expl | 2 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q010 · Distingue correctamente entre PIB total y PIB por actividad económica  | 2 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q011 · Un usuario pide el tamaño de la economía de Chile. ¿Es mejor PIB total | 2 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_SELECTION_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q012 · Un usuario pide el crecimiento económico de Argentina. ¿Qué serie corr | 2 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q013 · Un usuario pide una comparación internacional del PIB de Brazil. ¿Qué  | 2 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q014 · Compara el PIB de Mexico entre 2023 y 2024 y conserva la misma unidad  | 2 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q015 · ¿El dato de PIB de Colombia es anual o trimestral? Verifica la frecuen | 2 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q016 · ¿El PIB de Peru está expresado en moneda nacional, USD o USD por habit | 2 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q017 · Compara el PIB de Uruguay y Costa Rica en 2024 usando una medida estad | 2 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q018 · Compara el crecimiento del PIB de Costa Rica y Ecuador en 2024. | 2 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q019 · ¿Qué economía es mayor en 2024, Ecuador o Bolivia? Define la medida us | 2 | `GHED_GGHE-DGDP_SHA2011` Domestic general government health expenditur | **MODEL_SELECTION_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q020 · ¿Cuál es el último año disponible para el PIB de Bolivia? Indica fecha | 2 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q021 · Compara 2019, 2020 y 2024 para el PIB de Chile. | 2 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q022 · ¿Qué significa exactamente el indicador de PIB que encontraste para Ar | 2 | `GHED_GGHE-DGDP_SHA2011` Domestic general government health expenditur | **MODEL_SELECTION_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q023 · ¿Quién produce el dato de PIB de Brazil, cuál es la fuente y qué metod | 2 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q024 · Responde con el PIB de Mexico en 2024 y proporciona una cita o URL ver | 2 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q025 · Encuentra la fuente oficial para el PIB de Chile y dame la URL de la s | 2 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q026 · ¿Dónde puedo consultar oficialmente el PIB de Argentina para 2024? | 2 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q027 · Localiza el indicador oficial de PIB de Brazil y explica por qué esa p | 2 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q028 · Encuentra una página o API oficial con datos de PIB para Mexico y cita | 2 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q029 · ¿Cuál fue el PIB total de Colombia en 2024? | 2 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q030 · Dame el valor de PIB total de Peru para 2023 y 2024. | 2 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q001 · Encuentra la fuente oficial para el PIB de Chile y dame la URL de la s | 3 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q002 · ¿Dónde puedo consultar oficialmente el PIB de Argentina para 2024? | 3 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q003 · Localiza el indicador oficial de PIB de Brazil y explica por qué esa p | 3 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q004 · Encuentra una página o API oficial con datos de PIB para Mexico y cita | 3 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q005 · ¿Cuál fue el PIB total de Colombia en 2024? | 3 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q006 · Dame el valor de PIB total de Peru para 2023 y 2024. | 3 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q007 · Busca la serie oficial de PIB a precios corrientes de Uruguay y devuel | 3 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q008 · ¿Qué indicador usarías para responder: PIB en dólares corrientes de Co | 3 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q009 · Para Ecuador en 2024, ¿debo usar PIB nivel o crecimiento del PIB? Expl | 3 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q010 · Distingue correctamente entre PIB total y PIB por actividad económica  | 3 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q011 · Un usuario pide el tamaño de la economía de Chile. ¿Es mejor PIB total | 3 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_SELECTION_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q012 · Un usuario pide el crecimiento económico de Argentina. ¿Qué serie corr | 3 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q013 · Un usuario pide una comparación internacional del PIB de Brazil. ¿Qué  | 3 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q014 · Compara el PIB de Mexico entre 2023 y 2024 y conserva la misma unidad  | 3 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q015 · ¿El dato de PIB de Colombia es anual o trimestral? Verifica la frecuen | 3 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q016 · ¿El PIB de Peru está expresado en moneda nacional, USD o USD por habit | 3 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q017 · Compara el PIB de Uruguay y Costa Rica en 2024 usando una medida estad | 3 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q018 · Compara el crecimiento del PIB de Costa Rica y Ecuador en 2024. | 3 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q019 · ¿Qué economía es mayor en 2024, Ecuador o Bolivia? Define la medida us | 3 | `GHED_GGHE-DGDP_SHA2011` Domestic general government health expenditur | **MODEL_SELECTION_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q020 · ¿Cuál es el último año disponible para el PIB de Bolivia? Indica fecha | 3 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q021 · Compara 2019, 2020 y 2024 para el PIB de Chile. | 3 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q022 · ¿Qué significa exactamente el indicador de PIB que encontraste para Ar | 3 | `GHED_GGHE-DGDP_SHA2011` Domestic general government health expenditur | **MODEL_SELECTION_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q023 · ¿Quién produce el dato de PIB de Brazil, cuál es la fuente y qué metod | 3 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q024 · Responde con el PIB de Mexico en 2024 y proporciona una cita o URL ver | 3 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q025 · Encuentra la fuente oficial para el PIB de Chile y dame la URL de la s | 3 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q026 · ¿Dónde puedo consultar oficialmente el PIB de Argentina para 2024? | 3 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q027 · Localiza el indicador oficial de PIB de Brazil y explica por qué esa p | 3 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q028 · Encuentra una página o API oficial con datos de PIB para Mexico y cita | 3 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q029 · ¿Cuál fue el PIB total de Colombia en 2024? | 3 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |
| FRESH-Q030 · Dame el valor de PIB total de Peru para 2023 y 2024. | 3 | `GHED_CHEGDP_SHA2011` Current health expenditure (CHE) as percentag | **MODEL_RESPONSE_ERROR** | **PASS** | sí | completo | sí | `evidence/raw/` |

## Capa técnica

| Dimensión | Resultado | Peso |
|---|---|---:|
| Descubrimiento técnico (`discovery`) | PASS | 15 |
| API y acceso de datos (`retrieval`) | PASS | 25 |
| Renderizado/interacción (`rendering`) | PASS | 20 |
| Marcado HTML estructurado (`structured_data`) | ABSENT | 15 |
| Autoridad/cita (`authority_citation`) | PASS | 15 |
| Accesibilidad (`accessibility`) | PASS | 10 |

## Instancias no verificadas (ledger obligatorio)

Estas filas no significan ausencia ni fallo del portal. Identifican una observación que todavía no se capturó y la acción mínima para cerrarla.

| Check | Estado | Estado de evidencia | Evidencia observada | Brecha | Próxima acción |
|---|---|---|---|---|---|
| — | — | — | No quedaron instancias no verificadas en el ledger. | — | — |

## Acceso estructurado y exportación

`structured_data=ABSENT` se refiere exclusivamente a marcado embebido en HTML/DOM (JSON-LD, microdatos o equivalente). No significa que el portal carezca de datos estructurados. La prueba de exportación independiente queda en **NOT_TESTED**, formatos ****, con selección preservada **NOT_TESTED**; evidencia: `no probada en este run`.

## Fuentes y trazabilidad

Cada fila conserva la URL oficial consultada, los parámetros y los JSON crudos bajo `evidence/raw/`. La capa técnica incluye una captura del DOM asentado después de JavaScript y una solicitud aislada del registro representativo.

## Limitaciones

- `ABSENT` significa que la comprobación se ejecutó y no encontró el artefacto embebido (por ejemplo, JSON-LD o robots.txt); no equivale a `NOT_VERIFIED` ni a ausencia de API/exportación.
- El resultado es descriptivo de esta muestra y sus tres repeticiones; no prueba causalidad entre score técnico y visibilidad.
