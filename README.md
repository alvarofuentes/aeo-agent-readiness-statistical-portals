# AEO y AI readiness de portales estadísticos

Repositorio reproducible de la evaluación comparada de cuatro portales estadísticos globales:

- Banco Mundial (`data.worldbank.org`)
- WHO Data (`data.who.int`)
- Statista (`statista.com`)
- CEPALSTAT (`statistics.cepal.org`)

El proyecto aplica la habilidad `aeo-agent-readiness-auditor` en seis dimensiones: bots/gobernanza, descubrimiento, renderizado, datos estructurados, API para agentes de código y autoridad/citabilidad.

## Entregables

- `outputs/aeo-agent-readiness-*.md`: informes por portal.
- `outputs/aeo-comparative-report-2026-08-22.md`: comparación ejecutiva.
- `outputs/aeo-comparative-matrix-2026-08-22.csv`: matriz cuantitativa completa y armonizada.
- `outputs/aeo-referral-pilot-2026-08-22.csv`: resultados del piloto de direccionamiento.
- `outputs/aeo-referral-pilot-analysis-2026-08-22.py`: cálculo reproducible, incluido Spearman.
- `outputs/aeo-referral-pilot-analysis-2026-08-22.ipynb`: notebook companion; requiere Jupyter.
- `outputs/aeo-comparative-deck-2026-08-22.pptx`: presentación final.
- `audit_evidence/`: evidencia HTTP archivada de la evaluación previa.
- `tools/audit_http.py`: utilidad de captura HTTP.
- `tools/build_comparative_deck.mjs`: builder portable de la presentación.

## Reproducir el piloto

```powershell
python outputs/aeo-referral-pilot-analysis-2026-08-22.py
```

Resultado de referencia: exposición Banco Mundial 0,875; WHO 0,250; Statista 0,000; CEPALSTAT 0,125; Spearman rho = 0,800 (n=4 portales, 8 consultas). Es una señal exploratoria y no causal.

## Regenerar la PPT

El builder usa `@oai/artifact-tool` y Node.js. En el entorno de escritorio de Codex se deben configurar `RUNTIME_NODE`, `RUNTIME_NODE_MODULES` y `RUNTIME_BIN_DIR` según las dependencias locales, y ejecutar desde la raíz:

```powershell
node tools/build_comparative_deck.mjs
```

## Repetir la evaluación completa

En un computador con navegador automatizable y acceso HTTP sin las restricciones de este entorno:

1. Repetir cada auditoría con el skill `aeo-agent-readiness-auditor`.
2. Verificar directamente `robots.txt`, `sitemap.xml`, `llms.txt`, headers, DOM post-JavaScript y JSON-LD.
3. Mantener la puntuación estricta de seis dimensiones y documentar estados `Verified`, `Inferred` y `Not verified`.
4. Reportar además el núcleo armonizado (`D2 + D5 + D6`) para comparabilidad histórica.
5. Ampliar el piloto a 40–60 consultas estratificadas, varios agentes y controles por tema, autoridad, idioma y paywall.
6. Congelar fecha, URLs y evidencia antes de comparar cambios.

## Limitaciones conocidas

La ejecución original no pudo inicializar el navegador interactivo por un error local de cifrado de Windows. Por eso bots, DOM y JSON-LD se trataron como no verificables de forma equivalente y se reportó una sensibilidad armonizada. Statista también requiere separar preparación técnica de apertura comercial.

No se incluyen credenciales, tokens ni datos personales en este repositorio.