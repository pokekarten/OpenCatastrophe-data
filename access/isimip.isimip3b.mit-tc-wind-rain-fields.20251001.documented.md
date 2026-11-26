<!--
SPDX-FileCopyrightText: 2026 OpenCatastrophe contributors
SPDX-License-Identifier: Apache-2.0

GENERATED FILE — DO NOT EDIT DIRECTLY
Canonical source: access/isimip.isimip3b.mit-tc-wind-rain-fields.20251001.documented.json
Renderer: scripts/render_public_views.py
Change the canonical JSON and run `python scripts/render_public_views.py --write`.
-->

# Source access contract: `isimip.isimip3b.mit-tc-wind-rain-fields.20251001.documented.json`

> This Markdown file is a deterministic human-readable projection of the canonical JSON file named above. The JSON remains authoritative; this view does not change rights, admission, scientific meaning or execution authority.

**Schema version:** 1.0.0

**Access id:** isimip.isimip3b.mit-tc-wind-rain-fields.20251001.documented

## Source ids

- isimip.isimip3b.mit-tc-wind-rain-fields.20251001

**Provider:** ISIMIP Repository / Potsdam Institute for Climate Impact Research

**Interface type:** web_portal

**Status:** documented_only

**Documentation url:** <https://data.isimip.org/10.48364/ISIMIP.779038>

**Service root:** <https://data.isimip.org>

**Api version:** ISIMIP3b fields v1.0 / family vintage 20251001

## Access scope

- metadata
- catalogue

## Authentication

**Mode:** none

**Credential reference:** `null`

**Registration url:** `null`

**Secret in repository:** `false`

## Request contract

### Allowed operations

- review_pinned_file_metadata

### Path templates

- /files/1d48a26c-8483-4973-a8ba-8a49624abc55/

**Parameter rules:** One published file identity only: h08-wind_mit_mpi-esm1-2-hr_ssp585_windlifetimemax_2025.nc, UUID 1d48a26c-8483-4973-a8ba-8a49624abc55, provider SHA-512 ff9fdc51bf160f88e51a62b4a0508423c9a9ef9d687430332c1ad6c8caf6f3dcffdb50d8891212bfe0a26a69133c7a5b88a5a7a23456e6cecf70c02d2c0289e2. This contract is NOT an executable GET permission; no NetCDF retrieval, DOI crawl, search API, metadata auto-fetch, wildcard request, redirect, or user-configurable URL is allowed. Further asset-specific source, API and upstream licence review is required.

## Response contract

### Expected media types

- text/html

**Format:** ISIMIP publisher HTML describing the exact CC0-labelled NetCDF field and file identity, not a NetCDF byte response.

**Scientific semantics:** Climate-model-conditioned, synthetic TC H08 windlifetimemax field. Confirm native grid, units, time/event/annual aggregation, masks, wind averaging, scenario and interannual dependence from original CF metadata before using physical intensities; no per-risk insured loss, ELT or independent observational truth.

## Operational constraints

**Timeout seconds:** `20`

**Max probe bytes:** `262144`

**Max sample bytes:** `262144`

**Retry policy:** none

**Rate limit notes:** Documentation-only; no live provider request, bulk download or automated enumeration is authorized by this contract.

**Mutability notes:** Version 20251001 and publisher SHA-512 are only stated on the file metadata page; no independently acquired bytes, original response SHA-256, file-size exact integer, event metadata or model approval established.

## Rights and policy

**Dataset rights status:** not_reviewed

**Api terms status:** unknown

**Terms url:** <https://www.isimip.org/gettingstarted/terms-of-use/licenses-publicly-available-isimip-data/>

**Commercial automation status:** unknown

**Redistribution status:** unknown

**Notes:** Provider file page marks the selected derived fields CC0, but the underlying MIT tracks are a legally separate noncommercial product without a commercial licence. Do not download or reconstruct restricted tracks on the strength of field CC0, or grant commercial use or redistribution without exact product lineage and terms review.

## Probe contract

**Mode:** none

**Operation:** `null`

**Requires credentials:** `false`

### Expected evidence

_Empty array._

**Implementation decision:** document_only

**Reviewed at:** 2026-11-15

## Evidence urls

- <https://data.isimip.org/10.48364/ISIMIP.779038>
- <https://data.isimip.org/files/1d48a26c-8483-4973-a8ba-8a49624abc55/>
- <https://data.isimip.org/access/ISIMIP3b/InputData/climate/tropical_cyclones/MIT/tracks/>
- <https://www.isimip.org/gettingstarted/terms-of-use/licenses-publicly-available-isimip-data/>

**Notes:** Documented T0 identity for one exact derived field, preserving the legally distinct restricted upstream track family. The example field was not fetched, hashed, parsed or admitted; next gate is separately reviewed small metadata-only probe with bounded original response SHA-256 and scientific field-schema assessment.
