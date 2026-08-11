<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/fema.usa-structures.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `fema.usa-structures.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** fema.usa-structures

## Source ids

- fema.usa-structures

**Provider:** Federal Emergency Management Agency

**Interface type:** arcgis_rest

**Status:** documented_only

**Documentation url:** <https://catalog.data.gov/dataset/usa-structures-4749e>

**Service root:** <https://services.arcgis.com/VhMjCzR3cIjEkh7L>

**Api version:** `null`

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

- usa_structures_service_metadata
- bounded_structure_query

### Path templates

- /arcgis/rest/services/USA_Structures/FeatureServer
- /arcgis/rest/services/USA_Structures/FeatureServer/0/query

**Parameter rules:** This static contract records the currently discoverable USA Structures ArcGIS service shape only. Callers may not supply a host, arbitrary path, free-form where clause, output-field list, geometry, pagination state, headers or unrestricted query parameters. Before executable probing is enabled, a separate review must bind the ArcGIS item/service to FEMA's current authoritative USA Structures release and freeze one exact low-byte metadata or feature query with deterministic ordering and result limit.

## Response contract

### Expected media types

- application/json

**Format:** ArcGIS REST JSON service metadata or a future bounded feature-query response for the USA Structures building-footprint inventory.

**Scientific semantics:** USA Structures is a modeled national building-footprint inventory for structures larger than 450 square feet, assembled for emergency-management and flood-mitigation use. It is not parcel, ownership, insured-value or claims truth and does not meet National Map Accuracy standards for large-scale cartographic use. Any catastrophe-risk consumer must preserve release/vintage, geometry/source lineage and attribution fields and must not infer occupancy, value, construction characteristics, completeness or structure-level insurance exposure beyond what the exact reviewed release documents.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `65536`

**Max sample bytes:** `262144`

**Retry policy:** none

**Rate limit notes:** No repository-specific rate-limit assumption is made. The discoverable ArcGIS service advertises a 2000-record maximum, but this contract does not authorize pagination, bulk extraction or harvesting; any future executable operation must be separately bounded far below that ceiling.

**Mutability notes:** The public catalogue and ArcGIS service are mutable discovery/access surfaces. Reproducible use must bind the exact FEMA release/vintage separately from the live service URL and record retrieval UTC, normalized request identity, trusted execution-code SHA, response byte count and SHA-256 for any future receipt.

## Rights and policy

**Dataset rights status:** not_reviewed

**Api terms status:** unknown

**Terms url:** <https://www.usa.gov/government-works>

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** The federal data catalog currently marks USA Structures as public and points to the U.S. government-works licence reference, but this slice does not establish that the discovered ArcGIS service/item is the exact current FEMA release endpoint or that separate ArcGIS/API terms permit automated commercial extraction and redistribution. Public access is therefore not converted into execution or publication permission.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-08-11

## Evidence urls

- <https://catalog.data.gov/dataset/usa-structures-4749e>
- <https://gis-fema.hub.arcgis.com/pages/usa-structures>
- <https://services.arcgis.com/VhMjCzR3cIjEkh7L/arcgis/rest/services/USA_Structures/FeatureServer>
- <https://www.usa.gov/government-works>

**Notes:** Static access contract only. Current federal metadata identifies USA Structures as FEMA dataset FEMA-0209 and reports a 2025-04-01 data-modified timestamp; current ArcGIS discovery exposes a USA_Structures FeatureServer with JSON query support. This contract deliberately remains documented_only because the exact authoritative binding between the current FEMA release and the discovered ArcGIS item/service, plus API automation/redistribution terms, has not been independently proven. No provider bytes, source admission, scientific-fit claim or publication authorization is created.
