---
name: aeo-agent-readiness-auditor
description: Audit public websites for AEO, AI crawler accessibility, rendering barriers, structured data, APIs, and agent readiness; for statistical/data portals also run a portal-directed end-to-end visibility test that separates query recovery from technical readiness and produces evidence-backed reports and matrices.
---

# AEO and Agent Readiness Auditor

Audit a user-supplied public website from the perspective of an autonomous AI agent and deliver a self-contained Markdown report. Prefer direct evidence over inference. Never describe a client-side tool failure as a server-side website failure.

Read [references/report-template.md](references/report-template.md) before starting the audit and use it as the report skeleton.

When the target is a statistical, open-data, indicator, catalog, or planning portal, also read [references/statistical-portal-e2e.md](references/statistical-portal-e2e.md). It defines the required portal-directed query flow, candidate/near-match handling, evidence fields, gates, and the integration schema for comparative evaluations.

## Required input

Obtain or infer:

- Primary website URL. This is required.
- Audit language. Default to the user's language.
- One representative internal page. Discover it from navigation, search results, a sitemap, or the user-provided site. Prefer a dataset, indicator, product, article, or other core entity page.
- Output location. Default to `outputs/aeo-agent-readiness-<host-slug>-<YYYY-MM-DD>.md` in the current workspace.

## Operating modes

Use one or both modes explicitly in the report:

- **Technical readiness:** the six weighted dimensions below, based only on direct evidence.
- **Operational visibility:** for data and planning portals, a natural-language query is decomposed and executed against the portal's own search/catalog/API path until a specific entity or series, value, metadata, and primary citation are recovered.

Never collapse the operational gate into the technical score. A portal can pass one concrete end-to-end query while remaining technically fragile, and a technically strong API can still fail semantic selection or citation.

Ask the user only when the primary URL is missing or when authentication, a paywall, or a material scope choice prevents a reasonable audit. Do not ask for facts that can be discovered from the site.

## Evidence model

Classify every material finding as one of:

- **Verified:** observed directly in an HTTP response, HTML source, rendered DOM, structured-data block, API response, specification, or user-supplied command output.
- **Inferred:** supported by multiple observations but not directly proven.
- **Not verified:** the required test could not be completed.
- **Not applicable:** the check does not apply to the site's purpose.

For every `Not verified` finding, preserve three additional fields: `verification_gap`
(what was not observed), `evidence_state` (for example `initial_html_not_captured`,
`rendered_dom_not_captured`, `route_declared_only`, `client_or_network_block`), and
`next_verification_action` (the smallest read-only test that would close the gap).
Never shorten a missing observation to an apparently negative finding. A report must
show the unresolved item even when the overall portal score is otherwise complete.

Follow these rules:

1. Record the audit date, exact URL, HTTP status, content type, redirect target, and relevant evidence.
2. A browser or security-client message such as “unsafe to open” is not an origin response. Mark the test **Not verified**.
3. Do not report a resource as missing unless the origin returned 404/410 or equivalent direct evidence exists.
4. Distinguish “not detected” from “absent”. Use “absent” only after inspecting the relevant source or response.
5. Cite primary sources and link directly to the audited page, official API, official specification, or official vendor documentation. Do not cite search-result pages.
6. Treat crawler names and policies as time-sensitive. Verify current user-agent tokens against official vendor documentation when internet access is available.

## Audit workflow

### 1. Establish scope and inventory

1. Normalize the supplied URL into scheme, host, base path, language, and canonical version.
2. Record redirects between HTTP/HTTPS, `www`/non-`www`, and alternate language routes when observed.
3. Identify the site's purpose, authority, publisher, primary content types, and expected agent task.
4. Select the homepage and at least one representative internal entity page.
5. If the site has distinct subdomains for content and APIs, audit bot-control files per host because robots policies are host-specific.

### 2. Layer 1 — Bot access and discovery

Request these resources on the relevant host and record status, headers, redirect chain, and body:

