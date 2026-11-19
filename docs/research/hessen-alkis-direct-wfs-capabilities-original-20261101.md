<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Official Hessen ALKIS 2D direct WFS 2.0 source: original GetCapabilities receipt

**Date:** 2026-11-01. **Stage:** service/feature schema verification, not an observed
building footprint, building inventory, WorldCover join, CAT exposure or insurer TIV.

## Original source and rights

The [official Hessen geoportal catalogue](https://www.geoportal.hessen.de/spatial-objects/711)
links the direct WFS 2.0 endpoint for **INSPIRE-WFS HE Gebäude – 2D ALKIS**
to the publisher **Hessisches Landesamt für Bodenmanagement und Geoinformation**,
explicitly labels the public licence **Datenlizenz Deutschland Zero 2.0**,
and distinguishes *Gebäude* and *Gebäudeteil*.

The previous two fixed OGC API Features proxy samples returned valid but
**empty** feature collections; refer to
[hessen-alkis-hosenfeld-second-bbox-20261101.md](hessen-alkis-hosenfeld-second-bbox-20261101.md).
No absence of physical buildings was inferred from those empty results.

## One exact bounded live original WFS operation

[Original GitHub source run 41332732209](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41332732209)
passed **six** synthetic XML/HTTP/source security tests before exactly one
GetCapabilities request to the immutable official backend:

`https://inspire-hessen.de/ows/services/org.2.1f07430b-f7b0-4c4e-a698-fb6c60384f59_wfs?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetCapabilities`

Observed original provider evidence:

- HTTP **200**, WFS 2.0.0 namespaced XML, **30,873** source bytes.
- Retrieval UTC **2026-11-01T17:41:17.055885+00:00**.
- Original response SHA-256
  `abb7ae137eca6ffe31682b41751a258cd09e84a7445a686ca033c500cf76f2bf`.
- Frozen GET request SHA-256
  `476b85ba99ac1bfbd34cad0a97de81fd124fd2d25a10f87ccbd65a027be71ada`.
- Original parser code SHA-256
  `b8d7554324f7deb4813317cca101d89759e46537a2c26f0417b028e6e0843bb3`.
- Two original feature type names:
  `bu-core2d:BuildingPart` and `bu-core2d:Building`.
- Original `bu-core2d:Building` DefaultCRS:
  **`http://www.opengis.net/def/crs/EPSG/0/4258`**,
  i.e. geographic **ETRS89**, not the previous WorldCover GeoTIFF
  header's **EPSG:4326 WGS84**.
- The direct WFS advertises **GetFeature**, **DescribeFeatureType**
  and **GetCapabilities** operations.

The original response was handled transiently, maximum 2 MiB, no
redirects, XML DTD/entities rejected, no source XML or feature data saved.

## Next scientifically bounded query

A direct WFS `GetFeature` proof should use `count=1` and an exact
small geographic bounding box within the already-reviewed ESA WorldCover
N48E009 block185. **WFS 2.0.0 EPSG:4258 axis order is geographic
latitude then longitude** (the OGC API Features CRS84 BBOX used
longitude then latitude). For one Hosenfeld-box WFS original
request, the bounding box must therefore be explicitly reviewed as
`(min_lat=50.512,min_lon=9.479,max_lat=50.521,max_lon=9.487)` with
the EPSG:4258 CRS URI included; do not silently copy the CRS84 query.

If the direct GetFeature returns an empty FeatureCollection,
an OGC exception, unexpected XML CRS or a timeout, preserve the
actual blocker. Do not claim that the Hessian building layer has no
buildings, nor fall back to coordinates or IDs from unreviewed sources.

Any nonempty bounded original WFS feature would still require strict
GML coordinate/axis interpretation, per-part vs per-building mapping,
polygon validity, source metadata/vintage and rights before *any*
join to 2021 WorldCover pixels. Neither existing WorldCover pixel counts
nor any GML response automatically represent an insured property,
asset value, risk or catastrophe loss.

`actual_building_feature_geometry_verified=false`,
`feature_query_authorized=false`, `model_input_approved=false`.
No live insurance or Pokémon database was modified.
