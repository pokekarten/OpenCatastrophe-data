<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Synthetic address-point ↔ building-footprint linkage diagnostic v0

**2026-11-04 — offline synthetic research only.** This is a follow-up to
[open GIS-tool research](../research/open-geospatial-toolchain-fit-20261104.md)
and [merged geocoder QA PR #1241](https://github.com/pokekarten/OpenCatastrophe-data/pull/1241).
It is deliberately disjoint from the open
[Overture crosswalk PR #1107](https://github.com/pokekarten/OpenCatastrophe-data/pull/1107)
and [Luxembourg geocoding source PR #1239](https://github.com/pokekarten/OpenCatastrophe-data/pull/1239).

## Scope and method

Given separately labelled synthetic address points and Polygon/MultiPolygon
footprints in explicitly declared **EPSG:4326**, classify each point by GEOS
`contains` (strict interior) and `touches` (boundary). The aggregate-only
diagnostic distinguishes no match, a single **candidate**, boundary ambiguity,
multiple containing footprints, inside-plus-boundary ambiguity, and source
snapshots later than the hypothetical event date. Overlapping/repeated
geometries with different IDs remain ambiguous; no tie-breaking or forced
nearest-building assignment is performed.

A unique containment result **does not** prove a physical building identity,
address entrance, property, building age, occupancy, TIV, insurer policy, peril
exposure or calibrated hazard value. Even two different declared source-family
strings cannot establish independent origin. A user-declared synthetic flag
does not prove that submitted bytes are synthetic.

The script is intentionally not a general CRS transformer. Multipart geometry
and polygon holes are supported, but coordinates must be finite, two-dimensional
WGS84 longitude/latitude; invalid polygons and antimeridian-spanning extents
fail closed. For real provider data, the existing reviewed `pyproj` pipeline
must first verify CRS and provenance; do not silently treat ACT LUREF EPSG:2169
as EPSG:4326.

## Minimal example and execution

Save this **invented** example outside Git at `/tmp/synthetic-point-linkage.json`:

```json
{
  "schema_version": "oc-point-footprint-linkage-synthetic-v0",
  "synthetic_only": true,
  "crs": "EPSG:4326",
  "event_as_of": "2026-01-01",
  "address_source": {"family": "synthetic_addresses", "release": "v1", "as_of": "2025-01-01"},
  "building_source": {"family": "synthetic_buildings", "release": "v1", "as_of": "2025-01-01"},
  "addresses": [{"case_id": "synthetic:A", "lat": 49.61, "lon": 6.01}],
  "buildings": [{
    "building_id": "synthetic:B",
    "geometry": {"type": "Polygon", "coordinates": [[[6.0,49.60],[6.02,49.60],
                [6.02,49.62],[6.0,49.62],[6.0,49.60]]]}
  }]
}
```

```sh
python -m pip install -r requirements-eu-flood-spatial.txt
python scripts/point_footprint_linkage_diagnostic_v0.py --input /tmp/synthetic-point-linkage.json
python -m unittest tests.test_point_footprint_linkage_diagnostic_v0 -v
```

Input maximum: 2 MB, 250 points, 500 footprints. No provider API calls,
downloads or network are performed; only aggregate counts are emitted.

## Next field validation, not yet performed

Use an independently versioned Luxembourg ACT BD-Adresses original point
snapshot and exact licensed BD-L-GeoBase building polygons **in an isolated
authorized runtime**. ACT warns its address points may be parcel/largest-building
centroids, not entrances, and coverage is incomplete:
https://data.public.lu/en/datasets/adresses-georeferencees-bd-adresses/

The official dataset page advertises CC0; rights and scientific validity
remain separate. The two ACT products are not independent ground truth.
Freeze original asset hashes, EPSG:2169-to-4326 transformation, building
vintage, lineage, ambiguous matches and missing cases; validate separately
against a genuinely independent holdout. Only then consider a model-input
admission request under the repository's fail-closed rights system.
