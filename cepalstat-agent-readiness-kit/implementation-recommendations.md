# CEPALSTAT implementation recommendations

## Priority 1 — Make discovery explicit

1. Publish a stable XML sitemap for the public statistical information architecture.
2. Ensure indicator pages have canonical, language-aware URLs and do not require a user session.
3. Keep the Open Data/API documentation linked from the portal root and from every indicator page.
4. Publish a concise `llms.txt`-style orientation file as a supplement, not as a substitute for robots.txt or sitemap.xml.

## Priority 2 — Turn every indicator into a canonical semantic object

Each indicator should have one stable identifier that resolves to both a human page and machine-readable metadata. WHO's approach to persistent indicator identifiers and URI representations is a useful model. The identifier should remain stable across redesigns.

## Priority 3 — Expose disambiguation metadata

Add explicit fields for unit, frequency, price basis, reference year, geography, dimensions, aggregation, population denominator and source. Add `similar_indicators`, `do_not_confuse_with`, `semantic_fingerprint` and `disambiguation_rules`.

## Priority 4 — Keep data and metadata adjacent

CEPALSTAT already exposes separate indicator endpoints for data, metadata, dimensions, sources and notes. The recommended next step is to provide one canonical response or linked representation from which an agent can recover all of these without guessing endpoint relationships.

## Priority 5 — Structured data on indicator pages

Add JSON-LD describing the statistical indicator, its publisher/custodian, identifier, definition, temporal and geographic coverage and machine-readable endpoint. This should complement, not duplicate inaccurately, the authoritative API metadata.

## Priority 6 — Design for semantic retrieval, not just keyword retrieval

Expose alternate natural-language labels and example questions for every indicator. Use controlled vocabularies for geography, unit, frequency, price basis and dimensions. Preserve exact codes in API responses.

## Priority 7 — Create an agent benchmark before and after implementation

Use the 120-query benchmark in `benchmark/query-bank-120.csv` and add a larger repeated-agent experiment before any production change. Score discovery, retrieval, semantic correctness and citation separately.

## Priority 8 — Adopt machine-readable statistical metadata standards

The UN SDG ecosystem is an important reference because it provides machine-readable metadata and structured data access through SDMX/API mechanisms. Where appropriate, CEPALSTAT should align its semantic model with SDMX concepts rather than create proprietary terminology.
