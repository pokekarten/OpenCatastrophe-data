<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# CAT source metadata — pinned stage/prod reconciliation, 2026-11-09

This document is **snapshot evidence**, not a source-admission register, approved
migration or source of truth for any provider licence. Re-run the offline
comparator against new pinned receipts before acting.

## Inputs actually inspected

- Public OpenCatastrophe-data `main` commit:
  `a5af7add12f295e7334b78a333740c5d07847581`.
- Three GitHub API directory listings: `landscape/`, `access/`,
  `manifests/`, counting **only canonical JSON**, not generated Markdown.
- CAT Neon project `insurance-risk-core`, DB `insurance`, production
  branch `main`, project `square-resonance-68106861`.
- Independent historical research stage `access-contract-revision-proof-20261103`
  (`br-steep-lab-baeo8bmc`). Stage is **not** a substitute for a new
  production-cloned rehearsal branch.
- Initial read-only `registry.source_record` metadata SELECTs established the
  baseline. A subsequent **append-only rehearsal on a nonproduction branch**
  is documented below. No original provider bytes, model operation, or
  production database mutation occurred.

| Layer | Pinned GitHub files | Production matching path | Stage matching path |
| --- | ---: | ---: | ---: |
| Non-admission landscape source shards | 106 | 41 | 64 |
| Reviewed access contracts | 68 | 52 | 66 |
| Admitted metadata manifests | 15 | 15 | 15 |
| **Canonical metadata paths** | **189** | **108** | **145** |

- **Production:** 100 exact Git-blob matches, **81 missing** (65 landscape,
  16 access), **8 SHA/version differences**, and no missing admitted manifest.
- **Historical stage:** 136 exact matches, **44 missing** (42 landscape,
  2 access), **9 SHA/version differences**. Of the two absent access records,
  one is the newly documented, still non-executing Slovakia GKÚ Buildings
  GeoPackage contract; the other is the ISIMIP3a TC ER11 maxrain file-list
  research contract.
- The two additional noncanonical historic research receipts in the exported
  `repo` scope are not `access/*.json` source contracts. Do not manufacture
  canonical identities from their filenames.
- There are **no** raw source admissions implied by any of the 189 metadata files.

## Version differences that need explicit disposition

### Production/main versus pinned public GitHub: eight files

| Path | Scientific / access change | Safe next action |
| --- | --- | --- |
| `landscape/sources-europe-building-attribute-discovery.json` | Three new Luxembourg 2019 building/LiDAR/ortho source candidates; no changes to existing entries | Review new candidates separately, do not upgrade admission |
| `landscape/sources-europe-cat-model-components.json` | XWS European windstorms note refined | Preserve old/new scientific context |
| `landscape/sources-event-loss-benchmarks-2026.json` | CLIMK-WINDS footprint provenance note refined | Retain original event/support limitations |
| `landscape/sources-exposure-impact-validation.json` | Overture temporal scope, granularity and provenance notes changed | Reconcile release/vintage meaning before joins |
| `landscape/sources.json` | NOAA Storm Events and IBTrACS lineage/usage notes revised | Avoid conflating original event records and synthetic storms |
| `access/esa.worldcover.2021.v200.json` | `documented_only` to `probe_ready`, fixed original TIFF range/HEAD canary | Review exact byte and service evidence; no generic tile crawler |
| `access/globaldamwatch.gdw.v1.0.json` | `documented_only` to `probe_ready`, bounded metadata request, added publisher rehosting caution | Preserve attribution/asset rights limits |
| `access/noaa.coops.water-levels.json` | `documented_only` to `probe_ready`, reviewed fixed one-day NOAA API query | Retain request scope and original receipt proof |

Historical stage has one additional version discrepancy:
`landscape/sources-peer-cat-repositories-20261102.json`. Never silently
overwrite old version rows in stage or production just to reduce drift counts.

## Original Git blob version pairs: evidence, not automatic replacement

