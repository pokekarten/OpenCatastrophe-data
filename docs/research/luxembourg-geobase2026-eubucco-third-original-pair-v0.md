<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Luxembourg third source pair: original ACT GeoBase2026 vs EUBUCCO v0.2

Date 2026-11-01. Research only; no licensed CAT exposure, verified physical-building mapping, historical building stock change or source-independent model validation.

## Missing evidence before this work

The two first original-polygon pairs have been measured via pinned original publisher files:

| Compared sources | Fixed original research area | Observed source polygons | Unique IoU≥0.60 candidates | Ambiguous first-source polygons |
|---|---|---:|---:|---:|
| ACT2023 rooftop vs EUBUCCO v0.2 | 250×250 m central Luxembourg | 149 vs 45 | 9 | 136 |
| ACT2023 rooftop vs ACT GeoBase2026 | 100×100 m central Luxembourg | 55 vs 107 | 12 | 39 |

**The two previous rows have different study-area sizes and are not directly comparable as statistics.** This third pair uses the same frozen **100×100 m central Luxembourg city centre** study area as the ACT2023/GeoBase2026 pair, with centre 6.1319°E, 49.6116°N and EPSG:3035 half-width 50 metres. This enables an additional same-window diagnostic, NOT a three-way precision/recall or shared physical-building identity proof. In particular, EUBUCCO government-labelled geometry is upstream ACT2013 LoD1, so EUBUCCO vs ACT GeoBase2026 can be **related through ACT**; it is not independent evidence.

## Original exact-source immutable receipts

- Official GeoBase 2026-10-01 Buildings original ZIP: https://download.data.public.lu/resources/bd-l-geobase/20261001-010523/buildings-20261001.zip
  - ZIP SHA-256 `6630f217b39edde5f20f1078bef8a3d6eb4a09337af48394975f45f208bcfed3`, original GPKG SHA-256 `ec70bd1175b6f67b6dceaf8ab39e0433bc871e1099ff308c3eb8323127aa5676`.
  - 230,353 original records, `Buildings_BU_Building`, original `BU_BuildingID`, declared EPSG:2169.
- EUBUCCO v0.2 NUTS2 LU00 original: https://s3.eubucco.com/eubucco/v0.2/buildings/parquet/nuts_id=LU00/LU00.parquet
  - Parquet SHA-256 `d1e554de9db0b1f747575426ebb950ef96bb8b2956657554b5ff2998a91abe8c`; 186,171 original building rows, EPSG:3035 as documented by producer.
  - Upstream official source metadata (PR #920) explicitly identifies `gov-luxembourg` as ACT / Bâtiments 3D LoD1 2013. Other EUBUCCO geometry includes OSM and Microsoft with separate lineage; not all are equal measurement types.

## Implemented constrained executable check

New research runner `research_runners/luxembourg_geobase2026_eubucco_bounded_pair_v0.py` verifies complete original source hashes and populations, requires original GeoBase RTree and NUTS3 LU000 partition identity, samples at most **400** source polygons per side, transforms the native EPSG:2169 GeoBase bbox and EPSG:3035 EUBUCCO WKB in a temporary workspace, and calls the existing capped STRtree polygon matcher. It exposes only source-level polygon counts and aggregate geometric candidate IoU classifications. Checks that candidate groups conserve the original source sample; failure blocks output.

The separate workflow fetches only these two exact HTTPS original objects, first runs existing official metadata/CRC checks and the prior SHA-256 checks, extracts a verified original GeoPackage into temporary runner storage, executes synthetic regression tests with PyProj 3.7.2/Shapely 2.1.2/PyArrow 20.0.0, then runs a **single original source window**. It never uploads original files, geometry extracts, identifiers, candidate pairs or user/insurer information, and never writes to Neon. If source bytes change, RTree is missing, original source region has no rows or the 400-side cap is exceeded, fail closed; no fallback or silent sample truncation.

The original source run is **not** yet asserted successful until hosted exact-head CI demonstrates it. The as-stored EPSG:2169 coordinate order was only screened via source envelope, not surveyed with an independent control point. The 2013, 2023 and 2026 observation vintages, semantics (roof/LoD1/GeoBase objects), tile/geometry confidence and source licences remain separate. IoU≥0.60 is a research threshold, not science-calibrated identification and must never become `exposure.exposure_unit` or insured TIV.

## Next before insurance model admission

Manually adjudicate preselected, spatially stratified urban and rural examples; audit ID-vintage and source-specific rights; calibrate false-positive one-to-one / split / merge rates and per-source uncertainty; obtain independent dates/occupancy/use and replacement cost evidence; establish exact exposure portfolio and peril hazard event uncertainty.

## Verified real original-source result (2026-11-01)

**GitHub Actions original-source run:** https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41312729390

The run passed five optional spatial/Parquet synthetic tests and independently re-downloaded the frozen public ACT GeoBase2026 Buildings ZIP and EUBUCCO LU00 Parquet. Their extracted exact original file SHA-256 receipts matched the predeclared previous hashes, and the same spatial filter was executed on both. The original 100m×100m fixed area gave:

| Aggregate original source diagnostic | Measured |
| --- | ---: |
| GeoBase2026 building polygons in fixed window | **107** |
| EUBUCCO v0.2 polygons in fixed window | **11** |
| Spatial bounding-box candidate pairs examined | **139** |
| Unique GeoBase candidate with IoU≥0.60 | **1** |
| GeoBase polygon classifications with ambiguous candidate relations | **104** |
| Weak unique GeoBase polygons below IoU 0.60 | **0** |
| GeoBase polygons without substantial overlap | **2** |
| Median candidate IoU among the unique high-IoU candidates | **0.642198** |

**Conservation:** 1 + 104 + 0 + 2 = 107 original GeoBase-side polygons. These counts are consistent with the small local overlap; they are not true-positive/false-positive rates, and the 11 EUBUCCO records are not a census of all 107 modern GeoBase objects. The 2013 ACT LoD1 / EUBUCCO, 2023 ACT roof and 2026 ACT GeoBase use different segmentation and survey semantics. A one-pair high-IoU candidate is NOT a certified stable physical identity or independent source control.

For a same-window comparison, the separately completed ACT2023 roof vs GeoBase2026 audit found **55** ACT roof shapes and **107** GeoBase2026 shapes, **12** unique high-IoU candidates, **39** ambiguous and **4** below threshold. The original ACT2023 roof vs EUBUCCO v0.2 pilot used a *larger 250m square* and cannot be pooled without a new same-window rerun.

No provider original bytes, individual IDs, coordinates, match pairs, coverage estimates, estimated insurance values, 2013/2026 demolition claims or third-party dataset licences were admitted to the production insurance database. The next meaningful evidence is an independently sourced manually adjudicated control sample and a consistent three-way same-window evaluation with explicit 1:n/n:1 policies.
