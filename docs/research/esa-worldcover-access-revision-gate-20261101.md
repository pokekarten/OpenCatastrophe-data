<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# ESA WorldCover v200: immutable access-contract revision comparison

**Purpose:** a read-only, fail-closed comparison of public OpenCatastrophe-data
source-access contracts. This is **not** an automated Neon update, an
external-data download, or a source-/model-admission approval.

## Pinned and independently observed versions (2026-11-01)

| Property | Existing CAT-only Neon source record | GitHub current source contract |
| --- | --- | --- |
| Git commit | `2c9cfeeec62c81609e63e58465f7882622054b7e` | `4f34c21eb257d5e6fccba742d4c1081cfdc0d078` |
| Exact Git blob SHA-1 | `830fff1705d6b29d8c88dc423a27c7254608ca50` | `2884e2f50b495eee3b399f55c08d43cfa100b602` |
| Access status | `documented_only` | `probe_ready` |
| Dataset rights status | `verified` | `verified` |
| Raw CAT dataset / insurer input approval | **none** | **none** |

Both revisions refer to the same public access contract:
`access/esa.worldcover.2021.v200.json`, with source identity
`esa.worldcover.2021.v200`. The current version changes **16 JSON fields**,
including allowed operations, a fixed sample tile, bounded TIFF byte ranges,
source sample digests, transport/rights notes, review date and access status.
This is a **material operational contract update**, not a harmless SHA refresh.

The CAT-only Neon `registry.source_record` is a canonical single-row registry;
it has no approved built-in revision history for this access contract. Do not
silently replace its old `git_blob_sha`, `git_commit_sha`, `raw_metadata` or
`review_status`. The insurance SQL migration inventory / replay DAG are under
separate review in OpenCatastrophe PRs #8, #11 and #13; this change deliberately
adds **no SQL** to those frozen inventories.

## Reproduction and safe usage

Fetch the two public Git **file blobs** by the frozen commits above into separate
local temporary paths (e.g. with `git show SHA:access/...` from a verified clone).
Use the *exact raw bytes*, including whitespace and final newline. Do not
reserialize parsed JSON before checking the blob identity.

```sh
python -m scripts.audit_access_contract_revisions_v0 \
  --old /private/old-worldcover-contract.json \
  --new /private/new-worldcover-contract.json \
  --old-blob-sha 830fff1705d6b29d8c88dc423a27c7254608ca50 \
  --new-blob-sha 2884e2f50b495eee3b399f55c08d43cfa100b602
python -m unittest tests.test_audit_access_contract_revisions_v0 -v
```

Exit code `2` means **material review required**; `0` means same semantic
content but **still no authority** to overwrite an existing database receipt;
`1` means invalid input/identity/hash. The checker computes Git's actual
object SHA-1 over the Git blob header and exact raw bytes, rejects duplicate JSON
keys at any depth, checks unchanged access/source identity, and reports only
changed field **paths** rather than full source contents. It never calls the
provider, database, cloud APIs, or writes external data.

## Next controlled database change (separate workstream)

1. Define a versioned, immutable `registry` access-revision evidence table with
   pinned source record, Git commit/blob identity and rights/status review.
   Validate on an isolated PostgreSQL 17/PostGIS branch before production.
2. Preserve this historical `documented_only` receipt and a separate
   `probe_ready` receipt; do not use last-writer-wins or automatically infer
   either source operation or model permission from the revision comparison.
3. Review the pinned SQL migration DAG and recovery/retention policy before
   applying new production DDL. Source-service authorization, redistributable
   raw bytes and actuarial exposure admission remain distinct.

No WorldCover TIFF, pixel array or insured property is persisted as part of
this audit. A Git metadata contract does not prove an insured building, a
property vulnerability function, or a loss run.