On 2026-11-09 the eight **production-source** SHA differences were rechecked by
fetching both original Git objects from the public repository and comparing
candidate identity, fields and source status. All eight original
`registry.source_record` production rows and original rehearsal rows
remain intentionally untouched. Old/new SHAs below are **Git blob SHA-1**,
not the SHA-256 digest of a provider dataset.

| Source path (relative to repo) | Neon original Git blob SHA-1 | Current reviewed Git blob SHA-1 | Identity-preserving difference |
| --- | --- | --- | --- |
| `landscape/sources-europe-building-attribute-discovery.json` | `40e67dd494aea80775879ca768c77f37202a1c91` | `e1804ae540dd7e9bf2f8b78a7dab624e30975da1` | 16 to 19 candidates: VDL City 2019 3D, ACT LiDAR 2019 index, ACT orthophoto 2019; previous entries untouched; `review_date` changed |
| `landscape/sources-europe-cat-model-components.json` | `835daf700e2877cded1d169aa35f00486d6c3224` | `9b337498540a7e78e2158fd25560adcb6dc14bb7` | XWS windstorm `note` expanded with native Kyrill NetCDF comparison and explicit limitations |
| `landscape/sources-event-loss-benchmarks-2026.json` | `ba3e8446cc8eebf1a42ff39a2a884c55566f7b92` | `880c1851a066c3eb23e1677b4c3de0f767b50277` | CLIMK `note` adds verified original bytes, synthetic Oasis comparison, 50-event selections and cross-catalogue mismatch limits |
| `landscape/sources-exposure-impact-validation.json` | `79d91635a154b6ae20482b953021a6ade52c3491` | `f19346157e01d32a82a51bc511f4039aa09bfc9d` | Overture `temporal_scope`, `resolution_or_granularity`, `note` changed (2026-10-21.0 release, GERS identity and source conflation cautions); `review_date` changed |
| `landscape/sources.json` | `792719b1b3a577d108c46692f48ad8d5dd775872` | `c1aab3639f93f5f4ebf3cf0bed4644d966cc4a62` | NOAA Storm Events and IBTrACS `note` added observational row-count, join-multiplicity and historical track semantics |
| `access/esa.worldcover.2021.v200.json` | `830fff1705d6b29d8c88dc423a27c7254608ca50` | `2884e2f50b495eee3b399f55c08d43cfa100b602` | 16 changed contract fields; status `documented_only → probe_ready`, `none → head`, fixed original TIFF canary; commercial rights already marked allowed before |
| `access/globaldamwatch.gdw.v1.0.json` | `cfc4189609e8d69688b84f4f8ca8c842fb04c966` | `8710f53ee145fed31ae878fc0fe54c2a86cd054d` | 18 changed fields; `documented_only → probe_ready`, `none → metadata_get`; licensed dataset and author request not to mirror original files remain distinct |
| `access/noaa.coops.water-levels.json` | `53aa5e6e9f23dc0ddd153fae1c57a4752f31b0aa` | `f617e0a1915e84d0dbe51f08532793c7fb8accb4` | 15 changed fields; `documented_only → probe_ready`, `none → provider_specific`, API terms `separate_unreviewed → separate_reviewed`, commercial automation `unknown → allowed` |

The five landscape revisions **do not** delete or re-identify pre-existing
candidate IDs, and their metadata retain `rights_review_status=not_reviewed`,
`scientific_review_status=not_reviewed`, `admission_status=not_admitted`.
Three added Luxembourg sources remain **non-admitted** and must not be
counted as three verified exposure datasets.

All three access revisions preserve `access_id` and the exact
`source_ids` array but enable **new bounded probe modes** relative to
the historical production contract. NOAA also contains explicit API
terms and automation-rights upgrades. These must be separately reviewed
against provider terms and original receipts before a production
revision. An allowed dataset licence alone does not establish a
model-ready footprint or an unrestricted crawl.

An offline companion `scripts/audit_cat_landscape_revisions_v0.py`
SHA-checks old/new original metadata bytes, rejects silent candidate removal,
duplicate IDs, changed provider/source URL and unsafe admission status, and
reports added candidate IDs and changed existing fields. The older
`scripts/audit_access_contract_revisions_v0.py` already provides the
analogous SHA-pinned **access** contract review. Neither program writes
SQL, admits source bytes or approves a production UPDATE.

