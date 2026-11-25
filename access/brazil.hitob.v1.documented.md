<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/brazil.hitob.v1.documented.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `brazil.hitob.v1.documented.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** brazil.hitob.v1.documented

## Source ids

- brazil.hitob.v1

**Provider:** HIToB research authors

**Interface type:** http_file

**Status:** documented_only

**Documentation url:** <https://zenodo.org/records/11152458>

**Service root:** <https://zenodo.org>

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

- /records/11152458/files/HIToB_v1.db

**Parameter rules:** Documentation only. Exact asset path; no new automated requests or bulk transfer authorized.

## Response contract

### Expected media types

- application/octet-stream

**Format:** 2 km grid infrared cloud objects tracked with TATHU; database file

**Scientific semantics:** Paper https://pmc.ncbi.nlm.nih.gov/articles/PMC11295460/. Live Zenodo API 2026-11-25 returned cc-by-4.0 and HIToB_v1.db 6911950848 bytes, MD5 2ae0f679345d7a97c9e825692359de17. Archive not downloaded due to size; seek bounded subset or author-provided export, do not claim a byte range is a valid SQLite database. Cold cloud threshold 235 K; storms selected by hail association and cloud polygons not actual hail damage swaths. Check report bias, geometry, time and third-party report rights.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `65536`

**Max sample bytes:** `10485760`

**Retry policy:** none

**Rate limit notes:** Review provider terms and explicit request/byte budget before any future execution.

**Mutability notes:** Freeze exact asset/version, UTC retrieval, size and SHA-256; mutable metadata is not data identity.

## Rights and policy

**Dataset rights status:** not_reviewed

**Api terms status:** separate_unreviewed

**Terms url:** <https://about.zenodo.org/policies/>

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** CC BY 4.0 deposit; 6.91 GB archive. Request small regional/temporal export or plan disk budget; verify report rights and cloud polygon semantics.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-25

## Evidence urls

- <https://zenodo.org/records/11152458>

**Notes:** Open-first qualification. CC BY 4.0 deposit; 6.91 GB archive. Request small regional/temporal export or plan disk budget; verify report rights and cloud polygon semantics. No admission or authorization to acquire data.
