<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# ACT LiDAR2024 Luxembourg: true tile polygon intersections, not only RTree rectangles

**Research-only.** This stage builds on merged LiDAR source index receipt #931
and bounded two-indexed-candidate study #934. It does NOT access LAZ point-cloud
bytes or infer actual building heights. It resolves a specific technical
ambiguity: GeoPackage RTree bounding-box hits can return false positives.

## Original receipt / exact study scope

- Official source: https://data.public.lu/en/datasets/r/04cfeb86-c9df-4ee6-a45a-8671af98a114
- SHA-1 publisher-listed original GPKG: `3269aecb189271e7c3f86127c0e96f4e213557c9`.
- SHA-256 verified in merged PR #931: `3db50821b582b9247d97d6d8bba41d9f15cd45ff0356b180322521346ef04cc8`.
- Real original index: 10,905 tile Polygons in EPSG:2169, `TableauAssemblage`, with `fid`, `geom`, `Fichier`, `Dossier`, `DownloadLink` and spatial RTree.
- Existing target: **250 × 250 m** equal-area EPSG:3035 study window around public approximate coordinate **6.1319°E, 49.6116°N**, exactly the merged ACT2023/EUBUCCO original research pilot #924.
- Previous #934 result: **2 RTree bounding-box tile candidates**, both public HTTPS source links under `data.public.lu`. This was NOT exact polygon intersection.

## Implemented exact geometry challenge

`research_runners/luxembourg_lidar2024_true_tile_intersections_v0.py`
reuses the previous exact-source receipt and strict 12-candidate budget,
then:

1. Computes the exact four-corner equal-area study polygon converted to
   EPSG:2169 via pinned PyProj 3.7.2, rather than treating its axis-aligned
   envelope as the final geometry.
2. Reads only the bounded RTree candidate rows from **the exact verified GPKG**
   and decodes their GeoPackage geometry headers using the existing strict
   source parser and pinned Shapely 2.1.2.
3. Requires valid positive-area Polygon/MultiPolygon intersections, calculates
   the original study-window *union* coverage fraction and counts unique
   intersecting source URL strings and directory groups. Distinguishes
   geometric `touches` without area from a tile that actually covers a
   measurement location.
4. Validates only HTTPS official data.public.lu or download.data.public.lu
   source URL host and basic userinfo/query/fragment exclusion. No external
   URL is executed or logged.
5. Outputs only aggregate counts and coverage. **No tile ID, folder value,
   original geometry, full source URL, building identity, point cloud,
   insurer address or raw provider bytes are written to GitHub, Neon or
   published workflow artifacts**.

The exact-source workflow is separate from existing PR #934 and uses the same
fixed official 3.5MB temporary GPKG, deleted on exit. Synthetic regressions
challenge RTree false positives, real overlap, broken source pins, invalid WKB,
unsafe URL endpoints and privacy. Actual-source workflow results must be
recorded after execution, not inferred.

## Scientific boundaries and next causal step

Even a verified polygon intersection does not establish that the tile's
`DownloadLink` points directly to a LAZ file; there can be grouped ZIPs or
different products. Treat these links as **untrusted source data** and approve
the exact official resource URL before following one. Separately enforce max
compressed bytes, archive-member limits, original source SHA-256, legal rights,
point-cloud format/classification and true X/Y/Z vertical reference. Compare
only a small source-approved classification `building` versus `ground`
sample to EUBUCCO `height_source`, using an original independent validation
sample. The same ACT provider lineage is not independent by default.
No building replacement cost or insurer TIV may be inferred automatically.

No model_input or insurance exposure is admitted by this research receipt.
