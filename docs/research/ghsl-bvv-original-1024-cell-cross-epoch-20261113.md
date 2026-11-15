<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Original GHSL BUILT-S/V E2020 vs BVV HU-BY: paired 1,024 native grid cells

**2026-11-13.** Scientific research scope, **not an accepted original
1,024-cell run until its new trusted-main workflow has executed**.
The exact existing Munich-region original 32×32 JRC source study
window has been independently matched to the full official Bavarian
Oberbayern Shapefile *at the ROI aggregate level*. This PR makes a
reproducible **within-grid paired comparison**, not a hypothetical
data source, insurer asset register or accuracy estimate.

## Immutable source provenance and original data rights

Previous successful, actually executed source receipts:

- JRC GHSL BUILT-S R2023A E2020, official original TIFF
  compressed native 512×512 uint32 tile **#809**, one fixed
  32×32 original source window at global top-left `col=22973,row=4899`.
  Original source SHA-256, TIFF-CRS/scale and binary values were
  independently reproduced by
  [source action 43309743505](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43309743505)
  and [GDAL action 43317950827](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43317950827).
  Original window SHA-256:
  `2f1a3322b2081e70e8e7b08339dc14b61d5286605208f063fd57539e80121106`.
  Source **74,802,406 m²** modelled built-up surface, **937**
  positive/87 zero cells. Neon research-only sample **#49**.
- JRC GHSL BUILT-V same release/epoch/native window with
  **520,775,503 m³** modelled built volume,
  window SHA-256 `2929b3c7e33e00948ca6589bec268eb80ff59bafe13d9463e8440ee7bf298ec9`,
  already independently reproduced by the same two original JRC
  workflows. Neon original research-only sample **#50**.
  BUILT-V is **dependent on BUILT-S/building height**; it is included
  only in the ordered tuple provenance, *not* treated as independent
  measured reference for footprints.
- Official **Bayerische Vermessungsverwaltung Hausumringe Bayern
  (HU-BY)** Oberbayern regional original ZIP, specifically
  `hausumringe.shp`. Reviewed open-product licence **CC BY 4.0**,
  commercial reuse with attribution:
  **“Datenquelle: Bayerische Vermessungsverwaltung – www.geodaten.bayern.de”**.
  The linked publisher dataset ATOM retains an incomplete
  `<rights>TODO</rights>` metadata field; this does not grant
  rights over restricted ALKIS WFS, non-open individual cadastre
  fields or the national HU-DE product.
- Complete original [BVV SHP source main
  action 43471636096](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/43471636096)
  authenticated the public source byte stream using **20 exact
  contiguous HTTP206 Ranges**, complete original **166,172,236**
  Deflate-member bytes SHA-256
  `22364ef161d6411e2010be590d791508242ec6d36ffc3a314833cedcd6afc615`,
  full **501,212,696** native uncompressed SHP bytes SHA-256
  `977e35aa7764564be115776ea56f78ef228d3cc79939b28f08c6cbe96e2e7a0c`,
  publisher ZIP-local member **CRC32 `55540a66`**,
  **2,703,736** sequential source Polygon records and
  **417,565** actual source Polygons clipping into the frozen
  GHSL window. The source *member* is complete, not the entire
  four-file ZIP SHA proof. Neon overlapping source-provenance
  samples #56/#57 and research aggregate sample **#94**
  verified the exact same original full-SHP SHA.
- Official ROI footprint union **56,791,644.170 m²**
  after correcting **80,167.285 m²** of overlapping source
  polygons, within **588,514,088.109 m²** fixed projected
  research support. Before source-union, original individual
  Polygon clipped area sum **56,871,811.455 m²**.
  This is an **original footprint geometry measure**, not a
  count of unique insured buildings.
- JRC products above are also officially scoped **CC BY 4.0**.
  All source and output model-admission flags remain **false**.

## Exact original 1,024-cell geographic/geometry contract

The original raster is EPSG:4326 with geographic angular
30-arcsecond pixel pitch, not a projected 100-metre grid.
The exact 32×32 original source window is partitioned into
**1,024 native cells** (north-to-south, west-to-east,
row-major order). Each original source cell's geographic
four corners is transformed using pinned
`pyproj==3.7.2` from EPSG:4326 to the issuer's original
ETRS89 / UTM32 **EPSG:25832**, and constructed as a
GEOS (`shapely==2.1.2`) area polygon.

A numerical preflight tested that the union of all 1,024
native projected cell polygons and the previously verified
ROI perimeter agree within **0.01 m²**. The previously
computed preflight geometric symmetric difference is roughly
**0.000002 m²** due to source projection floating arithmetic,
not actual buildings. The exact source cell support is therefore
the same already verified BVV 2026-era ROI, not a new
road/block centroid approximation.

