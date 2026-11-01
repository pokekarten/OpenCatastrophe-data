<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Luxembourg ACT LiDAR2024: fixed 250m actual COG surface minus terrain probe

**Scientific status:** original-data bounded research raster sample only.
It does not determine building-specific heights, insurees, property values,
source independence, verified datum or acceptable CAT model input.

## Grounded source / why no 1.7 GB ZIP

Official publisher: https://data.public.lu/en/datasets/lidar-2024-releve-3d-du-territoire-luxembourgeois/

Merged PR #941 proved **two LiDAR2024 index polygons** actually overlap the
same fixed 250m × 250m Luxembourg-city ACT2023/EUBUCCO pilot; their union
covers the pilot. Merged PR #940 proved both point to **one 1.70 GB
provider grouped ZIP**, too large for the bounded sample. Merged #945
verified the publisher's original 2024 MNT/MNS **BigTIFF** URLs return HTTP
**206 Partial Content** and exactly 4096 requested bytes. Reported totals:

- Original MNT terrain BigTIFF: **40,131,787,860 bytes** (no full-file SHA).
- Original MNS surface BigTIFF: **42,849,815,758 bytes** (no full-file SHA).
- Both first 4096-byte fragment SHA256:
  `c2bceb795e786013f8d235e3aa3fe5707e75faf6a6be39b2a3d7da67113161c8`.
  This is only a **fragment** hash; same TIFF header digest is not same
  source dataset contents.

Exact fixed original COG URLs are only the two official original addresses
in `research_runners/luxembourg_lidar2024_cog_range_capability_v0.py`,
not user-supplied or feature-sourced URLs.

## Executable bounded experiment

`research_runners/luxembourg_lidar2024_bounded_cog_window_v0.py`
runs the prior small range/header checks before starting any raster IO,
then uses pinned Rasterio 1.5.0, NumPy 2.3.5 and PyProj 3.7.2 with
GDAL's `/vsicurl/` remote COG window access. It never creates
a local 40GB original-file copy or downloads the 1.7GB LAZ ZIP.

- Same previously reviewed **250×250m equal-area EPSG3035** study polygon,
  public city-center reference 6.1319°E / 49.6116°N. Its conservative
  **native EPSG2169 bounding rectangle**, not a national raster, is sampled.
- Require original raster EPSG2169, north-up, **0.5m pixels**, single band,
  containing the study rectangle.
- Fail on any raster band/window larger than 1024×1024 or **1,000,000**
  pixels, on mismatched MNT/MNS pixel grids, on no-data data coverage below
  half, or implausible physical differences.
- Read only a single band from each original URL and report **aggregate
  valid pixel counts, coverage, median/p90/max DSM–DTM differences, and
  surface-elevation threshold fraction**, not any source raster pixels,
  coordinates, building IDs, addresses, point-cloud classifications or
  personally identifiable information.
- GDAL configured to prevent directory enumeration or unlimited local
  caches and use bounded HTTP range reads only. A network error, weak
  COG layout or incompatible grid is a **failure**, not permission to
  acquire a full national file.

Reproduction (if provider and dependencies available):

~~~bash
python -m pip install rasterio==1.5.0 numpy==2.3.5 pyproj==3.7.2
python -m unittest tests.test_luxembourg_lidar2024_bounded_cog_window_v0 -v
python -m research_runners.luxembourg_lidar2024_bounded_cog_window_v0 --fixed-luxembourg-window
~~~

## Scientifically essential caveats

DSM minus DTM shows the height of **all above-ground features**, including
trees, poles, rooftop equipment and artifacts. The native rectangular
bounding window may include land outside the original 250m square.
Only a human-reviewed and geometry-masked subset restricted to source-
compatible roofs, with raw-class LiDAR support and vertical datum QA,
can support **real building heights**. A 2024 surface is also not
a certified independent ground truth for ACT2023v2 roof mapping until
overlap in producing imagery and LiDAR processing is assessed.

EUBUCCO v0.2 includes **estimated** heights and mixed government/OSM/MSFT
source footprints. Keep its `height_source` model estimates separate
from directly observed LiDAR heights. No insurer TIV, physical repair cost,
policy or claim is derived from this 250m proxy.

The hosted exact-head workflow must independently pass all synthetic
tests and the real original-source small-window execution before merging.
No source data admitted.

## Actually executed official-source window (2026-11-01)

Original real-source GitHub Actions run
[41314112544](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41314112544)
**passed**, including all **11 synthetic regression tests** and actual
partial Rasterio `/vsicurl/` windows from the two provider-hosted
MNT and MNS BigTIFF datasets. No whole source object, LAZ, per-building
geometry, pixel arrays, building identifiers or private location rows
were uploaded/persisted.

The official source COGs use an older **WKT1 LUREF/Luxembourg TM**
coordinate definition without recognized outer EPSG authority code.
Rasterio therefore returned `to_epsg()=None`, despite **matching the
official EPSG:2169 geodetic datum, ellipsoid, prime meridian, Transverse
Mercator method, all projection operation parameters and unit/axis
families** under a strict scientific parameter comparison. The
conversion was **NOT** silently overridden or checked only by name.
Actual source axis order and survey vertical datum require independent
field-control confirmation. Both original raster grids are native
north-up, 0.5 m, one band, **114,617 × 163,687 pixels** with declared
nodata, and the two sampled grids align.

| Genuine provider sample statistic | Actual result |
| --- | ---: |
| Original MNT HTTP total source bytes (no full SHA) | 40,131,787,860 |
| Original MNS HTTP total source bytes (no full SHA) | 42,849,815,758 |
| Original partial-window valid coincident cells | **277,202** |
| Joint valid pixel fraction | **100%** |
| Surface minus terrain minimum | **0.00 m** |
| Surface minus terrain median | **9.59 m** |
| Surface minus terrain p90 | **19.57 m** |
| Surface minus terrain maximum | **34.09 m** |
| Valid sampled pixels >3 m above terrain | **58.4375%** |

**Critical interpretation:** this is a source-level spatial elevation
proxy on the **native bounding rectangle around the same 250m equal-area
study polygon**, NOT a polygon-clipped sample, not an average building
height, not independent building-height calibration, and not an insured
CAT exposure. In this dense urban/vegetated study region, the 9.59 m
median and 19.57 m p90 include tree canopies, street furniture and any
other objects above bare earth. No independent EUBUCCO height comparison
was made in this stage. This is **technical/physical evidence that a
small raster window from official 40 GB COGs can be read efficiently
using true HTTP ranges**, not a substitute for source admission.

Next source-science step: combine approved roof footprints and
per-building `height_source` provenance with a geometric
roof-only mask, preserve one-to-many roof segmentation and observed
pixels, distinguish LiDAR classes 2/6 from 3–5, and manually validate
raster vertical datum/CRS and at least a bounded holdout before any
building-height calibration. No full original provider SHA256 from 40GB
data was established by the range reads.
