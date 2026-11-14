<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0
-->

# Cologne public geodata pilot — 2026-11-14

This note explains a *bounded source-access experiment*, not a model-data
admission, new insured portfolio or approved loss calculation.

Canonical candidate metadata belongs to
[`landscape/sources-cologne-hazard-exposure-20261114.json`](../../landscape/sources-cologne-hazard-exposure-20261114.json).
The generated Markdown view must not be edited independently.

## Why Cologne?

Cologne is a useful small-region validation slice because the city provides
statistical geography, a managed-tree inventory and an interactive urban-flood
viewer, while NRW publishes official multi-scenario river-flood depth rasters,
boundaries and velocities. These inputs have sharply different legal and
scientific meanings. They must not be conflated.

## Safe first technical step

The repository contains a **read-only, fixed-endpoint WMS metadata probe**:

```bash
python -m unittest tests.test_cologne_hwrm_service_probe_v0
python research_runners/cologne_hwrm_service_probe_v0.py --live
```

The second command requires deliberate `--live` opt-in. The endpoint now follows the official Open.NRW distribution URL at `https://www.wms.nrw.de/umwelt/wasser/HW_Gefahrenkarte?REQUEST=GetCapabilities&SERVICE=WMS` rather than the shortened legacy path. It requests only
`GetCapabilities` at the exact official NRW service URL. Redirects, non-XML responses, non-WMS XML, absent service identity,
missing GetCapabilities/GetMap operations, unexpected WMS versions,
empty or invalid layer inventories and responses above 4 MB fail closed. It prints only a JSON receipt containing bounded
layer metadata, SHA-256 of received XML and explicit non-admission flags. It
does **not** download or retain source rasters, tile images, GeoJSON, building
features or external raw bytes. The first command is fully offline.

A confirmed content-type from a website fetch or a source catalogue link
is not the same as the above complete live receipt. Until the real command
returns a parse-verified receipt on an authorized runner, the live canary
status is **not verified**.

## Original-provider flood-data path

**Distribution-specific rights must be kept separate:** the official WMS
GetCapabilities `Service/AccessConstraints` read on 2026-11-14 states
**Datenlizenz Deutschland Namensnennung 2.0**, attribution **Land NRW**.
The provider's independently published HWRM download directory states
**Datenlizenz Deutschland Zero 2.0** for those archives. Do not project
WMS attribution terms onto the archive or vice versa without an exact
per-asset source review. The external WMS XML was successfully rendered
as a public third-party XML-to-Markdown view, demonstrating service
metadata and `GetCapabilities` / `GetMap` descriptions; it did **not**
produce an original response-byte SHA or a tested `--live` runner receipt.

The authoritative NRW source directory is:

https://www.opengeodata.nrw.de/produkte/umwelt_klima/wasser/hochwasser/hwrm/

It lists distinct EPSG:25832 ZIP distributions for HQ10–50, HQ100 and
extreme scenarios, including raster depth and vector boundary/velocity
products. The original directory identifies 2026-01 release dates and
the **Datenlizenz Deutschland – Zero 2.0** for the original download products. The high-probability depth ZIP is
publisher-listed as approximately 2.4 GB. No original ZIP bytes were
downloaded or hashed during this change.

Next acquisition must select a single exact archive, confirm release
identity, obtain and hash its original bytes *outside Git* where separately
reviewed, inspect CRS and field/raster units, NoData, source vintage,
per-scenario depth semantics and local Cologne clipping, and log the source
selection and transformation. Never replace a full-file SHA-256 with an
HTTP ETag or a synthetic digest.


## Original Cologne city WFS service access (2026-11-14)

The following **publisher-linked public services** were discovered in the
original Offene Daten Köln distribution links, not through reverse-engineering:

- Baumkataster WFS GetCapabilities:
  https://geoportal.stadt-koeln.de/wss/service/baumkataster_extern_wfs/guest?SERVICE=WFS&REQUEST=GetCapabilities
  — layer `ms:baumkataster`, WFS 2.0.0, default EPSG:25832.
- Kommunale Gebietsgliederung WFS GetCapabilities:
  https://geoportal.stadt-koeln.de/arcgis/services/basiskarten/kgg/MapServer/WFSServer?request=GetCapabilities&service=WFS
  — `Basiskarten_kgg:Stadtviertel`, WFS 2.0.0, default EPSG:25832.
- The authoritative city distribution pages are
  https://www.offenedaten-koeln.de/dataset/baumkataster-koeln-fortlaufend-aktualisiert
  and https://www.offenedaten-koeln.de/dataset/geopackage-raumbezugssystem-koeln.

Both WFS ServiceIdentification blocks explicitly state **Datenlizenz
Deutschland Zero 2.0**. Their GetFeature operations are described by the
provider; KGG advertises GeoJSON and GeoPackage output, and Baumkataster
advertises `application/json; subtype=geojson`. This is an important
asset/service rights *signal*, not a substitute for an accepted OpenCatastrophe
source-admission review. Personal-data, source-lineage and scientific-fit
boundaries remain in force.

The following commands now support exact bounded source replay:

```bash
python -m unittest tests.test_cologne_public_wfs_hits_probe_v0
python -m unittest tests.test_cologne_public_wfs_feature_probe_v0
python research_runners/cologne_public_wfs_hits_probe_v0.py --source tree --live
python research_runners/cologne_public_wfs_hits_probe_v0.py --source kgg --live
python research_runners/cologne_public_wfs_feature_probe_v0.py --source tree --live
python research_runners/cologne_public_wfs_feature_probe_v0.py --source kgg --live
```

