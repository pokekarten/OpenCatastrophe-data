<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# ACT2023 roof / GeoBase2026 footprint: exactly paired LiDAR2024 pixel-mask research

**Research-only; strictly no physical-building identity certificate or CAT model input admission.**

## Problem solved

Our official original-source studies showed **54 ACT2023 rooftop polygons** versus
**104 GeoBase2026 building polygons** in one exact 100×100m square near the public
Luxembourg-city research center 6.1319E, 49.6116N. The same original 2024
LiDAR2024 terrain/surface COG window contained 44,521 jointly valid 0.5m pixels.

Prior unpaired object cohorts yielded 52 valid ACT rooftop median proxies (#963)
and 97 GeoBase footprint median proxies (#957). Those **different polygons and
counts cannot be compared as matched physical buildings**. Our exact same-window
geometry comparison (#948) had 12 high-IoU ACT2023–GeoBase2026 candidate pairs
among larger split/merge ambiguities, none independently certified.

This experiment tests only the strictly uncontested subset and quantifies
how much the **two alternative source polygon masks change the median
surface-minus-terrain proxy from the very same source raster pixel grid**.

## Exact original data and immutable source pins

- ACT2023v2 rooftop 2D GeoPackage original SHA256
  `9765b04eaeb9332aa606b8dca44031116588e285553aab061d61037938a002bf`,
  population **238,189** and original ZIP SHA256
  `a271b1cbcc22ded018f9bab0c150e9f33efa6cb7ebca8cf4dc4bdb1f5d84859a`.
- GeoBase2026 Buildings original GPKG SHA256
  `ec70bd1175b6f67b6dceaf8ab39e0433bc871e1099ff308c3eb8323127aa5676`,
  population **230,353**, original ZIP SHA256
  `6630f217b39edde5f20f1078bef8a3d6eb4a09337af48394975f45f208bcfed3`.
- Official LiDAR2024 MNT terrain and MNS surface COGs use fixed official
  `download.data.public.lu` HTTPS links and successful first-4096-byte
  HTTP206 BigTIFF header receipts from #945. Their full 40GB asset
  SHA256s are **not verified**. Rasterio accesses only the fixed source
  100m native study bounding box under hard pixel count and cache limits.
- All original GeoPackages are separately verified to exact full SHA256,
  each source population and EPSG2169 polygon feature schema before sampling.

## Algorithm and fail-closed gates

`research_runners/luxembourg_act_geobase_lidar2024_paired_pixel_cohort_v0.py`

1. Reuses the exact equal-area EPSG3035 **100m square** from #948/#957/#963.
   Select at most 400 original roof and 400 original building polygons, and
   remove RTree bounding rectangle hits with no actual positive area in the
   rotated square. No alternative/random/expanded study window.
2. Compute all cross-source polygon IoUs on the **complete, uncut
   original polygons**, before any clipping to the 100m study square.
   Otherwise two large neighboring polygons can appear artificially identical
   at the region edge. Admit only full-source IoU ≥0.60 with **no competing
   alternate polygon from either source** at full-source IoU ≥0.20. This yields
   at most one-to-one *spatial candidates*; even complete-source high IoU
   does not certify the same physical building. Competing source objects are
   detected when intersection is >=20% of **either** object's original
   area, consistent with `scripts/building_footprint_overlap_v0.py`.
   Thus a contained 2m roof fragment can veto a high-IoU building pair
   despite very low fragment-vs-whole IoU. Clip only the **raster masks**
   after that independent candidate gate.
3. Read exactly two matching MNT/MNS source raster windows, maximum 200k
   original pixels per raster and matching native source transform.
   Reject invalid/nodata/outlier source elevation pairs.
4. Construct separate source polygon raster ownership masks. A pixel is
   usable only if it is (i) valid MNT/MNS and (ii) assigned to exactly
   **one roof polygon and one GeoBase building polygon** in their respective
   source data. A candidate pair requires ≥8 pixels for each source mask
   and ≥8 pixels **shared by both masks**. No shared-with-competitor pixel is
   counted as evidence.
5. Compute within-source median surface-minus-terrain proxies only in
   ephemeral memory for each admitted pair. Output only aggregated absolute
   pairwise median-difference bins: below 0.5m, 0.5–2m, 2–5m and ≥5m;
   count qualifying and excluded pairs, aggregate shared-pixel count and
   quality flags. **Never print or store** original IDs, building locations,
   geometries, individual pair medians, pair indices or raster arrays.
6. If no uncontested spatial pair or no usable shared-pixel pair exists,
   **abort**, not silently claim an unsuccessful or synthetic source validation.

The exact-source GitHub Actions workflow is isolated from other PR work.
It retrieves just two exact official original building ZIPs and two
100m official 2024 COG windows. Original source files and intermediary
GeoJSON are deleted with temporary runner storage.

## Scientific interpretation

- A small absolute median-proxy difference means two masks sample similar
  **observed source 2024 DSM−DTM**, **not** that ACT2023 and GeoBase2026
  identify the same building, that either predicts real building height,
  or that one inventory is more correct.
- ACT2023 roof footprints and GeoBase2026 generalized building polygons are
  different segmentation products from a **related ACT source family**,
  with different observation dates. Their IoU matches are *not independent
  scientific truth*. Neither has original field axis order or vertical
  datum independently ground-controlled yet.
- DSM includes vegetation, pole and roof equipment elevation and potentially
  ground mask artifacts. An inner roof-only LiDAR point classification or
  manual survey holdout is needed before genuine building height validation.
- There is no property insured value, insurer building identity, occupancy,
  vulnerability, construction year, replacement cost or CAT model admission.
  All source rights and downstream data licensing remain separate proof gates.

## Reproduction

~~~bash
python -m pip install rasterio==1.5.0 numpy==2.3.5 pyproj==3.7.2 shapely==2.1.2
python -m unittest tests.test_luxembourg_act_geobase_lidar2024_paired_pixel_cohort_v0 -v
python -m research_runners.luxembourg_act_geobase_lidar2024_paired_pixel_cohort_v0 \
  --act2023-gpkg /private/official/ACT2023v2.gpkg \
  --geobase2026-gpkg /private/official/GeoBase2026.gpkg
~~~

**Actual original results must be recorded after the original source workflow
succeeds at the exact final PR head**, not asserted from the prior 12 spatial
candidates. CI/rights checks must pass before merge.

## Executed original-source result: strict 12 matched spatial candidates, 2026-11-01

**Real source SHA-pinned provider workflow run:** [41319568325](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41319568325). All **13 synthetic** original geometry/quality/anti-leak tests passed, followed by actual downloads and whole-original SHA verification of **both** official ACT2023 roof and GeoBase2026 building GeoPackages. The official 2024 MNT and MNS raster URLs passed bounded HTTP206 headers and were read only in the fixed 100m research window. No full 40GB COG, original source GPKG, output per-object value or actual raw LiDAR pixels were saved to the repo, artifacts or Neon.

The first trial matching after ROI cropping had a **false-positive IoU inflation risk**; this was explicitly corrected before the accepted result. A later intermediate full-source candidate pass used only IoU to detect competitors, missing contained 1:n roof components. The final method matches the repository canonical overlap rule: full **original** polygon IoU >=0.60 and competitor if >=20% of **either** original source object's area. The actual final run observed:

| Actual evidence from official source files / 100m study | Value |
| --- | ---: |
| Exact-roi ACT2023 roof polygons | **54** (55 RTree candidates, 1 excluded) |
| Exact-roi GeoBase2026 building polygons | **104** (107 RTree candidates, 3 excluded) |
| Valid 0.5m MNT/MNS source raster cells in native bounding rectangle | **44,521** |
| Full-original-source polygon pairs with IoU >=0.60 | **32** |
| High-IoU pairs rejected due to source split/merge competitors | **20** |
| **Uncontested unique 1:1 spatial candidate pairs** | **12** |
| Pairs with >=8 valid unique source-mask and >=8 **shared** source pixels | **12** |
| Pairs rejected for insufficient unique/shared pixels | **0** |
| Pairs rejected due to negative source median | **0** |
| Common source raster pixels uniquely attributed to both original polygons | **3,977** |
| Pixels uniquely attributed on accepted ACT rooftop masks, summed | **4,325** |
| Pixels uniquely attributed on accepted GeoBase2026 masks, summed | **4,108** |

For the **12 candidate pairs**, the difference between each ACT rooftop-mask median DSM–DTM and its corresponding GeoBase2026 building-footprint-mask median DSM–DTM was:

| Absolute difference between paired median **proxies** | Number of spatial candidates |
| --- | ---: |
| Below **0.5m** | **12** |
| 0.5–below 2m | **0** |
| 2–below 5m | **0** |
| 5m or more | **0** |

**Interpretation limited to this cohort:** On 12 strict source-geometric candidate pairs in one central urban 100m sample, the *median* 2024 DSM–DTM proxy is largely insensitive (absolute delta under 0.5m) to choice of ACT2023 vs GeoBase2026 polygon. The median for each source still uses its **own** uniquely owned raster-mask pixels, not literally an identical pixel subset; the 3,977 common raster pixels measure their overlap. No exact per-object match IDs or medians were saved, and no signed/independent surveyed building identities, representativeness, cross-vintage physical ground truth, complete source COG hashes, vegetation removal or commercial-source admission are asserted.

**Scientific next priority:** repeat the same strict paired method across stratified city/village sites and test boundary insets/point cloud class 2 vs class 6 or independent height controls, before extrapolating to insurance exposure. Twelve clean spatial pairs do not validate the 42 ambiguous ACT roofs or 92 unpaired GeoBase objects in this 100m source cohort.
