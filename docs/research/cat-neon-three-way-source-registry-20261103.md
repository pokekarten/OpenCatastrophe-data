<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Three-way CAT source registry snapshot and rights boundary — 2026-11-03

**Research-only, read-only audit.** Compares (1) public GitHub pinned
source/access file listing, (2) the independently isolated CAT Neon
research staging branch and (3) CAT Neon production/main. It **never**
executes database SQL, opens a network URL, reads original licensed
provider bytes, authorizes rights, or runs a CAT/NextGen model.

## Actual observed snapshot

- GitHub repo: `pokekarten/OpenCatastrophe-data`
- Pinned public **main** SHA: `095cc76f82ebb213289dfebec14e99b56020182e`
- CAT-only Neon project: `insurance-risk-core`, DB `insurance`
- Isolated metadata stage (not production):
  `access-contract-revision-proof-20261103`,
  `br-steep-lab-baeo8bmc`
- Actual production branch: `main`, `br-late-recipe-ba1cr8hc`

| Registry path class | GitHub | In isolated stage | In production |
| --- | ---: | ---: | ---: |
| `landscape/sources*.json` | 64 | 64 | 41 |
| Canonical `access/*.json` (excluding inventory) | 66 | 66 | 52 |
| **Total canonical metadata files** | **130** | **130** | **93** |

There are **36** exact Git-blob-matching, stage-present,
production-absent **manual append candidates**. These are **files**,
not 36 independent CAT models or rights-cleared dataset products.
The stage has no missing canonical files, but four file versions
differ from current GitHub and must **not** be silently replaced:

- `landscape/sources-peer-cat-repositories-20261102.json`
  (newer public source-family research; **not yet in production**).
- `landscape/sources.json`
  (existing canonical research registry, changed original blob).
- `access/esa.worldcover.2021.v200.json`
  (existing older `documented_only` vs newly `probe_ready`
  source contract; rights/probe changes are substantial).
- `access/noaa.coops.water-levels.json`
  (existing older `documented_only` vs newly `probe_ready`).

The last three also have production-GitHub SHA drift.
Production/main continues to contain **114 `registry.source_record` rows
overall** (including 15 manifest identities and six noncanonical
access-classified historical research receipts), with **zero**
`admissible_for_raw=true` rows. Staging adds no source/model
admissions. Do not misinterpret registered source metadata as actual
downloaded provider records.

One legitimate original naming exception needs explicit preservation:
`access/ucsb.chc.chirps.v3.0.documented.json` has
`source_id=ucsb.chc.chirps.v3.0` and
`source_key=access:ucsb.chc.chirps.v3.0`. Its `.documented`
filename suffix is a file role, **not a second source identity**.
The new comparator allows this exact suffix pattern only if both
source ID and key match, and regression-tests a forged unrelated ID.

## Reproduce without database credentials in this script

1. Re-fetch and pin the immutable repository commit immediately before
   creating the exported GitHub directory listing. Concatenate both
   REST `contents/landscape?ref=<SHA>` and
   `contents/access?ref=<SHA>` arrays. Only original
   `path`, `type`, `sha` metadata is necessary.
2. Independently export the following **read-only** query once against
   the **explicitly selected staging branch** and once against
   **production/main**. Include only source register metadata and
   leave out the original JSON payloads, company data and secrets:

```sql
SELECT source_key, source_id, classification, repo, git_path,
       git_blob_sha, review_status, rights_status, admissible_for_raw
FROM registry.source_record
WHERE classification IN ('landscape_candidate','access_contract')
ORDER BY git_path;
```

3. Run the offline comparator on the three exported JSON arrays:

```sh
python scripts/audit_cat_source_registry_three_way_v0.py \
  --github-inventory /private/gh-tree-pinned.json \
  --stage-export /private/neon-stage-metadata.json \
  --production-export /private/neon-main-metadata.json
python -m unittest tests.test_audit_cat_source_registry_three_way_v0 -v
python scripts/check_all.py
```

Exit 0: exact source identities and blobs already match, but **no
automatic production synchronization** is permitted. Exit 2:
review required, including candidate append, rights or version drift.
Exit 1: invalid or ambiguous inventory, duplicate keys or forbidden
source admission. The script deliberately outputs **no INSERT, UPDATE,
DELETE or migration**.

## Required separately reviewed migration

The existing untouched rehearsal branch
`source-registry-production-append-rehearsal-20261103`
(`br-solitary-truth-ba46euvb`) was cloned from production for a
future exact-transaction challenge; its 114 rows still match
production. **No migration was executed there by this audit.**
Only a later explicitly approved, bounded append-only metadata
transaction should be rehearsed, with controlled original-row
fingerprint parity, duplicate source ID/path rejection and a
post-transaction readback before any production decision.

The four version conflicts need immutable old/new per-source
receipts and rights review, separate from the 36 missing file rows.
The earlier two access revision proofs are in the
isolated `research.access_contract_revision_evidence_v0`
table, with UPDATE/DELETE forbidden and no production change.
Future release must retain the distinction between
`documented_only`, `probe_ready`, `restricted_by_terms`,
original data rights, insurer exposure, science and CAT model approval.
