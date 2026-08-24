# Statistical and planning portal mode

Use this protocol whenever the target is a statistical portal, open-data catalog, indicator database, planning catalog, SDG portal, or any site where the user expects an agent to find a specific observation or record.

## Why this mode exists

A homepage audit cannot establish data visibility. The user asks a model for an observation; the model decomposes the request, searches the portal, resolves candidates, retrieves the record or series, and cites it. The test must reproduce that chain. The technical audit then explains whether the portal makes that chain durable for agents and code.

Report two independent outcomes:

1. **Operational visibility gate:** did this query reach the correct portal object and produce a value/record with complete context and a primary citation?
2. **Technical readiness score:** how accessible, discoverable, renderable, structured, API-ready, and citable is the portal under the six-dimension rubric?

Do not average, add, or substitute one outcome for the other.

### Structured markup is not the same as structured data access

Keep these findings separate in every statistical-portal evaluation:

- `structured_data` / embedded structured markup: JSON-LD, microdata, RDFa,
  DCAT/SDMX markup or equivalent embedded in the initial HTML or settled DOM.
- `api_direct_verified`: an isolated API request returned the requested object,
  dimensions, metadata and provenance.
- `data_export_status`: an isolated CSV/XLSX/JSON/XML/SDMX download returned a
  parseable artifact for a representative indicator. Record the exact request,
  content type, artifact hash, selected dimensions and whether the selection is
  preserved in the file.

An API or XLSX download is structured machine-readable access even when the
HTML has no JSON-LD or microdata. Therefore `structured_data=ABSENT` must be
worded as “embedded markup absent in the inspected HTML/DOM”, never as “the
portal has no structured data”. A download control alone is not evidence:
complete one bounded request and parse the returned artifact before marking
`data_export_status=PASS`.

## Required end-to-end flow

For each representative query:

1. **Receive the natural question.** Preserve the exact user wording.
2. **Decompose it.** Record entity/indicator, geography, period, unit, frequency, price base, sex/age/measure, source, content type, and any other dimensions. Mark unresolved fields as unresolved rather than guessing.
3. **Search inside the portal.** Use the portal's own search box, catalog, filter, series/indicator index, or documented search endpoint. A homepage, external web search result, or a guessed API URL is not a portal-directed search.
4. **Record all candidates.** Store candidate labels, IDs, URLs, dimensions, and rank. Do not discard near-matches silently.
5. **Apply a semantic selection rule.** State why the selected candidate matches the question and why near-matches do not. Compare indicator, geography/scope, period, unit, frequency, price base, source and other dimensions. If the model selects an incompatible candidate, preserve that exact first selection, record `selection_status=FAIL` and `selection_failure_class=MODEL_SELECTION_ERROR`, then continue the retrieval using the selected candidate. Do not silently substitute a different candidate or reorganize the model's selection path: the error is itself a visibility result.
6. **Open the specific record/series.** The homepage does not count as a successful target. Prefer a canonical indicator/series/record URL or a documented API resource tied to that object.
7. **Retrieve the value or record.** Preserve the request URL/parameters, HTTP status, response format, row count, selected row, and dimension filters. For APIs, validate that the returned row is the requested geography/period/unit, not merely the first row.
8. **Validate metadata.** Require, where applicable, identifier, label, definition, unit, geography, period, source, update date, methodology/notes, and provenance. A numeric value without its dimensions is not a complete answer.
9. **Validate primary citation.** The output must preserve a stable, specific URL or API request and the upstream source organization. Secondary search snippets do not count.
10. **Write the gate and reason.** Keep `PASS`, `FAIL`, `MODEL_SELECTION_ERROR`, `NOT_VERIFIED`, and `NOT_APPLICABLE` distinct. `MODEL_SELECTION_ERROR` is a model/metadata-discrimination failure, not a portal transport failure and not an unresolved observation.

### Model selection errors are first-class evidence

When the model picks a semantically wrong series (for example, a subnational
GDP-by-activity indicator for a national total question), do not repair the row
by selecting a nearby national series. Preserve the model's selected ID, label,
rank, candidate metadata, near-matches, prompt decomposition and reason. Retrieve
the selected object where possible and continue the run. Record:

| Field | Meaning |
|---|---|
| `selection_status` | `PASS` when the selected candidate satisfies the dimensions; `FAIL` for a semantic mismatch. |
| `selection_failure_class` | `MODEL_SELECTION_ERROR` for a wrong indicator/series; keep transport/model-response errors separate. |
| `selection_error` | Expected versus observed metadata and the mismatch list. |
| `model_candidate_rejected` | Only populate if the protocol explicitly rejects a candidate; it must not be used for an automatic correction. |