```text
/robots.txt
/sitemap.xml
/sitemap_index.xml
/llms.txt
```

Also:

1. Parse every `Sitemap:` declaration in `robots.txt` and test the declared URLs.
2. Test a site-specific sitemap path only when navigation, source, CMS conventions, or search evidence suggests one.
3. Parse `robots.txt` by user-agent group, longest-match behavior, `Allow`, `Disallow`, wildcards, end anchors, and conflicts.
4. Check the current official tokens for major AI search, retrieval, and training controls. Include, when current and relevant, OpenAI, Anthropic, Perplexity, Google, Microsoft, Common Crawl, and other agents requested by the user.
5. Distinguish crawler access from training controls. Do not assume every token represents an independent crawler.
6. Review sitemap coverage, canonical URLs, language alternates, last-modified dates, duplicates, parameterized URLs, and content-type segmentation.
7. Review `llms.txt` for site identity, key sections, canonical sources, API documentation, attribution, update policy, and examples.

Interpretation:

- A missing `robots.txt` normally means no restrictions are published under the Robots Exclusion Protocol; it is not itself a crawl block.
- A reachable sitemap is not automatically good: inspect whether it covers the entities an agent needs.
- A missing `llms.txt` is an agent-discovery opportunity, not a standards-compliance violation.
- Note possible WAF, rate-limit, authentication, CDN, or IP controls separately when directly observed.

For a statistical or planning portal, a homepage-only inspection is insufficient. First execute the portal-directed end-to-end flow in [references/statistical-portal-e2e.md](references/statistical-portal-e2e.md), then use the technical layers below to explain why the flow is robust or fragile.

If direct HTTP tools are unavailable, ask the user to paste the complete output of commands equivalent to:

```powershell
curl.exe -sS -L -D - https://example.org/robots.txt
curl.exe -sS -L -D - https://example.org/sitemap.xml
curl.exe -sS -L -D - https://example.org/sitemap_index.xml
curl.exe -sS -L -D - https://example.org/llms.txt
```

Do not pause other audit work while awaiting optional evidence.

### 3. Layer 2 — Rendering and interaction barriers

Compare the homepage and representative internal page in two states:

1. Initial server response without executing JavaScript.
2. Rendered DOM after JavaScript settles.

For both states, capture or count:

- HTTP status, final URL, canonical, title, meta description, headings, main-text length, links, tables, form controls, structured-data blocks, and visible key values.
- Entity name, definition, unit, period, geography, source, update date, and numeric records.
- `noscript`, hydration markers, iframe use, shadow DOM, lazy loading, and API/network dependencies when observable.

Test whether core information requires:

- Selectors, tabs, accordions, modals, pagination, “Load more”, “View more”, or “Apply” actions.
- Physical DOM clicks instead of crawlable links.
- Authentication, consent dialogs, CAPTCHA, cookies, or geolocation.
- Canvas, SVG, chart tooltips, or images without an accessible data table.
- Client-side downloads whose URL is created only after an event.

Classify the rendering pattern as server-rendered, static, hybrid, client-rendered, or not determined. Require evidence; do not infer CSR solely from the use of a JavaScript framework.

### 4. Layer 3 — Structured web markup

In this layer, `structured_data` means machine-readable metadata embedded in the
HTML/DOM itself: JSON-LD, microdata, RDFa, Open Graph, DCAT, SDMX markup, or a
domain-specific equivalent. It does **not** mean that the portal lacks
structured data when it exposes a working API, CSV/XLSX export, SDMX feed, or
JSON response. Those are tested separately under API/data access below.

Inspect initial HTML and rendered DOM for:

- JSON-LD (`application/ld+json`).
- Microdata and RDFa when present.
- Open Graph, Dublin Core, DCAT, SDMX, or domain-specific machine metadata.

For each JSON-LD block:

