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

**Api version:** Frozen CAL FIRE FRAP firep25_1, published April 2026; 2026-09-30 mutable CA Open Data ArcGIS resource and 2026-11-11 catalogue updates are NOT independently proven identical to firep25_1

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

**Mutability notes:** Public service is mutable and historical shapes/attributes are corrected in later releases. Source edition firep25_1 must be frozen separately from the current API's present bytes, along with UTC, request identity, byte count and SHA-256. May 2026 source description says firep25_1 is the current edition. Official FRAP release notes independently confirm firep25_1 released April 2026; 516 2025 fires added, five fire polygons replaced, one duplicate removed, one prescribed-burn polygon transferred to rxburn25_1, and 12,097 collection-method NULLs set to Unknown. This matters to negative-missingness tests and event identity. California portal 'California Fire Perimeters (all)' now reports catalogue updated 2026-11-11 with resources updated 2026-09-30; a separate 'California Fire Perimeters (1950+)' dataset has a distinct publisher dataset identifier and 2026-10-08 metadata update. Neither is proof of the frozen April firep25_1 bytes.

## Rights and policy

**Dataset rights status:** not_reviewed

**Api terms status:** unknown

**Terms url:** `null`

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** State public portal identifies 'Creative Commons Attribution' and no public-use restrictions. Specific data-file attribution, exact version and API service-automation terms have not passed source-specific rights review; the contract thus cannot authorize sample download or public redistribution of derived geometry. Authoritative CAL FIRE portal currently labels the general '(all)' and separate '(1950+)' catalogue products Creative Commons Attribution, access level public and no restrictions on public use (checked 2026-11-14). They have different identifiers; the mutable Sep/Nov 2026 resource must not silently be relabelled the April 2026 firep25_1 release. Exact published original release-file licence/attribution and ArcGIS service terms remain unreviewed, so automation and redistribution are not granted.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-14

## Evidence urls

- <https://publish.data.ca.gov/dataset/california-fire-perimeters-all>
- <https://www.fire.ca.gov/what-we-do/fire-resource-assessment-program/fire-perimeters>
- <https://services.arcgis.com/V6ZHFr6zdgNZuVG0/ArcGIS/rest/services/California_Fire_Perimeters/FeatureServer>
- <https://publish.data.ca.gov/dataset/california-fire-perimeters-1950>

**Notes:** T0 documented service item and fixed layer 0 without consuming original metadata response bytes. Full versions and valid incident-identifier crosswalk with DINS remain unproven. This access record is a source-usage boundary, not an execution receipt or admission. Verified release/portal identity split on 2026-11-14 using official CAL FIRE and California government data catalogue pages. T0 documentary evidence only; no live ArcGIS GET, feature query, geometry, original byte sample, persisted receipt, Neon write or model admission. Next causal action: identify and freeze original April firep25_1 source asset or prove byte/edition equivalence of the current provider resource, then review its exact dataset and service terms before designing any bounded probe.
