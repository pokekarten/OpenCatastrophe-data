<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# WorldCover v200 original pixels × synthetic polygon: fractional-overlap pilot

**UTC:** 2026-11-01. **Scope:** methodology-only spatial overlay on the
**one previously verified original** ESA WorldCover 2021 v200 N48E009
compressed TIFF block 185. No real building polygons, insurers, addresses,
private exposures or valuation inputs were obtained or stored.

## Reproducible exact-source test

[GitHub Actions source job run 41329543575](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41329543575)
passed all **seven** existing Deflate/class/source HTTP tests and **five**
new geometry/negative tests before the real live acquisition.
The existing fixed three requests and access contract did not change:

- Exact 4,096-byte first TIFF header SHA-256:
  `a74fc1ff4733c3afff09328e014c0731eba2f1912f3f5cbc330ed0700f3f3529`.
- Exact 10,368-byte TIFF offset/bytecount directory SHA-256:
  `7de08710b64cad350b81da83a81fcfc0c74f5285e20e28b0a3e42d19151885ba`.
- Exact 56,442-byte compressed block `43278196–43334637`,
  SHA-256 `526eb0819a9101a4e23df17dd70a040444190bb034528237fee29b415f9dd29a`.
- Exactly 1,048,576 uint8 decoded classes; decoded SHA-256
  `5a7cd7ce34de5d054e0f134cd5823b6bac77314fd3a2431ee547fe40cc0b3b7e`.
- Live retrieval UTC `2026-11-01T17:04:26.225865+00:00`.
- Decoding code SHA-256:
  `5b5b66f5f7dfd357f66d6c0596ee9a167ae2aa55ba3bd16a4665434c35317729`.

The original raster is 2021 land cover, not a 2026 ground survey.
Provider attribution: ESA WorldCover 2021 v200 / VITO consortium,
CC BY 4.0, <https://esa-worldcover.org/en/data-access>.

## New polygon-vs-raster method

`scripts/worldcover_synthetic_polygon_overlap_v0.py` contains an explicit
**invented** four-corner EPSG:4326 polygon surrounding the previously
fixed synthetic geographic test point (9.5° E, 50.5° N). It is **not**
an observed roof or any ALKIS, EUBUCCO, OSM, address or insurance building.

The zero-external-dependency routine transforms the WGS84 polygon to
source georeferenced `(raster-column, raster-row)` coordinates, clips
the exterior ring against each affected pixel square, and weights each
original WorldCover class by its *actual fractional pixel overlap*.
It enforces one verified block, at most 64 candidate cells, no holes
or multipart polygons, bounded simple geometries and source class
whitelist. A 1e-8-pixel grid-line tolerance avoids false micro-slivers
on exact integer raster boundaries. In this review, the geometry is
fixed and the full original pixel buffer is discarded at exit.

Original live source results for the deliberately synthetic polygon:

| Diagnostic field | Observed |
| --- | ---: |
| Pixel cells intersected | 24 |
| Polygon fractional area in pixel-square units | 14.08 |
| Original class 10: tree cover, area-weighted share | 1.0 (100%) |
| Source class at polygon area-centroid raster cell | 10 (tree cover) |
| Distinct intersecting classes | 1 |
| Real building matched | **No** |
| Insurance model input admitted | **No** |

The 14.08 value is **not physical square metres**. It is a
dimensionless sum of angular raster cell fractions; EPSG:4326 cell ground
area varies with latitude. The result is not an independent land-cover
classification accuracy estimate or a property-level observation.

In a separate **completely synthetic pixel fixture**, the same polygon
covers **50% class 10 (trees)** and **50% class 50 (built-up)** while its
centroid raster cell has **class 50**. This controlled counterexample
demonstrates that centroid-only assignment can discard mixed land-cover
context. **The 50/50 mixture is not a real ESA observation.**

## Science gates before real buildings

A real asset pilot requires an independently admissible building source
with polygon shape, exact CRS/axis order, source vintage and license
clearance. Only then may researchers evaluate polygon intersections
against original land-cover classes for the *same geographic area*
and quantify overlap/timestamp/edge errors.

Holes, courtyards, multipart footprints, neighboring TIFF blocks,
large footprints, actual square-metre area computation and polygon
topology beyond this minimal synthetic example remain unsupported.
They must not be silently collapsed to centroids. Land-cover class
50 (built-up) includes non-building artificial surfaces; neither its
pixel counts nor polygon shares represent building inventory, insured
TIV, construction attributes, vulnerability, hazard intensity or
insurance loss.

`source_pixel_values_exported=false`,
`real_building_footprint_matched=false`,
`insured_tiv_inferred=false`,
`model_input_approved=false`.
No source or geometry bytes were added to Git, an object store or the
live insurance database. No Pokémon database was touched.
