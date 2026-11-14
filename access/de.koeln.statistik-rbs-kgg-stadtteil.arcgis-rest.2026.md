<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/de.koeln.statistik-rbs-kgg-stadtteil.arcgis-rest.2026.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `de.koeln.statistik-rbs-kgg-stadtteil.arcgis-rest.2026.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** de.koeln.statistik-rbs-kgg-stadtteil.arcgis-rest.2026

## Source ids

- de.koeln.statistik.rbs-geopackage.2026

**Provider:** Stadt Köln / Amt für Stadtentwicklung und Statistik

**Interface type:** arcgis_rest

**Status:** documented_only

**Documentation url:** <https://www.offenedaten-koeln.de/dataset/geopackage-raumbezugssystem-koeln>

**Service root:** <https://geoportal.stadt-koeln.de>

**Api version:** ArcGIS REST MapServer, official Stadtteil polygon layer 3

## Access scope

- metadata

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- point_stadtteil_membership

### Path templates

- /arcgis/rest/services/basiskarten/kgg/MapServer/3/query

**Parameter rules:** Research-only manual point/polygon check was performed with fixed official MapServer/3/query and where=1=1, geometryType=esriGeometryPoint, inSR=4326, spatialRel=esriSpatialRelIntersects, returnGeometry=false, outFields=name,nummer, f=json; five positions derived by transforming fixed bounded Baumkataster samples, plus one fixed Berlin negative control. No authorized recurring, bulk, user-chosen-coordinate or model pipeline invocation under this documentation-only contract. No other layers, paths, query formats, source geometry, full district records, geocoding, arbitrary hosts/redirects or arbitrary feature filters.

## Response contract

### Expected media types

- application/json

**Format:** Provider-side ArcGIS REST JSON: zero or one features with Stadtteil fields name, nummer; no original polygon geometry returned or retained.

**Scientific semantics:** The MapServer/3 point intersection tests whether a transformed Baumkataster sample lies inside one official Köln Stadtteil polygon. Five of five sorted sampled tree positions returned one Stadtteil; 4/4 nonblank tree district labels agreed, one was blank. Berlin control returned zero features. This independently validates approximate geographic support, not survey-level positional precision, full tree/municipal coverage, official dataset version synchronization, a flood-loss layer, building exposure or CAT model admission.

## Operational constraints

**Timeout seconds:** `20`

**Max probe bytes:** `16384`

**Max sample bytes:** `16384`

**Retry policy:** none

**Rate limit notes:** REST service access observed once in this bounded source investigation. No separately published numeric quota or REST-specific commercial automation terms were verified. Contract remains documentation-only, with probe mode none until endpoint terms and purpose are reviewed.

**Mutability notes:** Municipal KGG polygon service and daily Baumkataster WFS are mutable and may be updated independently. A match is not a frozen date-consistent source snapshot. Future production samples must bind service/version, independent timestamps, exact feature identities, response hashes, CRS handling and snapshot drift policy.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** separate_unreviewed

**Terms url:** `null`

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** Municipal dataset page and original WFS ServiceIdentification explicitly declare Datenlizenz Deutschland Zero 2.0 for the KGG WFS source. ArcGIS REST MapServer metadata identifies the city publisher and supports Query but did not state separate REST automation/redistribution permissions. Do not automatically transfer WFS service licence or provider access commitments to this REST interface. The recorded limited one-time external source research does not grant production automation, data retention, public raw redistribution or hazard-model training/admission.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-14

## Evidence urls

- <https://www.offenedaten-koeln.de/dataset/geopackage-raumbezugssystem-koeln>
- <https://geoportal.stadt-koeln.de/arcgis/services/basiskarten/kgg/MapServer/WFSServer?request=GetCapabilities&amp;service=WFS>
- <https://geoportal.stadt-koeln.de/arcgis/rest/services/basiskarten/kgg/MapServer?f=pjson>
- <https://www.govdata.de/dl-de/zero-2-0>

**Notes:** Five point-in-polygon queries on original Stadtteil layer 3 returned exactly one named district each; four nonblank tree Stadtteil labels matched; one tree label was missing. Fixed Berlin negative returned zero. A separate independent city layer 5 query returned five positive and one negative. No source geometry/feature rows/trees are stored in Git or NeonDB. Reproduce the syntax only through an explicit research runner research_runners/cologne_tree_polygon_challenge_v0.py after separate service-rights review; its offline tests are deterministic and synthetic. This contract deliberately cannot authorize production REST acquisition or model-admitted inputs.
