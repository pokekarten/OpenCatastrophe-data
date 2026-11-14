<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# GHSL R2023A E2020 — independent GDAL/LibTIFF original raster replay

**2026-11-12.** Scientific status: **independent original GDAL/LibTIFF
replay successful** on trusted main (run 43317950827). This establishes
two-decoder source-data equality, not building/insurer/CAT model validity.

## Frozen original source and provenance

Previously verified, original JRC BUILT-S and BUILT-V R2023A/2020
32 KiB source-prefix and original compressed TIFF block 809 have been
acquired under their product-scoped **CC BY 4.0** notices and tested in
[trusted-main original run 43309743505](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43309743505).
Those evidence items remain immutable, and the original native science
receipts are in separate Neon research samples **49** and **50**:
[original verified source record](ghsl-built-s-v-exact-native-block-execution-gate-20261112.md).

| Frozen JRC product | BUILT-S | BUILT-V |
| --- | --- | --- |
| Original compressed block SHA-256 | `eae39538ec234c80d43f135e7022e1c2ad4be3e10d72dcdc2e82534431a276d9` | `578a62b6164f30ab82479e37cbfbf4353af2db18ff2eef65552aff5dce12e53c` |
| Original decoded 512×512 uint32 block SHA-256 | `1d961e2c951e4db8df6e22776903aa06ea943a9f49728ef4a8fa8178506c8923` | `e91e026954d2f37d19c48ea87b3e33207e8c67e0efdda0d5c66589a3e751b5f5` |
| Original 32×32 window SHA-256 | `2f1a3322b2081e70e8e7b08339dc14b61d5286605208f063fd57539e80121106` | `2929b3c7e33e00948ca6589bec268eb80ff59bafe13d9463e8440ee7bf298ec9` |
| Fixed source units / sum in 1,024 cells | Built surface m², 74,802,406 | Modelled built volume m³, 520,775,503 |
| Original window composition | 937 positive, 87 zero, zero observed uint32-max candidates | same |

The new reproducibility method uses **GDAL/LibTIFF via
Rasterio 1.5.0 and NumPy 2.3.5**, a distinct numerical decoding
implementation from the earlier Python `struct` / `zlib` loop.
It does not redownload entire objects or open arbitrary `/vsicurl` URLs:
only the **exact two source reads per product** already permitted in
`scripts/probe_ghsl_built_native_original_block_v0.py` are used.
The frozen original prefix TIFF/GeoTIFF CRS is rechecked first, then
the frozen compressed source-block SHA is verified **before**
constructing one tiny 512×512, non-georeferenced, RAM-only TIFF wrapper
around those exact original compressed bytes. GDAL independently
decodes the transient uint32 grid and computes the frozen 32×32 window
statistics and hashes. The new wrapper is a decoding mechanism **not**
the original provider TIFF nor a verified source georeference.

The input contract requires exact source byte counts, HTTP **206**,
exact Content-Range/full-file size, no redirects/retries and the
original source SHA. The compressed stream's inflation envelope is
separately strictly bounded to **exactly 1,048,576 bytes** with no
unconsumed or trailing data before invoking GDAL. This extra protection
matters because LibTIFF can sometimes accept oversized Deflate
payloads while populating only the declared tile shape. The GDAL
implementation still independently reads and interprets **all uint32
science values** and rejects discrepancies against both original
decoded-block/window hashes and the eight predeclared summary metrics.

## Reproducible execution

`scripts/ghsl_original_gdal_independent_replay_v0.py` uses only fixed
source-owned product keys `surface` and `volume`; no free-form URL,
bbox, variable, year, retry, full TIFF, site crawl or external metadata
can change the provider scope. Synthetic unit tests are offline,
including uint64-safe sums, uint32-max sentinel exclusion, rejection
of malformed/bomb/trailing compressed frames and source SHA drift.

`.github/workflows/ghsl-original-gdal-replay.yml` runs pinned
synthetic GDAL tests during PR review. Actual original-provider
requests are **disabled in PRs**. On explicitly reviewed source-code
merge to main or manual dispatch only, an ephemeral GitHub runner
replays **each original product once**, emitting only SHA hashes,
counts/sums and boolean negative science/admission fields.
No source TIFF/pixels/window, transient georeferenced features,
reconstructed TIFF, secrets, spatial addresses or binary artifact
is persisted into public GitHub or Neon.

The new original-provider workflow **has succeeded independently**
on trusted main (run 43317950827). Synthetic tests alone were
insufficient, so the successful main source logs were inspected and
their original hash and numeric outputs are recorded below.

## Predeclared geometry and independent building-footprint follow-up

The exact **source** GHS 30-arcsecond `EPSG:4326` raster,
window top-left **column 22973, row 4899**, 32×32 cells,
has this approximate fixed geodetic cell-edge envelope from original
TIFF pixel scale/tiepoint (not a street address):

```text
min_lon = 11.440416643748 ; min_lat = 48.007916676356
max_lon = 11.707083309358 ; max_lat = 48.274583341950
```

