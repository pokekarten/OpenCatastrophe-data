<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Insurance CAT pipeline: non-vacuous two-branch evidence snapshot (2026-11-01)

This is a **live CAT-only Neon read-only check**, not a new data source or
permission to create real insurer portfolios. The database is `insurance`
in project `insurance-risk-core`. The SQL preflight
[`research_runners/sql/insurance_cat_nonvacuous_readiness_v0.sql`](../../research_runners/sql/insurance_cat_nonvacuous_readiness_v0.sql)
runs on the shared physical schema on **both** Neon branches.

## Why this exists

A query such as `NOT EXISTS (SELECT 1 FROM model.simulation_run WHERE ...bad...)`
passes with *zero* simulations. That is a useful integrity assertion but
**not** evidence the CAT model can run. The new query reports:
- `observed_rows`: source records/physical stored objects, including synthetic;
- `structurally_qualified_rows`: conservative positive prerequisites,
  *not a licence or scientific admission*;
- `evidence_status`: explicitly `MISSING_RECORDS`,
  `RESEARCH_OR_UNQUALIFIED_ONLY`, or
  `STRUCTURAL_EVIDENCE_PRESENT_NOT_ADMITTED`.

`automatic_model_admission` is always `false`. This is deliberate:
nonzero counts cannot, on their own, prove rights, insurer attribution,
physical model fitness, catastrophe vulnerability, claims quality,
contract terms or loss calibration.

## Live readback

| Core object / stage | Main observed | Main structural candidates | Validation observed | Validation structural candidates |
| --- | ---: | ---: | ---: | ---: |
| Source metadata | 104 | 0 | 83 | 0 |
| Content artifacts (original bytes/receipts in CAT DB) | 0 | 0 | 0 | 0 |
| Verified legal organizations | 22 | 22 | 22 | 22 |
| Portfolios | 0 | 0 | **1 synthetic** | 0 |
| Exposure units | 0 | 0 | **12 synthetic** | 0 |
| Hazard event catalogues | 0 | 0 | 0 | 0 |
| Physical hazard events | 0 | 0 | 0 | 0 |
| Reinsurance/retro contract rows | 0 | 0 | **1 synthetic** | 0 |
| Source+parameter pinned model versions | 0 | 0 | 0 | 0 |
| Loss artifacts | 0 | 0 | 0 | 0 |
| Completed shared-event 10,000-year run candidates | 0 | 0 | 0 | 0 |

This was executed against both live branches and then rerun using the
exact saved SQL file in GitHub. The source registry can change due to
parallel workers, so the counts are an observation, not a permanent baseline.

## Other independent context checks on main

- `research.cat_pipeline_evidence_v0` independently reports **104
  registered source documents**, **100 staged research observations**,
  **zero approved observations**, **zero** raw-admitted artifacts,
  **zero** model versions, **zero** admitted loss artifacts and
  **zero** joint insured/retro 10,000-year runs.
- `research.cat_source_bridge` contains **nine** bridge proposals,
  all `metadata_design_only`; no required original artifact SHA
  combination is fully proven. They are not operational joins.
- `research.natural_earth_country_locator_v0` holds only **two**
  present-day, source-hash-attributed national geometry research rows:
  DE and FR; geometry is SRID 4326 and PostGIS-valid, but neither is
  an admitted hazard or insured exposure. Important nuance: the FR
  source feature preserves original `ISO_A2='-99'` while the
  normalized research `country_code='FR'`; a consumer must not
  assume those columns are identical.
- `registry.source_record` has **10** empty canonical URLs in its
  104-entry main research registry. Some are broad discovery indexes,
  not downloadable exact dataset URLs; treat these as metadata
  granularity issues, not assumed dead provider links.

## Next causal path

1. Keep Florida/Texas original provider reports isolated and
   unadmitted while confirming commercial rights and time/selection
   parity. The 282-row Florida preview is an exact 282-key subset of
   the 442-row original source report, not 282 extra exposure risks.
2. Choose **one explicit peril, region and loss/validation window**;
   link pinned original hazard intensity to a geolocated, valuation-
   qualified building inventory, with separate source-specific rights.
3. Require vulnerability function version, units/intensity measurement
   mapping and independent holdout, plus a clear treatment of
   insurance penetration and uncertainty; geographic stock is
   **not** insured TIV.
4. Keep real insurer treaty terms, reinsurance, retro, annual event order,
   reinstatement and inuring rules distinct from synthetic toy examples.
5. Pin a runnable model version, source artifacts, scenario seeds,
   shared-year namespace and financially reconciled event loss output
   before claiming an independent real CAT financial simulation.

Caution: The portable SQL scorecard is a *prerequisites monitor*,
not a full scientific model-admission gate. In particular it does
not currently inspect vulnerability calibration, peril-specific
insurance terms, retrocession inuring or independent financial holdouts
in depth. The already existing main-only
`research.cat_pipeline_evidence_v0` remains a more specific global
CAT admission gate and currently reports **BLOCKED_MISSING_INPUT_EVIDENCE**.

## Re-execution

Run the saved SQL file once on `main` and again on
`validation-schema-20261031` with the explicitly selected
Neon branch ID and database name `insurance`. Never use only the
database name to infer branch identity. Save only the small aggregate
diagnostic results in CI logs or research notes; do not publish original
insurer customer data, source bytes, private credentials or individual
model portfolios.

This read-only checkpoint performed **no Neon schema/data changes**.
