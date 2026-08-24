# Entregables v2 · portal de planificación

Esta carpeta contiene una evaluación rehecha desde evidencia primaria fresca. No se reciclaron los scores ni las conclusiones de las entregas anteriores.

## Entregables

- `aeo-agent-readiness-observatorioplanificacion.cepal.org-v2.md` — informe técnico y prueba end-to-end.
- `aeo-agent-readiness-observatorioplanificacion-v2.docx` — versión Word renderizada y revisada visualmente.
- `aeo-agent-readiness-observatorioplanificacion-v2.pptx` — deck de 10 slides, con el diseño heredado del deck original del 22 de agosto.
- `aeo-planning-evaluation-v2.xlsx` — planilla auditable con resumen, traza E2E, candidatos, QA, fuentes y capa técnica.
- `evidence/planning-e2e-2026-08-23.json` — evidencia primaria estructurada.
- `statistical-portals-technical-layer-v2.csv` / `.json` — contrato de integración para rehacer los cinco portales estadísticos sin mezclar score técnico y visibilidad operacional.

Los archivos Word, Excel y PowerPoint son salidas locales regenerables y no se
versionan en Git; el Markdown, CSV, JSON y la evidencia estructurada quedan
como artefactos portables.

## Alcance

El gate E2E pasó en una consulta representativa (`Plan Nacional de Desarrollo 2025-2029 Ecuador`). El score técnico v2 es 40/100. La API HTTP independiente y el HTML inicial quedan explícitamente no verificados en esta pasada.
