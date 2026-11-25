<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/noaa.cimss.probsevere.archive.documented.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `noaa.cimss.probsevere.archive.documented.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** noaa.cimss.probsevere.archive.documented

## Source ids

- noaa.cimss.probsevere.archive

**Provider:** NOAA / University of Wisconsin CIMSS / Iowa State archive

**Interface type:** http_file

**Status:** restricted_by_terms

**Documentation url:** <https://cimss.ssec.wisc.edu/probsevere/ps/>

**Service root:** <https://mtarchive.geol.iastate.edu>

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

- /2025/12/30/mrms/ncep/ProbSevere/MRMS_PROBSEVERE_20251230_000000.json

**Parameter rules:** Documentation only. Exact asset path; no new automated requests or bulk transfer authorized.

## Response contract

### Expected media types

- application/json

**Format:** GeoJSON storm features, nominal 2 minute cadence; ProbHail, ProbWind, ProbTor

**Scientific semantics:** Exact bounded GET on 2026-11-25 https://mtarchive.geol.iastate.edu/2025/12/30/mrms/ncep/ProbSevere/MRMS_PROBSEVERE_20251230_000000.json returned 18033 bytes, SHA-256 2c51ef06867fe62c8e7f3c88c0b31d55755ea185cc730a1e4adf587864a5e6c8. JSON parsed 6 features; properties include MaxFED, MaxFCD, MUCAPE, EBSHEAR, MESH, EchoTop_50, VIL, FLASH_RATE, FLASH_DENSITY, WETBULB_0C_HGT, LJA, ProbHail, ID; many values encoded as strings. Provider live directory https://mrms.ncep.noaa.gov/ProbSevere/PROBSEVERE/. Model predicts severe hail &gt;=1 inch, not observed hail or diameter; probabilities and input predictors are dependent. CIMSS product page https://cimss.ssec.wisc.edu/severe_conv/psv3.html displays a reproduction/dissemination restriction; clarify scope and contracted upstream data rights before retention or reuse. No raw data committed or ingested.

## Operational constraints

**Timeout seconds:** `30`

**Max probe bytes:** `65536`

**Max sample bytes:** `10485760`

**Retry policy:** none

**Rate limit notes:** Review provider terms and explicit request/byte budget before any future execution.

**Mutability notes:** Freeze exact asset/version, UTC retrieval, size and SHA-256; mutable metadata is not data identity.

## Rights and policy

**Dataset rights status:** unknown

**Api terms status:** separate_unreviewed

**Terms url:** `null`

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** Original JSON read; CIMSS reproduction/dissemination terms need product-specific interpretation. Request written clarification; keep as benchmark only until clearance, not independent hail truth.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-25

## Evidence urls

- <https://cimss.ssec.wisc.edu/probsevere/ps/>

**Notes:** Open-first qualification. Original JSON read; CIMSS reproduction/dissemination terms need product-specific interpretation. Request written clarification; keep as benchmark only until clearance, not independent hail truth. No admission or authorization to acquire data.