1. Parse it as JSON and report syntax errors with the affected page.
2. Resolve `@graph` nodes and identify relationships.
3. Check context, types, identifiers, canonical URLs, language, dates, publisher, creator, citations, license, coverage, variables, and distributions.
4. For data portals, prioritize `DataCatalog`, `Dataset`, `DataDownload`, `Organization`/`GovernmentOrganization`, `WebSite`, `SearchAction`, and `BreadcrumbList`.
5. Compare structured values against visible HTML and API metadata. Flag contradictions and stale dates.
6. Validate with an official or established validator when callable. If validation cannot run, report manual findings only.

Use “JSON-LD not detected in the inspected state” when either the initial HTML or
rendered DOM is missing. Use “JSON-LD absent” only after both initial HTML and
rendered DOM have been inspected and captured. If the initial HTML itself was not
captured, the result is `NOT_VERIFIED` with `evidence_state=initial_html_not_captured`,
not `FAIL` and not `absent`.

This status is scoped to embedded HTML/DOM markup. It does not mean that the
portal lacks structured data access through an API or CSV/XLSX/JSON download.

### 5. Layer 4 — APIs and code-agent access

Discover APIs from navigation, HTML links, network calls, developer pages, and conventional paths. Search for OpenAPI/Swagger, GraphQL, SDMX, DCAT, CSV, bulk downloads, and official SDKs.

When an API exists, assess:

- Public documentation and machine-readable specification.
- Base URL, `servers`, paths, methods, parameters, schemas, examples, `operationId`, authentication, pagination, filtering, error models, rate limits, CORS, versioning, and terms.
- Whether the agent can discover an entity ID, retrieve metadata, request records, resolve dimension codes, and preserve sources/notes.
- Human-readable filters versus opaque internal IDs.
- Direct downloads and stable content URLs.
- Consistency between examples, schemas, actual responses, and declared content types.

For statistical portals, test data export independently from embedded markup.
When the catalog, API specification, or indicator page declares a format
parameter or download control, issue one safe read-only request for a
representative indicator in each available machine-readable format (for example
CSV, XLSX/Excel, JSON, XML, or SDMX). Record HTTP status, content type,
content-disposition, file signature/parseability, indicator ID, selected
dimensions, row count, unit, source and metadata. A visible download button is
not proof of a working export until the response is downloaded and parsed. If
the request is not made, record `NOT_VERIFIED`; if it returns a validated file,
record `data_export_status=PASS` and preserve the artifact and exact request URL.
Keep `data_export_status` separate from `structured_data` and from the E2E
selection gate. A correct export with `structured_data=ABSENT` is coherent: the
portal has structured data access but lacks embedded HTML markup.

For OpenAPI 3, flag Swagger 2 fields such as top-level `host`, operation-level `produces`, or top-level `definitions` when they are used instead of the OpenAPI 3 structures. Do not label a specification invalid without either a validator result or a clearly cited structural conflict.

Run one safe read-only example request when possible. A route or identifier observed
only in JavaScript, a bundle, or a network log is `route_declared_only`; it is not
proof that an independent HTTP request works. Mark `api_direct_verified=true` only
after issuing the isolated request and validating its status, content type, payload,
requested identifier, dimensions, and provenance. If that request was not possible,
record `NOT_VERIFIED` and the verification action instead of marking the route as
missing or broken.

### 6. Citability and answer-engine test

Evaluate whether an agent can produce a citation containing:

- Exact entity or indicator name.
- Numeric value or primary claim.
- Unit and dimensions.
- Geography and period.
- Source organization and upstream source.
- Methodological notes.
- Last-updated date.
- Stable canonical URL and direct data URL.

Record any point at which the agent must guess, click, infer a dimension ID, read a chart tooltip, join disconnected pages, or use a secondary source.

