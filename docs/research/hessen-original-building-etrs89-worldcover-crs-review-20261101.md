<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Hessen original ALKIS one-building ETRS89 → WorldCover WGS84 transformation review

**Scope:** one already reviewed original GML `Building` query in Hosenfeld.
This is a source/CRS research check, **not** an admitted building inventory,
physical roof area, insured location or catastrophe-model input.

The previous [source-original ring receipt](hessen-alkis-one-original-building-gml-ring-20261101.md)
recorded one closed exterior ring with six GML positions and no interiors.
The official direct WFS advertised ETRS89 **EPSG:4258**, whose coordinate
axis order is **latitude, longitude**. ESA WorldCover 2021 v200
N48E009's audited GeoTIFF grid uses **WGS84 EPSG:4326**. The
original provider's WFS FeatureCollection **still** reported
`numberReturned=0` despite its one parsed `Building` member.
A separate hits-only request reported 29 potential matches, not 29
verified physical/insured buildings.

## Implemented scientific audit contract

`research_runners/hessen_alkis_one_building_crs_geos_v0.py`
uses only the **same fixed, bounded original WFS GetFeature COUNT=1**
request from previous runs; no other building is queried. Source bytes
are ephemeral, at most 512 KiB, and neither coordinates nor IDs leave
the execution.

The diagnostic requires a single source Building surface, one closed
exterior, zero interiors, no unsupported extra geometries and at most
128 vertices. It then uses the repository's already-pinned
**PyProj 3.7.2** and **Shapely 2.1.2**:

- Reject malformed or GEOS-invalid original 2D geometry, rather than
  make it valid with `buffer(0)`, centroids or geometry simplification.
- Apply explicit `Transformer.from_crs("EPSG:4258", "EPSG:4326",`
  `always_xy=True, allow_ballpark=False, only_best=True)`; the
  source parser first converts the GML latitude/longitude axis order
  into the GIS longitude/latitude order.
- Disable PROJ network requests. Require an EPSG operation whose
  metadata declares a positive accuracy of at most **1 metre**.
  This is a **coordinate operation accuracy claim**, not a guarantee
  of the original building survey position or observation epoch.
- Validate finite, GEOS-valid transformed coordinates. Check each
  WGS84 vertex against original WorldCover 1024×1024 block 185's
  audited bounds; report only whether the **vertex-to-gridline** and
  **vertex-to-block-edge** distances exceed the transformation's
  declared accuracy, not a location or cell index.
- Do not interpret safe vertex margins as a guarantee of all
  polygon/raster intersections: a polygon boundary can cross many
  raster lines even if all vertices avoid them.

References for CRS semantics:
[EPSG ETRS89 / 4258](https://epsg.io/4258);
[PyProj Transformer API](https://pyproj4.github.io/pyproj/latest/api/transformer.html).

## Explicit source admission boundaries

The WFS `numberReturned` contradiction remains **blocked**, as do
source-vintage uncertainty, ETRS89/WGS84 physical-frame epoch accuracy,
interior/multipolygon building topology and the validity of any real
pixel-overlap result. The nominal pixel pitch is 1/12000 degrees; the
physical east–west cell width is latitude-dependent and must **not**
be relabelled uniform 10 metres on the ground.

Only count/quality Boolean results, transformation accuracy metadata,
exact source/request/code hashes and UTC may be logged. No GML,
original coordinate tuples, WGS84 polygon vertices or insurer data
are committed, persisted, or sent to a database.

`wfs_count_discrepancy_still_blocked=true`,
`source_building_survey_vintage_verified=false`,
`worldcover_2021_original_pixel_intersection_performed=false`,
`model_input_approved=false`.

A source-specific original provider execution receipt and scientific
outcome should be recorded only after the dedicated pinned PyProj/GEOS
workflow passes. Until then the analysis is an implemented,
unadmitted diagnostic, not a completed original coordinate validation.

## Executed original-source result — 2026-11-01

The [source-specific GitHub Actions run 41356160767](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41356160767)
**succeeded** with the eight synthetic/negative tests and the one
original 4,395-byte Hessen WFS GetFeature body. No additional feature,
WFS layer, original raster block or PROJ grid was downloaded.

- Source retrieval UTC: `2026-11-01T22:15:10.903066+00:00`.
- Exact frozen source GET SHA-256:
  `84582b7a6ef60abdf41fadcadaa83ec1b68daf9463f420fe9ea9a13bff385bc4`.
- Original 4,395-byte WFS response SHA-256:
  `6189e33dc4c24a8f2b5246e5dbd860c62efdf8570a3297b3f59b618bc02a41a6`.
- Source diagnostic code SHA-256:
  `efc32ee328e3ceccd5e13d537d174e6aad3c141cef386d9a238a89e155dafa2a`.
- Real original: **one** Building GML polygon with **six** exterior
  coordinate positions (including closure); independent GEOS validity
  is **true** for source EPSG:4258 and transformed EPSG:4326 geometry.
- PROJ selected an offline, **non-ballpark** 4258→4326 transformation
  with explicitly declared **1.0 m** operation accuracy.
- All transformed polygon vertices are inside WorldCover's originally
  audited internal TIFF block 185 and more than the declared 1 m
  operation uncertainty from **block boundaries**.
- **Not all vertices are more than 1 m from the nearest WorldCover
  raster-grid line.** This directly falsifies any implicit assumption
  that vertex cell index assignment is robust to this datum-operation
  accuracy for the original building. Exact fractional class assignments
  require uncertainty-aware spatial sampling and original pixel reads.
- Crucially **one** actual member is still paired with original
  `numberReturned=0`; `wfs_count_discrepancy_still_blocked=true`.
- No source coordinates, raw GML, building IDs, address, original raster
  data or project files were emitted, committed or stored.

This result is **not** a license to call ETRS89/WGS84 identical, claim
survey-grade 1 m building accuracy, infer one insured address, or force
land-cover class 50 onto the building. The source frame/epoch and
observed building vintage remain unknown, and the validated 2021
WorldCover tile was not fetched in this CRS-only source run.

Next causal step: implement a bounded **synthetic** tolerance/sensitivity
experiment for a one-pixel positional shift and multiple land-cover
class cells, and require full topology/source-count resolution before
any real building-pixel class or CAT exposure admission.
