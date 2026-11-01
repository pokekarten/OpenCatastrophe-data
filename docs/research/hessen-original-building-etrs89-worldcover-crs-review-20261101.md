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