These are **opt-in public-source requests**, not automatic CI downloads or
production database imports. The hits runners request `COUNT=1` and
`RESULTTYPE=hits`, require `numberReturned=0` and retain only metadata
receipts. Real original GetFeature hits results observed with this query:

| Dataset | WFS 2.0 reply | Provider-reported numberMatched | numberReturned |
|---|---|---:|---:|
| Baumkataster `ms:baumkataster` | FeatureCollection, XML | 1 | 0 |
| KGG `Basiskarten_kgg:Stadtviertel` | FeatureCollection, XML | 374 | 0 |

**Caution:** `COUNT=1` can cap or alter server-reported `numberMatched`
(tree service: 1), so no full tree count is established. KGG's 374 is
specific to the tested Stadtviertel layer and query, not all city divisions.

### Exact first-feature metadata-only receipts

A separate read-only original GetFeature `COUNT=1` response was inspected in
memory using a public external fetch service, including original bytes; no
source row or geometry is committed. Python replay scripts above compute
SHA-256 independently, enforce size/media type and emit schema-only receipts.
The following hashes identify the observed response bodies (not immutable
vendor releases):

| Source | Original response | SHA-256 | Geometry/fields |
|---|---:|---|---|
| Tree WFS, GeoJSON subtype | 643 bytes | `e958485ea97d6aa80e8d19575fc2fa8c472eeedb23abebce1e5c0f2c8f0b34ad` | Point, 16 property keys |
| KGG Stadtviertel WFS, GeoJSON | 5650 bytes | `4c3e48d56fbcdcbc703d142b6caea4cd0546965331fa94ded300279057be44b6` | MultiPolygon, 13 property keys |

The KGG GeoJSON reported `EPSG:4326` with plausible longitude/latitude
coordinates. **Critical georeferencing caution:** The tree GeoJSON example
omitted `crs` and contained **projected metre-like coordinates**, despite
being labelled GeoJSON. An additional query with `SRSNAME=EPSG:4326` still
returned metre-like coordinates in the inspected JSON. The source's WFS
GetCapabilities instead advertises default **EPSG:25832**. Do not
interpret the raw tree coordinates as RFC 7946 WGS84, visually align them
with KGG polygons, or join them to building portfolios until a verified
source CRS and explicit reprojection has passed an independent spatial
challenge. An additional bounded **original GML 3.2** GetFeature request for the tree
layer with `SRSNAME=EPSG:4326` returned a Point whose geometry declares
`srsName=urn:ogc:def:crs:EPSG::4326`, yet the `gml:pos` values were
metre-like, not valid geographic degrees. This is an independent format
confirmation of the numerical CRS mismatch; the declared GML CRS must not
override the coordinate-range challenge. For the inspected tree Point, a
test transformation from EPSG:25832 to EPSG:4326 yields approximately
6.92931 E, 50.92123 N, plausibly in Cologne. That single successful
transformation is **only a hypothesis check**, not proof of correct CRS
for all features or permission to overlay model hazard data.

The single-feature reader deliberately returns
`coordinate_status=not_approved_geographic_crs_must_reproject_and_verify`
for tree results; no model admission is made for either source. The next
spatial challenge should verify multiple well-distributed original tree
points against independently authoritative Cologne geometry, then pin
the provider's response/projection semantics and implement a reviewed
explicit reprojection; never silently accept an `EPSG:4326` label whose
coordinate magnitudes contradict it.

These receipts are ephemeral observations at the date above, not frozen
complete provider files and not an approved warehouse import.

## Boundaries for model consumers

- Cologne statistics GeoPackage: confirm **exact ZIP/WFS distribution URLs**,
  asset-specific reuse terms, stable identifiers and geometrical/CRS
  semantics before local joins. Addresses and ALKIS building attributes
  are not insured asset or policy records.
- Cologne tree register: verify exact WFS endpoint, published terms,
  response schema, positional precision and municipality-managed coverage.
  Incomplete managed-tree inventory cannot be converted to complete
  urban tree exposure or a fall probability without independent science.
- StEB Köln 2025 3D pluvial maps: **viewer only** under current evidence.
  No authorized raw machine endpoint or redistribution scope is shown.
  Do not scrape internal map tiles or model payloads.
- NRW river-flood data: public publisher licensing is promising, but
  asset-identity, scientific fitness and OpenCatastrophe source-admission
  gates remain independent. Regulatory HQ classes are scenario
  descriptors, not directly event-specific stochastic occurrence rates.

A future model experiment needs a reviewed `manifests/` admission, raw or
derived artifact identity, full hashes, science and rights review, and a
`schemas/run-evidence-v2.schema.json` binding before consuming these
data as hazard, exposure or validation inputs.

## Checked provider entry points

- https://open.nrw/dataset/053549cf-b9c4-4633-80f9-680888ae5a04
- https://www.offenedaten-koeln.de/dataset/geopackage-raumbezugssystem-koeln
- https://www.offenedaten-koeln.de/dataset/baumkataster-koeln-fortlaufend-aktualisiert
- https://steb-koeln.de/service/karten-und-anwendungen/ueberflutungsgefahrenkarten
