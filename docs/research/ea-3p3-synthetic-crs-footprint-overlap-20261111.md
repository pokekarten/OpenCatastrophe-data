<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# EA 3.3% AEP defended flood: source CRS check and synthetic footprint overlay

**Status (2026-11-11): synthetic-only spatial test, no source-data admission.**
This is a small causal step toward an exposure/hazard spatial adapter;
it does **not** assert property water depths, model flood damage, a frequency
catalogue, commercial dataset rights or real building risk.

## Original source observation that determines the CRS contract

A read-only, limited original-provider OGC API Features request to the
[EA present-day 3.3% defended river/sea collection](https://environment.data.gov.uk/geoservices/datasets/767c96e6-b149-4744-9d4d-34b32f6c0e1b/ogc/features/v1/collections/Rivers_1in30_Sea_1in30_defended_depths)
returned one **2,489-byte GeoJSON FeatureCollection** for
`depth_band = '150-300mm'`. Its response advertises
`crs.properties.name=urn:ogc:def:crs:EPSG::4326` and the actual
coordinates are longitude/latitude: aggregate bounds
`[-6.332526, 49.890311, -6.331644, 49.891144]`.
The single feature is a **MultiPolygon with 13 component polygons,
13 closed rings and 70 coordinate pairs** (no malformed coordinate pairs
in this one response). This is a one-record structural check, not a proof
that the entire provider collection has valid topology or complete coverage.

The [original collection metadata receipt](ea-river-3p3-present-ogc-metadata-proof-20261110.md)
independently advertises **native storage CRS EPSG:27700** but
the published **collection extent is CRS84** (longitude/latitude).
Therefore the OGC GeoJSON response must **not be treated as already
EPSG:27700 metres**. Its coordinates need an explicit
`EPSG:4326 -> EPSG:27700` transformation using
`always_xy=True` before area measurement or intersection.
No original provider GeoJSON, feature ID, coordinates or original
building data are stored in Git.

## Executable synthetic-only proof

- [`scripts/ea_flood_synthetic_crs_overlay_v0.py`](../../scripts/ea_flood_synthetic_crs_overlay_v0.py)
  transforms bounded **synthetic** Polygon/MultiPolygon GeoJSON coordinates
  from EPSG:4326 to EPSG:27700 with `pyproj.Transformer(always_xy=True)`,
  validates Shapely topology and envelope, and intersects synthetic
  building footprints with disjoint synthetic flood-depth polygons.
- [`tests/test_ea_flood_synthetic_crs_overlay_v0.py`](../../tests/test_ea_flood_synthetic_crs_overlay_v0.py)
  contains 17 synthetic cases: area conservation, unavailable depth and
  source axes, exact contiguous boundaries, polygon holes, MultiPolygon
  support, overlapping polygons/buildings, swapped CRS/coordinate axis,
  envelope escape, self-intersection, unknown field values, forbidden real
  data flags, malformed/oversized source JSON.
- `.github/workflows/ci.yml` explicitly executes the 17 tests in the
  **EU flood spatial A1** job after installing pinned Shapely/pyproj:
  the spatial proof does not silently pass due to optional-dependency
  test skips.

### Reproducible control example

One synthetic rectangular building is 100 square metres in projected
EPSG:27700, and is overlapped by two non-overlapping synthetic
categorical hazard rectangles. Input is converted via inverse projection
into synthetic EPSG:4326 GeoJSON before testing the forward transform.

| Synthetic footprint area (m²) | Value |
| --- | ---: |
| Total | 100 |
| Supported area with known `150-300mm` class | 40 |
| Supported area with `depth_band=unavailable` | 30 |
| Outside these two synthetic hazard polygons | 30 |
| Source-unknown area (`flood_source=unavailable`, **nonadditive**) | 30 |
| Conserved `40 + 30 + 30` | **100** |

The source-unknown area is a separate dimension that can overlap the
known/unknown depth partition. It is **not** an additional disjoint area
to sum into the 100 m². Areas not covered by the two synthetic hazard
polygons cannot be inferred dry. Depth values here are only class labels;
none is interpreted as observed metres or loss severity.

Run locally without any source acquisition:

```sh
python -m pip install -r requirements-eu-flood-spatial.txt
python -m unittest tests.test_ea_flood_synthetic_crs_overlay_v0 -v
```

The CLI accepts a specially marked `synthetic_test_only` JSON payload
(`--synthetic-input /private/synthetic-overlay.json`); it explicitly
rejects any real-source or real-insurance input schema. Only compact
aggregate synthetic areas are emitted. No geometry, IDs, addresses,
assets, loss factors or source geometry is echoed, stored or published.

## Limitations before a real R&V/insurer property join

The original source record's rings being closed does not prove
topology, coverage, spatial vintage or model suitability. The actual
EA collection could contain overlapping classes, invalid rings,
`unavailable` polygons, multipart boundaries, or geometry-alignment
uncertainties. The OGC service's official licence/attribution and
third-party component rights remain to be reviewed for the **exact
geospatial asset**. National flood depth classes do not establish
physical building-floor depth, vulnerability or event/year ordering.

The next *separate, permission-gated* step is a tightly bounded
provider-original polygon QA with CRS/provenance receipt and explicit
real-source reuse rights, **not** passing real features into this
synthetic test. `model_data_admitted=false` remains unchanged.
