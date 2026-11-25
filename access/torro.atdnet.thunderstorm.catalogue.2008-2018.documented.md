<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/torro.atdnet.thunderstorm.catalogue.2008-2018.documented.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `torro.atdnet.thunderstorm.catalogue.2008-2018.documented.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** torro.atdnet.thunderstorm.catalogue.2008-2018.documented

## Source ids

- torro.atdnet.thunderstorm.catalogue.2008-2018

**Provider:** Hayward et al. / TORRO / UK Met Office ATDnet

**Interface type:** http_file

**Status:** documented_only

**Documentation url:** <https://www.torro.org.uk/research/thunderstorm-observer>

**Service root:** <https://www.torro.org.uk>

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

- /pdf/Thunderstorm_catalogue_2008-2018_(LH).xlsx

**Parameter rules:** Documented exact path only. No execution authorized by this contract; review provider terms, fixed request and bounded acquisition plan before activation.

## Response contract

### Expected media types

- application/vnd.openxmlformats-officedocument.spreadsheetml.sheet

**Format:** Tracked lightning clusters of at least three flashes; duration, motion, flash rate

**Scientific semantics:** Publisher links a catalogue; paper https://doi.org/10.1002/joc.8123. Underlying Met Office ATDnet is third party; public link and open-access article do not establish commercial reuse. Confirm catalogue terms and file identity before downloading or ingesting. Thunderstorms are not hail events. Direct provider link https://www.torro.org.uk/pdf/Thunderstorm_catalogue_2008-2018_(LH).xlsx returned anonymous HEAD 200, XLSX content type and 16213773 byte length on 2026-11-25. No workbook bytes acquired pending exact reuse permission; underlying ATDnet terms remain open.

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

**Terms url:** `null`

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** Anonymous HEAD 200, 16213773 bytes. Obtain explicit reuse/commercial permission for catalogue and Met Office ATDnet lineage before workbook retrieval or storage. Not a hail catalogue.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-25

## Evidence urls

- <https://www.torro.org.uk/research/thunderstorm-observer>

**Notes:** Open-first qualification queue. Anonymous HEAD 200, 16213773 bytes. Obtain explicit reuse/commercial permission for catalogue and Met Office ATDnet lineage before workbook retrieval or storage. Not a hail catalogue. Discovery/access only: no admission, no external bytes in Git, no model approval.
