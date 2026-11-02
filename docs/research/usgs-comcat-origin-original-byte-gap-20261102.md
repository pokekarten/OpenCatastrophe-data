<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# USGS ComCat research origin quality: original-byte admission gap (2026-11-02)

**Scope:** Live, aggregate-only, **read-only** check of the separate CAT-only Neon
`insurance-risk-core` project, `insurance` database, explicit `main` branch
`br-late-recipe-ba1cr8hc`. Source: `research.usgs_comcat_origin_observation_v0`.
This is a research preflight and **does not** acquire or approve provider bytes,
create physical events, infer insured exposure, or modify Neon.

Run the canonical SQL
[`research_runners/sql/usgs_comcat_origin_readiness_v0.sql`](../../research_runners/sql/usgs_comcat_origin_readiness_v0.sql)
in an explicitly selected CAT-only Neon branch. The query always returns a
single aggregate row and leaves all scientific/model admission booleans `false`.
The query deliberately keeps *provider URLs and stable event IDs* separate
from SHA-256 verification of the original provider response.

## Observed live result

| Check | Main result |
| --- | ---: |
| Research origin observations | 1,333 |
| Distinct USGS event IDs | 1,333 |
| Missing event IDs / timestamps / source URLs | 0 / 0 / 0 |
| Suspect magnitudes / coordinates / depth review candidates | 0 / 0 / 0 |
| Distinct source query URLs | 10 |
| Original response SHA-256 missing | **1,333** |
| Original response SHA-256 malformed (non-null) | 0 |
| SHA-256-present observations | **0** |
| Records with `model_admitted=true` | 0 |
| Recorded event years | 2016 through 2025 |
| Recorded magnitudes | 6.0 through 8.8 |
| `evidence_status` | `RESEARCH_ORIGINAL_BYTES_NOT_PINNED` |

All rows are labelled `historical_origin_observation`, from `USGS ComCat`,
with `source_review_status=reviewed`. **Reviewed research rows are not
source-byte-proven**. The null original SHA is not evidence that the event
does not exist, only that this particular recorded row lacks an original
response byte commitment. Do **not** substitute a hash of an exported Neon
row or an event URL for the original source body hash.

The observed 2016–2025, magnitude-at-least-6 subset is not a completeness
claim about the global USGS event universe or a long-term annual hazard-rate
model. USGS origin point/magnitude/depth are not site-level shaking footprints,
fragility functions, insured losses, or a stochastic catalogue of correlated
event years. No insurance TIV/claims/financial results follow from this table.

## Causal next step

1. Review the original source-specific ComCat access contract and API terms.
   Freeze an exact, bounded query/source vintage and allowed response-byte
   retrieval before any re-acquisition. Never infer permission from a URL.
2. Capture **original response bytes** and SHA-256 in isolated CAT-only
   staging if allowed, plus the exact retrieval time, query, response schema,
   pagination/completeness and source-event identity. Keep original data out
   of Git and public logs.
3. Independently reconcile parsed rows against the hash-pinned original
   response, identify duplicate/update semantics and explain the temporal
   and magnitude selection. A source hash alone cannot verify scientific
   completeness.
4. Link to independently reviewed ground-motion intensity and building
   exposure/vulnerability input artifacts for one declared event/region.
   Any catalogue/financial model admission remains a separate rights,
   model-science and validation decision.

Do not mutate `registry.source_record.admissible_for_raw`,
`research.usgs_comcat_origin_observation_v0.model_admitted` or publish a
simulation based on these metadata observations.

## Read-only adversarial PostgreSQL checks

The canonical query and **four** controlled CTE variants were run against
the same live `insurance` main branch. They alter only the SELECT text and
never modify source tables:

| SELECT-only case | Observed `evidence_status` | Model admitted |
| --- | --- | --- |
| Unmodified 1,333 rows | `RESEARCH_ORIGINAL_BYTES_NOT_PINNED` | false |
| Force empty observations | `MISSING_RESEARCH_ROWS` | false |
| Duplicate one already stored event ID | `RESEARCH_RECORD_QUALITY_BLOCKED` | false |
| Hypothetically set `model_admitted=true` in SELECT | `UNEXPECTED_ADMISSION_REQUIRES_REVIEW` | false |
| Hypothetically supply 64-hex SHA for every SELECT row | `RESEARCH_STRUCTURALLY_CHECKED_NOT_ADMITTED` | false |

The final case **does not establish any real hash**: the SHA was invented
inside a SELECT expression solely to challenge the status logic. It proves
that even a source-structurally-green result cannot become an accepted
hazard catalogue by this query. The source itself still has zero original
response SHA attestations. Local unit tests cover fail-closed status,
source-hash-vs-URL distinctions and read-only SQL shape.
