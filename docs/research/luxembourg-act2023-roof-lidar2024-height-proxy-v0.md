<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# ACT2023 roof extent × LiDAR2024 MNT/MNS: fixed Luxembourg 100m pilot

**Research only.** This experiment measures a *roof-geometry-dependent proxy*, not actual surveyed per-building height or an insurance model input. Compare it with the merged #957 GeoBase2026 mask **only after matching study windows and geometric semantics**.

## Why this is the next necessary source comparison

The original GeoBase2026/LiDAR2024 pilot (#957) measured **104 actual-area 2026 building polygons** and **97 valid surface-minus-terrain median proxies** in the same 100×100m city-center square, based on 44,521 original 50cm coincident pixels. Its height-proxy median bins were 0 below 3m, 2 in 3–6m, 5 in 6–10m, 28 in 10–15m, 62 in 15–25m and 0 at/above 25m. This cannot be called building height due to roof/ground confusion, vegetation, source vintages, official LUREF axis field control and vertical datum uncertainty.

The 2023 ACT rooftop-extent original is a **different source geometry product**, although from the same ACT producer family:

- Official ACT2023v2 original resource: https://data.public.lu/en/datasets/r/d62942ec-0dc8-40e2-9fa4-27841e6e1ac1
- ZIP original SHA256 `a271b1cbcc22ded018f9bab0c150e9f33efa6cb7ebca8cf4dc4bdb1f5d84859a`, GeoPackage original SHA256 `9765b04eaeb9332aa606b8dca44031116588e285553aab061d61037938a002bf`, 238,189 original `ACT2023v2_Buildings3d_Footprints` geometries
- MNT 2024 40,131,787,860 HTTP source declared bytes; MNS 2024 42,849,815,758 bytes, exact fixed provider HTTPS COG paths and independently checked HTTP206 BigTIFF prefix from merged #945
- CRS LUREF/EPSG2169 native-as-stored horizontal axis is a **research hypothesis**, not independently field-controlled.

The original same-window #948 three pair experiment measured **55 ACT2023 RTree roof polygons, 107 GeoBase2026 RTree building polygons, 11 EUBUCCO v0.2 polygons** in the 100m research square. The 55 and 107 are not a shared physical-building population; pairwise IoU can be ambiguous/one-to-many.

## Implemented

`research_runners/luxembourg_act2023_roof_lidar2024_proxy_v0.py` reuses the previously verified original ACT GeoPackage and current `#957` two-pass raster-mask code, rather than inventing a new height or geometric assignment method.

1. Accept only an original ACT2023 GPKG pinned to its entire source SHA256, verified original 238,189 rows, EPSG2169 registered polygon layer, original `buildingid`, and source RTree.
2. Select at most 400 roof polygons from the exact **100×100m equal-area** city-center window in native EPSG2169, then remove RTree bbox-only polygons that do not intersect the true rotated study window.
3. Read only official 2024 MNT/MNS COG HTTP ranges under a **200,000 raster-pixel** ceiling with Rasterio 1.5.0, PyProj 3.7.2, NumPy 2.3.5 and Shapely 2.1.2; require matching pixel grids and preverified official 4KiB HTTP206 prefix receipts.
4. Reuse `aggregate` from #957 to clip original roof polygons to the study, **exclude all pixels in overlapping polygons**, demand at least eight unique valid pixels and 50% polygon-unique raster coverage, reject negative median proxy as an observation-quality issue.
5. Report only original roof count, false RTree candidates, aggregate bins of the median *within-roof MNS minus MNT* proxy, masked-cell occupancy and quality exclusions. No original source building IDs, geometries, pixel values or per-roof medians are printed or persisted. Original ZIP/GPKG exist only in the temporary GitHub Actions runner.

Dedicated source job plus eight synthetic regression tests challenge true intersections, shared-mask ambiguity, nodata and negative differences. Repository CI remains mandatory for merge.

## Interpretation before use

**Do not subtract the ACT2023 55-roof count from the GeoBase2026 104-building count** or assign different height distributions to a newer building stock without an actual reviewed source-specific crosswalk. These are two differently segmented government datasets, not independent observations. Differences between the two aggregate cohorts may be entirely geometric sampling effects or measurement-year effects. Both proxy distributions include vegetation/other surfaces. The 2023 ACT roof extents are 2D footprints of roof outlines, not direct height surveys.

For scientific model validation, next stratify a bounded common-pixel cohort with adjudicated high-confidence 1:1 geometry and independently field-surveyed vertical controls. Only then compare methods quantitatively. Individual insurers, replacement cost, floor count and all CAT model-input admission remain absent.

**No original source whole COG SHA verified, no feature or raw source redistribution rights conferred, no Neon write, no model input admission.**
