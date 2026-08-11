<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/nasa.coolr.landslides.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `nasa.coolr.landslides.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning, validation semantics or execution authority.

**Schema version:** 1.0.0

**Access id:** nasa.coolr.landslides

## Source ids

- nasa.coolr.landslides

**Provider:** NASA Goddard Space Flight Center

**Interface type:** arcgis_rest

**Status:** documented_only

**Documentation url:** <https://gpm.nasa.gov/applications/landslides/coolr>

**Service root:** <https://gis.earthdata.nasa.gov>

**Api version:** `null`

## Access scope

- metadata
- catalogue

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- document_coolr_feature_services

### Path templates

- /gis05/rest/services/Landslides/COOLR_Reports_Polygons/FeatureServer
- /gis05/rest/services/Landslides/COOLR_Events_Polygons/FeatureServer

**Parameter rules:** Documentation-only contract. NASA Earthdata publishes COOLR report and event ArcGIS FeatureServer services with query support, but this contract authorizes no network query or data acquisition. Any future executable operation must be separately reviewed, repository-constructed and bounded to an exact COOLR layer and small result limit; callers must not supply a host, arbitrary path, free-form where clause, output fields, geometry, pagination, headers or unrestricted query parameters.

## Response contract

### Expected media types

- application/json

**Format:** NASA Earthdata ArcGIS REST service/layer metadata or a future separately reviewed bounded COOLR feature-query response.

**Scientific semantics:** COOLR combines report-based records from NASA's Global Landslide Catalog and citizen-science Landslide Reporter Catalog with event-based inventories contributed or produced by NASA and the research community. Reports and event inventories are not interchangeable. Source/citation lineage, event_import_source or equivalent provenance, mapping method, event date, landslide type, geometry type and per-record or per-inventory citation fields remain material. Reporting density, media-language coverage, citizen-science selection and automated/manual mapping limitations prevent treating COOLR as a spatially or temporally complete landslide census.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `262144`

**Max sample bytes:** `1048576`

**Retry policy:** none

**Rate limit notes:** No automated provider probe or feature retrieval is authorized by this documentation-only contract. NASA's current FeatureServer metadata reports a maximum record count of 2000; any future OpenCatastrophe operation must impose a much smaller repository-owned bound and recheck current provider limits before execution.

**Mutability notes:** The current COOLR ArcGIS services report non-versioned live data and continuing submissions/contributed inventories. A future receipt must bind retrieval UTC, exact service and layer identity, service item identity where exposed, normalized request identity, result count and response hash. Do not treat a live service URL alone as immutable dataset identity.

## Rights and policy

**Dataset rights status:** not_reviewed

**Api terms status:** unknown

**Terms url:** `null`

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** NASA describes COOLR as an open/public platform and states that Landslide Reporter data are publicly available for research, while the ArcGIS services contain NASA, citizen-science and research-community contributions and require source/citation preservation. This evidence does not establish one current uniform commercial-automation or redistribution grant for every contributed record or inventory. Keep rights fail-closed until an exact source/API terms review resolves the intended use and any contributor-specific obligations.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-08-11

## Evidence urls

- <https://gpm.nasa.gov/applications/landslides/coolr>
- <https://gpm.nasa.gov/applications/landslides/reporter-faq>
- <https://gis.earthdata.nasa.gov/gis05/rest/services/Landslides/COOLR_Reports_Polygons/FeatureServer>
- <https://gis.earthdata.nasa.gov/gis05/rest/services/Landslides/COOLR_Events_Polygons/FeatureServer>

**Notes:** Static access documentation only. This records the authoritative NASA ArcGIS machine route without turning public reachability into a rights, scientific-fitness, admission or publication decision. A later live probe/sample must be separately authorized through the reviewed trusted Actions plane after exact rights and bounded-query semantics are approved.
