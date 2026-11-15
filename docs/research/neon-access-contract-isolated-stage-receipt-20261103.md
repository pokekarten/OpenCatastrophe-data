<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Isolated Neon access-contract metadata staging — actual receipt (2026-11-03)

**Executed only on isolated CAT-only Neon** project `insurance-risk-core`,
database `insurance`, branch `access-contract-metadata-stage-20261103`
(`br-wild-wave-bazb2ck2`). The branch was cloned from the previously
validated *non-production* landscape staging branch `br-raspy-cell-ba5j7191`.
**Production main was not modified.**

Original GitHub repository `pokekarten/OpenCatastrophe-data` was pinned to
main commit `5481c214d5e2c233d4d5cb95204f67d584f53599`.
The source access contract registry already had its own conservative
`scripts/audit_insurance_access_sync_v0.py` offline comparator. This research
receipt does **not** duplicate it or authorize automated registration.

## Exact live inventory and staging result

| Observation | GitHub pinned | Neon production main | Isolated access stage |
| --- | ---: | ---: | ---: |
| Canonical `access/*.json` contracts | **63** | **52** | **63** |
| GitHub-only contract paths | — | **11** | **0** |
| Shared paths with differing Git blob SHA | — | **2** | **2** |
| Entire `registry.source_record` rows | — | **114** | **146** |
| Landscape file receipts | **62** (at prior pinned tree) | **41** | **62** |
| Original raw data admitted | — | **0** | **0** |

The stage contains **11 new, metadata-only, immutable Git blob-pinned
`access_contract` receipts**, in three bounded append batches. All original
contract JSON was retrieved at the same pinned repository commit and checked
against the independently listed Git blob SHA, `access_id`, source IDs, status,
`rights_and_policy.dataset_rights_status` and probe mode. One row per new
canonical access contract was inserted with `admissible_for_raw=false`.
No original product records, credentials, measurements or provider bytes were
downloaded, stored or model-admitted.

New metadata contract paths:

- `access/geoglows.rfs-v2.s3-catalogue.documented.json`
- `access/nasa.giss.gfwed.geos5-v2.http-file.documented.json`
- `access/nasa.opera.dswx-s1.v1.cmr-discovery.json`
- `access/noaa.ncei.ghcnd-central-park-gzip.json`
- `access/noaa.nodd.ghcnd-central-park-complete.json`
- `access/noaa.nodd.ghcnd-central-park-range.json`
- `access/noaa.nodd.ghcnd-version-country.json`
- `access/pbl.grip4.catalogue.documented.json`
- `access/smithsonian.gvp.votw.v5-4.wfs.documented.json`
- `access/ucsb.chc.chirps.v3.0.documented.json`
- `access/usgs.3dep.s1m.tnmaccess.json`

Status distribution of those eleven: **5 `documented_only`**,
**5 `probe_ready`**, **1 `restricted_by_terms`**.
The Smithsonian source retains `rights_status=restricted` and a disabled
probe. GEOGLOWS and GRIP4 retain `rights_status=conflicting`.
Probe-ready status is **only historical contract metadata** and is not
authority to execute an external request from this staging exercise.

### Two unresolved historical contract revisions, held fail-closed

Neither changed contract was overwritten:

1. **ESA WorldCover 2021 v200**
   `access/esa.worldcover.2021.v200.json`: old Neon blob
   `830fff1705d6b29d8c88dc423a27c7254608ca50`, latest GitHub
   `2884e2f50b495eee3b399f55c08d43cfa100b602`.
   Exact Git comparison shows **24 changed nested fields**; in particular
   original `documented_only` / `probe_contract.mode=none` became
   `probe_ready` / `mode=head`, with additional bounded TIFF header/table/
   block sample operations. This is an **access authority** change, not
   an innocuous Git hash refresh.
2. **NOAA CO-OPS Water Levels**
   `access/noaa.coops.water-levels.json`: old Neon blob
   `53aa5e6e9f23dc0ddd153fae1c57a4752f31b0aa`, latest GitHub
   `f617e0a1915e84d0dbe51f08532793c7fb8accb4`.
   Exact Git comparison shows **17 changed nested fields**; the contract
   shifts from `documented_only` / `probe_contract.mode=none` /
   `api_terms_status=separate_unreviewed` to `probe_ready` /
   `mode=provider_specific` / `api_terms_status=separate_reviewed`.
   This must be recorded as an independently reviewed immutable contract
   revision, never overwritten in the prior registry row.

In particular the fixed NOAA six-minute water-level test cannot be treated
as verified insured coastal flood loss, and a WorldCover tile block cannot
be treated as measured building value, calibrated vulnerability or
automatically eligible model input.

## Independent repeatable check

The unchanged GitHub file
`research_runners/sql/insurance_access_contract_stage_readonly_verify_20261103.sql`
was **executed directly and read-only** on `br-wild-wave-bazb2ck2`:

- Total 146, landscape 62, manifest 15, access-classified 69.
- Exactly **63 canonical** `access/*.json` contracts plus six historical
  noncanonical research receipts classified as `access_contract`.
- **11 newly staged**, **52 historical canonical**, 63 unique access keys
  and 63 unique canonical file paths.
- **0** mismatched access IDs, original Git commit/blob hash malformations,
  rights/status reinterpretations, or raw-data admissions.
- Both historical version conflicts preserved as *previous* original
  metadata, not rewritten or upgraded.
- Explicitly **false** for automatic production promotion, restricted-source
  probing, provider-byte acquisition and insurance CAT-model input.

The **previously existing 135 entire `source_record` metadata rows**
were independently fingerprint-compared on parent and child branches:
both have digest `a01163704659e7dce6e71baae46cff4f`.
The MD5 digest is a **change-detection receipt**, not cryptographic proof
of provider authenticity. No original rows were changed or removed.

Run the exact read-only SQL on an explicitly selected Neon branch and run
the companion Python source assertions
`tests/test_insurance_access_contract_stage_readonly_verify_20261103.py`.

## Release boundary

Do **not** merge the staging branch into production. Any later
production metadata-only append needs a separate reviewed migration pinned
to fresh GitHub/Neon snapshots and rights-state regression checks. The two
changed prior access contracts require append-only **revision histories**
that retain old and new Git blobs and their different permission semantics;
the canonical `registry.source_record` primary-key row cannot simply be
replaced. Real data downloading, source-level science, licensing and
model-input admission are separate approvals.

This receipt authorizes **no** GitHub Actions workflow bypass and **no**
private data publication, remote Mac execution, model backtest or
insurance portfolio import.
