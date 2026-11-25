<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/dong.global.mcs.1985-2024.documented.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `dong.global.mcs.1985-2024.documented.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** dong.global.mcs.1985-2024.documented

## Source ids

- dong.global.mcs.1985-2024

**Provider:** Wenhao Dong

**Interface type:** http_file

**Status:** documented_only

**Documentation url:** <https://zenodo.org/records/19634724>

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

- /records/19634724/files/CLAUS_CSVFILE.tar.gz

**Parameter rules:** Documentation only. Exact asset path; no new automated requests or bulk transfer authorized.

## Response contract

### Expected media types

- application/gzip

**Format:** KFyAO tracked systems from CLAUS and NCEP/CPC brightness temperature, CSV and NetCDF

**Scientific semantics:** Live Zenodo metadata 2026-11-25: 6 files, 15032621710 bytes, cc-by-4.0; smallest CLAUS_CSVFILE.tar.gz 218241779 bytes. Transition adjustments are latitude/season dependent; check homogeneity and storm definition, avoid double-counting overlapping source years. No direct hail intensity or isolated cell representation. No source bytes downloaded.

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

**Notes:** CC BY 4.0 deposit; smallest archive 218 MB. Plan bounded acquisition with disk budget, upstream CLAUS/NCEP rights and overlap/homogeneity checks; not hail diameter.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-25

## Evidence urls

- <https://zenodo.org/records/19634724>

**Notes:** Open-first qualification. CC BY 4.0 deposit; smallest archive 218 MB. Plan bounded acquisition with disk budget, upstream CLAUS/NCEP rights and overlap/homogeneity checks; not hail diameter. No admission or authorization to acquire data.
