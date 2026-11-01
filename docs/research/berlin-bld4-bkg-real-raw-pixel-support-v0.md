<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Berlin pilot original BLD4 building × BKG 1 m raw-source support v0

**Research-only, reproducible proof of geometry support, never a flood-depth
unit, insurer policy loss or CAT model admission.**

## Independent originals and source-identity requirements

BLD4 five-building original-derived study geometry follows the fixed
original monthly Berlin ALKIS WFS source and *two independently pinned*
CAT1 geoBoundaries 2021 / CAT2 Eurostat NUTS2021 10M boundary sources.
The source staging retains only up to five bounded **EPSG:25833
projected polygons**, area, and aggregate DE3 region, dropping
original WFS addresses, feature IDs and raw response bytes.

The hazard source is a **different** original product:
BKG's official KOSTRA maximum-water-depth **direct GeoTIFF**,
exact filename \`starkregen_maxdepth_kostra_32790_5820_10_be.tif\`.
Original source verification:
[run 41348217549](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41348217549),
47,280,200 bytes, original **full-file SHA-256**
\`7e11fcf4cac2ce07fdefa3dc0fa4414b2cc248c516a373a12c14c33b30726a6f\`.
It is **not** any of the separately examined large
2022-named GDI Berlin ZIPs. Original BKG raster header EPSG:25832,
1 m north-up, 10,000 × 10,000, signed int16, NoData=−9999.
Previous 217×217-pixel pilot *envelope* contained 37,840 positive
raw codes, 4,503 finite raw zeros and 4,746 NoData.

## First truly intersected research evidence

\`research_runners/berlin_bld4_bkg_original_raw_cell_support_v0.py\`:
- Enforces exact original full BKG source **bytes and SHA-256**
  before rasterio opens or reads pixels. No silent changed source
  or arbitrary source URL. BLD4 SQLite reader independently verifies
  application-ID, schema, provenance, DE3, up-to-five separate
  valid non-overlapping polygons, and model non-admission.
- Clips **each original building footprint to the exact fixed
  200×200 m research pilot** in EPSG:25833 *before* reprojection,
  so original provider WFS features extending outside the sample
  cannot be silently counted as raster support.
- Densifies polygon boundaries at 1 m and then explicitly
  transforms EPSG:25833 into BKG EPSG:25832 without ballpark.
  It does not pretend the two UTM zone grid coordinates are equal.
- Loads **only a maximum 512×512 raster pixel window** enclosing
  the transformed pilot. Counts no source properties, IDs or
  coordinates in logs; no building-level results leave process.
- Computes exact **Shapely polygon∩cell** fractional intersection
  areas (not centroid-only), for four categories in the BKG
  raster's projected-area coordinate system:
  **positive raw integer code**, **valid numeric zero code**,
  **original mask/NoData**, **outside the cropped sample**.
  Their summed projected areas must equal the total clipped
  source-polygon area within explicit numeric tolerances.
- The report has only aggregate areas and aggregate numbers of
  buildings with any positive code, complete valid numeric-code
  support, or no valid numeric-code support. It never exports
  building ID, geometry, WKB, geographic location, individual
  raster value or monetary result.

**Critical interpretation:** Positive raw numbers are **not
asserted metres of water depth**. Source-scenario rainfall frequency,
physical scale, BKG unit publication, missing/suppressed map
support, source vintage and building age all remain scientifically
uncertain. A valid zero raw code is a provider numeric zero, **not
an observed dry event**. NoData is always a distinct unsupported
classification. No loss, TIV, insured-share or vulnerability
estimate is created, and no persistent database changes occur.

## Execution and boundaries

PR runs only adversarial synthetic geometry/NoData/negative
pixel and area-conservation tests using the reviewed exact
Shapely, PyProj and rasterio versions on Python 3.12.
The separate source-specific workflow
\`.github/workflows/berlin-bld4-bkg-real-raw-support.yml\`
performs at most **one** 5-feature Berlin WFS, **one** 47 MB BKG
direct TIFF GET and the fixed two reviewed boundary downloads
**only on a reviewed main workflow change or manual dispatch**.
Both original providers are treated as distinct source clocks.
Temporary GeoJSON, source TIFF and BLD4 SQLite are securely
removed after the run; only aggregate proof, source hashes and
non-admission flags are printed.

If a 2026 original WFS source or 2025 BKG TIFF hash/rights or
geography diverges, this source pairing blocks. The earlier
five-building original source sample may change because ALKIS
is mutable, and five *first* records never represent all buildings
in the box. No cross-vintage or per-building insurance exposure
is inferred. BKG attribution under DL-DE/BY 2.0 must accompany
future authorized derivative use; publisher's third-party
sources and permitted model usage require separate review.

**Original actual source building∩BKG pixel outcome:** pending
successful source-specific GitHub Actions run after review and
merge; do not substitute synthetic test statistics as real source
measurements.
