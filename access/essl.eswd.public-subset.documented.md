<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/essl.eswd.public-subset.documented.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `essl.eswd.public-subset.documented.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning, validation semantics or execution authority.

**Schema version:** 1.0.0

**Access id:** essl.eswd.public-subset.documented

## Source ids

- essl.eswd

**Provider:** European Severe Storms Laboratory and partner networks

**Interface type:** web_portal

**Status:** restricted_by_terms

**Documentation url:** <https://www.essl.org/cms/european-severe-weather-database/>

**Service root:** <https://www.essl.org>

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

- inspect_public_access_terms

### Path templates

- /cms/european-severe-weather-database/

**Parameter rules:** Documentation-only contract. Do not add automated event-data acquisition until a source-specific rights/access review establishes the exact permitted interface, purpose and redistribution boundary. No arbitrary host, path, headers or query parameters are allowed.

## Response contract

### Expected media types

- text/html

**Format:** Provider access/description page only; no event-data payload is authorized by this contract.

**Scientific semantics:** ESWD contains heterogeneous severe-weather reports with quality-control levels and source provenance. Any later statistical use must preserve report type, QC level, duplication/source semantics and coverage bias.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `524288`

**Max sample bytes:** `524288`

**Retry policy:** none

**Rate limit notes:** No automated dataset probing is authorized by this documentation-only contract.

**Mutability notes:** Provider access rules and public-subset availability may change; re-review authoritative terms before changing this status.

## Rights and policy

**Dataset rights status:** restricted

**Api terms status:** unknown

**Terms url:** <https://www.essl.org/cms/european-severe-weather-database/>

**Commercial automation status:** prohibited

**Redistribution status:** unknown

**Notes:** The existing source-landscape review records that commercial use of the public ESWD data is not allowed and that broader access is agreement-based. This contract therefore documents the boundary and deliberately does not create an automated data adapter. Exact rights must be re-reviewed before any use beyond provider-permitted public access.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** do_not_automate

**Reviewed at:** 2026-08-10

## Evidence urls

- <https://www.essl.org/cms/european-severe-weather-database/>

**Notes:** This is intentionally a documentation-only rights/access contract. It demonstrates that 100% connector coverage does not mean bypassing provider terms: where access is legally constrained, the correct machine-readable result is a durable prohibition or review gate, not a scraper.
