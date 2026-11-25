<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/wwlln.wglc.v2026.documented.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `wwlln.wglc.v2026.documented.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** wwlln.wglc.v2026.documented

## Source ids

- wwlln.wglc.v2026

**Provider:** Jed O. Kaplan / WWLLN

**Interface type:** http_file

**Status:** documented_only

**Documentation url:** <https://zenodo.org/records/20277101>

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

- /records/20277101/files/wglc_climatology_30m_monthly.nc

**Parameter rules:** Documented exact path only. No execution authorized by this contract; review provider terms, fixed request and bounded acquisition plan before activation.

## Response contract

### Expected media types

- application/octet-stream

**Format:** NetCDF; monthly 5 arc-minute and 0.5 degree; daily 0.5 degree; stroke density and power

**Scientific semantics:** Live Zenodo API returned 7 files totaling 3299540376 bytes, metadata license cc-by-4.0; deposit description explicitly states CC BY-SA 4.0. Treat rights as conflicting until publisher confirms; no WGLC data downloaded or admitted. README is 2747 bytes, 30m monthly climatology 27325956 bytes. Detection-efficiency-adjusted stroke density is not optical flash count; no event-level tracks or jumps. Do not generalize derived grid licence to raw WWLLN.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `65536`

**Max sample bytes:** `10485760`

**Retry policy:** none

**Rate limit notes:** No new automated requests authorized. Future route must review service terms and enforce explicit provider-specific request and byte limits.

**Mutability notes:** Freeze exact version, UTC retrieval time, selected object, response byte size, SHA-256 and coverage; never use a mutable directory or catalogue as original byte identity.

## Rights and policy

**Dataset rights status:** conflicting

**Api terms status:** separate_unreviewed

**Terms url:** <https://zenodo.org/records/20277101>

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** API licence CC BY 4.0 conflicts with deposit description CC BY-SA 4.0. Ask depositor for written correction or clarification; do not download/ingest or automate until resolved. Raw WWLLN separately licensed.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-25

## Evidence urls

- <https://zenodo.org/records/20277101>

**Notes:** Open-first qualification queue. API licence CC BY 4.0 conflicts with deposit description CC BY-SA 4.0. Ask depositor for written correction or clarification; do not download/ingest or automate until resolved. Raw WWLLN separately licensed. Discovery/access only: no admission, no external bytes in Git, no model approval.
