<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/giordani.ot.sphera.hail.2024.documented.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `giordani.ot.sphera.hail.2024.documented.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** giordani.ot.sphera.hail.2024.documented

## Source ids

- giordani.ot.sphera.hail.2024

**Provider:** University of Bologna / KIT / NASA / ARPAE

**Interface type:** web_portal

**Status:** documented_only

**Documentation url:** <https://doi.org/10.5194/nhess-24-2331-2024>

**Service root:** <https://github.com>

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

- /agiord/hail-analysis

**Parameter rules:** Documented exact path only. No execution authorized by this contract; review provider terms, fixed request and bounded acquisition plan before activation.

## Response contract

### Expected media types

- text/html

**Format:** OT detections joined to convection-permitting reanalysis and hail reports

**Scientific semantics:** Code https://github.com/agiord/hail-analysis; SPHERA from corresponding author; NASA OT data via provider request; ESWD reports separate restricted terms. Inspect code licence and verify exact feature definitions. No external data downloaded. Avoid circular validation against reports used for training. GitHub REST metadata on 2026-11-25 identifies hail-analysis repository licence as CC0-1.0; inspect actual licence and third-party dependencies before incorporating code. This does not grant SPHERA, NASA OT or ESWD dataset rights.

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

**Terms url:** <https://github.com/agiord/hail-analysis>

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** Code GitHub metadata CC0-1.0; verify actual licence and dependencies. Separate NASA OT, SPHERA and ESWD terms and provider requests; code access does not license data. Research method only.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-25

## Evidence urls

- <https://doi.org/10.5194/nhess-24-2331-2024>
- <https://github.com/agiord/hail-analysis>

**Notes:** Open-first qualification queue. Code GitHub metadata CC0-1.0; verify actual licence and dependencies. Separate NASA OT, SPHERA and ESWD terms and provider requests; code access does not license data. Research method only. Discovery/access only: no admission, no external bytes in Git, no model approval.
