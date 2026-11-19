<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Hessen official ALKIS: one original Building GML ring quality receipt

**Original provider read:** 2026-11-01 18:23:07 UTC,
[GitHub Actions run 41336323802](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41336323802).
**Status:** bounded scientific *ring-structure preflight* succeeded,
original provider-count inconsistency **still blocks any real-building
inventory or CAT model admission**.

## Source identity and independent evidence

Official dataset: Hessisches Landesamt für Bodenmanagement und
Geoinformation, INSPIRE-WFS HE Gebäude – 2D ALKIS. The
[Hessen source catalogue](https://www.geoportal.hessen.de/spatial-objects/711)
labels the official layer as Datenlizenz Deutschland Zero 2.0 and
differentiates Building from BuildingPart.

The direct WFS 2.0.0 `GetCapabilities` independently advertised
`bu-core2d:Building` with ETRS89 `EPSG:4258` default CRS and
`DescribeFeatureType` verified the global element
`bu-core2d:Building` with `bu-core2d:BuildingType`, but two XSD
imports remain unresolved. A separate fixed `resultType=hits`
request previously reported `numberMatched=29` for the same
small Hosenfeld query. It did not retrieve any features and the
29 is a provider-reported *matching feature* count, not a
verified physical building census.

## New original 1-feature response and ring diagnostic

This research step uses exactly the **same previously reviewed**
one-building WFS GetFeature source URL, one `COUNT=1` response
in the same fixed Hosenfeld region and explicit **EPSG:4258
(latitude, longitude) axis order**. No building ID, user-selected
query, page, different tile or second feature was requested.

- Source response HTTP 200, **4,395** bytes.
- Original source byte SHA-256:
  `a3e262bcc006deb9925e5ab6511f8964ba98ffe2eae2308567aef7b777c471ae`.
- Exact GET request SHA-256:
  `84582b7a6ef60abdf41fadcadaa83ec1b68daf9463f420fe9ea9a13bff385bc4`.
- Source parser code SHA-256:
  `9cb55a5085238f90d76d81a5a84eb0dc379816bb622ffed2a4defc1c208b4ecc`.
- **One** actual original GML polygon surface, **one** exterior
  `LinearRing`, **zero** interior rings.
- The exterior ring contains **six** coordinate positions including
  an explicit closing position; its 2D coordinates were finite and
  within a plausible Hessen geographic range, the ring was closed
  and had nonzero signed area.
- The source parser detected **no proper segment self-crossing** in
  this bounded ring and its positions fall in the geographic envelope
  of the previously reviewed original ESA WorldCover 2021 v200
  N48E009 TIFF raster block 185. This is an envelope-level diagnostic
  only: CRS transformations have **not** been certified.
- Crucially, the same original `FeatureCollection` has **one**
  parsed `Building` XML member but still claims
  **`numberReturned=0`**. The source inconsistency is retained
  as `provider_count_discrepancy_remains_blocked=true`; do not
  silently replace the source count with the parser count.

Nine synthetic regression/security tests passed before this
original-source operation: correct/invalid rings, holes, crossing,
bounding envelope, wrong CRS, unsupported GML geometry, original
HTTP response and no source persistence.

A previous original GetFeature request produced a different response
SHA-256 even though the exact source URL and response length matched.
This may reflect source mutability or metadata/serialization, and
**does not establish that the underlying original geometry itself
changed**. Do not infer immutability or geometry-level source
history without a coordinate-safe semantic identity audit.

## What this does not prove

These are **not** observed insured properties, building valuations,
occupancies, structures/vulnerabilities, a whole Hessian building
inventory, or insurance loss records. A closed non-crossing
exterior ring is not a complete topology check across building
parts, future multipart/multi-ring features, and GIS source
vintage/accuracy.

The GML coordinates use ETRS89 EPSG:4258. The ESA WorldCover
verified grid uses WGS84 EPSG:4326. This research performed
**no verified transformation to WorldCover's CRS**,
no area in physical square metres and **no actual
polygon-versus-original-pixel intersection**.

Only bounded counts, Boolean flags, source/request/code hashes and
timestamps were logged. Raw GML, original coordinates, building IDs,
addresses, properties and other geometry payload bytes were transient
and not committed or persisted.

`provider_count_discrepancy_remains_blocked=true`;
`physical_building_polygon_topology_verified=false`;
`etrs89_to_worldcover_wgs84_transform_verified=false`;
`actual_building_worldcover_overlap_verified=false`;
`model_input_approved=false`.

Next: validate actual GML geometry with an independently reviewed
GIS topology method and authoritative CRS transformation, then
decide whether the source `numberReturned` metadata conflict
can be explained or must stay blocked. Only after resolution may
a true verified polygon be overlaid with original source
WorldCover pixel classes. Neither the insurance CAT database
nor Pokémon data were modified.
