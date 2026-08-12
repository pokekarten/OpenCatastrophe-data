<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/geoboundaries.gbopen.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `geoboundaries.gbopen.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** geoboundaries.gbopen

## Source ids

- geoboundaries.gbopen

**Provider:** William &amp; Mary geoLab / geoBoundaries

**Interface type:** rest

**Status:** probe_ready

**Documentation url:** <https://www.geoboundaries.org/api.html>

**Service root:** <https://www.geoboundaries.org>

**Api version:** gbOpen current metadata API; DEU/ADM1 canary frozen to reviewed boundary identity

## Access scope

- metadata

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- deu_adm1_metadata

### Path templates

- /api/current/gbOpen/DEU/ADM1/

**Parameter rules:** The probe is one repository-constructed fixed metadata request only. Callers cannot supply or override release type, ISO code, ADM level, host, path, query, headers or redirect target. The reviewed canary expects boundaryISO=DEU, boundaryType=ADM1 and boundaryID=DEU-ADM1-10402087. Because /current/ is mutable, any boundaryID, original licence metadata or returned static download commit change is contract drift and requires review before further use. Returned download URLs are evidence only and are not executable operations under this contract.

## Response contract

### Expected media types

- application/json

**Format:** One geoBoundaries gbOpen metadata JSON object for the fixed DEU/ADM1 canary. The response must expose the reviewed boundary identity plus item-level source/licence metadata and provider-generated download links.

**Scientific semantics:** geoBoundaries gbOpen describes political administrative boundaries. For this canary, boundaryISO must be DEU and boundaryType ADM1; boundaryID binds the reviewed geometry/metadata identity and changes when underlying data change. boundaryYearRepresented, boundarySource, boundaryLicense, licenseSource, sourceDataUpdateDate and buildDate are provenance fields and must be preserved. staticDownloadLink, gjDownloadURL, tjDownloadURL and simplifiedGeometryGeoJSON are provider-returned asset references; they do not by themselves admit boundary bytes, establish suitability for catastrophe exposure modelling or authorize a raw-data publication step.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `65536`

**Max sample bytes:** `65536`

**Retry policy:** none

**Rate limit notes:** geoBoundaries explicitly encourages automated use but does not publish a repository-specific request quota on the reviewed API page. This contract permits exactly one small fixed metadata canary. No ALL-country/ALL-ADM request, crawling, repeated polling or asset download is authorized.

**Mutability notes:** The /api/current/ alias is intentionally mutable. The reviewed DEU/ADM1 response currently identifies boundaryID DEU-ADM1-10402087 and returns asset URLs pinned to geoBoundaries Git commit 9469f09. A future receipt must bind retrieval UTC, response byte count/SHA-256, boundaryID, original boundaryLicense/licenseSource and every returned asset URL. Any identity or pinned-commit change requires re-review rather than silent acceptance.

## Rights and policy

**Dataset rights status:** verified

**Api terms status:** separate_reviewed

**Terms url:** <https://www.geoboundaries.org/api.html>

**Commercial automation status:** allowed

**Redistribution status:** allowed

**Notes:** The official geoBoundaries API page states that automated uses are encouraged and that gbOpen is CC-BY 4.0 compliant with attribution. The main site likewise describes geoBoundaries data as CC BY 4.0 and requires acknowledgement. The API also exposes each boundary's original boundaryLicense and licenseSource; these item-level provenance/licence fields must be preserved in any later asset review. This contract records the source/service rights ceiling only and does not itself authorize committing or publishing returned boundary files.

## Probe contract

**Mode:** metadata_get

**Operation:** deu_adm1_metadata

**Requires credentials:** `false`

### Expected evidence

- provider success status without unsafe payload logging
- application/json response media type
- bounded response byte count and SHA-256
- boundaryISO=DEU and boundaryType=ADM1
- boundaryID=DEU-ADM1-10402087 or explicit contract_mismatch
- item-level boundaryLicense and licenseSource captured
- returned asset URLs captured and verified as provider-generated evidence only
- retrieval UTC and trusted execution-code identity
- external_bytes_persisted=false

**Implementation decision:** build_later

**Reviewed at:** 2026-08-12

## Evidence urls

- <https://www.geoboundaries.org/api.html>
- <https://www.geoboundaries.org/>
- <https://www.geoboundaries.org/api/current/gbOpen/DEU/ADM1/>

**Notes:** Static Tier-1 access contract only. It freezes one small anonymous metadata canary and adds no provider adapter or trusted network worker. It deliberately does not expose arbitrary ISO/ADM selection and does not authorize any returned ZIP/GeoJSON/TopoJSON asset download. A later asset sample must be a separate review that freezes the exact boundaryID, commit-pinned provider URL, byte identity, geoBoundaries attribution and item-level original licence provenance. Connectivity is not admission or scientific validation.
