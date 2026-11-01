<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Synthetic exposure + illustrative CAT-XL relational smoke fixture (v0)

**Scope:** independent demonstration of the *insurance database schema and PostGIS joins*, not a real exposure portfolio, not a CAT loss model, and not evidence about an insurer or its treaty program.

## Exact separation and safeguards

- The only intended target is the separate Neon `insurance-risk-core` project, database `insurance`, branch `validation-schema-20261031`. The authoritative production `main` must not be changed by these scripts. The SQL aborts if two branch-specific research objects are absent; this is a safeguard, **not** proof of branch identity if the schema is later cloned. An operator must still explicitly choose the validation branch.
- All 12 invented coordinates are an arbitrary grid with **no claimed real building/address correspondence**. All 12 values are round, arbitrary EUR numbers created from a closed-form formula, not estimated or obtained from insurer market exposures. No source-data bytes, real insured property records, private files, insurance contacts or insurer identity rows are used.
- `portfolio_type='synthetic'`, `organization_id IS NULL`, `assumption_status='synthetic'`, `source_key IS NULL`, and `assumption_metadata.model_input_approved=false` are intentionally preserved. No source discovery entry, real insurer, building register or flood/earthquake record is promoted.
- The fictional `cat_xl` treaty has **no cedent or reinsurer linked**. The test numbers (EUR 200,000 attachment, EUR 500,000 layer limit, one reinstatement) are unrelated to any actual contract. Loss ordering, actual reinstatement premium, event attribution and contract wording are deliberately **unspecified**; the row does not authorize a financial treaty payout calculation.

## Reproducible execution (only on isolated validation branch)

1. Select the independent Neon validation branch; **never** default to `main`. Verify its presence of `exposure.market_policy_stock_research_v0` and `research.fl_nc_legal_naic_overlap_research_v1` and confirm that it is not the production branch in the Neon console/API.
2. Apply `research_runners/sql/synthetic_exposure_smoke_v0.sql` using a PostgreSQL 17/PostGIS connection to that validation branch. The single `DO` block either passes its inserts and invariants or fails atomically. The key/version/unit/contract inserts use explicit conflict handling so replay cannot produce duplicate rows.
3. Execute `research_runners/sql/synthetic_exposure_smoke_invariants_v0.sql` in the **same validation branch**, and require every returned `passed` flag to be `true`. Do not treat zero failed smoke checks as real peril calibration.
4. Compare `main`: its `exposure.portfolio`, `exposure.exposure_unit`, `insurance.contract` and `model.simulation_run` must remain unchanged. This fixture never writes `main`.

## Observed execution on 2026-11-01 (Neon live SQL)

- Validation branch `br-summer-sky-bawujqu8`: **1 portfolio**, **1 portfolio version**, **12 synthetic exposure units**, **1 fictional CAT-XL contract**, **1 portfolio-contract link**.
- Invented aggregate example sum = **EUR 3,150,000**, exactly `sum(100000 + 25000*n)` for `n=1..12`. All twelve have synthetic assumption flags and independent illustrative EPSG:4326 points.
- **21/21 read-only relational/guard assertions passed** against the live validation database, including synthetic status, absent real organization link, no external source rows, unit/location counts, sum conservation, contract properties and no simulations attached to the fixture.
- A second execution returned without error and counts remained exactly 1/12/1/1 (portfolio/units/contract/link), demonstrating idempotence under the observed state.
- Production `main` remained at **0 portfolio / 0 exposure units / 0 contracts / 0 simulation runs** after the validation execution.

## Next causal step

Build a **separate, wholly synthetic loss-event adapter** with declared loss ordering and complete fictional contract terms, then verify that `ground-up -> gross -> ceded -> net` reconciles for each event, including aggregate/reinstatement conventions. Do **not** bind the test portfolio to actual USGS/Copernicus events or to verified insurer entities without a source-specific rights/scientific admission and appropriate geocoded, valued exposure evidence. A genuine CAT model remains unproven until an admitted peril event catalogue, vulnerability/intensity relationship and a reproducible simulation implementation exist.

## Testing boundary

The two SQL scripts have been executed in Neon with explicit validation branch IDs. Full repository `python scripts/check_all.py` was not run in the local Linux environment because external GitHub DNS/network access to clone the branch was unavailable; exact-head GitHub CI should be reviewed before merging this draft.
