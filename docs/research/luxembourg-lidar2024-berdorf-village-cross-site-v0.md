<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Luxembourg LiDAR2024 × GeoBase2026 — first *named* village vs city control site

**Date:** 2026-11-01. **Research-only, no CAT model input admission.**
The large national COG source complete-file SHA-256 values, independent height
and coordinate control, vertical datum and per-object source rights remain unverified.

## Motivation: one city block is not representative

The frozen city study around (6.1319 E, 49.6116 N) was successfully evaluated
in merged #957 and #961. In the same original **100 m × 100 m EPSG:3035**
equal-area area, 104 GeoBase 2026 source building polygons intersected the
exact study polygon, 97 provided source MNS2024 minus MNT2024 object height
**proxies**, and 83 provided interior MNS 5-pixel **surface-steepness proxies**
with 21 exclusions. The 83 observations were neither measured roof pitches
nor a population-wide insured-building sample.

Original government rooftop geometry ACT2023v2 has been compared to these
sources in merged #963. However city-only results do not establish reliability
for smaller village buildings, irregular roofs, vegetation and more spatially
isolated properties.

## Second, preselected public village anchor and source gates

**Berdorf village-centre landmark**: public church St John the Baptist at
**latitude 49.820946° N, longitude 6.348821° E**, as published by
Luxembourg tourism partner Visit Luxembourg through:
<https://www.outdooractive.com/mobile/en/poi/mullerthal-region-luxembourg-s-little-switzerland/the-parish-church-of-berdorf/58578388/>.

We call this a **village-centre study**, not a representative random rural
sample or an independent measured reference roof. The study preselects a fixed
100 m × 100 m square in equal-area EPSG:3035 and converts its four corners
to source native EPSG:2169 under the same unverified, but plausible, stored-XY
hypothesis as the city control. It does not query residences by address.

The existing exact original sources and source read contracts remain:
- ACT Luxembourg GeoBase Buildings October 2026, national original GPKG
  SHA-256 `ec70bd1175b6f67b6dceaf8ab39e0433bc871e1099ff308c3eb8323127aa5676`,
  230,353 source building geometries and native spatial RTree.
- ACT official 2024 MNT (ground) and MNS (surface) 0.5 m COG national
  resources: **original HTTP 4KiB ranges**, declared projection, finite
  100m window, aligned grids; entire ~40GB provider file hashes **not**
  established by a small range read.
- Same maximum **400 original polygon candidates** and **200,000 local
  raster window pixels**, strict unique-source-pixel ownership and
  fail-closed outlier and nodata rules. No free-form arbitrary longitude,
  latitude, source path, address search, buffering or adaptive regional
  enumeration.
- First compute old height proxy categorical distribution and then the
  already reviewed 5-cell interior **local surface-steepness proxy** in
  the **same polygon masks** as merged #961. Neither may be called
  surveyed height, roof pitch, building material or solar panel inventory.

`research_runners/luxembourg_geobase_lidar2024_object_proxy_v0.py` now
accepts two explicit `--site` choices:
`luxembourg-city` (frozen previous baseline) and `berdorf-village`.
Existing callers of `original_window()` retain the city geometry.

The dedicated original-source workflow performs **both study sites
in sequence after one authorized, exactly version-pinned GeoBase download**.
The same public LiDAR URLs are queried by small GDAL HTTP 206 windows.
Original GPKG, individual building identities, coordinates, per-object
heights, gradients or source raster samples are **never** emitted or
saved into the insurance Neon database or GitHub artifacts.

## Actual two-source-region experiment (GitHub Actions 2026-11-01)

**Verified real-source execution:** <https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41317490206>.
All **28 synthetic tests** passed; city reference and Berdorf village fixed
windows completed. Both queried the same already-pinned official
`2026-10-01` GeoBase Buildings original GeoPackage (entire file
SHA-256 `ec70bd1175b6f67b6dceaf8ab39e0433bc871e1099ff308c3eb8323127aa5676`)
and the original official 2024 MNT/MNS half-metre COGs through bounded
read windows only. No full 40GB COG hash was verified, and no original
geometries, raster values or building identifiers were persisted.

| Measured bounded diagnostic | Frozen Luxembourg-city | Fixed Berdorf village |
| --- | ---: | ---: |
| GeoBase RTree envelope candidates | **107** | **18** |
| Candidates outside exact rotated ROI | **3** | **2** |
| Original polygons intersecting 100 m × 100 m ROI | **104** | **16** |
| Valid within-footprint LiDAR height **proxies** | **97** | **16** |
| Valid interior local surface-steepness **proxies** | **83** | **16** |
| Unassigned original raster pixel cells | 20,878 | 27,625 |
| Uniquely assigned original pixel cells | 23,293 | 16,896 |
| Multiply assigned source pixel cells (excluded) | **350** | **0** |
| Steep (≥70°) interior gradient candidate centers excluded | 767 | 182 |
| Valid five-cell gradient centers before steep-screen | 16,390 | 13,407 |

All counts conserve: city 107−3=104 and 83+21=104;
Berdorf 18−2=16, 16+0=16,
and **27,625 + 16,896 + 0 = 44,521** village raster cells.

### Provisional within-footprint height-proxy bands, not actual heights

| MNS2024−MNT2024 per-object median band | City (97 eligible) | Berdorf (16 eligible) |
| --- | ---: | ---: |
| Below 3 m | 0 | **1** |
| 3–<6 m | 2 | **5** |
| 6–<10 m | 5 | **8** |
| 10–<15 m | 28 | **2** |
| 15–<25 m | 62 | **0** |
| ≥25 m | 0 | **0** |

### Provisional median **MNS surface-gradient**, NOT roof-pitch bands

| MNS surface-steepness band | City (83 eligible) | Berdorf (16 eligible) |
| --- | ---: | ---: |
| 0–<5° | 10 | **1** |
| 5–<15° | 14 | **1** |
| 15–<30° | 17 | **4** |
| 30–<50° | 30 | **10** |
| 50–<70° | 12 | **0** |

**Interpretation:** in this one selected town-centre village site, all
16 source polygons have enough valid, unambiguously assigned source
pixels for both proxy calculations; no sample polygon overlap pixels
were shared, compared to 350 excluded overlapping cells in city.
But low counts and purposive selection (including a public church in
Berdorf) prevent any statement that rural Luxembourg buildings are
generally smaller, lower, steeper, less ambiguous or better measured.
The 2024 LiDAR and 2026 building GIS share the government data
family, aren't independent source truth, and may have 2024–2026 change.

**Model admission stays false.** The source MNS gradient is not
validated rooftop tilt, regardless of apparent regional differences.
No building-year, material, occupancy, insured value, roof-facing
azimuth or actual solar equipment has been inferred. Next scientific
step: choose a *predeclared stratified suite of sites* and independent
control roof/vegetation-labelled ground-truth features, not a
post-hoc region selected to optimise apparent data quality.

## Acceptance / interpretation

Require **all** synthetic tests, exact original-source checks, repeated
city baseline 104/97/83 totals, and a nonempty valid village window.
If absent or too dense the village result must **fail closed**, without
moving the research centre to find a favourable sample. Once successful,
record village cohort: actual intersecting source footprints, eligible
height and gradient proxy counts, nonoverlapping pixels and exclusion
statistics alongside the city baseline.

These are **two convenience areas**, not a representative urban/rural
statistical sample. Comparing two sites may surface differences in
coverage and failure modes; it cannot validate nationwide accuracy,
remove tree canopies, supply independent ground truth, prove building
identity or assert source rights. Scientific admission requires
stratified samples and independent roof/terrain controls.
