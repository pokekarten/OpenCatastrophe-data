<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/pnnl.pyflextrkr.global.mcs.v3.documented.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `pnnl.pyflextrkr.global.mcs.v3.documented.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** pnnl.pyflextrkr.global.mcs.v3.documented

## Source ids

- pnnl.pyflextrkr.global.mcs.v3

**Provider:** Feng and Zhang / PNNL

**Interface type:** http_file

**Status:** documented_only

**Documentation url:** <https://zenodo.org/records/23523604>

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

- /records/23523604/files/01_README.md

**Parameter rules:** Documentation only. Exact asset path; no new automated requests or bulk transfer authorized.

## Response contract

### Expected media types

- text/plain

**Format:** Hourly 0.1 degree merged IR and IMERG V07B, two MCS definitions

**Scientific semantics:** Live Zenodo metadata 2026-11-25: 20 files, 29569660540 bytes, cc-by-4.0. Small README 6783 bytes and checksum file 1670 bytes; smallest climatology archive 270842421 bytes. MCS definition requires spatial/temporal persistence and precipitation thresholds; misses small isolated hailstorms, excludes tracks overlapping tropical cyclones, not a hail catalogue. Read README and choose bounded region/month export before full archive acquisition; no source data downloaded.

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

**Notes:** CC BY 4.0 deposit; 29.57 GB. Read README and choose regional or monthly subset; confirm source lineage and model role before transfer. Large organized storms only.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-25

## Evidence urls

- <https://zenodo.org/records/23523604>

**Notes:** Open-first qualification. CC BY 4.0 deposit; 29.57 GB. Read README and choose regional or monthly subset; confirm source lineage and model role before transfer. Large organized storms only. No admission or authorization to acquire data.
