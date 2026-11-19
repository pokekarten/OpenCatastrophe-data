<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/de.koeln.city-tree-register.wfs.2026.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `de.koeln.city-tree-register.wfs.2026.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** de.koeln.city-tree-register.wfs.2026

## Source ids

- de.koeln.city-tree-register.2026

**Provider:** Stadt Köln / Amt für Landschaftspflege und Grünflächen

**Interface type:** wfs

**Status:** verified_anonymous

**Documentation url:** <https://www.offenedaten-koeln.de/dataset/baumkataster-koeln-fortlaufend-aktualisiert>

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

- /wss/service/baumkataster_extern_wfs/guest

**Parameter rules:** Only the provider-published ms:baumkataster layer under fixed WFS 2.0.0 requests. GetCapabilities; GetFeature RESULTTYPE=hits COUNT=1; or one GeoJSON feature with COUNT=1, SORTBY=Baumnummer, optionally fixed STARTINDEX=0,750,2500,5000,10000 for a separate explicitly opted-in six-call CRS challenge. No caller-defined host, uncontrolled offsets, BBOX, arbitrary field filters, redirects, pagination loops, credentials or bulk download. Read and discard original responses in memory; never print individual tree IDs, names, street labels or original coordinates.

## Response contract

### Expected media types

- application/xml
- text/xml
- application/json

**Format:** Official WFS 2.0 GetCapabilities XML; FeatureCollection hits XML; one FeatureCollection Point GeoJSON subtype with 16 source attribute keys. Provider GetCapabilities default EPSG:25832.

**Scientific semantics:** Only municipality-managed street and municipal-object trees, not all Köln trees. GeoJSON source Points were empirically metre-like and had NO CRS declaration; even EPSG:4326-requested JSON and GML may expose metre coordinates. A sample of five sorted offsets projected under the EPSG:25832 hypothesis into the city KGG bounding envelope, which is not full georeferencing validation. Baumnummer sort is necessary because unsorted first feature differed on immediate repeated requests. These trees do not represent insured assets, storm damage observations or validated fall frequencies.

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

- <https://www.offenedaten-koeln.de/dataset/baumkataster-koeln-fortlaufend-aktualisiert>
- <https://geoportal.stadt-koeln.de/wss/service/baumkataster_extern_wfs/guest?SERVICE=WFS&amp;REQUEST=GetCapabilities>
- <https://www.govdata.de/dl-de/zero-2-0>
- <https://github.com/pokekarten/OpenCatastrophe-data/blob/research/cologne-open-geodata-20261114/docs/research/cologne-public-geodata-pilot-20261114.md>

**Notes:** Original source WFS GetCapabilities independently observed, service uses DL-DE Zero 2.0. Original read-only GetFeature hits with COUNT=1 returned FeatureCollection numberReturned=0, numberMatched=1, which is not the total tree count. Original one-feature GeoJSON response 643 bytes had SHA-256 e958485ea97d6aa80e8d19575fc2fa8c472eeedb23abebce1e5c0f2c8f0b34ad before explicit sorting; that byte hash is not immutable source identity. Additional sorted five-offset original feature inspections plus repeated sort-key tests are documented. Exact source runner research_runners/cologne_public_wfs_feature_probe_v0.py and optional challenge runner research_runners/cologne_tree_crs_challenge_v0.py; external tree objects remain outside Git and production DB.
