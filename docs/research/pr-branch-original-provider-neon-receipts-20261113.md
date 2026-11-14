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

## Actual Neon evidence advancement, verified on 2026-11-13

The public-source proof gap has been **partially closed immediately without a
schema migration**. As separately authorized source-research inserts, the
existing private research Neon tables now contain:

- **Source sample #124**: NOAA SWPC 2026 rolling RTSW **metadata only**,
  pinned original response SHA, 1,719,377-byte response length, exact public
  GitHub run 43489514680 and source commit. No spacecraft readings.
- **Source sample #125**: DWD corrected 2021 RADKLIM RW archive **metadata
  only**, exact 2,048-byte HTTP206 original compressed range, header proof,
  run 43488656039 and unchanged original prefix digest. No rainfall arrays.
- **Source sample #126**: GFZ definitive 2024-01-01 Kp **metadata only**,
  original 361-byte HTTP200 response checksum, run 43491158483, eight-record
  definitive day shape. Existing private original **observed-values sample #1**
  remains distinct and was not overwritten.

All three new metadata samples have **canonical SHA-256 of PostgreSQL JSONB
text verified on the live database**, a matching independently recorded
original provider response SHA-256, `research_only=true`,
`source_byte_persistence_authorized=false` and
`model_input_approved=false`.

