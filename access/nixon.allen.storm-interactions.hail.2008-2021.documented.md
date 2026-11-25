<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/nixon.allen.storm-interactions.hail.2008-2021.documented.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `nixon.allen.storm-interactions.hail.2008-2021.documented.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** nixon.allen.storm-interactions.hail.2008-2021.documented

## Source ids

- nixon.allen.storm-interactions.hail.2008-2021

**Provider:** Nixon and Allen / Central Michigan University

**Interface type:** http_file

**Status:** documented_only

**Documentation url:** <https://zenodo.org/records/10672225>

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

- /records/10672225/files/StormInteractions_HAIL.csv

**Parameter rules:** Documentation only. Exact asset path; no new automated requests or bulk transfer authorized.

## Response contract

### Expected media types

- text/plain

**Format:** CSV point reports and surrounding cell characteristics

**Scientific semantics:** Zenodo API license cc-by-4.0. Bounded original GET on 2026-11-25 https://zenodo.org/records/10672225/files/StormInteractions_HAIL.csv?download=1 yielded 48878 bytes, SHA-256 1f5d061ddee6e721bbf356ede3358dcb667f0cc0fba64991a0df3ff1440cc696 and MD5 2fc284273a32085b35fb0b3d2c4e60a2 matching provider. CSV parsed 331 data rows; observed Date, Time, Radar, Lat, Lon, Mag, SM, Sample, Mode1-4, Orientation, neighboring Cell1-5 at 00/10/20/30 minute offsets and blank spacer columns. Selected &gt;=3 inch hail reports, not representative occurrence sample; do not infer annual rates, treat blank headers explicitly, confirm magnitude units and date/time convention from authors. No original data in Git or database; third-party report lineage and scientific independence require review.

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

**Notes:** CC BY 4.0 deposit; original 331-row CSV and MD5 verified. Review report lineage, magnitude/time definitions and exact reuse scope; priority open source for extreme hail validation, not frequency.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-25

## Evidence urls

- <https://zenodo.org/records/10672225>

**Notes:** Open-first qualification. CC BY 4.0 deposit; original 331-row CSV and MD5 verified. Review report lineage, magnitude/time definitions and exact reuse scope; priority open source for extreme hail validation, not frequency. No admission or authorization to acquire data.
