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
- Read-only `registry.source_record` metadata SELECTs; no original
  provider data, database DML or model operation was performed.

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

## Branch-capacity blocker and bounded next action

Creating another isolated Neon branch named
`source-registry-stage-20261109-pinned-a5af7add`, parented on the historical
isolated stage, returned **HTTP 422: branches limit exceeded**. No branches
were deleted; no existing stage or production data was modified to make room.

The companion offline tool
`scripts/build_cat_source_stage_append_review_v0.py` now prepares a
**manual, source-byte-checked candidate list** using the pinned GitHub
inventory, separate stage/prod exports and canonical JSON checked out at
the pinned version. It validates Git blob SHA-1, also records SHA-256,
enforces source-access and landscape contract state and refuses to append
manifest admissions or identities already present in production. The
program produces **no SQL** and does not authorize a database write.

When an **independent isolated Neon branch is explicitly available**, the
next safe experiment is to re-run the pinned comparison and separately
rehearse an append-only metadata transaction with original-row fingerprint
parity, duplicate-ID/path rejection, and exact post-write readback. The
eight/nine version drifts require their own immutable revision evidence
and separate scientific/rights review. Do **not** run this against
`main` or infer model readiness from source-register coverage.
