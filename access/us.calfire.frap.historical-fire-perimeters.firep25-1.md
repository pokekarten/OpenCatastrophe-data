<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/us.calfire.frap.historical-fire-perimeters.firep25-1.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `us.calfire.frap.historical-fire-perimeters.firep25-1.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** us.calfire.frap.historical-fire-perimeters.firep25-1

## Source ids

- us.calfire.frap.historical-fire-perimeters.firep25-1

**Provider:** CAL FIRE / Fire and Resource Assessment Program (FRAP)

**Interface type:** arcgis_rest

**Status:** documented_only

**Documentation url:** <https://publish.data.ca.gov/dataset/california-fire-perimeters-all>

**Service root:** <https://services.arcgis.com/V6ZHFr6zdgNZuVG0/ArcGIS/rest/services/California_Fire_Perimeters/FeatureServer>

**Api version:** CAL FIRE FRAP firep25_1, April 2026 (public ArcGIS FeatureServer layer 0)

## Access scope

- metadata

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- inspect_frap_perimeter_metadata

### Path templates

- /0

**Parameter rules:** Documentation-only exact official ArcGIS service item 14c312c213fb4be8b97a37238a871255, unfiltered 'California_Fire_Perimeters__all_' layer 0. A future metadata-only review may consider f=pjson on the fixed path; there is NO authorized feature query, geometry download, pagination, user-provided URL/headers, arbitrary where clause, export or external dataset acquisition under this contract.

## Response contract

### Expected media types

- application/json

**Format:** Official ArcGIS Feature Layer metadata description and field schema only; not a feature collection or fire polygon.

**Scientific semantics:** FRAP firep25_1 historical wildfire perimeters are multiagency final-mapped wildfire polygons spanning decades to 2025. Their geometry is not fire intensity, building-level burn, independent survey of all fires or a full exposed-building denominator. The archive includes version-dependent collection thresholds, missing events, duplicate and generalized polygons and sometimes unburned areas inside final perimeters; they must not be equated with DINS observed building damage.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `524288`

**Max sample bytes:** `524288`

**Retry policy:** none

**Rate limit notes:** Do not automate, query or crawl the ArcGIS service until exact API terms, release-specific rights and a separately fixed metadata-only recipe have been reviewed.

**Mutability notes:** Public service is mutable and historical shapes/attributes are corrected in later releases. Source edition firep25_1 must be frozen separately from the current API's present bytes, along with UTC, request identity, byte count and SHA-256. May 2026 source description says firep25_1 is the current edition.

## Rights and policy

**Dataset rights status:** not_reviewed

**Api terms status:** unknown

**Terms url:** `null`

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** State public portal identifies 'Creative Commons Attribution' and no public-use restrictions. Specific data-file attribution, exact version and API service-automation terms have not passed source-specific rights review; the contract thus cannot authorize sample download or public redistribution of derived geometry.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-01

## Evidence urls

- <https://publish.data.ca.gov/dataset/california-fire-perimeters-all>
- <https://www.fire.ca.gov/what-we-do/fire-resource-assessment-program/fire-perimeters>
- <https://services.arcgis.com/V6ZHFr6zdgNZuVG0/ArcGIS/rest/services/California_Fire_Perimeters/FeatureServer>

**Notes:** T0 documented service item and fixed layer 0 without consuming original metadata response bytes. Full versions and valid incident-identifier crosswalk with DINS remain unproven. This access record is a source-usage boundary, not an execution receipt or admission.
