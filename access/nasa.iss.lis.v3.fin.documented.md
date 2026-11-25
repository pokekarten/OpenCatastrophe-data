<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/nasa.iss.lis.v3.fin.documented.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `nasa.iss.lis.v3.fin.documented.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** nasa.iss.lis.v3.fin.documented

## Source ids

- nasa.iss.lis.v3.fin

**Provider:** NASA GHRC DAAC

**Interface type:** web_portal

**Status:** blocked_registration

**Documentation url:** <https://doi.org/10.5067/LIS/ISSLIS/DATA114>

**Service root:** <https://search.earthdata.nasa.gov>

**Api version:** `null`

## Access scope

- metadata
- sample

## Authentication

**Mode:** provider_account

**Credential reference:** EARTHDATA_CREDENTIAL

**Registration url:** <https://urs.earthdata.nasa.gov/>

**Secret in repository:** `false`

## Request contract

### Allowed operations

- inspect_documented_route

### Path templates

- /search/granules

**Parameter rules:** Documented exact path only. No execution authorized by this contract; review provider terms, fixed request and bounded acquisition plan before activation.

## Response contract

### Expected media types

- text/html

**Format:** NetCDF-4/HDF4 optical total-lightning detections

**Scientific semantics:** CMR collection C3838944284-GHRC_DAAC. Intermittent ISS observation windows require exposure normalization; flash/stroke distinction and detection efficiency must be retained. Not continuous tracks. Exact granule rights and bytes untested.

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

**Terms url:** <https://science.data.nasa.gov/about/license>

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** Earthdata registration and exact granule rights; obtain one small granule and decode flash time, viewing exposure and flags. Orbit sampling is not continuous.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `true`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-25

## Evidence urls

- <https://doi.org/10.5067/LIS/ISSLIS/DATA114>
- <https://science.data.nasa.gov/about/license>

**Notes:** Open-first qualification queue. Earthdata registration and exact granule rights; obtain one small granule and decode flash time, viewing exposure and flags. Orbit sampling is not continuous. Discovery/access only: no admission, no external bytes in Git, no model approval.
