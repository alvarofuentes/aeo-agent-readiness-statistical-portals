# AEO & AI-readiness of statistical portals — expanded audit

## Scope

The comparative universe is now five portals: World Bank Open Data, WHO Data, CEPALSTAT, UN Data Commons (UNSD), and UN SDG Indicators / Global SDG Data Platform. Statista is removed from the active comparison.

## Technical score

| Portal | Score | Interpretation |
|---|---:|---|
| UN SDG Indicators | 88 | strongest combination of API, metadata and citation infrastructure |
| UN Data Commons (UNSD) | 78 | particularly strong natural-language discovery and authoritative aggregation |
| World Bank Open Data | 77 | strong discoverability, API and machine-facing pages |
| WHO Data | 77 | strong indicator semantics and persistent identifiers |
| CEPALSTAT | 48 | strong public API, but weaker discovery, rendering and structured page representation |

These scores are evidence-based technical scores. They are **not** agent-performance scores and should not be interpreted causally.

## Directly verified strengths

CEPALSTAT's Open Data page documents a public OAS3 API and separate indicator endpoints for data, metadata, dimensions, footnotes, publications and sources. The indicator data endpoint explicitly returns data, metadata, dimensions, sources and notes. [CEPALSTAT Open Data](https://statistics.cepal.org/portal/cepalstat/open-data.html?lang=es)

WHO's Data Description Schema explicitly aims to harmonize descriptions across products and workflows, including column names, metadata, API queries and filenames. WHO also describes persistent unique indicator identifiers and URI representations for pages and APIs. [WHO data-description schema](https://data.who.int/es/about/datadot/data-description-schema) · [WHO coding and identifiers](https://data.who.int/es/about/datadot/coding-and-identifiers)

UN Data Commons publicly advertises natural-language search, country/region filtering and comparison workflows and describes itself as integrating authoritative UN-system data. [UN Data Commons](https://unstats.un.org/UNSDWebsite/undatacommons/search)

UNSD SDG documentation describes programmatic SDG API/OpenAPI access and later machine-readable SDMX reference metadata. [SDG API documentation history](https://unstats.un.org/unsd/statcom/50th-session/documents/2019-3-SG-SDG-EE.pdf) · [SDMX metadata development](https://unstats.un.org/UNSDWebsite/statcom/session_54/documents/2023-2-SDG-IAEG-EE.pdf)

## Expanded benchmark

The repository now contains a 120-instance benchmark bank covering five portal families: discovery, exact indicator selection, semantic disambiguation and comparison. The benchmark intentionally includes confusing GDP cases because statistical correctness depends on selecting among conceptually adjacent series.

The recommended production execution is 120 query instances × three repeated agent runs × five portals = up to 1,800 executions, with clustered inference by query and portal.

### Important execution limitation

This environment could directly execute web/search and official-page/API verification, but it could not launch the user's external agent harness or clone the repository into a local git working tree because outbound `git` DNS access is disabled. Therefore, no 1,800-run LLM-agent result has been fabricated. The benchmark specification is committed, and the technical audit has been expanded with directly verified evidence. The next run in a network-enabled agent runner should populate `benchmark/results-120x5x3.csv`.

## AI-readiness outcome variable

The independent experimental outcome should be scored as:

- discovery success;
- retrieval success;
- temporal/geographic correctness;
- semantic indicator correctness;
- metadata interpretation correctness;
- citation/evidence correctness.

Do not derive this outcome from the technical AEO score itself.

## Validation design

Use Spearman, Kendall, exact permutation tests at portal level, bootstrap by query template, sensitivity to AEO weighting, and leave-one-portal-out analyses. At resource level, use clustered or hierarchical models where the number of genuinely independent pages/series is adequate.

## CEPALSTAT implementation conclusions

The highest-return changes do not require rebuilding the data platform. CEPALSTAT already has a strong API layer. The priorities are:

1. canonical, crawlable indicator URLs;
2. sitemap coverage;
3. explicit machine-readable indicator pages;
4. persistent semantic identifiers;
5. AI-friendly metadata cards;
6. explicit disambiguation fields;
7. optional llms.txt-style orientation;
8. benchmark-driven before/after measurement.

## GDP semantic disambiguation

The kit includes worked examples based on current CEPALSTAT technical sheets: indicator 2203 (total GDP, current USD), 2205 (GDP per capita, current USD), 2214 (GDP per capita, constant USD, 2018 reference, expenditure dimension) and 2196 (GDP by economic activity, constant national currency). The technical sheets show materially different units and methodologies, illustrating why shortened labels are not sufficient for agent selection.
