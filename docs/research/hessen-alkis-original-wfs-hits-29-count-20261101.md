<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Hessen official ALKIS 2D WFS: independent original hits-only count evidence

**Date:** 2026-11-01. **Research boundary:** one provider-reported
match-count result for a frozen Hessen/Hosenfeld small-area bounding
box. **No building inventory or insurable exposure admitted.**

## Root cause investigation

The public [Hessen publisher
catalogue](https://www.geoportal.hessen.de/spatial-objects/711)
provides the public original `INSPIRE-WFS HE Gebäude – 2D ALKIS`
WFS service and labels its data licence DL-DE Zero 2.0.

Previous independently tested source operations:

1. Two OGC API Features proxy requests through the official geoportal:
   both HTTP 200 but each returned **zero** GeoJSON features. These
   are **not** evidence that there are no physical buildings.
2. Original WFS 2.0.0 `GetCapabilities`: the service advertised
   `bu-core2d:Building`, `bu-core2d:BuildingPart`, `GetFeature`
   and default **EPSG:4258 / ETRS89** for Building. Source
   sample SHA-256 `abb7ae137eca6ffe31682b41751a258cd09e84a7445a686ca033c500cf76f2bf`.
3. One direct WFS `GetFeature` `COUNT=1` in Hosenfeld with explicit
   EPSG:4258 **latitude/longitude** BBOX found one `Building` XML
   member with GML geometry markup, but contradictory
   `numberReturned=0`. The request was rejected by the strict
   feature parser; only safe diagnostic metadata was retained.
   Source SHA-256 `3fef39eed3bd0d149d65f0cc5741db99e7d215e11a7115a762de26d855265f58`.

## New exact independent WFS count-only operation

[GitHub Actions original source execution
41333994339](https://github.com/pokekarten/OpenCatastrophe-data/actions/runs/41333994339)
passed **six** synthetic negative/security tests, then executed a
single frozen WFS 2.0.0 `GetFeature` with `RESULTTYPE=hits`:

`https://inspire-hessen.de/ows/services/org.2.1f07430b-f7b0-4c4e-a698-fb6c60384f59_wfs?SERVICE=WFS&VERSION=2.0.0&REQUEST=GetFeature&TYPENAMES=bu-core2d:Building&COUNT=1&RESULTTYPE=hits&SRSNAME=urn:ogc:def:crs:EPSG::4258&BBOX=50.512,9.479,50.521,9.487,urn:ogc:def:crs:EPSG::4258`

- UTC 2026-11-01T17:56:26.471952+00:00.
- HTTP 200; original XML **350** bytes.
- Original WFS `FeatureCollection` explicitly advertises
  **`numberMatched=29`**, `numberReturned=0`.
- Zero feature members were included: **correct** for WFS
  `resultType=hits`; no GML building bodies requested.
- Original response SHA-256
  `d6f7c61445b81a61efe1a4c8fc98a088ba76c20142e9ec8bd3663afc808e621a`.
- Frozen source GET SHA-256
  `dd65ef2f2b7ba141b315252187301e148252921d46e9f350c626c15081285ab0`.
- Code SHA-256
  `e4949fc25aae894bbfec3cd121e3f4e720e6f0a54fbc64fc6a3b6c1479093a36`.
- No source XML, building IDs, geometry, attributes or coordinate
  bytes were committed, saved or emitted.

**Scientific interpretation:** `29` is the **original service's
declared number of matching `Building` features in that exact fixed
query**, not an independently counted/quality-controlled physical
building stock, number of building parts or insured properties.
It does materially disprove a *definitive negative conclusion* from
the two empty OGC Features proxy responses, but it does **not**
resolve the original data source's `numberReturned=0` contradiction
in the separate `COUNT=1` feature-body response.

## Next highest-value source work

Reconcile the direct WFS `GetFeature` member count discrepancy with
the service's advertised schema and an independently reviewed exact
alternative response shape (e.g. `DescribeFeatureType` plus one
strictly bounded GML geometry diagnostic) while preserving the
original count mismatch; never patch a true source inconsistency away.

For a practical polygon/land-cover join, independently verify one
official ALKIS building exterior ring and any interior rings, exact
ETRS89 spatial axis order, source vintage, physical topological
validity, whether a `Building` represents one object or parts, and
location inside the same original ESA WorldCover 2021 v200 N48E009
raster block. ETRS89 to WGS84 comparison must be assessed and
recorded, not silently assumed equivalent at sub-pixel precision.

No commercial-model admission, derived insurer TIV, private address
matching, actual exposure counts or database changes took place.
`model_input_approved=false`.
