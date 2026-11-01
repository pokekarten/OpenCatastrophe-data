<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Research-only Luxembourg 2026 building polygons × LiDAR2024 MNS/MNT

Date: 2026-11-01. **Not** a certified building height product, a validated ground-truth dataset or admitted insurance exposure.

## Why this stage matters

Prior original-source research:
- GeoBase2026 Buildings original GPKG (SHA256 `ec70bd1175b6f67b6dceaf8ab39e0433bc871e1099ff308c3eb8323127aa5676`): 230,353 records with unique `BU_BuildingID` and 0 null geometries (#926/#933).
- LiDAR2024 official MNT (terrain) and MNS (surface) national 0.5-m COGs can be read with small HTTPS byte-range requests (#945/#952/#950). Prior 250m rectangle analysis reported 277,202 joint-valid original pixels, median **9.59 m** and p90 **19.57 m** MNS minus MNT, including trees/roads and other non-buildings. The full 40GB sources **have not** been cryptographically authenticated.
- Existing ACT2023 / GeoBase2026 / EUBUCCO same-window geometry research (#948) fixed an actual 100m square around public centre 6.1319E,49.6116N. All such matched objects are **spatial candidates**, not certified identities.
- Solar cadastre 2025 original building SHP has no facet slope/aspect/3D-area fields (#951). Public roof-facet WMS `GetCapabilities` returned **HTTP 401** (#954). Do not bypass access controls or equate PV potential with installed insured assets.

This PR verifies whether the **already accessible** 2024 MNS and MNT raster pixels can be spatially restricted to the **original 2026 GeoBase building shapes** in the exact same 100m square, including overlap-safe in-memory raster masks. It is a *proxy distribution* experiment, not a new public per-building height dataset.

## New strict bounded procedure

`research_runners/luxembourg_geobase_lidar2024_object_proxy_v0.py`:

1. Revalidates original 2026 GeoBase entire original GPKG SHA-256 and 230,353-source feature population, requires original EPSG:2169 registered polygon layer and RTree, and samples ≤400 original footprints in a **fixed 100m × 100m** equal-area study area.
2. Requires both reviewed 2024 LiDAR original-COG **first 4KiB HTTP 206 header receipts**, correct projected CRS equivalent to EPSG:2169 (with stored-X/Y field order still *unverified by independent geodetic control*), one band and 0.5-m north-up pixel grid.
3. Reads only ≤200,000 MNT and MNS pixels per source window via bounded GDAL `/vsicurl/` range reads, validates identical grid and actual finite/in-range elevation values; refuses ≥200m pixel-value disagreements, mismatched grids, insufficient joint data, missing source metadata or out-of-budget region.
4. Rasterizes original source polygons **twice**, after clipping to the exact public 100m square: first to count pixels covered by 0, 1, or 2+ footprints, then to calculate the within-footprint MNS–MNT median using **only cells assigned to precisely one original footprint**. This removes pixels shared by ambiguous footprint fragments.
5. Refuses polygon-level proxies with fewer than **eight unambiguously assigned valid pixels** or with less than 50% valid unique raster pixels. Counts negative medians as exclusions, not zero heights. Publishes solely coarse count bins: below 3m, 3–6m, 6–10m, 10–15m, 15–25m and ≥25m, plus no-unique and insufficient-coverage exclusions. All counts must conserve original in-sample polygons.

**No** original GeoBase building IDs, GeoJSON, polygons, coordinates, per-object heights, source raster elevation grids, full COG or original ZIP are saved to GitHub artifacts, output or Neon. The temporary sample is local to the runner and removed on exit. The existing independent CAT-only/Pokémon data separation is preserved.

## Scientific and licence cautions

- MNS includes trees, vegetation, facades, roofs and other surfaces; MNT may vary under buildings. The within-building polygon median is **only a vegetation-contaminated proxy**, not the vertical height of a building. A footprint may contain courtyards or an incorrect polygon. Height does not imply number of storeys, occupancy, replacement value, or insured sum.
- **2024 LiDAR** and **2026 GeoBase** are different vintages, although from related Luxembourg government data families; official source rights for commercial insurance use need review. Neither this procedure nor the 2025 solar cadastre proves independent scientific ground truth or cross-vintage asset identity.
- The COG source complete 40GB file SHA256 is **not** verified. A 4KiB official prefix, internal metadata and HTTP range support only evidence the served resource and declared structure, not full-file provenance integrity.
- CRS as-stored orientation still requires an external ground-control check. Vertical datum, classification/vegetation removal, independent survey data and roof-specific measurements remain open.
- No real CAT hazard, vulnerability, insurer portfolio, or economic replacement value is inferred. Output flags explicitly mark `building_heights_certified=false`, `original_source_rights_admitted=false` and `cat_model_input_admitted=false`.

## Reproduction

Run synthetic QA with pinned Rasterio 1.5.0, NumPy 2.3.5, PyProj 3.7.2, Shapely 2.1.2:

```bash
python -m unittest tests.test_luxembourg_geobase_lidar2024_object_proxy_v0 -v
python -m research_runners.luxembourg_geobase_lidar2024_object_proxy_v0 \
  --geobase-gpkg /secure/path/to/official-sha256-verified-buildings-20261001.gpkg
```

Dedicated workflow `.github/workflows/luxembourg-geobase-lidar-object-proxy.yml` downloads **only the previously pinned official GeoBase ZIP**, extracts an exact previously SHA-verified GeoPackage and ranges the two official fixed COG URLs. Per-object results are not logged. Before a hosted exact-head original-source workflow succeeds, **no actual object-level proxy distribution is claimed**.

The follow-up after this stage is point-cloud semantic classification / independently surveyed roof and ground controls and manually adjudicated building cohort; these must be validated before an insurance-specific hazard/vulnerability input can be created.

## Actual pinned-source spatial execution (2026-11-01)

**Successful exact-head original-source job:** https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41315305678 . The original GeoBase2026 ZIP/GPKG matched its previously observed publisher MD5 and exact original GPKG SHA-256, while both official MNT/MNS national COGs passed the reviewed 4KiB HTTP206 source-prefix checks and read **only the fixed 100m native-envelope raster window**. All twelve synthetic tests passed before the original-source read.

| Observed original research metric | Count |
| --- | ---: |
| Original GeoBase RTree bounding-rectangle candidates | **107** |
| Of these, excluded after exact rotated 100m ROI polygon check | **3** |
| Distinct source footprint polygons with positive-area intersection | **104** |
| Footprint polygons with eligible ≥8 unique, valid raster pixels | **97** |
| Footprint polygons with insufficient raster pixels/coverage | **4** |
| Footprint polygons with no uniquely assigned raster pixel | **3** |
| Valid MNT and MNS pixels in 100m raster bounding envelope | **44,521** |
| Raster pixels covered by exactly one clipped polygon | **23,293** |
| Raster pixels covered by multiple polygons, NOT assigned as building proxy | **350** |
| Raster pixels outside any sampled footprint | **20,878** |

Two independent sanity checks hold: **107−3=104** exact-area footprints, **97+4+3=104** sample polygons and **23,293+350+20,878=44,521** raster pixels. The reported occupancy is an **in-memory temporary raster proxy** only; pixel arrays, individual footprint IDs, actual height medians, geometries and source raster bytes were not exported.

The 97 potentially useful **within-footprint MNS–MNT *proxy median*** aggregates were:

| Source proxy median band | Number of footprint polygons |
| --- | ---: |
| Below 3m | 0 |
| 3m to below 6m | 2 |
| 6m to below 10m | 5 |
| 10m to below 15m | 28 |
| 15m to below 25m | 62 |
| 25m and above | 0 |
| **Total** | **97** |

These bins are **not insured building-height distributions**: there is no canopy removal, object-level independent height or storey verification, survey-age harmonisation, original full-COG SHA, certified as-stored horizontal-axis and vertical-datum control, source commercial-rights admission, vulnerability calibration or model/portfolio admission.

The 3 RTree rectangle false positives initially caused a correct fail-closed run; the reader now excludes them **before** polygon-median calculation, explicitly logs the excluded count and continues only on positive-area intersections with the exact fixed rotated area. The original-source rerun then passed.

**Scientifically next:** obtain bounded LiDAR point-cloud ground-vs-building classification and/or independently verified roof heights for a stratified urban/rural control sample; inspect actual source access rights. Only then evaluate footprint-specific height-proxy bias and whether to introduce optional weighted building attributes into a **research** table.