**14 exact product/use-case rights rows** were also inserted into the
existing `research.source_usage_rights_v0` table: seven for GFZ definitive
Kp, seven for NOAA SWPC rolling RTSW. The publisher originals are
[GFZ CC BY 4.0](https://kp.gfz.de/en/about-kp) and
[NOAA/NWS public-domain, third-party content and appropriate-use disclaimer](https://www.weather.gov/disclaimer).
In particular, NOAA raw third-party spacecraft reuse and unbounded
automated polling remain **unknown or conditional**, not approved; GFZ API
bulk/recurring automation remains **unknown** separately from CC BY rights.
Neither rights nor samples authorize CAT model use.

At this live-audit snapshot: **126 samples / 43 source IDs**, **191
product-specific rights rows / 24 source IDs**, **45 older smoke API
observations**, two trusted-main original source Range receipts and two
trusted-main metadata receipts.

### Executed now: no-migration read-only fallback reconciliation

The executable `research_runners/sql/insurance_source_pr_branch_live_metadata_readonly_v1.sql`
is a single read-only SQL SELECT **actually executed against Neon main**.
It joins existing metadata-only source proof samples #124/#125/#126 to
source/use-case rights, canonical source inventory, prior strict-main Range
and metadata registers. It returned **exactly three rows**:

- DWD sample #125, **7** rights/use-case rows
- GFZ sample #126, **7** rights/use-case rows
- NOAA sample #124, **7** rights/use-case rows

**All three rows** independently returned true for live PostgreSQL JSONB
canonical SHA check, frozen original provider SHA match, exact GitHub run ID
and public run URL, metadata rights and source inventory ID presence,
while returning `metadata_only_no_admission=true`,
`separately_trusted_main_range_exists=false`,
`separately_trusted_main_metadata_exists=false`,
`grants_cat_scientific_admission=false`, and raw redistribution not
unconditionally allowed. This is an **immediate usable source proof join**,
not a backdoor to source or trust admission.

### Postgres DDL rehearsal blocked by Neon branch quota

The planned strictly isolated Neon rehearsal branch could **not be created**
because the Neon API replied **HTTP 422: branches limit exceeded**.
We did **not** overwrite one of the user's existing research branches,
delete any branch, weaken main-only trust checks or apply the new schema
to the default branch. The future PR-branch-specific receipt table
schema/seed remains a reviewed **proposal** with successful hosted Python
static/offline regression, **not yet a PostgreSQL-executed migration**.

The two paths are complementary: use the no-migration SELECT now, then
reviewed source-specific proof table + seed only after a free Neon test
branch is available and a database owner authorizes the migration.

## Executed complete 707-source queue correction, 2026-11-14

The new standalone, read-only
`research_runners/sql/insurance_707_source_original_pr_branch_priority_overlay_v1.sql`
**was executed directly on the live Neon main research database**. It retains
the full baseline 707-entry candidate / manifest SQL from open PR #1536 at
commit `71eaa025ebd497d197bed43620b6c4d173c3224e`
and overlays only **three exact previously observed source responses**.
Every provider identity is independently pinned to a real original GitHub
run/job, 40-character head commit, exact provider URL, raw-response SHA-256,
request SHA-256, runner-code SHA-256 and a matching canonical JSONB SHA-256
metadata sample.

The query joins `source_usage_rights_v0` with
**exact source-product scopes**, including the specific original DWD RADKLIM
product, GFZ **definitive** Kp (not nowcast), and NOAA **2026 rolling**
multi-spacecraft RTSW product. Rights are checked as `EXISTS`, avoiding
one-to-many sample multiplication when a source gains additional rights rows.
Source-restricted/prohibited rights, data integrity failures and manifest
checks retain their existing safety priority.

**Observed exact live results:**

| Measure | Actual |
| --- | ---: |
| Canonical inventory entries | 707 |
| PR-branch original-response proofs validated | 3 |
| Queue priorities changed | **2** |
| Historical inconclusive responses independently superseded | **1** |
| Duplicated source proof matches | 0 |
| NULL inconclusive flags | 0 |
| Newly granted main trust or model admission | **0** |

Two **source-specific** priorities were adjusted, without changing their
historical API receipts or any licensing status.

**NOAA SWPC** (`noaa.swpc.real-time-solar-wind`):

- Original historic queue: `P1_retest_provider_with_trusted_runner`
  because its old intermediary smoke receipt remains `inconclusive`.
- New evidence-adjusted next action:
  **`P2_review_product_rights_and_science_after_original_probe`** because
  a separately verified original NOAA source-provider GitHub GET succeeded,
  and exact rights scope and original hashes also matched.
- The original historic P1 label, timestamp and `inconclusive` receipt
  are **retained** as distinct fields (not overwritten or falsified).
  It is **not** a claim of a trusted-main check, unconditional data rights,
  sensor lineage integrity, scientific validity or CAT model approval.

**JRC Global Surface Water v1.5**
(`ec-jrc.global-surface-water.1984-2024`):

- Original historic queue: `P1_review_bounded_first_source_sample`.
- New rights-safe queue action:
  `P1_review_cloudferro_service_terms_before_original_occurrence_sample`.
- The publisher's official [V1.5 download page](https://global-surface-water.appspot.com/download)
  confirms free Copernicus data reuse, required attribution, the exact
  version, the **2026-11-10 Occurrence >100% correction**, and availability
  of its own download script. The official
  [Python downloader instructions](https://global-surface-water.appspot.com/gsw/Download_Instructions.html)
  specify source-hosting and raster asset layout, but do not independently
  grant unlimited CloudFerro API requests. The independently reviewed
  source contract in PR #1533 (`e72f8ab853f8b9d4639c0173bb8e70c4f16b53bd`)
  remains `documented_only` with
  `commercial_automation_status=unknown`. Therefore **no original
  listing/GeoTIFF GET was attempted**, and the source still has **zero
  native samples**. First review the exact hosted service terms and a
  single bounded original request. Original pixel/science/model admission
  remains separately blocked.

DWD RADKLIM remains `P2_review_native_observation_sample` because a 2,048-byte
original corrected NetCDF compressed archive prefix has **no rainfall data**.
GFZ remains `P2_scientific_native_sample_validation` because the definitive
day JSON format is confirmed, but physical validity and model use are not.

The overlay uses only existing read-only Neon tables. The **proposed**
additional `research.source_strict_pr_branch_receipt_v1` DDL/seed is **still
unexecuted**, and the Neon branch quota blocks an isolated SQL schema
rehearsal. Any changes in the original #1536 queue require a new diff/review
rather than automatically treating this frozen baseline as updated.

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
