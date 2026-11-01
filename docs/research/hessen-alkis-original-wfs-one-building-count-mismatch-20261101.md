<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Hessen original ALKIS Building: bounded direct WFS GetFeature count discrepancy

**Date:** 2026-11-01. **Disposition:** the original direct
INSPIRE-WFS 2.0 source returned one `Building` XML member, but its
own `numberReturned` attribute reported zero. **Blocked for
building-geometries admission; no insurer or CAT model import.**

## Independent source context and rights

The publisher's [official Hessen 2D ALKIS WFS
catalogue](https://www.geoportal.hessen.de/spatial-objects/711)
labels the INSPIRE Buildings dataset as **Datenlizenz Deutschland Zero
2.0** and distinguishes `Building` from `BuildingPart`.

The [verified original direct WFS GetCapabilities
receipt](hessen-alkis-direct-wfs-capabilities-original-20261101.md)
proves that `bu-core2d:Building` is an actual advertised feature
type, `GetFeature` is available and default CRS is **ETRS89
EPSG:4258**. Separately, two correctly bounded public OGC API
Features GeoJSON requests had returned zero features; see
[hessen-alkis-hosenfeld-second-bbox-20261101.md](hessen-alkis-hosenfeld-second-bbox-20261101.md).

## Exact original WFS one-feature diagnostic

[Original one-feature source workflow 41333542441](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41333542441)
ran **eight** fully synthetic strict negative/security checks before
one source request. No additional page, feature, region or provider
request was performed.

Reviewed original source URL:

`https://inspire-hessen.de/ows/services/org.2.1f07430b-f7b0-4c4e-a698-fb6c60384f59_wfs?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature&TYPENAMES=bu-core2d:Building&COUNT=1&SRSNAME=urn:ogc:def:crs:EPSG::4258&BBOX=50.512,9.479,50.521,9.487,urn:ogc:def:crs:EPSG::4258`

- Frozen BBOX **EPSG:4258 latitude, longitude** order, unlike the
  earlier OGC API Features default CRS84 longitude, latitude order.
  The Hosenfeld window is within the verified ESA WorldCover N48E009
  tile and selected 1,024×1,024 original TIFF block.
- UTC original execution **2026-11-01T17:51:01.592287+00:00**.
- HTTP **200**; original GML/XML body **4,395 bytes**.
- Raw source response SHA-256
  `3fef39eed3bd0d149d65f0cc5741db99e7d215e11a7115a762de26d855265f58`.
- Immutable GET request SHA-256
  `84582b7a6ef60abdf41fadcadaa83ec1b68daf9463f420fe9ea9a13bff385bc4`.
- Reviewer-side parser SHA-256
  `8e8dcf297075ca3319a7708f60d6371fac6756babd70b50a73f7467d11362384`.
- Original WFS `FeatureCollection` contained **one**
  `wfs:member` with a `Building` element and **GML geometry
  markup**; its declared GML CRS matches requested EPSG:4258.
- Critically, the same source response sets **`numberReturned=0`**.
  `numberMatched` is not a verified integer.
- The parser's strict default mode **rejects** this contradictory
  response. An explicit `--diagnostic-only` mode records only the
  source's safe numeric contradictions and digests:
  `source_validation_status=BLOCKED_CONTRADICTORY_WFS_COUNTS`,
  `reported_member_count_consistent=false`.
- Source feature IDs, properties, addresses, original polygons and
  coordinate values were **not emitted or stored**. The original
  bytes were kept transient for the bounded parse, never committed.

A parsed `Building` XML member is an independently relevant
**source-availability indication**, but it is **not** a scientifically
validated building footprint, verified closed polygon, single
physical property, roof, insured dwelling, asset value or exposure.
The source count contradiction must not be silently normalized, and
the GML geometry marker does not prove topology accuracy or the
actual survey/source vintage.

## Next causal verification

Research the GetFeature service's own `numberReturned` semantics
and whether an independently bounded request using its advertised
`resultType=hits` or a reviewed output-format alternative
confirms the response's feature-count metadata. Do not change the
original strict one-feature handler to accept conflicting counts.

Before any real WorldCover intersection, require an exact
GML feature geometry and CRS interpretation, independent
topology/source-vintage checks, an auditable source identifier
policy and a defensible source-rights determination. The 2021
WorldCover raster and the mutable ALKIS geometry do not have the
same confirmed acquisition date.

`actual_2d_polygon_topology_verified=false`,
`actual_building_survey_vintage_verified=false`,
`actual_building_worldcover_overlap_verified=false`,
`source_raw_features_or_gml_persisted=false`,
`model_input_approved=false`.

The separate insurance CAT and Pokémon databases were not altered.
