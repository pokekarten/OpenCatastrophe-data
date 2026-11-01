<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Insurance Neon: three source divergences and index coverage (2026-11-01)

**Scope:** independent CAT-only Neon `insurance-risk-core`, database `insurance`,
root `main` and `validation-schema-20261031`. This is an **evidence
reconciliation and an executable metadata preflight**, not an authorized
database migration, source admission, automatic merge or insurance CAT model.

## Executed checks

- `research_runners/sql/insurance_source_conflict_evidence_v0.sql`: **3/3
  pinned evidence records consistent on each branch** in live read-only SQL.
  The query explicitly sets both `merge_authorized=false` and
  `model_input_authorized=false`. The historical Git SHA and source
  admission status are checked independently of mutable branch names.
- `research_runners/sql/insurance_source_registry_index_coverage_v0.sql`:
  independent read-only index coverage count on both branches.
- The eleven common candidates in the two historical
  `landscape/sources-exposure-impact-validation.json` versions were
  compared by `candidate_id` and complete JSON item; there were **zero
  changed common candidate objects**. Two GEM 2026 source candidates were
  added in the 13-entry version.

## Conflict dispositions (evidence vs decision)

| Source key | Observation | Technical conclusion | Still prohibited |
| --- | --- | --- | --- |
| `landscape_file:sources-exposure-impact-validation` | main Git blob `79d91635a154b6ae20482b953021a6ade52c3491` = **13** candidates; validation blob `cecaf867a47e83069a27b179268942b900b771b4` = **11** candidates | **Verified additive metadata version**: two additions, `gem.global-exposure-model.v2026.0.0` and `gem.global-vulnerability-model.v2026.0.0`. Keep both Git versions addressable; current repository `main` points to 13-entry file. | Do not treat GEM replacement costs as insured TIV or promote GEM commercial reuse. |
| `official_api:usgs_comcat_2025_jan_m6_sample` | Both branches point to Git blob `1527daa259d1ac697e1356dc35eb2171438538cc`, seven global M6+ January 2025 event **samples**. Review labels differ but source object matches. The pinned record has no archived original API-response SHA and no ShakeMap/intensity footprint. | **Same source bytes, differing review vocabulary**. Preserve the review histories; do not assert one right-status label is legally final. | No inferred earthquake recurrence rate, hazard footprint, vulnerability, claims, event catalogue or model approval. |
| `official_fl_oir:2025_12_mir_original_full_company_policy_v1` | Same Git blob `b4318d9a4c51a628088546c36b2697b6e919ca92` and original XLSX SHA-256 `a4fc7d5e20daed10299b06b2b661480b7c92c2cbaecc697a26567156bf1d4d3a`. **442** company × policy-type rows, 160 distinct NAIC codes, 25 reported types. Review/rights labels differ; neither grants admission. | **Same cited original report identity**, not evidence of identical validation branch scientific rights decisions. Keep both audit-trail labels and the original report receipt. | No invented company-ZIP positions, geocoded insured buildings, corporate parents, CAT losses, or commercial reuse permission. |

The 11-item landscape file's recorded Git ref is
`2c9cfeeec62c81609e63e58465f7882622054b7e`; the 13-item revision
is `98c6391a05af0b5d622487aca3ff214a14d00695`.
USGS and Florida source Git blobs were independently retrieved at **both**
recorded branch-specific FFBK commit references and matched byte-identical
Git blob IDs.

### External publisher rules (checked)

- GEM's [Global Exposure Model](https://github.com/gem/global_exposure_model)
  documents **CC BY-NC-SA 4.0** and the need for a separate agreement for
  commercial use; public modelled replacement cost is **not** insured
  policy TIV. Preserve release tags and per-file taxonomy, not a mutable
  default branch.
- USGS [copyright guidance](https://www.usgs.gov/faqs/are-usgs-reportspublications-copyrighted)
  says USGS-produced data are generally in the U.S. public domain, while
  third-party material may not be. Publication terms and credit are distinct
  from a scientific event-to-hazard-footprint admission decision.
- The official [Florida OIR MIR reporting service](https://qsrng.floir.gov/Reports/ReportCriteriaWizard.aspx)
  says results can change due to resubmissions or user selectors, gives
  the need to record exact selector/time, and says company-submitted numbers
  are **not audited** before publication and trade secrets excluded.
  This is not a blanket commercial redistribution grant.

## Source registry and repository index coverage

Read-only execution:

| Classification | main sources | main exact blob indexed | validation sources | validation exact blob indexed |
| --- | ---: | ---: | ---: | ---: |
| `landscape_candidate` | 38 | 38 | 23 | 0 |
| `access_contract` | 48 | 3 | 45 | 0 |
| `admitted_manifest` | 15 | 0 | 15 | 0 |

All `registry.source_record.admissible_for_raw` flags remain false on both
branches. `admitted_manifest` is a source **classification label**, not
permission to download/redistribute or a CAT-model admission. Missing index
rows only mean that the *separately sampled*
`registry.repository_asset` does not yet cover the source file. They do not
prove the linked Git object is missing. A linked Git blob from an upstream
repository and an original provider-download hash are also distinct things.

## Safe continuation

1. **No full branch merge or status upsert.** Persist a source-specific
   provenance/review observation when a new status has independent evidence;
   do not overwrite another branch's review labels blindly.
2. Keep the validation-only Florida partial 282-row receipt alongside
   the full 442-row receipt with explicit non-duplicative subset lineage.
   The 442-row official workbook must remain company × reported policy type,
   not company × ZIP or insured building records.
3. Coordinate Florida/Texas research work with
   [PR #907](https://github.com/pokekarten/OpenCatastrophe-data/pull/907)
   and international insurer evidence with
   [PR #899](https://github.com/pokekarten/OpenCatastrophe-data/pull/899).
   Apply only an independently reviewed additive migration on a safely
   provisioned target branch, with a reproducible row-count/hash check,
   source rights decision and rollback path.
4. Backup limitation: the manual root `main` snapshot
   `pre-fl-tx-research-integration-2026-11-01` was created; automatic
   snapshot schedules were refused by Neon for this project and a
   non-root validation snapshot request was disallowed. Do **not** assume
   validation is separately restorable from a recent snapshot.
5. Require approved source-original payload checksums, hazard intensity
   footprints, insurer-specific geocoded TIV, vulnerability and explicit
   contract/retro terms before any 10,000-year financial model attribution.

**Current conclusion:** all three discrepancies have reproducible technical
explanations; **zero** provide permission for raw-data admission, scientific
use or automatic database merging.
