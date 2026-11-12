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

**Status:** probe_ready

**Documentation url:** <https://daten.berlin.de/datensaetze/alkis-berlin-gebaude-wfs-728b368a>

**Service root:** <https://gdi.berlin.de>

**Api version:** OGC WFS 2.0.0 (provider also lists 1.0.0 and 1.1.0)

## Access scope

- metadata

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- get_capabilities

### Path templates

- /services/wfs/alkis_gebaeude

**Parameter rules:** Only one exact manually initiated anonymous HTTPS GET https://gdi.berlin.de/services/wfs/alkis_gebaeude?request=GetCapabilities&amp;service=WFS; verify original WFS 2.0.0 service identity, Berlin provider, licence/access constraints, and fixed layer alkis_gebaeude:gebaeude with EPSG:25833. No GetFeature, DescribeFeatureType, pagination, BBOX, parameters, arbitrary hosts/paths, redirects, feature attributes, cadastral coordinates, owners, credentials, bulk downloads or scheduled provider polling.

## Response contract

### Expected media types

- application/xml
- text/xml
- application/gml+xml

**Format:** WFS 2.0.0 GetCapabilities XML metadata only: exact ALKIS Berlin Gebaeude identity, OWS ServiceIdentification, OWS Fees/AccessConstraints, FeatureTypeList containing alkis_gebaeude:gebaeude and EPSG:25833. No feature geometry or attributes requested.

**Scientific semantics:** Official mutable cadastral building and building-part geometry; updated monthly. An individual ALKIS feature may represent a building or building part rather than one insured asset. Original EPSG:25833 feature identity, date/vintage, geometry type and provenance must survive ingestion. Do not infer building age, insured location, replacement value, TIV, construction type or hazard vulnerability. A separately produced 2022 LoD2 building-height layer derives from ALKIS footprints and height surfaces and is not geometrically independent of this WFS. Historical 2021 building stock cannot be inferred from a current 2026 feature alone.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `1048576`

**Max sample bytes:** `5242880`

**Retry policy:** none

**Rate limit notes:** Official WFS capabilities and government geodata catalogue allow public anonymous access to the building layer; no numerical quota was published. Permit exactly one metadata-only GET on an explicit manually dispatched reviewed action, no retry or automatic recurrence. A wider automated data acquisition, GetFeature or large-scale query requires an independent service and rights review.

**Mutability notes:** Provider describes monthly ALKIS updates; catalogue metadata show 2026 publication/update dates. Bind every later source read to exact UTC retrieval time, service response SHA-256, feature schema/CRS, requested bbox and dataset vintage; never silently substitute current geometry for the 2021 stock or 2022 LoD2 baseline.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** separate_reviewed

**Terms url:** <https://www.berlin.de/sen/stadt/stadtdaten/geoinformation/liegenschaftskataster/geobasisdaten-online/nutzungsbedingungen/>

**Commercial automation status:** allowed

**Redistribution status:** allowed

**Notes:** Original provider WFS GetCapabilities (2026-11-12) self-declares Datenlizenz Deutschland Zero 2.0 and 'Es gelten keine Zugriffsbeschraenkungen'. Berlin official dataset metadata identifies anonymous download access and same licence. Berlin general cadastral-use terms distinguish protected owner/measurement records from other ALKIS data and those remain out of scope. Commercial automated access judgement is limited to one manually dispatched WFS capabilities metadata GET; there is no approved poll rate, commercial bulk extraction, feature-level personal data processing, redistribution of unreviewed attributes, CAT exposure or model admission.

## Probe contract

**Mode:** metadata_get

**Operation:** get_capabilities

**Requires credentials:** `false`

### Expected evidence

- Exact single original HTTPS 200 GetCapabilities XML, no redirects or arbitrary parameters
- At most 1 MiB; strict XML parsing with no DTD or entity expansion; OGC WFS 2.0.0 and Berlin ALKIS Gebaeude identity
- Original provider official data licence DL-DE Zero 2.0 and access constraints no restrictions recorded as metadata only
- Frozen alkis_gebaeude:gebaeude feature type and EPSG:25833 default CRS in original capabilities
- Request SHA-256, original response SHA-256, response byte count, executable code SHA-256 and retrieval UTC
- No provider payload persistence, GetFeature, owner or building data, geometry download or CAT model admission

**Implementation decision:** build_later

**Reviewed at:** 2026-11-12

## Evidence urls

- <https://daten.berlin.de/datensaetze/alkis-berlin-gebaude-wfs-728b368a>
- <https://www.berlin.de/sen/stadt/stadtdaten/geoinformation/liegenschaftskataster/geobasisdaten-online/datenbereitstellung/>
- <https://www.geoportal.de/info/78d98821-42e2-3c82-a0f7-1baad959b74e>
- <https://www.berlin.de/umweltatlas/nutzung/gebaeudehoehen/fortlaufend-aktualisiert/datengrundlage/>
- <https://www.govdata.de/dl-de/zero-2-0>
- <https://gdi.berlin.de/services/wfs/alkis_gebaeude?request=GetCapabilities&amp;service=WFS>
- <https://gdi.berlin.de/geonetwork/geonetwork/api/records/986ea575-6141-36f1-89e1-1cbf27fe0c7d>
- <https://www.berlin.de/sen/stadt/stadtdaten/geoinformation/liegenschaftskataster/geobasisdaten-online/nutzungsbedingungen/>

**Notes:** Exactly one reviewed metadata-only WFS capabilities probe was added, not a GetFeature approval. This remains a landscape non-admission. Berlin buildings/building parts do not constitute independent insured assets or TIV; past five-feature evidence is not upgraded, and owner information remains excluded.