For data portals, the answer-engine test must preserve the candidate list, the selected record/series, the selection rule, the retrieved value, all dimensions, source notes, and the exact URL/API request. A single specific URL is not a failure when it is the correct object for a specific query. If the model selects the wrong indicator or series because metadata did not discriminate scope, geography, unit, frequency or price base, record `MODEL_SELECTION_ERROR` with the original candidate and continue the retrieval; never silently reselect the near-match. This is a visibility/model-selection result, not `NOT_VERIFIED` and not a portal transport failure.

## Scoring

Score each dimension using only evidence collected:

| Dimension | Weight |
|---|---:|
| Bot access and governance | 10 |
| Technical discovery | 15 |
| Rendering and interaction accessibility | 20 |
| Embedded structured web markup | 15 |
| API and code-agent usability | 25 |
| Authority, attribution, and citability | 15 |

Use these readiness bands:

- 0–24: Not Ready.
- 25–49: Low or partial readiness; still Not Ready.
- 50–74: Intermediate readiness.
- 75–89: Ready with gaps.
- 90–100: Agent Ready.

Do not award points for an unverified capability. Do not assign zero merely because a tool failed; score the verified evidence and explain the confidence limitation. Provide the arithmetic in the report. The six-dimension score keeps embedded markup (`structured_data`) separate from machine-readable API/export access; the latter is scored under API/code-agent usability and must also be reported as explicit evidence fields.

The technical score is not a visibility rate and must not be correlated with a single query. If the user asks for an AEO–visibility comparison, report the portal-level unit, sample size, coverage, model/agent/repetition strata, and uncertainty; distinguish descriptive association from causality.

## Recommendations

Prioritize recommendations by implementation horizon and impact:

- **P0 / 0–2 weeks:** bot policy, sitemap, crawlable links, canonical metadata, accessible tables, `llms.txt`, direct downloads.
- **P1 / 2–6 weeks:** JSON-LD, OpenAPI repair, readable API filters, entity cross-linking, automated validation.
- **P2 / 6–12 weeks:** DCAT/SDMX, persistent identifiers, versioning, citation metadata, monitoring, and parity tests.

Each recommendation must state the barrier it fixes. Avoid generic SEO advice unrelated to agents, answer engines, data access, or citation.

## Report delivery

1. Copy the structure from [references/report-template.md](references/report-template.md).
2. Write in the user's language and define technical terms briefly.
3. Lead with the verdict and score.
4. Include a findings matrix with status and confidence.
5. Separate verified failures from unverified checks.
6. Link citations directly to primary sources near the supported claim.
7. For a statistical/data portal, include both the operational E2E section and the six-dimension technical score, plus the machine-readable technical-layer fields defined in [references/statistical-portal-e2e.md](references/statistical-portal-e2e.md).
8. Save as UTF-8 Markdown at:

```text
outputs/aeo-agent-readiness-<host-slug>-<YYYY-MM-DD>.md
```

9. Use a new dated filename; do not overwrite an existing report unless the user explicitly requests replacement.
10. Return a clickable absolute path to the completed file and, when requested, the evidence JSON/CSV or workbook used to audit it.

## Final quality checks

Before delivery, verify:

- The primary URL, audit date, language, and representative internal page are recorded.
- Every categorical absence is backed by direct evidence.
- HTTP client safety errors are not attributed to the site.
- `robots.txt`, sitemap, `llms.txt`, rendering, embedded JSON-LD/microdata, API,
  data export, and citability are all addressed.
- For data portals, the report proves or explicitly holds the full chain: natural query → decomposition → portal search/catalog → candidates → semantic selection → specific record/series → value → metadata → primary citation.
- Candidate counts, near-matches, specific-URL rate, metadata completeness, citation reproducibility, and E2E pass rate are reported separately from the technical score.
- Transport failures, client-side browser blocks, unavailable APIs, `NA`, `not_applicable`, and missing-but-validated data remain explicit; none is silently converted to zero.
- The score components add to the final score and weights add to 100.
- Recommendations map to observed barriers.
- Markdown headings, tables, code fences, links, and UTF-8 characters render correctly.
- The report is self-contained and understandable without the conversation.