It covers a Munich-region research area. Source cell pitch is angular
degrees, **not 100 m or constant square metres**; never combine it
directly with the separately projected `ESRI:54009/100 m`
GHSL layers or the Google Earth Engine 100 m asset without a versioned
grid/CRS reprojection and aggregation contract.

An independent reference candidate is Bavaria's **official ALKIS
Hausumringe** polygons, source candidate
`de.bayern.hausumringe`, not an OSM/GHSL-derived proxy.
The [official Bayern Geoportal Hausumringe catalogue](https://geoportal.bayern.de/geoportalbayern/seiten/dienste)
advertises unauthenticated, cost-free ATOM downloads. The
[AdV source licence review](https://www.distributions.informationgrid.eu/freitextsuche?inspire=inspire_false&productgroup=at15&q=view&type=)
states **CC BY 4.0**, with required attribution:
**“Datenquelle: Bayerische Vermessungsverwaltung – www.geodaten.bayern.de”**.
The published [Hausumringe format contract](https://www.ldbv.bayern.de/mam/ldbv/dateien/hausumringe-by_datenformatbeschreibung.pdf)
uses shapefile polygon/multipolygon geometries and municipality AGS,
but **not building-level insured values**, claim history, occupancy,
full construction year or source GHSL volume.

A scientifically valid comparison needs exactly bounded official
polygon input in a controlled local environment, exact archive SHA,
geometry/CRS/AGS validation, polygon clipping/reprojection into an
appropriate metre-based local CRS such as EPSG:25832, conservation
of partial polygon overlap area by GHSL source cell, boundary
deduplication, source vintage and completeness checks, and holdout
definitions. **We have not yet acquired those building polygons nor
performed the spatial join.** In particular **2026 public ALKIS
building footprints are not unbiased 2020 building footprint truth**
without historical change/vintage controls.

## Admission and rights

Both licensed GHSL numerical products are dependent JRC estimates
(`BUILT-V` uses `BUILT-S` and building height), not independent
observations of unique insured buildings. This exercise validates
**decoder parity**, not building counts, modelled volume truth,
building identity, raw pixels' uncertainty, insurer TIV,
hazard, vulnerability, insured losses or production model fitness.
No model input approval and no raw data persistence is granted by
a successful test. Existing Neon research hashes and source-rights
verdicts stay scoped to the original reviewed samples.


## Independent original-source main acceptance receipt — 2026-11-12

**SUCCESS:** [GHSL independent original GDAL Actions run
43317950827](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43317950827)
completed on reviewed main commit
`52ee936b92a288d9c2ddf38013c1f104828516ea`.
The source-specific PR tests passed six synthetic cases with pinned
Rasterio 1.5.0 / NumPy 2.3.5 and the complete repository CI matrix
passed before merge. Two subsequent **live JRC provider probes** each
enforced original header SHA, HTTP-206 Content-Range and object size,
one fixed compressed source block #809, and its original block SHA.

| Independently decoded original evidence | BUILT-S | BUILT-V |
| --- | --- | --- |
| UTC successful live read | 22:14:00, 12 Nov 2026 | 22:14:01, 12 Nov 2026 |
| Original compressed source block SHA-256 | `eae39538ec234c80d43f135e7022e1c2ad4be3e10d72dcdc2e82534431a276d9` | `578a62b6164f30ab82479e37cbfbf4353af2db18ff2eef65552aff5dce12e53c` |
| Independently decoded original 512² UINT32 SHA-256 | `1d961e2c951e4db8df6e22776903aa06ea943a9f49728ef4a8fa8178506c8923` | `e91e026954d2f37d19c48ea87b3e33207e8c67e0efdda0d5c66589a3e751b5f5` |
| Original fixed 32²-window SHA-256 | `2f1a3322b2081e70e8e7b08339dc14b61d5286605208f063fd57539e80121106` | `2929b3c7e33e00948ca6589bec268eb80ff59bafe13d9463e8440ee7bf298ec9` |
| Positive / zero / candidate sentinel cells | **937 / 87 / 0** | **937 / 87 / 0** |
| Positive source-unit sum | **74,802,406 m²** | **520,775,503 m³** |
| Min / max positive source-unit value | 1 / 321,677 | 1 / 3,168,579 |
| Original Neon observed-value sample (unchanged) | **49** | **50** |

Thus **two distinct decoder implementations** reproduced the frozen
original decompressed source SHA, window SHA and all predeclared
numeric aggregates. GDAL/LibTIFF read the original uint32 values from
a transient in-memory one-tile TIFF, with a strict 1MiB Deflate frame
integrity gate. The independent code never emits, writes or commits
native source pixel arrays or reconstructed TIFF bytes.

**Do not double-count:** this corroboration concerns the same two
Neon samples #49/#50; no new observation area or separate building
inventory was added, and no model admission occurred. No full-original-
TIFF hash or independent building ground truth exists. The official
BVV Hausumringe database/index/CRS receipts and current public issuer
ATOM feed are tracked separately in
[the existing BVV research record](by-hausumringe-wsf2019-alignment-20261112.md).
In particular actual BVV .shp polygon geometries and survey vintage
remain unverified and no 2020-vs-2026 spatial accuracy was claimed.