This error does not trigger the `NOT_VERIFIED` stop rule. The run continues and
the editorial layer reports both the selection failure and what the selected
series returned. Stop/review/relaunch remains mandatory for `NOT_VERIFIED` or
for zero observations after the configured attempts.

### Mandatory unresolved-evidence ledger

Every portal run must include an unresolved-evidence ledger. It is not optional
editorial commentary. For each check that could not be completed, write:

| Field | Meaning |
|---|---|
| `check_id` | Stable check name, such as `jsonld_initial_html` or `api_direct_id_50678`. |
| `status` | Always `NOT_VERIFIED` until the required observation is made. |
| `evidence_state` | `initial_html_not_captured`, `rendered_dom_not_captured`, `route_declared_only`, `client_or_network_block`, or another precise state. |
| `observed_evidence` | What was actually seen, including the source URL or script/bundle reference. |
| `verification_gap` | The missing observation; do not write a generic “not tested”. |
| `next_verification_action` | A bounded, read-only HTTP/browser/DOM action that would close the gap. |

Examples that must remain visible in the statistical-portal report:

```text
Datos estructurados / HTML inicial | NOT_VERIFIED |
evidence_state=initial_html_not_captured; verification_gap=the response before
JavaScript was not captured; next_verification_action=save the origin HTML and
inspect JSON-LD/microdata before hydration.

API independent / id=50678 | NOT_VERIFIED |
evidence_state=route_declared_only; verification_gap=the route was seen in scripts
but no isolated HTTP request was made; next_verification_action=issue one safe GET,
validate status/content-type/payload and confirm id=50678.
```

Do not turn these rows into zeros, `FAIL`, or a positive score. They remain separate
from confirmed absence (`ABSENT`, which requires the full state coverage) and from a
client-side error. A portal can have passing E2E retrievals while retaining technical
`NOT_VERIFIED` checks.

### When one URL is correct

A very specific question may legitimately resolve to one URL. Do not penalize that result for not returning multiple pages. The gate passes if the single object is the correct semantic object, the value/record is present, context is complete, and the citation is reproducible. Conversely, multiple candidates are not automatically a failure; they are a required disambiguation step.

### Minimum query evidence

Store one JSON object per query with at least:

```json
{
  "portal_id": "cepalstat",
  "query": "PIB ...",
  "decomposition": {"indicator": "...", "geography": "...", "period": "...", "unit": "..."},
  "search": {
    "catalog_url": "https://...",
    "input_or_endpoint": "...",
    "candidate_count": 2,
    "candidates": [{"id": "...", "url": "...", "label": "...", "selection_metadata": {"scope": "...", "frequency": "...", "unit_class": "...", "price_base": "..."}, "selected": true}],
    "selection_rule": "..."
  },
  "selection": {
    "status": "PASS | FAIL",
    "failure_class": "MODEL_SELECTION_ERROR | ...",
    "selected_candidate": {"id": "...", "label": "..."},
    "error": {"expected": {}, "observed": {}, "mismatches": []}
  },
  "retrieval": {
    "request_url": "https://...",
    "http_status": 200,
    "rows_returned": 8,
    "selected_row": {"value": 1.2, "unit": "...", "period": "...", "geography": "..."}
  },
  "unverified_checks": [
    {
      "check_id": "jsonld_initial_html",
      "status": "NOT_VERIFIED",
      "evidence_state": "initial_html_not_captured",
      "observed_evidence": "",
      "verification_gap": "",
      "next_verification_action": ""
    }
  ],
  "verdict": {
    "search_success": true,
    "candidate_allowed": true,
    "retrieval_success": true,
    "metadata_complete": true,
    "citation_reproducible": true,
    "e2e_pass": true,
    "selection_error": false,
    "reason": "..."
  }
}
```

## Evidence and failure discipline

- A browser safety error, local DNS failure, client block, or missing connector is a limitation of the test environment. Do not call it a portal failure; use `NOT_VERIFIED` and retry through an authorized route when appropriate.
- A 404/410 observed at the origin is evidence for that exact resource. It does not prove that every alternate sitemap, API, or data route is absent.
- Distinguish `not detected` from `absent`. For JSON-LD or metadata, “absent” requires both initial HTML and rendered DOM coverage; otherwise report “not detected in the inspected state”.
- Do not turn a transport failure, validated missing target, `NA`, or `NOT_APPLICABLE` into numeric zero. Keep an explicit status and confidence.
- Do not turn a model-selected wrong indicator into `NOT_VERIFIED`, a portal
  failure, or a corrected national result. It is `MODEL_SELECTION_ERROR`; keep
  the original candidate and continue the retrieval so the error can be measured.
