<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/de.koeln.statistik-rbs-kgg.wfs.2026.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `de.koeln.statistik-rbs-kgg.wfs.2026.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** de.koeln.statistik-rbs-kgg.wfs.2026

## Source ids

- de.koeln.statistik.rbs-geopackage.2026

**Provider:** Stadt Köln / Amt für Stadtentwicklung und Statistik

**Interface type:** wfs

**Status:** verified_anonymous

**Documentation url:** <https://www.offenedaten-koeln.de/dataset/geopackage-raumbezugssystem-koeln>

**Service root:** <https://geoportal.stadt-koeln.de>

**Api version:** OGC WFS 2.0.0

## Access scope

- metadata
- sample

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- get_capabilities
- get_feature_hits
- get_one_feature

### Path templates

- /arcgis/services/basiskarten/kgg/MapServer/WFSServer

**Parameter rules:** Only the publicly documented Basiskarten_kgg:Stadtviertel WFS 2.0 layer. GetCapabilities; GetFeature RESULTTYPE=hits COUNT=1; or one original GeoJSON MultiPolygon with COUNT=1 and OUTPUTFORMAT=GEOJSON. No arbitrary geographies, addresses, bulk ZIP, hidden fields, arbitrary query parameters, redirects, uncontrolled pagination or automated polling. Never treat the first returned district polygon as a frozen or representative sample.

## Response contract

### Expected media types

- application/xml
- text/xml
- application/json

**Format:** OGC WFS 2.0 GetCapabilities XML; hits-only FeatureCollection; one GeoJSON MultiPolygon with provider-declared EPSG:4326 and 13 source attribute keys.

**Scientific semantics:** Municipal administrative Stadtviertel polygon geometry and attributes are spatial join context, NOT individual building exposure or insurance policy records. WFS default CRS is EPSG:25832 but GeoJSON returned named EPSG:4326; honor exact per-response CRS and axis handling. The provider listed 374 matching Stadtviertel features for one bounded hits query, not a national building count or immutable vintage. BBOX may exclude places outside city but is not a point-in-polygon proof.

## Operational constraints

**Timeout seconds:** `20`

**Max probe bytes:** `8192`

**Max sample bytes:** `160000`

**Retry policy:** none

**Rate limit notes:** Only explicitly initiated bounded research checks, no provider polling, uncontrolled pagination, arbitrary BBOX or bulk extracts. No numeric API quota established.

**Mutability notes:** Live municipality layers are mutable. Pin request URL, retrieval UTC, response SHA-256, source identity and geometry/CRS; offset ordering alone is not a stable snapshot.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** same_as_dataset

**Terms url:** <https://www.govdata.de/dl-de/zero-2-0>

**Commercial automation status:** allowed

**Redistribution status:** unknown

**Notes:** Original city WFS ServiceIdentification/AccessConstraints explicitly states Datenlizenz Deutschland Zero 2.0 and no fees. For this access contract only a tightly bounded anonymous manual metadata/hits/one-feature research operation is treated as technically and legally accessible. General redistribution, committed raw source rows, automatic scheduled collection, model training, insurer allocation, personal claims or asset-specific model admission are NOT approved. Independent source/scientific/admission review remains required. No unbounded automated polling is authorised.

## Probe contract

**Mode:** provider_specific

**Operation:** get_one_feature

**Requires credentials:** `false`

### Expected evidence

- Original anonymous HTTP 200, no redirect; exact official host, path, fixed WFS query and documented layer.
- Bounded Content-Type and original response SHA-256, byte count and retrieval UTC.
- Response XML/JSON structure, layer identity, limited count and geometry/CRS semantics explicitly inspected.
- External source bytes persisted=false, model admitted=false; protect source fields and IDs from raw logging.

**Implementation decision:** build_later

**Reviewed at:** 2026-11-14

## Evidence urls

- <https://www.offenedaten-koeln.de/dataset/geopackage-raumbezugssystem-koeln>
- <https://geoportal.stadt-koeln.de/arcgis/services/basiskarten/kgg/MapServer/WFSServer?request=GetCapabilities&amp;service=WFS>
- <https://www.govdata.de/dl-de/zero-2-0>
- <https://github.com/pokekarten/OpenCatastrophe-data/blob/research/cologne-open-geodata-20261114/docs/research/cologne-public-geodata-pilot-20261114.md>

**Notes:** Original official WFS GetCapabilities advertises GeoJSON and GeoPackage output and states Datenlizenz Deutschland Zero 2.0. Original COUNT=1 hits returned WFS 2.0 FeatureCollection numberMatched=374, numberReturned=0. The independently examined first original GeoJSON MultiPolygon response measured 5650 bytes with SHA-256 4c3e48d56fbcdcbc703d142b6caea4cd0546965331fa94ded300279057be44b6. The probe only establishes technical source access and a per-response CRS/range sanity check, not accurate boundary membership, model admission or insured exposure. Replay via research_runners/cologne_public_wfs_feature_probe_v0.py. No original provider row committed.
