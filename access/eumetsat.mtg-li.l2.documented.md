<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/eumetsat.mtg-li.l2.documented.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `eumetsat.mtg-li.l2.documented.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** eumetsat.mtg-li.l2.documented

## Source ids

- eumetsat.mtg-li.l2

**Provider:** EUMETSAT

**Interface type:** rest

**Status:** blocked_credentials

**Documentation url:** <https://user.eumetsat.int/resources/user-guides/mtg-li-level-2-data-guide>

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

**Format:** continuous optical total-lightning detections grouped into events, groups and flashes

**Scientific semantics:** LI detects optical total-lightning activity rather than surface damage or precipitation; freeze product processing version and preserve event/group/flash definitions and detection-efficiency limitations. Live catalogue JSON for collection EO:EUM:DAT:0691 returned HTTP 200 on 2026-11-25. Anonymous OpenSearch with pi EO:EUM:DAT:0691, dtstart 2025-06-15T12:00:00Z, dtend 2025-06-15T12:15:00Z, c 1, format json returned totalResults 3, product W_XX-EUMETSAT-Darmstadt,IMG+SAT,MTI1+LI-2-LFL--FD--x-x--ARC-x_C_EUMT_20250615122021_L2PF_OPE_20250615121003_20250615122003_N__O_0074_0000, 12:10:03 to 12:20:03 UTC. Catalogue lists NoConditions for flash product; exact provider ZIP link anonymous bounded Range GET returned HTTP 404; authenticated Data Store download and exact service terms still need verification. No flash bytes downloaded; do not interpret anonymous 404 as absence of archive.

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

**Notes:** NoConditions flash collection 0691; anonymous search returned three products for 2025-06-15 12:00-12:15 UTC, exact anonymous ZIP GET 404. Register Data Store account and supply OAuth credentials outside Git, confirm exact product policy and sample; never equate optical flashes with ground strikes.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `true`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-25

## Evidence urls

- <https://user.eumetsat.int/resources/user-guides/mtg-li-level-2-data-guide>
- <https://www.eumetsat.int/legal-framework/data-policy>

**Notes:** Open-first qualification queue. NoConditions flash collection 0691; anonymous search returned three products for 2025-06-15 12:00-12:15 UTC, exact anonymous ZIP GET 404. Register Data Store account and supply OAuth credentials outside Git, confirm exact product policy and sample; never equate optical flashes with ground strikes. Discovery/access only: no admission, no external bytes in Git, no model approval.