- A client-declared API route is evidence that a route is referenced, not proof that an independent request, contract, pagination, filters, or provenance work. Mark those checks separately.
- Never use only the homepage, a search-engine snippet, a model's unsupported answer, or a frozen previous score as evidence of current data visibility.

## Technical-layer fields for comparative statistical evaluations

Maintain one row per portal, dated to the evidence run. The operational and technical fields are intentionally separate:

| Field | Meaning |
|---|---|
| `portal_id`, `portal`, `evidence_date` | Stable identity and evidence cutoff. |
| `technical_score`, `technical_confidence` | Six-dimension AEO score and confidence. |
| `e2e_queries`, `e2e_passes`, `e2e_pass_rate` | Query-level operational visibility, not a technical score. |
| `selection_error_count`, `selection_error_rate` | Model semantic-selection errors, kept separate from retrieval/transport outcomes. |
| `candidate_count_mean`, `specific_url_rate` | Candidate/disambiguation and specific-object recovery. |
| `metadata_complete_rate`, `citation_reproducible_rate` | Completeness and reproducibility gates. |
| `robots_status`, `sitemap_status`, `llms_status` | Direct observations for each host. Use 404, 200, blocked, or `not_verified`. |
| `jsonld_rendered` | Count of detected JSON-LD blocks in the inspected rendered state; do not infer source absence. |
| `jsonld_initial_status`, `jsonld_rendered_status` | `PASS`, `ABSENT`, `NOT_VERIFIED`, or `NOT_APPLICABLE` for each captured state. |
| `api_route_declared`, `api_direct_http_status` | A script/bundle route and the status of the isolated request, kept separate. |
| `api_direct_verified` | True only after an independent read-only request and response validation; `NOT_VERIFIED` otherwise. |
| `data_export_status` | `PASS`, `ABSENT`, `NOT_VERIFIED`, or `NOT_APPLICABLE` for a validated machine-readable download. |
| `data_export_formats` | Formats actually tested, such as `xlsx`, `csv`, `json`, `xml`, or `sdmx`. |
| `data_export_selection_preserved` | Whether the returned artifact retains the requested indicator and selected dimensions. |
| `data_export_evidence_path` | Local artifact/JSON path plus the exact request URL and hash. |
| `structured_markup_scope` | Explicitly `embedded_html_initial_and_rendered` so readers do not confuse it with API/export access. |
| `unverified_count`, `unverified_checks_path` | Count and evidence path for unresolved checks; never coerce to zero. |
| `source_evidence_path` | Local JSON/HTML/HTTP capture or workbook reference. |
| `status`, `notes` | `verified_one_case`, `verified_sample`, `not_rebuilt`, `hold`, or another explicit state. |

For a portal not yet rerun with this protocol, leave technical and E2E metrics as `NA`/blank and set `status=not_rebuilt`. Do not copy a prior pilot score into the v2 matrix.

## Sampling and interpretation

- One query proves a case, not a portal-wide rate. Use multiple queries stratified by indicator family, geography, period, units, and known near-matches before reporting a rate.
- Keep agent/model/repetition strata in the evidence. They are sensitivity dimensions; they do not increase the number of independent portals.
- If comparing AEO with visibility, state the inferential unit (`n` portals), coverage, missingness policy, and confidence intervals or exact tests when the sample permits. Describe association; do not claim causality.
- Recompute scores and rates outside the language model judge. The judge may classify a response, but it must not silently convert missingness or transport problems into a score.
- Include at least one live export probe for a portal that advertises downloadable
  data. A representative indicator is sufficient for a case-level verification;
  do not generalize to every indicator without sampling indicator families or
  relying on a generic documented endpoint contract.
- Publish the unresolved-evidence ledger alongside every score. If initial HTML,
  rendered DOM, or isolated API validation is missing, report `NOT_VERIFIED` and
  cap the confidence of the affected technical dimension; do not silently treat it
  as `FAIL`, `ABSENT`, or `0`.

## Deliverables for this mode

When the user asks for a full statistical-portal evaluation, produce or update as requested:

- one detailed report per portal with the E2E trace and technical score;
- a query/evidence workbook with sheets for summary, steps, candidates, retrieval, metadata, QA, and sources;
- a machine-readable technical-layer CSV/JSON matrix;
- a comparison report that keeps E2E rates and technical scores in separate columns;
- a presentation that states the evidence date, sample, gates, caveats, and primary sources;
- an unresolved-evidence ledger that names every state not captured (including the
  initial HTML/DOM distinction and script-declared-but-unqueried API routes);
- export evidence for advertised machine-readable downloads, with the returned
  artifact and selection-preservation check;
- final project documentation only after reports, matrices, workbook, and presentation pass QA.

The editorial conclusion must name what was actually observed and what remains pending. Do not present a homepage-only test or a frozen pilot as a complete statistical-portal evaluation.
