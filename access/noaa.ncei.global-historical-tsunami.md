<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/noaa.ncei.global-historical-tsunami.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `noaa.ncei.global-historical-tsunami.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** noaa.ncei.global-historical-tsunami

## Source ids

- noaa.ncei.global-historical-tsunami

**Provider:** NOAA National Centers for Environmental Information

**Interface type:** arcgis_rest

**Status:** documented_only

**Documentation url:** <https://www.ncei.noaa.gov/products/natural-hazards/tsunamis-earthquakes-volcanoes/tsunamis/global-historical-data>

**Service root:** <https://gis.ngdc.noaa.gov>

**Api version:** ArcGIS Server 11.5

## Access scope

- metadata
- catalogue
- sample

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- tsunami_events_layer_metadata
- bounded_tsunami_event_query

### Path templates

- /arcgis/rest/services/web_mercator/hazards/MapServer/0
- /arcgis/rest/services/web_mercator/hazards/MapServer/0/query

**Parameter rules:** This contract records the NOAA/NCEI Tsunami Events feature layer and a future repository-constructed bounded query only. Callers may not supply a host, arbitrary path, free-form SQL where clause, output-field list, geometry, spatial filter, pagination state, headers or unrestricted query parameters. Before any executable probe is enabled, a separately reviewed operation must freeze an exact small query, output fields, ordering and result limit against the authoritative layer schema.

## Response contract

### Expected media types

- application/json

**Format:** ArcGIS REST JSON metadata or bounded feature-query response for NOAA/NCEI Tsunami Events layer 0.

**Scientific semantics:** The layer represents historical tsunami-event records from NOAA/NCEI's global historical hazards holdings. Event presence, location, cause, validity, magnitude and runup-related fields reflect a curated historical database with uneven reporting through time and geography; absence of a record is not evidence that no tsunami occurred. ArcGIS service geometry and fields are an access view and do not replace the authoritative NCEI/HazEL database identity, DOI provenance or source interpretation guidance.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `65536`

**Max sample bytes:** `262144`

**Retry policy:** none

**Rate limit notes:** No repository-specific rate-limit assumption is made. The current ArcGIS layer advertises MaxRecordCount=2000, but any future probe must be far smaller and separately reviewed; this static contract does not authorize harvesting or pagination.

**Mutability notes:** The ArcGIS service is a mutable access surface. Reproducible scientific use must bind retrieval UTC, exact normalized request identity, trusted execution-code SHA and response byte hash/size, while preserving the NCEI database DOI and product identity separately from the live service URL.

## Rights and policy

**Dataset rights status:** not_reviewed

**Api terms status:** unknown

**Terms url:** `null`

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** Current authoritative evidence establishes a public NOAA/NCEI product page and anonymous ArcGIS REST access, but this slice does not establish an exact current commercial-automation or redistribution grant for the historical tsunami database/service. Public reachability is therefore not treated as permission. Any future executable query, persisted receipt or sample-publication decision requires a separate exact rights/API-terms review.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-08-11

## Evidence urls

- <https://www.ncei.noaa.gov/products/natural-hazards/tsunamis-earthquakes-volcanoes/tsunamis/global-historical-data>
- <https://gis.ngdc.noaa.gov/arcgis/rest/services/web_mercator/hazards/MapServer>
- <https://gis.ngdc.noaa.gov/arcgis/rest/services/web_mercator/hazards/MapServer/0>
- <https://doi.org/10.7289/V5PN93H7>

**Notes:** Static contract only. NOAA/NCEI's current ArcGIS service exposes Tsunami Events layer 0 with JSON/GeoJSON/PBF query support and a 2000-record service maximum. This file deliberately remains documented_only until exact service/data rights and bounded query semantics are independently reviewed. No external provider bytes, source admission, scientific-fit claim or publication authorization is created by this contract.
