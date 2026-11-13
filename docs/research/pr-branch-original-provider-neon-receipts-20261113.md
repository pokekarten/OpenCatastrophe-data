<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Three exact original-source GitHub PR-branch receipts: reviewed Neon separation

**Date:** 2026-11-13. **Research only.** Proposed separate Neon evidence ledger,
not a source scientific/admission engine. No provider raw data and no production
Neon mutation are performed by this PR.

## Why a distinct, additive table is necessary

Read-only verification in insurance-risk-core (Neon project
square-resonance-68106861, database insurance, default main branch) found:

- **100 private research samples from 42 source IDs** at the time of the check.
- **45 historical smoke API rows** in research.source_api_smoke_receipt_v0.
  Its hard CHECK (NOT strict_repository_runner_executed) is intentional.
- **Two trusted-main direct original Range receipts** in
  research.source_strict_original_probe_receipt_v1: DWD CatRaRE W3 and T5,
  both from main GitHub run 43480623017.
- **One trusted-main original metadata receipt** in
  research.source_strict_metadata_probe_receipt_v1: PDOK BRP, run 43489886311.

Both existing strict-v1 tables enforce github_ref=refs/heads/main.
The three actual original source checks below were on individually reviewed
**research PR branch** revisions, not on main. They cannot truthfully be inserted
into the existing main-only schema. Relaxing an old CHECK or storing false
runner flags would lose important provenance.

## Three independently public original-provider proofs

| Source | GitHub original job | Original HTTP | Bytes | Original response SHA-256 |
| --- | --- | --- | ---: | --- |
| DWD RADKLIM RW corrected 2021 | [43488656039 / 132103695178](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43488656039/job/132103695178) | 206, exact bytes 0–2047 of 820143312 | 2,048 | 741c1320301be519a57818655d0380d94a6b6865adc3249f454f9c9cdf254867 |
| NOAA SWPC RTSW 2026 | [43489514680 / 132106651956](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43489514680/job/132106651956) | 200, single fixed rolling JSON | 1,719,377 | bc35b0a375b85efe559f132cfae46d8c79b7e8f19400299ae223d067f6091159 |
| GFZ definitive 2024 Kp | [43491158483 / 132112397671](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43491158483/job/132112397671) | 200, fixed 2024-01-01 eight-bin JSON | 361 | f03506f678672a99c4c5a2c1d251740bd484b064853db18177b9b5ba4ad27d0a |

The seed SQL additionally pins the exact original request, source URL, runner code
SHA, original body digest, source branch commit/ref, provider retrieval UTC and
GitHub run/job. All three one-shot branch live workflows were removed after
their recorded successes; no new automated polling is proposed.

The DWD fixed 2,048-byte range is **not** a complete TAR or NetCDF, NOAA is
a volatile rolling feed rather than a frozen stable archive, and GFZ checks
one definitive day but not independent instrument accuracy. No value/feature
rows are published or admitted into insurance or hazard modelling.

## Read-only live Neon cross-check (already executed)

The three source IDs are present in research.all_source_inventory_v0. Their
private research sample counts at the audit time were:

- DWD RADKLIM: **3** private samples; **2** prior original-prefix SHA matches
  the later actual strict GitHub run.
- GFZ Kp: **1** private sample; **1** original JSON response SHA match.
- NOAA SWPC: **0** source samples stored; the original GitHub response digest
  therefore does not imply a Neon sample or time-series ingestion.

These matches are **provenance cross-checks**, not scientific source admission.
Older smoke receipts or PR workflow job GREEN labels, by themselves, must
not be treated as original provider response evidence: the actual source
job step and nonempty original SHA were verified separately.

## Proposed additive database artefacts (not applied)

- research_runners/sql/insurance_source_strict_pr_branch_receipt_v1_schema.sql
  introduces only the separate research.source_strict_pr_branch_receipt_v1 table.
  It enforces actual PR-branch rather than trusted-main identity, exact run/job
  URL, 40-char commit and 64-char digests, source-specific operation/status/range,
  no original bytes, no full source SHA, no scientific verification and no
  insurer model admission.
- research_runners/sql/insurance_source_strict_pr_branch_receipt_v1_seed.sql
  inserts **only** those three independently checked GitHub receipts,
  idempotently. Never overwrite main-only ledgers or the historical smoke table.
- research_runners/sql/insurance_source_strict_pr_branch_receipt_v1_verify.sql
  is read-only and compares proposed PR-branch receipts with historical private
  sample SHA evidence, the registry and **both** trusted-main registers,
  without promoting one trust level to another.
- tests/test_source_strict_pr_branch_receipts_v1.py is a no-network
  regression on fixed receipt identity, immutable hashes, access scopes,
  false admission flags and prohibited SQL mutations.

**Production review gate:** A Neon database owner should explicitly approve
the additive CREATE and idempotent INSERT after checking live public Actions
logs and source rights. Prefer a reversible temporary-branch schema migration
first, then a separately authorized production apply. This PR does not issue
CREATE, INSERT, ALTER or UPDATE to the live insurance Neon database. Existing
accepted main receipts remain untouched.

## Next scientific step

For DWD, obtain the **full corrected monthly 2021 NetCDF original member**
with a full-file SHA-256 and verify CF variables, CRS, rainfall units,
time coordinate, nodata and temporal completeness. Retain year-2021
original-bad NetCDF exclusion. For NOAA and GFZ, science quality and model
use case need independent assessments after fixed API shape passes.

Every future provider run must be individually source-reviewed and its exact
asset scope and licensing documented. Public GitHub actions success alone
never grants insurer CAT model permissions.
