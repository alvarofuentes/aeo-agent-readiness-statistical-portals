# Agent retrieval execution status

## What was actually executed in this environment

- Expanded the technical five-portal audit with current public web evidence.
- Verified CEPALSTAT's current public OAS3 API documentation and indicator endpoint families.
- Verified WHO's current Data Description Schema and persistent identifier/URI approach.
- Verified UN Data Commons natural-language discovery and comparison positioning.
- Verified UNSD SDG API/OpenAPI and machine-readable SDMX metadata evidence.
- Ran live search-engine discovery probes for representative GDP queries; World Bank returned directly indexable comparison pages with current GDP, GDP per capita and GDP growth fields and CSV/XML/Excel download options.
- Created the full 120-instance cross-portal benchmark bank.

## What was intentionally not fabricated

The full 1,800-run agent experiment (120 query instances × 5 portals × 3 repeats) requires an independent agent runner with the target models/harnesses. This runtime can browse the web but cannot launch that external harness. The repository therefore contains the benchmark specification but does not invent agent success/failure labels.

## Required next experiment

Run the 120 queries against at least two independent agent configurations, three repeats per query/portal, capturing:
- discovery_success
- retrieval_success
- semantic_correctness
- metadata_correctness
- citation_correctness
- final_answer_score
- latency
- tokens/tool calls where available

Then estimate association between technical AEO score and the independent AIRSC outcome with query/portal clustering.
