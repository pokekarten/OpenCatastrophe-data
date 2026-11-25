<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/nasa.jaxa.gpm.dpr.v07.documented.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `nasa.jaxa.gpm.dpr.v07.documented.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** nasa.jaxa.gpm.dpr.v07.documented

## Source ids

- nasa.jaxa.gpm.dpr.v07

**Provider:** NASA / JAXA

**Interface type:** provider_sdk

**Status:** blocked_registration

**Documentation url:** <https://doi.org/10.5067/GPM/DPR/GPM/2A/07>

**Service root:** <https://disc.gsfc.nasa.gov>

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

- /datasets/GPM_2ADPR_07/summary

**Parameter rules:** Documented exact path only. No execution authorized by this contract; review provider terms, fixed request and bounded acquisition plan before activation.

## Response contract

### Expected media types

- text/html

**Format:** HDF5 orbital swaths, nominal 5 km footprints; V07 hail classification

**Scientific semantics:** Catalogue https://disc.gsfc.nasa.gov/datasets/GPM_2ADPR_07/summary; algorithm basis https://gpm.nasa.gov/sites/default/files/2022-06/ATBD_DPR_V07A.pdf. flagHail/flagGraupelHail are algorithmic hydrometeor indicators, not ground diameter. Validate exact field path and flags with small authenticated subset before bulk download; full granules large. Orbit sampling, attenuation and nonuniform beam filling matter.

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

**Notes:** Earthdata account and exact V07 field path, units and product terms needed; seek small OPeNDAP subset, not 400 MB full orbit; validate flagHail against independent ground labels.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `true`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-25

## Evidence urls

- <https://doi.org/10.5067/GPM/DPR/GPM/2A/07>
- <https://science.data.nasa.gov/about/license>

**Notes:** Open-first qualification queue. Earthdata account and exact V07 field path, units and product terms needed; seek small OPeNDAP subset, not 400 MB full orbit; validate flagHail against independent ground labels. Discovery/access only: no admission, no external bytes in Git, no model approval.
