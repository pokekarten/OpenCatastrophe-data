<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Türkiye 2023 three-USGS-anchor read-only Neon execution receipt

**Research receipt, 2026-11-03; no admission.** The query from
`research_runners/sql/usgs_turkiye_2023_three_event_anchor_readiness_v0.sql`
was executed verbatim as a single read-only SQL statement against the
`insurance-risk-core` Neon project's `insurance` database, default branch.
The exact reviewed source was Git blob
`86386632525edbd06234c724f0a065508de57e17`
at PR #1148 head `81f904f2ed3e95ab2bdeec21d01a4d3f8de06110`.
No write operations, data downloads, secret values or insurer rows were involved.

## Executed result (not an inferred status)

| Check | Verified result |
|---|---|
| Expected anchors / stored rows / distinct IDs | 3 / 3 / 3 |
| Missing IDs / inconsistent stored origins | 0 / 0 |
| Missing original USGS response SHA-256 | **3** |
| Well-shaped original SHA-256 rows | **0** |
| Unexpected model approvals | 0 |
| Matching source-access contracts | 1 |
| Access review | `documented_only` |
| Source rights | `unknown` |
| Source raw-admission flags | 0 |
| Earliest anchor origin UTC | 2023-02-06 01:17:34.342 |
| Latest anchor origin UTC | 2023-02-06 10:24:48.811 |
| `origin_evidence_status` | `ORIGINAL_USGS_RESPONSE_BYTES_NOT_PINNED` |
| `source_access_status` | `RAW_ACCESS_NOT_ADMITTED` |

All six separate producer/contract/simulation interpretation flags in the
query returned `false`: physical event-family crosswalk, single contractual
occurrence, historic product vintages, ground motion, insured portfolio loss,
and annual CAT capital metric.

**Interpretation:** All three selected USGS event IDs are present in the
existing research table, but original authoritative response bytes are **not
authenticated**. Even a later 64-character SHA value would not independently
prove the provider response was obtained and verified. None of this is a
complete earthquake sequence, a shaking field, a source-use licence, or an
insurance event/catastrophe model.

## Merge boundary

A successful CI run on the **exact current PR head**, including
`tests/test_usgs_turkiye_2023_three_event_anchor_readiness_v0.py`, and a
conflict-free latest-main comparison are required before merging the research
checker. Merging the checker must never modify Neon, grant provider rights,
introduce a commercial CAT model input, or combine distinct USGS events as a
contractual single occurrence.

Separate future tasks: independently retrieve rights-cleared original USGS
response metadata, verify exact bytes and hashes, establish event relationships
and hazard fields, then evaluate model-appropriate portfolio losses. No
automatic extraction or promotion is authorized by this receipt.
