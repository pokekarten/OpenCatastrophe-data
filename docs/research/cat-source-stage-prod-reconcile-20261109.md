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
