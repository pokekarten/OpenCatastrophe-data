<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Florida OIR / Texas TDI isolated research Neon re-verification (2026-11-03)

**Scope:** Executed the unchanged, read-only
`research_runners/sql/exposure_research_invariants_v0.sql` from PR #907
at GitHub head `605fc59e4b700f4f25333144196cc69f3ce84a49`
(Git blob `06beeba68a28a0dfcc990921aef7961adc4d6b8a`) against
Neon `insurance-risk-core` / database `insurance` / **isolated validation
branch** `validation-schema-20261031` (`br-summer-sky-bawujqu8`).

The query was a single `WITH ... SELECT` statement. No source tables or
views were modified, no provider bytes were fetched, and **main** was not used.

## Actual checks

All **11 of 11** data-structure and arithmetic invariants returned true:
- Florida original source cardinality, policy counts, reported exposure
  and premium sums conserved; component arithmetic reconciled.
- Florida reporting-universe caveat and `model_input_approved=false` enforced.
- Texas ZIP/policy keys and nonnegative stock sums conserved; negative
  counts quarantined; no invented insurer-ZIP identity or insured TIV.

Separately queried **existing** research views on the same validation branch:

| Finding | Live result |
| --- | ---: |
| Florida reported company groups | 160 |
| Florida groups still blocked by unknown regulatory reporting universe | 160 |
| Florida approved model groups | 0 |
| Texas source research rows | 9,194 |
| Texas quarantined negative source rows | 4 |
| Texas rows with legal insurer per ZIP | 0 |
| Texas rows with actual insured TIV | 0 |
| Texas model-approved rows | 0 |

## Hard release boundary

These are **staged research observations on the validation branch**, not an
original authenticated live carrier/ZIP exposure feed. The existing SQL files
define research views but this verification **did not execute** their
`CREATE OR REPLACE VIEW` statements. Original source rights, reporting
universe, insurer-geography granularity, exposure-to-building identity,
peril-specific underwriting, policies/limits/deductibles and correct hazard /
vulnerability matches remain unverified.

**Do not** use the results as geocoded insurer portfolio values, an insured
loss sample, market accumulation, CAT-XL pricing, or source-scientific admission.
No automatic Neon main DDL/DML or source acquisition is authorized.

This receipt makes the existing validation query independently reproducible;
it does not resolve the outstanding source rights/coverage gates.