**Separate decision still required:** preserve old production rows until
the eight field-level scientific/access reviews are accepted; then
perform a separately authorized, conditional revision in an isolated
Neon branch with unchanged historical receipts, followed by a
production change review. Do not treat this table as that authorization.

## Branch capacity and completed isolated append rehearsal

A request for a **new** isolated Neon branch
`source-registry-stage-20261109-pinned-a5af7add`, parented on the historical
stage, returned **HTTP 422: branches limit exceeded**. No branch was
deleted. The historical stage `br-steep-lab-baeo8bmc` was **not** mutated.

Instead, an existing *purpose-built* append rehearsal branch,
`source-registry-production-append-rehearsal-20261103`
(`br-solitary-truth-ba46euvb`), was checked against actual production.
Both held **114** identical source-record rows, no raw admission flags,
and the **same complete-row fingerprint**
`3785c2f4e842ce5a1c8457f29d07d924`
(MD5 over sorted `to_jsonb(row)::text`, including original timestamps).
The branch is not `main`.

After checking the exact pinned GitHub canonical JSON file SHA against
the corresponding pinned GitHub directory listing and checking
fail-closed discovery/access statuses, **81 missing metadata records**
were appended to this rehearsal branch in bounded inserts:

- **65** new non-admission `landscape/sources*.json` shard receipts;
  `review_status=non_admission_discovery_only`, `rights_status=not_reviewed`.
- **16** new `access/*.json` reviewed interface receipts, preserving their
  original contract status and rights, including the Slovakia GKÚ Buildings
  `documented_only` route. No contract was promoted to executable/model-ready.
- **0** new manifest identities; existing 15 matched pinned GitHub exactly.
- **0** existing rows replaced, updated or deleted, and **0** raw admissions.
  Full public canonical JSON metadata were retained as JSONB; provider asset
  bytes and customer/claims/insured location data remain outside this proof.

### Verified post-transaction readback

| Metric | Production (unchanged) | Isolated append rehearsal |
| --- | ---: | ---: |
| Entire `registry.source_record` rows | 114 | **195** |
| Canonical GitHub JSON paths present | 108 / 189 | **189 / 189** |
| Exact current Git blob matches | 100 | **181** |
| Missing canonical paths | 81 | **0** |
| Existing blob/version conflicts | 8 | **8** |
| `admissible_for_raw=true` | 0 | **0** |

- Pinned GitHub source commit for all 81 inserts:
  `a5af7add12f295e7334b78a333740c5d07847581`.
- Original **114** baseline rows preserved with identical full-row MD5
  `3785c2f4e842ce5a1c8457f29d07d924`, verified again in both
  production and rehearsal after the inserts.
- **81** newly tagged metadata records; their sorted
  `source_key|git_blob_sha|review_status|rights_status` MD5 fingerprint:
  `4bd8b5e3e3596aed0cd261682aa18498`.
- Post-write checks: 0 changed or promoted landscape rights labels,
  0 inconsistent new access JSON vs recorded status, 0 raw admission flags.
- The eight original production/rehearsal SHA differences are *still*
  present and have **not** been silently rewritten.

The companion offline code
`scripts/build_cat_source_stage_append_review_v0.py`
produces a separate **manual**, source-byte-checked review queue from an
original checkout and independently exported inventories. That script
does **not** access SQL or perform the above insert operation; the rehearsal
was performed separately against the specifically selected nonproduction
Neon branch. No automatic production synchronization is authorised.

## Remaining release boundary

Source registration is **not** licensing, scientific/model suitability,
provider asset download or an insured exposure portfolio. The eight
version differences require independently reviewed old/new receipts
before either stage or production is updated. Promotion of the 81
rehearsal-only registrations into production needs an **explicitly
reviewed migration**, production precondition checks and a separate
post-write verification. Do **not** run unreviewed migrations on
`main` or infer CAT/Oasis/NextGen readiness from metadata coverage.
