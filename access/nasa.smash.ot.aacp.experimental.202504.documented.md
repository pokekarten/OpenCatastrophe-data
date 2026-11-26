<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/nasa.smash.ot.aacp.experimental.202504.documented.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `nasa.smash.ot.aacp.experimental.202504.documented.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** nasa.smash.ot.aacp.experimental.202504.documented

## Source ids

- nasa.smash.ot.aacp.experimental.202504

**Provider:** NASA Earthdata GIS / Langley

**Interface type:** arcgis_rest

**Status:** documented_only

**Documentation url:** <https://gis.earthdata.nasa.gov/portal/home/item.html?id=b1dbafac653b41e8b4716de1020a201e>

**Service root:** <https://gis.earthdata.nasa.gov>

**Api version:** `null`

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

- inspect_documented_route

### Path templates

- /portal/sharing/rest/content/items/b1dbafac653b41e8b4716de1020a201e

**Parameter rules:** Documented exact path only. No execution authorized by this contract; review provider terms, fixed request and bounded acquisition plan before activation.

## Response contract

### Expected media types

- application/json

**Format:** Experimental raster detections derived from GOES 500 m imagery at 5-minute cadence

**Scientific semantics:** Provider marks product experimental. Time-aggregated repeated detections may indicate severe storm tracks but not hail swaths. Check exact raster service/licence and independent surface hail reports before quantitative use.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `65536`

**Max sample bytes:** `10485760`

**Retry policy:** none

**Rate limit notes:** No new automated requests authorized. Future route must review service terms and enforce explicit provider-specific request and byte limits.

**Mutability notes:** Freeze exact version, UTC retrieval time, selected object, response byte size, SHA-256 and coverage; never use a mutable directory or catalogue as original byte identity.

## Rights and policy

**Dataset rights status:** unknown

**Api terms status:** separate_unreviewed

**Terms url:** <https://science.data.nasa.gov/about/license>

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** Experimental April 2025 event raster; inspect exact item/service and licence, then small numerical export. Not a validated hail footprint.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-25

## Evidence urls

- <https://gis.earthdata.nasa.gov/portal/home/item.html?id=b1dbafac653b41e8b4716de1020a201e>
- <https://science.data.nasa.gov/about/license>

**Notes:** Open-first qualification queue. Experimental April 2025 event raster; inspect exact item/service and licence, then small numerical export. Not a validated hail footprint. Discovery/access only: no admission, no external bytes in Git, no model approval.
