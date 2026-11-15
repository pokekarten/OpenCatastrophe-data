<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Source-contract revision staging: fresh Neon branch rehearsal (2026-11-02)

**Scope:** `insurance-risk-core` / database `insurance` only. Non-admission metadata research; no raw source acquisition, hazard event, insurer exposure, loss event or production schema write. This report records a **real, isolated Neon execution**, not a claim that GitHub CI has a live database connection.

## Exact source baseline and isolation

- Origin: existing Neon default `main` with **114** `registry.source_record` rows; `registry.source_contract_revision_v0` did not exist on that parent.
- Rehearsal branch: `pr1105-source-revisions-rehearsal-20261102`, created from default `main` specifically for this PR.
- Postgres major/runtime: **17.11** at check time; core `sha256(bytea)` was available without installing `pgcrypto`.
- Pinned baseline fingerprint for the **six staged source-record fields** (`source_key`, `git_commit_sha`, `git_blob_sha`, `git_path`, `raw_metadata`, `review_status`): `dce4e12c3aa9385c4a5b6805b1ad13682e2f7f91969eb1b7ed302c14c78fa822`.
- Fingerprint uses sorted `source_key`, PostgreSQL `jsonb_build_object` text serialization, `E'\\n'` record separation, UTF-8 and built-in SHA-256. This is a controlled **snapshot-drift** gate for the pinned Postgres representation, not an independently authenticated provider-data hash.
- The initial end-to-end rehearsal ran the actual six SQL steps from `research_runners/sql/insurance_source_contract_revision_stage_v0.sql` within **one Neon transaction**: snapshot guard, table creation, schema guard, historical INSERT, ESA WorldCover pointer INSERT, revision guard. All steps succeeded. The full transaction was executed a second time with no duplicate or new rows.
- Following this rehearsal, the snapshot guard was strengthened to compare the full SHA-256 fingerprint. The **revised entire six-step transaction** also succeeded on the same isolated branch; it was an idempotent rerun rather than a second virgin-schema creation.

## Verified isolated-branch result

| Check | Observed |
| --- | ---: |
| Total historical and new source-contract revision receipts | **115** |
| Distinct source identities | **114** |
| Legacy receipts preserved with `receipt_kind=neon_historical` | **114** |
| New strictly pinned ESA WorldCover Git metadata pointer | **1** |
| Unauthorized `raw_import_allowed` / `model_input_approved` flags | **0** |
| Historical receipt-to-`registry.source_record` semantic conflicts | **0** |
| First and last `recorded_at` after repeat runs | **2026-11-02 19:01:15.890 UTC** |

The repeated migration did **not** rewrite timestamp fields. The source SHA-256 fingerprint independently matched between the production parent and the fresh test branch, before any changes to the test branch's `source_record`.

A read-only hypothetical source drift substituted `"synthetic_tamper"` for the selected WorldCover `raw_metadata.status` field in a SELECT-only CTE: the recomputed fingerprint was `fce0f137c04ccef8f031151e6fa77e0e8129ca900a220cf2c925273bbc8ac8ab`, **not** the pinned baseline. No actual source row was edited. The `$schema_guard$` and `$revision_guard$` were also run independently as read-only PostgreSQL `DO` checks on an earlier isolated staging branch; both passed.

## Repeatable read-only verifications

```sql
SELECT count(*) AS revisions,
       count(DISTINCT source_key) AS sources,
       count(*) FILTER (WHERE receipt_kind='neon_historical') AS historical,
       count(*) FILTER (WHERE receipt_kind='github_pinned_review') AS new_metadata,
       count(*) FILTER (WHERE raw_import_allowed OR model_input_approved) AS unsafe
FROM registry.source_contract_revision_v0;

SELECT count(*) AS conflicts
FROM registry.source_record AS s
LEFT JOIN registry.source_contract_revision_v0 AS r
  ON r.source_key=s.source_key AND r.git_blob_sha=s.git_blob_sha
WHERE r.source_key IS NULL
   OR r.contract_record IS DISTINCT FROM s.raw_metadata
   OR r.git_commit_sha IS DISTINCT FROM s.git_commit_sha
   OR r.contract_status IS DISTINCT FROM s.review_status;
```

Run those only against the designated **staging branch** after an isolated rehearsal. For production, read-only `to_regclass('registry.source_contract_revision_v0')` remained **NULL**, with **114** source records, **0** real exposure units and **0** simulation runs. The rehearsal did not execute migration DDL/DML on production.

## Remaining gates

This verifies a specific, unchanged snapshot and idempotent database behavior, not unrestricted source rights. A changed legitimate source registry **must** trigger review and an explicitly updated fingerprint rather than silently pass. Independent review still needs to approve the full schema and original source permissions before any production migration. The ESA WorldCover pointer is **metadata-only**, `raw_data_import=prohibited`, `model_admission=prohibited`, and all original source-data acquisition and CAT-model admission gates remain false.
