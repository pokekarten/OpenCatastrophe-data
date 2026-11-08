<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# FEMA Building Codes Save / FEMA-0173: original-XLSX source preflight

Research date: 2026-11-08. This is a **non-admission** research checkpoint, not an external-data asset or validation of any actual file bytes.

## Source identity and limits (official publication)

- [data.gov FEMA-0173](https://catalog.data.gov/dataset/aals-from-the-adoption-of-i-codes) identifies FEMA/Resilience/Risk Management Directorate as publisher, access level public, and one original Excel resource at `https://www.fema.gov/sites/default/files/documents/fema_building-codes-save-study-results.xlsx`. The data.gov **catalogue metadata** was modified in July 2024; that is *not* proof of the workbook data vintage, schema, or numeric contents. The catalogue references [government-works rights guidance](https://www.usa.gov/government-works), not an independently reviewed item-level licence.
- [FEMA Building Codes Save: A Nationwide Study (November 2020)](https://www.fema.gov/sites/default/files/2020-11/fema_building-codes-save_study.pdf) evaluates **buildings constructed 2000-2016**, explicitly noting incomplete assessor records for 2017/2018; hazards modeled are **flood, hurricane wind, and earthquake/seismic**. Dollars in the 2020 study's national AALA totals use **2020 USD**, not claims-year dollars or insurer premium. It models damage to buildings/contents but excludes business interruption, life-safety benefits, and extra code compliance construction cost. Main inputs include Hazus and proprietary CoreLogic parcels; results are model-derived, not observed insurance claims.
- [FEMA report appendices, Appendix A.2](https://www.fema.gov/sites/default/files/2020-11/fema_building-codes-save_study-appendices.pdf) describe an external sortable Excel results file and list tables A2-1 through A2-8. Examples include A2-6 (nationwide county AALA by building/contents and floor area) and A2-8 (positive, negative, neutral loss-avoidance categories by state). These are report *table captions*, **not verified worksheet names, column labels, row counts or evidence of workbook access**. Confirm actual workbook shape before applying any mappings.

## Acquisition blocker and precise outstanding checks

The original FEMA XLSX download URL is known from the catalogue, but binary retrieval in the 2026-11-08 research environment failed. **No original workbook bytes were inspected, no SHA-256 obtained, and no actual sheet names, values, or columns verified.** No FEMA XLSX or source-derived data are committed to Git.

Before any operational use, in an explicitly rights-authorized external processing environment:
1. Record exact retrieval URL, UTC timestamp, HTTP redirect chain, original file size, SHA-256, and applicable dataset/source rights; no raw external bytes or secrets in Git.
2. Inspect actual XLSX sheet titles, table/field headers, geography IDs (county/state/FIPS), hazard and occupancy columns, missing/negative/neutral entries, cell formulas, hidden/external sheets, units and year/currency base. Keep original workbook/version strictly outside Git. Do not extrapolate from the Appendix A captions.
3. Reconcile any compatible aggregate outputs with the reported FEMA national 2020 results; avoid summing overlapping physical building populations across perils. Record per-peril sampling frames and missing geography.
4. Fix split rules and potential Hazus/CoreLogic input overlap **before** using any reported modeled loss difference as a calibration benchmark or holdout. The workbook's AALA is not a vulnerability curve, independently measured claim outcome, insurer-specific insured loss, or event loss table.
5. Keep `rights_review_status=not_reviewed` and `admission_status=not_admitted` in the discovery registry until formal source-specific rights/science review approves an exact bounded model role.

## Narrow synthetic regression improvement

`research_runners/fema_bcs_aala_semantic_guard_v0.py` intentionally accepts *synthetic data only*, with paired risk baseline, annualized code scenario, perils, integer cents, and no event-loss/model claims. Its historical construction-cohort bounds now match **2000-2016** (inclusive), rejecting 2017/2018 whose source-building records were incomplete. This is a reproducible research constraint, not empirical validation. The guard cannot parse FEMA workbooks or claim AEP/OEP outputs.
