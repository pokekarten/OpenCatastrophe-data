<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/de.berlin.alkis-gebaeude.wfs.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `de.berlin.alkis-gebaeude.wfs.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** de.berlin.alkis-gebaeude.wfs

## Source ids

- de.berlin.alkis-gebaeude.wfs

**Provider:** Senatsverwaltung für Stadtentwicklung, Bauen und Wohnen Berlin

**Interface type:** wfs

**Status:** documented_only

**Documentation url:** <https://daten.berlin.de/datensaetze/alkis-berlin-gebaude-wfs-728b368a>

**Service root:** <https://gdi.berlin.de>

**Api version:** OGC WFS 2.0.0 (provider also lists 1.0.0 and 1.1.0)

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
- get_bounded_features

### Path templates

- /services/wfs/alkis_gebaeude

**Parameter rules:** Documentation-only identity for the official Berlin ALKIS building and building-part WFS. This contract does not authorize sending either operation. A future provider-specific worker must freeze WFS version, exact GetCapabilities parameters, feature type(s) from the original capabilities/schema, a predeclared 200m x 200m EPSG:25833 Berlin research bounding box, response CRS, page/feature cap, content-type and byte limit; reject any caller-selected host, arbitrary query, redirects, unbounded feature traversal or whole-Berlin extraction. The existing five-feature source receipt does not turn this generic interface into an executable access contract.

## Response contract

### Expected media types

- application/xml
- text/xml
- application/gml+xml

**Format:** Official ALKIS Berlin Gebäude WFS service capabilities and building/building-part vector features; authoritative service metadata indicate OGC WFS 1.0.0, 1.1.0 and 2.0.0, CRS EPSG:25833.

**Scientific semantics:** Official mutable cadastral building and building-part geometry; updated monthly. An individual ALKIS feature may represent a building or building part rather than one insured asset. Original EPSG:25833 feature identity, date/vintage, geometry type and provenance must survive ingestion. Do not infer building age, insured location, replacement value, TIV, construction type or hazard vulnerability. A separately produced 2022 LoD2 building-height layer derives from ALKIS footprints and height surfaces and is not geometrically independent of this WFS. Historical 2021 building stock cannot be inferred from a current 2026 feature alone.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `1048576`

**Max sample bytes:** `5242880`

**Retry policy:** none

**Rate limit notes:** The official Berlin Geoportal identifies anonymous web feature access but no approved automated request rate or bulk-download quota was established in this contract. No new request is enabled by this documentation; future operations require a bounded site-specific worker and current official service terms review.

**Mutability notes:** Provider describes monthly ALKIS updates; catalogue metadata show 2026 publication/update dates. Bind every later source read to exact UTC retrieval time, service response SHA-256, feature schema/CRS, requested bbox and dataset vintage; never silently substitute current geometry for the 2021 stock or 2022 LoD2 baseline.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** unknown

**Terms url:** `null`

**Commercial automation status:** unknown

**Redistribution status:** allowed

**Notes:** The official Berlin Open Data catalogue and government spatial metadata identify Datenlizenz Deutschland – Zero – Version 2.0 for the ALKIS buildings layer, without access restrictions. This validates the published layer license, not a numeric provider automation quota, personal-attribute reuse, independent model-input science or all possible derivative publications. Separate WFS service/request conditions have not been reviewed; status therefore remains documented_only and execution disabled.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-01

## Evidence urls

- <https://daten.berlin.de/datensaetze/alkis-berlin-gebaude-wfs-728b368a>
- <https://www.berlin.de/sen/stadt/stadtdaten/geoinformation/liegenschaftskataster/geobasisdaten-online/datenbereitstellung/>
- <https://www.geoportal.de/info/78d98821-42e2-3c82-a0f7-1baad959b74e>
- <https://www.berlin.de/umweltatlas/nutzung/gebaeudehoehen/fortlaufend-aktualisiert/datengrundlage/>
- <https://www.govdata.de/dl-de/zero-2-0>

**Notes:** New contract documents a previously inventoried Berlin source and the official endpoint. This is not a network probe or original feature retrieval. Prior five-feature work is independent evidence recorded elsewhere in the repo; do not promote its science or rights status by implication. No new CAT4 data, insured values, building identities or model inputs are admitted here.
