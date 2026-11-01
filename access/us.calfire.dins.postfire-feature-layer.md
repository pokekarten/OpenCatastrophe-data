<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/us.calfire.dins.postfire-feature-layer.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `us.calfire.dins.postfire-feature-layer.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** us.calfire.dins.postfire-feature-layer

## Source ids

- us.calfire.dins.structure-damage

**Provider:** California Department of Forestry and Fire Protection (CAL FIRE)

**Interface type:** arcgis_rest

**Status:** documented_only

**Documentation url:** <https://publish.data.ca.gov/dataset/cal-fire-damage-inspection-dins-data>

**Service root:** <https://services1.arcgis.com/jUJYIo9tSA7EHvfZ/arcgis/rest/services/POSTFIRE_MASTER_DATA_SHARE/FeatureServer>

**Api version:** ArcGIS FeatureServer layer 0, live schema subject to updates

## Access scope

- metadata

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- inspect_layer_metadata

### Path templates

- /0

**Parameter rules:** Documentation-only description of one official CAL FIRE POSTFIRE layer (layer 0, service item 994d3dc4569640caadbbc3198d5a3da1). Any future metadata-only request must be limited to the fixed layer path and f=pjson; no feature /query, spatial, field, pagination, geometry, SQL, edits, arbitrary URL, headers or redirects may be supplied by users. This contract intentionally does not authorize any network probe or feature export.

## Response contract

### Expected media types

- application/json

**Format:** ArcGIS FeatureServer layer metadata only (fields, type, geometryType, objectIdField, service metadata). No features array or feature rows.

**Scientific semantics:** The POSTFIRE layer declares point geometry, damage-code domains, structure type, roof/siding and other inspection attributes. These are inspection observations from a selected damaged-area frame, not independently sampled insured losses or a full census of structures. Provider descriptions say digital damaged-structure records start in 2013 and no-damage structures were collected from 2018; earlier damage state denominators cannot be reconstructed naively. Field names for addresses, parcel APN and coordinates are sensitive enrichment context and remain outside any public import.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `524288`

**Max sample bytes:** `524288`

**Retry policy:** none

**Rate limit notes:** This documented_only contract prohibits automated provider requests until exact ArcGIS service/API terms and privacy-safe extraction policy are separately approved. Never paginate or bulk download under this record.

**Mutability notes:** CAL FIRE portal lists an irregular update schedule and the upstream ArcGIS layer is mutable. Future permissible metadata receipts must freeze request identity, UTC, response byte count and SHA-256; later data receipts must freeze event/inspection time and source version.

## Rights and policy

**Dataset rights status:** not_reviewed

**Api terms status:** unknown

**Terms url:** `null`

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** Official California portal labels this dataset Creative Commons Attribution and public access with no general public-use restrictions; exact layer/service terms, attribution, commercial automated retrieval and privacy-safe redistribution have NOT received a source-specific acceptance review. Do not infer that the CC license authorizes unrestricted API activity, public export of address/APN fields or model-input admission.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-01

## Evidence urls

- <https://publish.data.ca.gov/dataset/cal-fire-damage-inspection-dins-data>
- <https://catalog.data.gov/dataset/cal-fire-damage-inspection-dins-data>
- <https://services1.arcgis.com/jUJYIo9tSA7EHvfZ/arcgis/rest/services/POSTFIRE_MASTER_DATA_SHARE/FeatureServer/0>

**Notes:** T0 reviewed provider documentation; official catalogue identifies service item 994d3dc4569640caadbbc3198d5a3da1 and layer 0. No raw data, feature records, schema bytes, SHA-stamped live probe, personal fields, or vulnerability coefficient has been acquired or committed. Separately review service terms, field redaction, selection bias and a bounded one-event non-sensitive aggregate recipe before enabling T1/T3.
