<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Luxembourg 2024 LiDAR / 2026 GeoBase: 1-metre footprint inset sensitivity

**2026-11-01, research-only.** This does **not** certify building heights or source rights, and does **not** admit CAT exposure.

## Motivation

Merged #957 first verified that 2024 LiDAR surface-minus-terrain values can be measured *within* original 2026 GeoBase building polygons: 107 native RTree rectangle candidates, 3 false-area hits, 104 positive-area study polygons; 97 had usable medians under at least eight unique valid 50cm LiDAR pixels. The aggregates were 2 buildings with research proxy 3–6 m, 5 with 6–10 m, 28 with 10–15 m, 62 with 15–25 m, 0 others. But low-quality polygon boundaries can intersect vegetation, driveways, adjacent roofs and different building vintages. **These are not independently surveyed heights.**

New `research_runners/luxembourg_lidar2024_footprint_inset_sensitivity_v0.py` reads the **same original 2026 GeoBase** GeoPackage and **the same fixed official LiDAR2024 MNT/MNS 0.5-m cloud-optimized raster source bytes** via tiny GDAL HTTPS range windows. It uses the exactly same public **100m × 100m** Luxembourg study area, same whole GeoPackage SHA-256, full original source population, 4KiB range-prefix checks, alignment and conservative masked-pixel quality gates.

The critical change: each original polygon is shrunk inward **1 metre in projected native EPSG:2169**, then its median source MNS–MNT proxy is compared **in process** with the already proven, non-eroded same-polygon median. Pixels assigned to more than one **original non-eroded** polygon are permanently excluded from **both** cohorts. Pixels must remain inside the positive-area original and the exact public study area; erosion must never create a formerly ineligible object. Any polygon with fewer than eight unambiguously assigned valid raster pixels or under 50% coverage is excluded.

Only the following low-dimensional **aggregate** counts leave the process: original/inset eligible totals and losses, invalid/eroded-away polygons, counts crossing proxy *height bands*, absolute median drifts ≤0.5 m, 0.5–1 m, 1–2 m and above 2 m, plus the two cohorts' categorical proxy-bin distributions. Per-building identity, source polygons, actual values, coordinates and raster pixels are never logged, exported or written to Neon. Source files are temporary. All output count conservation and original #957 baseline data are explicitly checked fail-closed before reporting any provider observation.

## Scientific non-independence and limitations

1. Eroding a building footprint is **not** a scientific ground-truth height check and does not remove vegetation in courtyards or tree canopy; it only tests **sensitivity to polygon-edge pixels**. A small building may lose all pixels. We do not describe a decrease in inclusion as increased certainty.
2. 2024 LiDAR and 2026 GeoBase are two years apart and share Luxembourg ACT source-family governance. They do not establish same-date physical building identity. Absolute geodetic axis and vertical datum need independent surveyed controls.
3. We have verified exact entire GeoBase source SHA-256 `ec70bd1175b6f67b6dceaf8ab39e0433bc871e1099ff308c3eb8323127aa5676`; **only first 4KiB** and provider HTTP Range/metadata were independently checked for each approximately 40GB LiDAR MNT/MNS source. Do not imply an entire LiDAR COG SHA-256.
4. Commercial use/redistribution rights, accurate roof height, building occupancy, construction year, replacement cost, insurer TIV, vulnerability and hazard field all remain unadmitted.

## Tests and reproduction

```sh
python -m unittest tests.test_luxembourg_lidar2024_footprint_inset_sensitivity_v0 -v
python -m research_runners.luxembourg_lidar2024_footprint_inset_sensitivity_v0 \
  --geobase-gpkg /private/previously-sha-verified-buildings-20261001.gpkg
```

The specialized workflow `.github/workflows/luxembourg-lidar-footprint-inset-sensitivity.yml` (pinned Rasterio 1.5.0, NumPy 2.3.5, PyProj 3.7.2 and Shapely 2.1.2) repeats synthetic testing and one original-source data pilot. All source bytes, transient ID-bearing GeoJSON and per-building temporary calculated medians are confined to a runner and deleted. No geospatial per-record source data, building heights or CAT model inputs go to Git or the insurance Neon DB.

**Do not report actual 1m-inset measurements until the exact-head original workflow has passed.** Results and workflow run ID can be appended after completion. Next scientific validation should collect independently surveyed building-specific roof controls and compare a stratified test cohort, taking care not to assume external datasets are independent simply because they have distinct product labels.

## Verified original-source 1 m inward-mask result (2026-11-01)

**Authoritative hosted original source workflow:** https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41316435696 . The workflow first passed all **13** synthetic pixel-mask tests, then repeated the exact earlier 2026 GeoBase original GPKG SHA256 and official MNT/MNS 2024 cloud-optimized raster bounded source reads. This run executed the **new inward sensitivity command**, not the old PR #957 baseline command.

| Population/quality | Original-data result |
| --- | ---: |
| Original GeoBase footprints with positive intersection in frozen 100m study | **104** |
| Original PR #957 in-footprint proxies passing unique valid-pixel gate | **97** |
| Still eligible after 1m inward polygon erosion | **73** |
| Previously eligible but excluded after erosion | **24** |
| Original missing/ineligible newly counted after erosion | **0** |
| 1m erosion generated no remaining polygon geometry | **20** of 104 |
| Shared pixels excluded from BOTH baseline and inward cohorts | **350** |
| Of 73 eligible both times, median shift ≤0.5m | **57** |
| Of 73 eligible both times, >0.5m through 1m | **14** |
| Of 73 eligible both times, >1m through 2m | **2** |
| Of 73 eligible both times, >2m | **0** |
| Of 73 eligible both times, remained in same categorical proxy band | **68** |
| Of 73 eligible both times, crossed proxy band boundary | **5** |

Source/pixel conservation: **97 − 24 = 73**, **57+14+2+0 = 73**, **68+5 = 73**. Original source masks have 350 multiply assigned pixels that remain excluded in both cohorts; never promote overlap pixels based on erosion alone.

The **73** inward-cohort source MNS-minus-MNT median proxy **categories**, for scientific diagnostic only, are: **3** (3–6m), **3** (6–10m), **17** (10–15m), **50** (15–25m), **0** outside those bands. The *comparison-conditioned 68/73 stable proxy bands* do not establish actual independent roof height, measurement bias, construction vintage or building-to-building identity; the 24 lost sample members could systematically differ in size and building type (selection bias). Vegetation/cloud surface, MNT ambiguity, horizontal and vertical CRS control, source rights and 2024/2026 age mismatch remain unverified.

**Scientific decision:** This demonstrates *limited edge sensitivity in the retained cohort* but **not** validated building heights. A future model should represent 24 dropped buildings as missing/low-confidence instead of estimating their values from the retained 73. No insurer insured values, countrywide roof height product, original source rows or CAT model input were admitted.
