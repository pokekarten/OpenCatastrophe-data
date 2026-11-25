<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/eumetsat.msg.hrseviri.l15.documented.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `eumetsat.msg.hrseviri.l15.documented.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** eumetsat.msg.hrseviri.l15.documented

## Source ids

- eumetsat.msg.hrseviri.l15

**Provider:** EUMETSAT

**Interface type:** rest

**Status:** blocked_credentials

**Documentation url:** <https://user.eumetsat.int/catalogue/EO:EUM:DAT:MSG:HRSEVIRI>

**Service root:** <https://api.eumetsat.int>

**Api version:** `null`

## Access scope

- metadata
- sample

## Authentication

**Mode:** oauth2

**Credential reference:** EUMETSAT_DATASTORE_CREDENTIAL

**Registration url:** <https://user.eumetsat.int/>

**Secret in repository:** `false`

## Request contract

### Allowed operations

- inspect_documented_route

### Path templates

- /data/search-products/1.0.0/os

**Parameter rules:** Documented exact path only. No execution authorized by this contract; review provider terms, fixed request and bounded acquisition plan before activation.

## Response contract

### Expected media types

- application/json

**Format:** 12 spectral channels, historical 15-minute nominal imagery; latency-dependent availability

**Scientific semantics:** Exact collection EO:EUM:DAT:MSG:HRSEVIRI. Preserve platform transitions, spectral response, scan timing, calibration and parallax; review historical archive completeness and product-specific licence before authenticated acquisition. Raw imagery, not OT catalogue. Pair with published OT detector rather than assuming GOES model transfers. Live anonymous EUMETSAT OpenSearch https://api.eumetsat.int/data/search-products/1.0.0/os with pi EO:EUM:DAT:MSG:HRSEVIRI, dtstart 2013-07-28T12:00:00Z, dtend 2013-07-28T12:30:00Z, c 1, format json returned totalResults 2; product MSG3-SEVI-MSG15-0100-NA-20130728122744.999000000Z-NA (12:15:11.055 to 12:27:44.999 UTC) with provider ZIP download link. Anonymous bounded range GET on exact advertised link returned HTTP 404; authenticated service test required, not evidence archive missing. No image data downloaded.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `65536`

**Max sample bytes:** `10485760`

**Retry policy:** none

**Rate limit notes:** No new automated requests authorized. Future route must review service terms and enforce explicit provider-specific request and byte limits.

**Mutability notes:** Freeze exact version, UTC retrieval time, selected object, response byte size, SHA-256 and coverage; never use a mutable directory or catalogue as original byte identity.

## Rights and policy

**Dataset rights status:** not_reviewed

**Api terms status:** separate_unreviewed

**Terms url:** <https://www.eumetsat.int/legal-framework/data-policy>

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** Historic search returned two products for 2013-07-28 12:00-12:30 UTC; exact anonymous ZIP GET 404. EUMETSAT account and Data Store OAuth credentials, exact historical collection policy, bounded authenticated sample then sensor-specific calibration.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `true`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-25

## Evidence urls

- <https://user.eumetsat.int/catalogue/EO:EUM:DAT:MSG:HRSEVIRI>
- <https://www.eumetsat.int/legal-framework/data-policy>

**Notes:** Open-first qualification queue. Historic search returned two products for 2013-07-28 12:00-12:30 UTC; exact anonymous ZIP GET 404. EUMETSAT account and Data Store OAuth credentials, exact historical collection policy, bounded authenticated sample then sensor-specific calibration. Discovery/access only: no admission, no external bytes in Git, no model approval.
