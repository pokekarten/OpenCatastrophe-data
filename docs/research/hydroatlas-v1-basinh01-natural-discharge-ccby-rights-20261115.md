<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# HydroATLAS v1.0 — BasinATLAS H01 natural discharge: exact CC BY 4.0 rights boundary

Reviewed 2026-11-15. Source ID `hydrosheds.hydroatlas.v1`; not an accepted model input.

## Authoritative original sources and exact identity

- **Provider/product:** HydroSHEDS HydroATLAS version 1.0, BasinATLAS H01 **Natural Discharge** in Figshare article [9890531.v1](https://doi.org/10.6084/m9.figshare.9890531.v1), collective database CC BY 4.0.
- **Per-variable original catalogue:** [BasinATLAS_Catalog_v10.pdf](https://data.hydrosheds.org/file/technical-documentation/BasinATLAS_Catalog_v10.pdf), Hydrology **ID-H01** individual attribute information sheet. Its printed licence is **Creative Commons CC BY 4.0**. An independent low-resolution [catalogue copy](https://communities.unep.org/download/attachments/38306013/BasinATLAS_Catalog_v10_low_res.pdf?api=v2) exposes the same H01 sheet.
- **Legal combination:** [HydroATLAS_TechDoc_v10.pdf](https://data.hydrosheds.org/file/technical-documentation/HydroATLAS_TechDoc_v10.pdf), §4.1. HydroATLAS v1.0's collective database is CC BY 4.0 but each attribute column is individually CC BY 4.0 or ODbL 1.0. This H01 review does **not** cover all 281 attributes or third-party upstream WaterGAP files.
- **Exactly scoped fields:** `dis_m3_pyr` (annual mean), `dis_m3_pmn` (annual minimum), `dis_m3_pmx` (annual maximum). Units m³/s, taken at sub-basin pour point; annual extrema are computed from long-term monthly means, **not** return-period flood peaks.
- **Physical data semantics:** modelled **naturalized** discharge, WaterGAP v2.2 (2014 source product), reference period **1971–2000**; originally ~0.5° grid downscaled to HydroSHEDS 15 arc-second network. Nominal 15 arc-second output is not independent 500 m hydraulic observation. Source documentation flags additional uncertainty for snow/glacier/wetland/(semi-)arid regions.

## What is now evidenced

The exact HydroATLAS version-1 BasinATLAS H01 **three-column subset has a publisher-printed CC BY 4.0 data-reuse licence**, including commercial purposes subject to attribution and licence/modification requirements. This clears the *source-product-column legal ceiling* for research and commercially oriented exploratory work, **not** data acquisition, attribute-level quality, source-archive redistribution, model calibration or CAT input admission.

In authorized insurance Neon research `research.source_usage_rights_v0`, seven idempotently inserted decisions are keyed by exactly that original/version/column group: internal research, commercial analysis and metadata storage = **allowed (legal rights only)**; raw archive redistribution, automation, GIS sample persistence and publication of derived products = **conditional**. Every row has `scientific_model_admission=false` and `original_asset_admitted=false`. The wider all-attribute candidate remains `not_admitted`/licensing not fully reviewed; a narrow licence does not promote that candidate.

Existing Neon source sample **#70** is **public Figshare article metadata only**, not a source GIS archive or H01 numerical values. It remains research-only with consistent normalized JSONB SHA-256 and `source_byte_persistence_authorized=false`.

## Reproducible executable evidence and negative controls

Run the strictly SELECT-only SQL `research_runners/sql/hydroatlas_v1_basinh01_rights_only_gate_v0.sql` against the authorized insurance research database. It always emits **one** result row and fails closed when the precise rights-scope record, expected use-case classification, original H01 catalogue URL, exact sample #70, normalized sample hash or separate candidate non-admission is absent. No GIS columns/values, source bytes, credentials or private DB connection string are printed or committed.

2026-11-15 observed authorized database checks:
- Real sample #70 and all seven exact rights decisions: **PASS** (rights-only).
- Replacing only exact metadata sample ID 70 by a nonexistent ID: **FAIL** (missing sample cannot yield an empty/false-positive result).
- Replacing the exact product/column scope by nonexistent version identity: **FAIL**.
- No new provider assets downloaded; no model training/calibration/validation authorization, insurer/TIV mapping or source/asset admission; no change to provider service access contracts.

## Next missing gates

1. Select a *provider-approved exact original* BasinATLAS release/archive with immutable source byte SHA-256; clarify per-asset automated transfer and sample storage policy.
2. On a trusted bounded runner, acquire one small original-source **H01 only** geographic sample outside Git, record original bytes + version + hash, and verify numeric field types, missing-value codes, CRS, geometry/support and temporal semantics.
3. Independently compare this historic long-term naturalized discharge with an official, time-matched local gauge/flow observation holdout, noting method/model limitations. This is contextual hydraulic covariate screening, **not** flood-event hazard, vulnerability, claims or CAT-loss calibration.