The **entire source** is reread only in ephemeral,
source-version-checked 20×HTTP-206 segments on reviewed main.
The source class `NativeSHPStream` now accepts one optional
**read-only research callback** taking the transient complete
ROI GEOS union and its anonymous aggregate statistics. It is
invoked once *only after the entire native record count and
decoded original-member byte length are complete*, before
global original CRC verification. The enclosing source runner
must then validate the unchanged full-original SHA,
`55540a66` CRC32, total count, original clipped ROI union,
source authorisation and original source identities **before
emitting any result**. Callback outputs are restricted to
scalar typed fields, cannot overwrite existing source evidence,
and are never called during ordinary source-only workflows.

For each cell, a transient STRtree over already unioned
official source geometry selects only the intersecting
sub-polygons; the source cell clips are measured as **m² in
EPSG:25832**. The sum of all 1,024 official cell areas must
equal the independently source-verified
**56,791,644.170 m²** full-ROI union to within **0.5 m²**.
A support mismatch, badly formed source, unreviewed SOURCE
SHA, potential UINT32-max NoData in the JRC window,
invalid GEOS clip, missing one of the 2,703,736 original
records or failed whole-SHP CRC **blocks the run**.

The original S/V values are read fresh from **only the exact
whitelisted TIFF 32-KiB source prefix plus one compressed
original block per product**. No full GeoTIFF, other block,
region, or tile is queried. Only on success of source prefix,
original tile and window hashes, original decoded block SHA
and unchanged 937/87 counts may the runner hold the 1,024
actual `uint32` original source values transiently in memory.

## Research output: hashed native pairs, only global statistics

No original per-cell JRC source numbers, BVV footprint per-cell
values, polygons, parcel/building identifiers, lat/lon, building
addresses, individual source features, rendered maps or raster
arrays are written to Git, Neon, GitHub logs or artifacts.

For all 1,024 source cells in fixed row-major order, the transient
tuple is hashed into one ordered SHA-256 receipt:

```text
little-endian 16 bytes per cell:
    uint32 JRC 2020 source BUILT-S area, m²
    uint32 JRC 2020 source BUILT-V volume, m³
    uint64 current BVV source polygon-union area (m² × 1000, rounded)
SHA256(concatenation of all 1,024 tuples)  [never print individual tuples]
```

Only **global aggregates** are returned: original source and
window SHA, official projected per-cell sum, 1,024-cell
conservation check, 2×2 count of GHSL-positive/BVV-positive,
GHSL-only, current BVV-only and both-zero study cells,
and exploratory 1,024-cell **Pearson correlation** of
JRC built surface and current issuer footprint area.

**Correlation and positive/zero cell cross-tabulation are not
precision, recall, 2020 accuracy or building footprint
calibration metrics.** BVV is a **current-era source** with
unverified feature-by-feature creation/survey date; GHSL is
**model epoch 2020**. Any differences may represent 2020–2026
building changes, different definitions or coverage, not
JRC model error. BUILT-V per-cell is only included in the
hashes/provenance, not used as an independent physical 2D
building count or insured-asset height.

This script does not write to Neon automatically. After
a real successful original source main run, an anonymised
**research-only** sample may be inserted with its verified
aggregate/cellwise SHA receipt and product attribution,
expressly overlapping prior Neon original source samples
#49/#50/#94. No unique-building count, OED exposure,
insurer TIV, loss distribution, peril calibration, or CAT
model admission is authorized.

## Reproducible execution and acceptance gates

New source-specific source runner:
`research_runners/ghsl_bvv_original_1024_cell_pairwise_v0.py`.

New [Actions workflow](../../.github/workflows/ghsl-bvv-original-1024-cell-paired.yml)
runs offline synthetic original TIFF window, source support,
ordered paired SHA and privacy tests on PRs.
**Only trusted reviewed main** or an explicit trusted workflow
dispatch executes the actual original JRC TIFF source fetches
and the complete BVV native Shapefile 20-segment read.
The source-complete runner shares the original BVV workflow's
GitHub concurrency group to avoid simultaneous big source reads.
The existing original BVV-only source workflow remains independent
as a regression check for its separate source parser change.

Expected real success gates:
- all source-specific synthetic tests pass, complete repository
  Python 3.11–3.14 and Berlin CI succeed on the reviewed commit;
- new main source-run successfully fetches the exact two
  source-owned JRC products and confirms their original
  compressed/native/window SHA-256 receipts;
- 20 individually original verified Bavarian source ranges,
  full 2.7m native records, original compressed/uncompressed SHA,
  original source CRC and exact 417,565 ROI records succeed;
- each of the 1,024 native projected cells contributes one
  anonymous paired tuple, all 1,024 current official cell-area
  values sum to 56,791,644.170 m² within 0.5 m²,
  contingency counts sum to 1,024, pairwise hash is
  reproducible, all scientific admission flags remain false.

**Until the actual trusted-main original workflow succeeds,
do not report the per-cell hash, correlation, or contingency
counts as real observed evidence**. The already verified
global 75.9222% cross-epoch area ratio remains an independent
area-level descriptive source result, not 1,024-cell validation.
