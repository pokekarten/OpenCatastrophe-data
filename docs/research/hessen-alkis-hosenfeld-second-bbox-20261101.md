<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Hessen ALKIS 2D: second empty original building-feature API receipt

**Date:** 2026-11-01. **Decision:** OGC API Features transport is
reachable, but the two executed original service selections have
provided **no actual building geometries**. Do not count a zero-feature
page as evidence that the town or raster cell lacks buildings.

## Independent fixed settlement-centre source test

Public source: official Hessisches Landesamt für Bodenmanagement und
Geoinformation OGC API, product INSPIRE-WFS HE Gebäude 2D ALKIS,
collection `bu-core2d:Building`, provider catalogue:
<https://www.geoportal.hessen.de/spatial-objects/711>.

The official catalogue labels the layer as DL-DE Zero 2.0 and lists
`bu-core2d:BuildingPart` separately. The producer's
[Hessen open-data statement](https://hvbg.hessen.de/geoinformation/open-data)
allows public automated reuse, but the exact survey/vintage of the
mutable source remains unknown.

The [first live rectangle receipt](hessen-alkis-official-buildings-wgs84-bbox-20261101.md)
used `bbox=9.427,50.489,9.511,50.573` and received zero features.

A second, distinct frozen read-only original request was selected
around the approximate Hosenfeld town-centre location, itself inside
the already verified ESA WorldCover 2021 v200 N48E009 block 185.

[Actual GitHub Actions run 41330829493](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41330829493):

- Fixed host: `https://www.geoportal.hessen.de`.
- Collection: `/spatial-objects/711/collections/bu-core2d:Building/items`.
- Exact query: `f=json&limit=5&bbox=9.479,50.512,9.487,50.521`.
- UTC `2026-11-01T17:18:58.386191+00:00`.
- Original HTTP **200**, GeoJSON FeatureCollection, **1,001 bytes**.
- SHA-256 of the original response bytes:
  `b723c22984f08d45401eb4c2946ad73a6ad7dd44009790946a77b5a7422ae37f`.
- Exact GET request identity SHA-256:
  `39f43959ff21fc71054fd48963e9ac97f88d0f7581688926b3e14a44b0337388`.
- Updated code SHA-256:
  `0e521ee33ff7b1bb51597461d10c3a5a7c33628168509a9a8c46eab586a49855`.
- Original returned features: **0**, inspected coordinate pairs: **0**,
  source metadata `numberMatched` not provided as an integer, and no
  pagination was followed.
- `geometry_available_in_this_sample=false`,
  `returned_geometry_envelope_intersects_exact_bbox=null`,
  `real_building_worldcover_overlap_verified=false`,
  `model_input_approved=false`.
- **Eight** fully synthetic tests passed before the one live query.

Both original responses were valid but empty. The identical source
body length of 1,001 bytes does **not** prove the same source data
content or consistent service semantics. Original response hashes
are different. Do not silently substitute source catalogue metadata,
land-cover class-50 pixel counts, OpenStreetMap estimates or synthetic
polygons for real ALKIS features.

## What to do next

1. Investigate the direct official source WFS endpoint via one
   bounded `GetCapabilities` request, and determine supported
   INSPIRE Buildings2D layer names, output formats and axis order:
   `https://inspire-hessen.de/ows/services/org.2.1f07430b-f7b0-4c4e-a698-fb6c60384f59_wfs?`.
   A transport-level valid but empty proxy API is not confirmed usable
   for real source building-feature downloads.
2. Only after schema/rights checks, freeze one minimal bounded WFS
   feature query with `count` and a small selected bbox; guard GML
   namespace, coordinate CRS and 2021/2026 vintage differences.
3. Do not join to the one WorldCover original block until at least
   one actual verified, independently licensed building polygon is
   acquired in the same geographic region with valid topology.
   Distinguish individual buildings from INSPIRE building-part
   objects, roof footprints and parcel/insurer properties.

No original source feature properties, IDs, coordinate pairs, raw
geometry or insurer TIV were emitted, persisted or committed. The
actual insurance CAT database and the Pokémon databases remain unchanged.
