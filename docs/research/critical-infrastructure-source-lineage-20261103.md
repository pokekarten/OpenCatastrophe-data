<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Critical-infrastructure damage source lineage and acceptance boundaries — 2026-11-03

**Research only:** no licensed data acquisition, provider feature query, insurance data, model run or Neon writes. Three source products are canonical research candidates in [JSON](../../landscape/sources-ci-vulnerability-surveys-20261103.json) and [generated Markdown](../../landscape/sources-ci-vulnerability-surveys-20261103.md).

## What is genuinely additive

1. **Nirandjan et al. V1.1.0 [original Zenodo record](https://zenodo.org/records/13889558)**: the primary 3-table data includes source quality/curve metadata **D1**, physical fragility and vulnerability curves **D2**, and infrastructure cost tables **D3**; unlike already registered `sebkrantz.infrastructure-vulnerability-curves.2026` derivative, the original tables include cost evidence and correction history. This is *upstream*, not independent.
2. **[NHERI SimCenter DLML](https://github.com/NHERI-SimCenter/DamageAndLossModelLibrary)**: a genuine versioned model-parameter store with separate `fragility`, `consequence_repair`, `loss_repair` CSV + JSON metadata. Collections include Hazus and FEMA P-58 plus other research. The underlying model families must not be double-counted as new observations. Pin Git tag, source model version, hazard, input/output units and asset taxonomy before comparing results.
3. **[NWS preliminary DAT FeatureServer](https://services.dat.noaa.gov/arcgis/rest/services/nws_damageassessmenttoolkit/DamageViewer/FeatureServer)**: source-level damage points (0), lines (1) and polygons (2). The already registered NCEI Event Footprint Catalog can derive from NWS DAT; these are correlated, not independent observed events.

## Source identities and cautious join directions

| ID | Original identity | Existing join family | Never infer |
| --- | --- | --- | --- |
| `nirandjan.ci-physical-vulnerability.v1.1.0` | Zenodo record 13889558 / version 1.1.0 / three Excel files | `sebkrantz.infrastructure-vulnerability-curves.2026` and reference asset taxonomy | 394 derivative curves exhaust original fragility/cost table, or a repair count is a 0–1 damage fraction |
| `nheri.simcenter.dlml.versioned-model-library` | Pinned library release/tag + per-dataset collection | FEMA Hazus / P-58, other model curves | BSD-3-Clause repository grant proves every provider dataset reuse right, or all models are independent |
| `noaa.nws.damage-assessment-toolkit.preliminary` | NOAA live FeatureServer / layer 0, 1, 2; per-feature event ID | `noaa.ncei.event-footprint-catalog.2026` / `noaa.ncei.storm-events` | Survey points measure insurer claim amounts, all damage sites are sampled, or strange global min/max dates are reliable |

## Source-specific technical preflights after rights review

### Nirandjan exact file identity and science
Provider publishes three files: `Table_D1_Summary_CI_Vulnerability_Data_V1.1.0.xlsx`, `Table_D2_Hazard_Fragility_and_Vulnerability_Curves_V1.1.0.xlsx`, and `Table_D3_Costs_V1.1.0.xlsx`. Publication metadata lists MD5 fingerprints `4f333d943952dc3f41037db55b14932d`, `be78fec572a0833938fcbaab0540468e`, `3517d7b9408e3c68a56a36465029da21`. These are **provider metadata claims, not independently verified original receipts**. Test hashes and validate three workbook schemas once legally cleared; assign original curve IDs and exact repair-cost basis. In v1.1.0, E16.24 is labelled *Repair rate* rather than *Damage factor*, F2.1-3/F21.3b/L7.* received corrections. Never treat output labels as interchangeable; forbid silent dimensionless coercion.

### DLML per-library release gate
Inspect exact tag/commit and subset in `src/dlml/data` for 3.x or legacy layouts for 2.1.0. Validate that CSV columns and paired JSON model metadata can be used with a narrowly defined asset and demand measure; separate damage state, repair cost and repair time. Crosswalk source citations against existing GEM/EFEHR/FEMA lines to prevent double-counting.

### NOAA DAT event survey metadata gate
Read only provider-published service/layer metadata after terms review; layer IDs 0/1/2, CRS, available fields, object identifiers, date fields, paging and maximum record count must be pinned. Report anomalous service time extents as a **quality issue**, not literal ancient/future events. Do not query all features, use photos, addresses or private details before policy review. Match events to NCEI Storm Data by verified local time and source field IDs, not spatial proximity alone.

## Acceptance gates
1. Record exact source-specific licence and commercial derivative permissions, source version/release and original provider data hashes.
2. Validate geographic/temporal coverage and data-collection biases; establish immutable event/model IDs.
3. Implement a narrow synthetic-only curve semantics unit test (repair-rate vs fractional loss) before ingesting real source arrays.
4. Review and approve a model-specific `manifests/` entry only after an independent scientific quality assessment. An entry in `landscape/` remains `not_admitted`.

**Cross-check:** WRI Aqueduct Floods, CEMS/GloFAS, GFD MODIS, GEM global seismic vulnerability, NCEI Storm Data, NCEI Event Footprint Catalog and prior `sebkrantz` curve export were already registered. This source pass does not duplicate those provider identities or promote their model rights.
