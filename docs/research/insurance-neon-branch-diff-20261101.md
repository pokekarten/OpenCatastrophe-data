<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Insurance Neon branch-diff guard (2026-11-01)

Research-only, independent CAT database `insurance-risk-core` / `insurance`.
This is a **metadata and identity candidate diff**, not a migration, legal-entity
resolution, rights clearance, insured exposure observation or CAT-model approval.

## Reproducible non-destructive check

1. Explicitly select Neon **main** and run
   `research_runners/sql/insurance_neon_branch_manifest_v0.sql`.
   Save its single JSON result outside Git as `main.json`.
2. Explicitly select `validation-schema-20261031` and repeat; save it
   outside Git as `validation.json`. The database name is `insurance` on
   both branches, so checking `current_database()` does **not** prove which
   branch you selected.
3. Locally run:
   ```bash
   python -m scripts.insurance_neon_branch_merge_preflight_v0 \
     --main /private/main.json --validation /private/validation.json --details
   python -m unittest tests/test_insurance_neon_branch_merge_preflight_v0.py
   ```
   The process returns exit code 2 when manual review is needed; this is a
   deliberate fail-closed result, not a crash. It never writes to Neon or
   GitHub and never approves a merge.

The SQL emits only registry source identifiers, blob hashes, review/rights flags,
and organization-candidate link statuses. Do not commit connection credentials,
raw publisher bytes, unredacted proprietary source dumps or insurer portfolios.
Even these metadata exports should be held privately until reviewed.

## Observed read-only result (live independently selected branches, 2026-11-01)

| Measure | main | validation |
| --- | ---: | ---: |
| `registry.source_record` | 101 | 83 |
| `entity.organization_candidate` | 161 | 154 |

- Sources: **82 shared keys**, **19 only on main**, **1 only on validation**.
- Three shared source keys conflict: one Git blob hash difference
  (`landscape_file:sources-exposure-impact-validation`) and two separate
  rights/review-status disagreements
  (`official_api:usgs_comcat_2025_jan_m6_sample` and
  `official_fl_oir:2025_12_mir_original_full_company_policy_v1`).
  None can safely be overwritten just because the identifier matches.
- Organization candidates: 154 shared keys, seven only on main (SEC HMN
  research entries), zero only on validation; no mismatches in the
  identity-resolution status / linked-organization fields on shared keys.
- Newer research tables differ strongly across branches. Validation contains
  separately staged Florida/Texas research observations and a synthetic
  portfolio; main contains newer international insurer and hazard research.
  This manifest intentionally does **not** certify table equivalence or
  database-wide data convergence.

## Blockers and next causal action

- Review the one validation-only original Florida source record and the
  three same-key source disagreements with exact Git/publisher provenance
  and rights notes. No unconditional last-writer-wins upserts.
- Keep all source-specific model-input gates closed: researched Florida
  company statistics and Texas market ZIP counts are not observed
  company-ZIP insured buildings or individual TIV.
- `main` manual snapshot `pre-fl-tx-research-integration-2026-11-01`
  succeeded. Automatic snapshot schedule requests returned
  `backup schedule creation is not enabled for this project` for both
  branches, and a manual snapshot request on the non-root validation branch
  returned `not allowed to snapshot non-root branch`. Treat validation
  backup as **unresolved**; do not claim it is protected by a fresh snapshot.
- Coordinate any additive schema transfer with existing research PR #907
  (Florida/Texas) and PR #899 (insurer-directory) before migrations.
  Require a separate technical QA on the target branch, exact source rights
  and explicit review before production data/model admission.

The checks are offline and deterministic; the committed unit test suite has
six synthetic cases, including collisions, duplicate keys, and refusal to
authorize automatic merging.
