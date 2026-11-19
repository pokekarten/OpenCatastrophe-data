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

## First actual original building-polygon × raster-cell area receipt

**Verified real source proof, 2026-11-01**. The one-shot
[GitHub Actions run 41349226673](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41349226673)
completed successfully against reviewed main commit
\`275a326cf5a1e5dfdd7815203d5eb1fc0247a768\`,
with source report recorded at approximately
2026-11-01 20:54:47 UTC. This is the **first true original
WFS-derived building polygon × original BKG KOSTRA source raster
pixel-area computation** in the 200×200 m Berlin pilot.

| Verified original source proof | Aggregate result |
| --- | ---: |
| Original official ALKIS WFS response SHA-256, currently mutable | \`fe7f5e65823ac72430b677a63f0d1a33ed3c3f84bf0d45340650dceaa97c2460\` |
| BKG original **full** TIFF SHA-256 | \`7e11fcf4cac2ce07fdefa3dc0fa4414b2cc248c516a373a12c14c33b30726a6f\` |
| Original BKG TIFF bytes independently verified | **47,280,200** |
| Original first-five ALKIS buildings with positive pilot intersection | **5** |
| Raster cells scanned in fixed pilot window | **47,089** |
| **Total clipped building area in reprojected raster CRS** | **683.311267 m²** |
| Building area with original **positive raw integer** code | **2.752013 m²** |
| Building area with original **valid raw zero** code | **14.434404 m²** |
| Building area with original **NoData / missing** raster mask | **666.124849 m²** |
| Building area outside inspected window | **0.000000 m²** |
| Buildings with any positive raw code | **3** |
| Buildings with entire pilot-clipped area valid numeric raster support | **0** |
| Buildings with no valid numeric raster cells under footprint | **2** |
| Area conservation (positive+valid zero+NoData+outside = clipped area) | **Passed** |

All area metrics describe **polygon∩cell fractional overlap in
EPSG:25832** after bounded, densified reprojection, **not** the
unclipped full cadastral footprints nor the entire pilot's
217×217-cell totals. Values are *aggregate-only*: no original
feature IDs/coordinates, individual building values, addresses,
original TIFF or source footprint bytes are exported. The 5
cadastral source features are a *first-five WFS sample* and not
a complete building inventory for the research box.

**Very material scientific limitation:** Of 683.311267 m²
original-derived pilot-clipped building area, **666.124849 m² are
NoData**, not proven dry or safe and not zero simulated water depth.
Although three building polygons touch a positive raw-code cell
by nonzero area, that does **not** mean three buildings flooded,
faced insured loss, or were physically assigned a verified depth.
Source TIFF band-value units remain **unverified**; KOSTRA is a
simulated design rainfall scenario, not an actual loss event.

The original BKG site explicitly describes use of building
geometry as a hydrodynamic model input, but whether that process
causes this footprint NoData pattern is **not established** by
the above spatial data. Before any exposure or loss conclusion,
independently research provider NoData masks / buildings-as-obstacles,
physical depth encoding and the geometry-date mismatch. NoData
cannot be extrapolated from nearby ground cells without a
separate scientifically defended building-perimeter method.

### Next high-value causal task

Create a separate bounded **outside-building ground/perimeter
support** experiment: classify an independently defined narrow
buffer ring in the original TIFF CRS, distinguish valid zero,
positive raw codes and NoData, enforce disjoint adjacent rings,
and report only **aggregate ring support** alongside—not in
place of—the footprint support. A valid nearby ground pixel
should not automatically become an assigned building-level
water depth, entrance threshold or insured damage. Keep
source-specific model rights and attribution review before
CAT model admission.

