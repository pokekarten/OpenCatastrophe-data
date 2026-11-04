<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# NHSL v1.0 settled-area aggregate to Oasis OED staging: first executable boundary

**Date:** 2026-11-04. **Purpose:** make the registered Canadian `can.nrcan.nhsl.physical-exposure.2016-2020` exposure candidate easier to assess and eventually use without silently converting an area-level **modelled public exposure estimate** into a real site-level insured-location portfolio.

**Implementation:** [one-row, bounded offline preflight](../../scripts/nhsl_oed_staging_preflight_v0.py) with [synthetic-only negative tests](../../tests/test_nhsl_oed_staging_preflight_v0.py). This is *not* an OED exporter, not an insurer portfolio, not NHSL source admission, and not a native Oasis execution.

## Original dictionaries, not invented source fields

- [NHSL source-published physical exposure attribute descriptions](https://github.com/OpenDRR/national-human-settlement/blob/main/docs/_data/nhsl_physical_exposure_attributes.yml), read from GitHub on 2026-11-04, blob SHA `d54f926c6ee1309f8c8c1ec864820bcc4428ea88`; **66 field names**. The published descriptions clearly state a **Settled Area SAUID** polygon and its **centroid** in `E_SauidLat` and `E_SauidLon`. `Et_BldgNum` is an **estimated** stock count, not one verified rooftop per feature.
- [NHSL release v1.0 original asset inventory](https://api.github.com/repos/OpenDRR/national-human-settlement/releases/tags/v1.0) and [pinned GitHub asset metadata gate](../../scripts/nhsl_release_metadata_preflight_v0.py), already merged into main. Specifically `nhsl_physical_exposure_indicators_b.zip` is the archetype/point layer at settlement centroids, `nhsl_physical_exposure_indicators_s.zip` the settled-area polygons, and `nhsl_physical_exposure_attributes_en.xlsx` the 17,888-byte English dictionary.
- [Oasis Open Exposure Data CSV schema](https://github.com/OasisLMF/ODS_OpenExposureData/blob/main/OpenExposureData/OEDInputFields.csv) read on 2026-11-04, blob SHA `8351e6fbb2efa2f6f55d61bab82853b42f6b2a97`. See [OED documentation](https://oasislmf.github.io/oed/index.html). OED target `5.0.0` chosen to match this repository's existing [synthetic OED export](../../research_runners/export_synthetic_oed_v0.py).
- **Version caveat:** the current GitHub `docs/_data/...` YAML is independently visible source documentation, **but has not been byte-compared** with the `v1.0` release English XLSX or the GeoPackage itself. Actual `v1.0` field presence/type/unit and file bytes remain unverified. This staging pass is consequently *source-shaped*, not proven source-release input.

## Exact attribute crosswalk and prohibited semantics

| NHSL source field | Actual NHSL meaning | OED candidate | Safe rule |
| --- | --- | --- | --- |
| `Sauid` | unique **settled area** ID (approximate building footprint area) | `LocNumber` | **Do not map:** a settlement area identifier is not an insured site or risk location. Preserve only as an input grouping identity. |
| `E_SauidLat`, `E_SauidLon` | degrees at SAUID **polygon centroid** | `Latitude`, `Longitude` | Only a **spatial proxy**, do not use as a geocoded building without polygon-scale hazard uncertainty and site-resolution review. |
| `Et_StrValue`, `Et_NStrValue` | estimated structural / nonstructural component replacement cost | none directly | Check values are nonnegative and sum to `Et_BldgValue`; preserve components as source lineage and do not double count. |
| `Et_BldgValue` | total building replacement cost, structural + nonstructural | `BuildingTIV` | **Proxy only:** modeled replacement costs in base-year CAD 2019, *not* insured TIV or cover limit. |
| `Et_ContValue` | modeled contents replacement cost | `ContentsTIV` | **Proxy only:** does not imply insured contents cover. |
| `Et_AssetValue` | total buildings + contents | none directly | Validate `Et_AssetValue = Et_BldgValue + Et_ContValue`, do **not** allocate again to BuildingTIV (would double count). |
| `Et_BldgNum` | estimated building stock count per settled area | `NumberOfBuildings` | Preserve estimate as decimal, not an observed integer/site count; never silently round and claim individual buildings. |
| `Et_BldgArea` | sum of finished **square feet** for estimated building stock | `FloorArea` | Aggregate floor area, not an individual OED location's floor area. Do not infer OED coded `FloorAreaUnit` or convert to square metres without a scoped plan. |
| `E_LandUse`, `Et_ResLD`, `Et_Wood` etc | source land-use mix, occupancy/construction **aggregate estimates** | `OccupancyCode`, `ConstructionCode` | No direct deterministic one-to-one OED code from aggregate distributions. Require a disclosed, validated synthetic allocation model before any code assignment. |
| *(no NHSL source fields)* | no actual contract data | `PortNumber`, `AccNumber`, `LocPerilsCovered`, `OtherTIV`, `BITIV`, `LocCurrency`, financial terms | **Prohibited inference:** these describe actual/simulated insurer contracts. Choosing all-perils `AA1`, an account number, zero cover, or a policy is a separate **hypothetical assumption**, not source data. No OED CSV produced. |

OED v5 property documentation describes `BuildingTIV` and `ContentsTIV` as **insured** values, `NumberOfBuildings` as an integer, and `BITIV` as annualised. The source-mapped NHSL values do not prove these insurance semantics. **Do not use the existing independent synthetic 12-location OED smoke export as a license to convert real NHSL rows into insurance exposure.**

## Executable checks

The preflight accepts **one local JSON object** with source-shaped keys, not a ZIP, GPKG, URL, portfolio, or release dump. It enforces:

1. Named original source fields, safe bounded identifiers and numeric values; Canada-bounded centroid coordinates; source/OED fields kept separate.
2. `Et_StrValue + Et_NStrValue = Et_BldgValue` and `Et_BldgValue + Et_ContValue = Et_AssetValue` (absolute cent-level tolerance CAD 0.02 for source rounding); rejects negative, nonfinite, inconsistent, out-of-range values, zero-buildings with positive assets, missing finished area when stock >0.
3. Aggregate **estimated building count retained as decimal**, even if nonintegral; no forced `NumberOfBuildings=1` or site-level risk ID.
4. A receipt always declares `can_export_oed_loc_or_account=false`, `insurance_coverage_verified=false`, `source_rights_reviewed=false`, `model_input_approved=false`, `admission_status=not_admitted`. No OED loc/acc/RI CSV is created; original source data are never bundled into the test repo.

Run the synthetic tests (no internet, no source bytes):

```bash
python -m unittest discover -s tests -p 'test_nhsl_oed_staging_preflight_v0.py' -v
```

To inspect *one source-shaped row* already held **locally** under authorised use, write it to an external JSON file and call:

```bash
python scripts/nhsl_oed_staging_preflight_v0.py --row-json /tmp/nhsl-single-aggregate-row.json
```

This does **not** establish permission to acquire/provider terms or model-readiness. Never commit actual source rows or output receipts that contain original location-level IDs/values without exact provenance/admission permission.

## Next causal step

Inspect the original **17,888-byte** [NHSL English release dictionary](https://github.com/OpenDRR/national-human-settlement/releases/download/v1.0/nhsl_physical_exposure_attributes_en.xlsx) and a bounded read-only subset of the appropriate v1.0 GPKG **outside Git**. Confirm field names, numeric types, CRS, centroid coordinates, missing/no-data conventions, value/currency base year and a real observation that can pass a source-shape/identity reconciliation. Resolve source rights and the different published NHSL denominators before attempting a geo-aware weighted hazard overlay or **clearly invented** OED synthetic insurance assumptions.

No original NHSL XLSX/GPKG bytes, private insurer portfolio, real OED insured location or licence clearance are committed in this PR.
