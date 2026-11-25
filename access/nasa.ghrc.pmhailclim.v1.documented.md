<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/nasa.ghrc.pmhailclim.v1.documented.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `nasa.ghrc.pmhailclim.v1.documented.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** nasa.ghrc.pmhailclim.v1.documented

## Source ids

- nasa.ghrc.pmhailclim.v1

**Provider:** NASA GHRC DAAC

**Interface type:** http_file

**Status:** blocked_registration

**Documentation url:** <https://doi.org/10.5067/MODEL/DATA101>

**Service root:** <https://data.ghrc.earthdata.nasa.gov>

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

- /ghrcw-protected/pmhailclim__1/COMBO_HailClimatology_BC2019_2deg.nc

**Parameter rules:** Documented exact path only. No execution authorized by this contract; review provider terms, fixed request and bounded acquisition plan before activation.

## Response contract

### Expected media types

- application/octet-stream

**Format:** 2-degree NetCDF-3 annual severe-hailstorm frequency estimates; three CMR granules

**Scientific semantics:** Live CMR collection C2196515446-GHRC_DAAC returned COMBO_HailClimatology_BC2019_2deg.nc, TRMM_HailClimatology_BC2019_2deg.nc and GPM_HailClimatology_BC2019_2deg.nc with protected Earthdata URLs; metadata only, no NetCDF downloaded. Older NASA landing page ended March 2025; live CMR confirms March 2026. Severe-hail frequency inferred from passive microwave ice scattering; coarse climatology, not observed hail diameter or swath. Account, licence and granule variable/normalization check needed. Anonymous HEAD to the exact COMBO protected URL returned 303 to a CloudFront host on 2026-11-25, not a data payload. Earthdata login flow not completed; no access claim.

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

**Notes:** CMR metadata identified exact 2-degree file through March 2026; protected HEAD 303. Earthdata account and product-specific rights/normalization review needed; then bounded NetCDF acquisition.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `true`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-25

## Evidence urls

- <https://doi.org/10.5067/MODEL/DATA101>
- <https://science.data.nasa.gov/about/license>

**Notes:** Open-first qualification queue. CMR metadata identified exact 2-degree file through March 2026; protected HEAD 303. Earthdata account and product-specific rights/normalization review needed; then bounded NetCDF acquisition. Discovery/access only: no admission, no external bytes in Git, no model approval.
