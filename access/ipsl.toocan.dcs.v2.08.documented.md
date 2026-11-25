<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/ipsl.toocan.dcs.v2.08.documented.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `ipsl.toocan.dcs.v2.08.documented.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** ipsl.toocan.dcs.v2.08.documented

## Source ids

- ipsl.toocan.dcs.v2.08

**Provider:** Fiolleau and Roca / IPSL ESPRI

**Interface type:** web_portal

**Status:** documented_only

**Documentation url:** <https://doi.org/10.14768/1be7fd53-8b81-416e-90d5-002b36b30cf8>

**Service root:** <https://doi.org>

**Api version:** `null`

## Access scope

- metadata
- sample

## Authentication

**Mode:** other

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- inspect_documented_route

### Path templates

- /10.14768/1be7fd53-8b81-416e-90d5-002b36b30cf8

**Parameter rules:** Documentation only. Exact asset path; no new automated requests or bulk transfer authorized.

## Response contract

### Expected media types

- text/html

**Format:** 30 minute lifecycle statistics, regional monthly NetCDF4/ASCII and segmented images

**Scientific semantics:** Paper https://doi.org/10.5194/essd-16-4021-2024. Provider page https://toocan.ipsl.fr/toocandatabase/2012-2020tropicaltoocandataset/ names CC BY 4.0 with research/publication attribution wording; confirm exact product rights and required acknowledgment before commercial use. DCS cloud shield not hail footprint; misses Germany entirely, useful tropical context only. No original sample.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `65536`

**Max sample bytes:** `10485760`

**Retry policy:** none

**Rate limit notes:** Review provider terms and explicit request/byte budget before any future execution.

**Mutability notes:** Freeze exact asset/version, UTC retrieval, size and SHA-256; mutable metadata is not data identity.

## Rights and policy

**Dataset rights status:** unknown

**Api terms status:** separate_unreviewed

**Terms url:** `null`

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** Provider mentions CC BY 4.0 with research attribution wording; resolve exact product conditions and regional files, then sample. Tropical-only context.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `true`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-25

## Evidence urls

- <https://doi.org/10.14768/1be7fd53-8b81-416e-90d5-002b36b30cf8>

**Notes:** Open-first qualification. Provider mentions CC BY 4.0 with research attribution wording; resolve exact product conditions and regional files, then sample. Tropical-only context. No admission or authorization to acquire data.
